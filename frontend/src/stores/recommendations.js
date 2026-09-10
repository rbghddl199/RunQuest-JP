import { defineStore } from 'pinia'

import api from '../services/api'

const CHAT_RECOMMENDATION_KEY = 'runquest_chat_recommendation'

function readChatRecommendation() {
  try {
    return JSON.parse(localStorage.getItem(CHAT_RECOMMENDATION_KEY) ?? 'null')
  } catch {
    return null
  }
}

export const useRecommendationStore = defineStore('recommendations', {
  state: () => ({
    session: null,
    recommendation: null,
    isLoading: false,
    isAdvancing: false,
    errorMessage: '',
    location: null,
    locationStatus: 'idle',
  }),
  getters: {
    course: (state) => state.recommendation?.course ?? null,
  },
  actions: {
    applyResponse(data) {
      this.session = data.session
      this.recommendation = data.recommendation
    },
    applyChatRecommendation(message) {
      if (!message?.recommended_course) return
      const data = {
        session: {
          id: `chat-${message.id}`,
          user_state: 'chat',
          current_position: 1,
          total_items: 1,
          location: {
            applied: Boolean(message.metadata?.location?.applied),
            distance_km: message.metadata?.location?.distance_km ?? null,
          },
        },
        recommendation: {
          rank: 1,
          total_score: message.metadata?.score ?? null,
          reasons: message.metadata?.reasons ?? [],
          score_details: {
            location: message.metadata?.location ?? {
              applied: false,
              distance_km: null,
            },
          },
          course: message.recommended_course,
        },
        created_at: message.created_at,
      }
      localStorage.setItem(CHAT_RECOMMENDATION_KEY, JSON.stringify(data))
      this.applyResponse(data)
    },
    clearChatRecommendation() {
      localStorage.removeItem(CHAT_RECOMMENDATION_KEY)
    },
    resolveLocation() {
      if (!navigator.geolocation) {
        this.locationStatus = 'unsupported'
        return Promise.resolve(null)
      }
      this.locationStatus = 'loading'
      return new Promise((resolve) => {
        navigator.geolocation.getCurrentPosition(
          ({ coords }) => {
            this.location = {
              latitude: coords.latitude,
              longitude: coords.longitude,
            }
            this.locationStatus = 'ready'
            resolve(this.location)
          },
          () => {
            this.locationStatus = 'denied'
            resolve(null)
          },
          { enableHighAccuracy: false, timeout: 6000, maximumAge: 300000 },
        )
      })
    },
    locationChanged(sessionLocation) {
      if (!this.location || !sessionLocation?.applied) return Boolean(this.location)
      const latitudeGap = Math.abs(this.location.latitude - sessionLocation.latitude)
      const longitudeGap = Math.abs(this.location.longitude - sessionLocation.longitude)
      return latitudeGap > 0.01 || longitudeGap > 0.01
    },
    async loadOrGenerate() {
      this.isLoading = true
      this.errorMessage = ''
      const location = await this.resolveLocation()

      try {
        await this.generate(location)
      } catch (error) {
        this.errorMessage = error.response?.data?.detail
          ?? '맞춤 추천을 불러오지 못했습니다.'
      } finally {
        this.isLoading = false
      }
    },
    async loadCurrent() {
      this.isLoading = true
      this.errorMessage = ''

      try {
        const { data } = await api.get('/recommendations/current/')
        this.applyResponse(data)
        return true
      } catch (error) {
        if (error.response?.status === 404) {
          this.session = null
          this.recommendation = null
          return false
        }
        this.errorMessage = error.response?.data?.detail
          ?? '맞춤 추천을 불러오지 못했습니다.'
        return false
      } finally {
        this.isLoading = false
      }
    },
    async generate(location = this.location) {
      this.isLoading = true
      this.errorMessage = ''
      try {
        const { data } = await api.post(
          '/recommendations/generate/',
          location ?? {},
        )
        localStorage.removeItem(CHAT_RECOMMENDATION_KEY)
        this.applyResponse(data)
      } catch (error) {
        this.errorMessage = error.response?.data?.detail
          ?? '맞춤 추천을 생성하지 못했습니다.'
      } finally {
        this.isLoading = false
      }
    },
    async requestLocationAndRegenerate() {
      const location = await this.resolveLocation()
      if (location) {
        await this.generate(location)
      }
    },
    async regenerateWithDefaultSystem() {
      this.clearChatRecommendation()
      const location = await this.resolveLocation()
      await this.generate(location)
    },
    async recommendAgain() {
      if (!this.session) {
        await this.regenerateWithDefaultSystem()
        return
      }
      if (this.session?.user_state === 'chat') {
        await this.regenerateWithDefaultSystem()
        return
      }
      await this.next()
    },
    async next() {
      if (this.isAdvancing) return

      this.isAdvancing = true
      this.errorMessage = ''
      try {
        const location = await this.resolveLocation()
        const { data } = await api.post('/recommendations/next/', location ?? {})
        this.applyResponse(data)
        this.clearChatRecommendation()
      } catch {
        this.errorMessage = '다음 추천을 불러오지 못했습니다.'
      } finally {
        this.isAdvancing = false
      }
    },
    loadChatRecommendation() {
      const data = readChatRecommendation()
      if (!data?.recommendation?.course) return false
      this.applyResponse(data)
      return true
    },
  },
})
