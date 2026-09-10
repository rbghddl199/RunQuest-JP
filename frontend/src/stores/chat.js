import { defineStore } from 'pinia'

import api from '../services/api'

export const useChatStore = defineStore('chat', {
  state: () => ({
    messages: [],
    context: {},
    cachedLocation: null,
    cachedLocationAt: 0,
    isLoading: false,
    isSending: false,
    errorMessage: '',
  }),
  actions: {
    resolveLocation(timeout = 1200) {
      if (
        this.cachedLocation
        && Date.now() - this.cachedLocationAt < 5 * 60 * 1000
      ) {
        return Promise.resolve(this.cachedLocation)
      }
      if (!navigator.geolocation) return Promise.resolve(null)
      return new Promise((resolve) => {
        let settled = false
        const timer = window.setTimeout(() => {
          if (settled) return
          settled = true
          resolve(null)
        }, timeout)
        navigator.geolocation.getCurrentPosition(
          ({ coords }) => {
            if (settled) return
            settled = true
            window.clearTimeout(timer)
            this.cachedLocation = {
              latitude: coords.latitude,
              longitude: coords.longitude,
            }
            this.cachedLocationAt = Date.now()
            resolve(this.cachedLocation)
          },
          () => {
            if (settled) return
            settled = true
            window.clearTimeout(timer)
            resolve(null)
          },
          { enableHighAccuracy: false, timeout, maximumAge: 300000 },
        )
      })
    },
    async loadConversation() {
      this.isLoading = true
      this.errorMessage = ''
      try {
        const { data } = await api.get('/chat/conversation/')
        this.messages = data.messages.filter((item) => item.intent !== 'welcome')
        this.context = data.context
      } catch {
        this.errorMessage = '대화를 불러오지 못했습니다.'
      } finally {
        this.isLoading = false
      }
    },
    async send(content) {
      if (!content.trim() || this.isSending) return null
      this.isSending = true
      this.errorMessage = ''
      const trimmed = content.trim()
      const temporaryId = `local-${Date.now()}`
      this.messages.push({
        id: temporaryId,
        role: 'user',
        content: trimmed,
        intent: '',
        recommended_course: null,
        metadata: {},
        created_at: new Date().toISOString(),
      })
      try {
        const location = await this.resolveLocation()
        const { data } = await api.post(
          '/chat/conversation/',
          {
            content: trimmed,
            ...(location ?? {}),
          },
          { timeout: 35000 },
        )
        const index = this.messages.findIndex((item) => item.id === temporaryId)
        if (index >= 0) {
          this.messages.splice(index, 1, data.user_message)
        }
        this.messages.push(data.assistant_message)
        this.context = data.context
        return data.assistant_message
      } catch (error) {
        this.messages = this.messages.filter((item) => item.id !== temporaryId)
        this.errorMessage = error.response?.data?.content?.[0]
          ?? '답변을 생성하지 못했어요. 잠시 후 다시 시도해 주세요.'
        return null
      } finally {
        this.isSending = false
      }
    },
    async reset() {
      await api.delete('/chat/conversation/')
      this.messages = []
      this.context = {}
    },
  },
})
