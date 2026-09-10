import { defineStore } from 'pinia'

import api from '../services/api'
import { useAuthStore } from './auth'

function readError(error, fallback) {
  const data = error.response?.data
  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail

  const first = Object.values(data)[0]
  if (Array.isArray(first)) return first[0]
  if (typeof first === 'string') return first
  return fallback
}

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    settings: null,
    isLoading: false,
    isSaving: false,
    errorMessage: '',
    successMessage: '',
  }),
  actions: {
    async loadSettings() {
      this.isLoading = true
      this.errorMessage = ''
      try {
        const { data } = await api.get('/auth/settings/')
        this.settings = data
        return data
      } catch (error) {
        this.errorMessage = readError(error, '설정을 불러오지 못했습니다.')
        throw error
      } finally {
        this.isLoading = false
      }
    },
    async saveSettings(payload) {
      this.isSaving = true
      this.errorMessage = ''
      this.successMessage = ''
      try {
        const { data } = await api.patch('/auth/settings/', payload)
        this.settings = data

        const authStore = useAuthStore()
        if (authStore.user?.profile) {
          authStore.user.profile.nickname = data.nickname
        }
        this.successMessage = '설정이 저장되었습니다.'
        return data
      } catch (error) {
        this.errorMessage = readError(error, '설정을 저장하지 못했습니다.')
        throw error
      } finally {
        this.isSaving = false
      }
    },
    async changePassword(payload) {
      this.isSaving = true
      this.errorMessage = ''
      this.successMessage = ''
      try {
        const { data } = await api.post('/auth/password/change/', payload)
        this.successMessage = data.detail
        return data
      } catch (error) {
        this.errorMessage = readError(error, '비밀번호를 변경하지 못했습니다.')
        throw error
      } finally {
        this.isSaving = false
      }
    },
  },
})
