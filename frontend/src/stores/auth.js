import { defineStore } from 'pinia'

import api from '../services/api'

const ACCESS_TOKEN_KEY = 'runquest_access_token'
const REFRESH_TOKEN_KEY = 'runquest_refresh_token'
const REMEMBER_EMAIL_KEY = 'runquest_remembered_email'

function getStoredValue(key) {
  return localStorage.getItem(key) ?? sessionStorage.getItem(key)
}

function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  sessionStorage.removeItem(ACCESS_TOKEN_KEY)
  sessionStorage.removeItem(REFRESH_TOKEN_KEY)
}

function readApiError(error, fallback) {
  const data = error.response?.data
  if (!data) return fallback

  if (typeof data.detail === 'string') return data.detail
  if (Array.isArray(data.non_field_errors)) return data.non_field_errors[0]

  const firstValue = Object.values(data)[0]
  if (Array.isArray(firstValue)) return firstValue[0]
  if (typeof firstValue === 'string') return firstValue

  return fallback
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    isLoading: false,
    isRestoring: false,
    errorMessage: '',
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.user),
    rememberedEmail: () => localStorage.getItem(REMEMBER_EMAIL_KEY) ?? '',
  },
  actions: {
    saveSession(tokens, remember = true) {
      clearTokens()
      const storage = remember ? localStorage : sessionStorage
      storage.setItem(ACCESS_TOKEN_KEY, tokens.access)
      storage.setItem(REFRESH_TOKEN_KEY, tokens.refresh)
    },
    async login(credentials, remember = true) {
      this.isLoading = true
      this.errorMessage = ''

      try {
        const { data } = await api.post('/auth/login/', credentials)
        this.saveSession(data.tokens, remember)
        this.user = data.user
        await api.delete('/chat/conversation/').catch(() => {})
        localStorage.removeItem('runquest_chat_recommendation')

        if (remember) {
          localStorage.setItem(REMEMBER_EMAIL_KEY, credentials.email)
        } else {
          localStorage.removeItem(REMEMBER_EMAIL_KEY)
        }

        return data.user
      } catch (error) {
        this.errorMessage = readApiError(
          error,
          '로그인 중 문제가 발생했습니다. 잠시 후 다시 시도해 주세요.',
        )
        throw error
      } finally {
        this.isLoading = false
      }
    },
    async signup(payload) {
      this.isLoading = true
      this.errorMessage = ''

      try {
        const { data } = await api.post('/auth/signup/', payload)
        this.saveSession(data.tokens, true)
        this.user = data.user
        localStorage.removeItem('runquest_chat_recommendation')
        localStorage.setItem(REMEMBER_EMAIL_KEY, payload.email)
        return data.user
      } catch (error) {
        this.errorMessage = readApiError(
          error,
          '회원가입 중 문제가 발생했습니다. 입력 내용을 확인해 주세요.',
        )
        throw error
      } finally {
        this.isLoading = false
      }
    },
    async checkNickname(nickname) {
      const { data } = await api.get('/auth/nickname-availability/', {
        params: { nickname },
      })
      return data
    },
    async restoreSession() {
      if (this.user || !getStoredValue(REFRESH_TOKEN_KEY)) return

      this.isRestoring = true
      try {
        const { data } = await api.get('/auth/me/')
        this.user = data
      } catch {
        clearTokens()
        this.user = null
      } finally {
        this.isRestoring = false
      }
    },
    async logout() {
      const refresh = getStoredValue(REFRESH_TOKEN_KEY)

      try {
        await api.delete('/chat/conversation/').catch(() => {})
        if (refresh) {
          await api.post('/auth/logout/', { refresh })
        }
      } finally {
        clearTokens()
        this.user = null
      }
    },
  },
})
