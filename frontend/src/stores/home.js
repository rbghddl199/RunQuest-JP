import { defineStore } from 'pinia'

import api from '../services/api'

export const useHomeStore = defineStore('home', {
  state: () => ({
    dashboard: null,
    isLoading: false,
    errorMessage: '',
  }),
  actions: {
    async loadDashboard(location = null) {
      this.isLoading = true
      this.errorMessage = ''
      try {
        const params = location?.latitude && location?.longitude
          ? {
              latitude: location.latitude,
              longitude: location.longitude,
            }
          : undefined
        const { data } = await api.get('/home/', { params })
        this.dashboard = data
        return data
      } catch (error) {
        this.errorMessage = error.response?.data?.detail
          ?? '홈 정보를 불러오지 못했습니다.'
        return null
      } finally {
        this.isLoading = false
      }
    },
  },
})
