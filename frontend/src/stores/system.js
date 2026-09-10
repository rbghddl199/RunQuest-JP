import { defineStore } from 'pinia'

import api from '../services/api'

export const useSystemStore = defineStore('system', {
  state: () => ({
    apiStatus: 'idle',
    serviceName: '',
    errorMessage: '',
  }),
  actions: {
    async checkApi() {
      this.apiStatus = 'loading'
      this.errorMessage = ''

      try {
        const { data } = await api.get('/health/')
        this.apiStatus = data.status === 'ok' ? 'connected' : 'error'
        this.serviceName = data.service
      } catch {
        this.apiStatus = 'error'
        this.errorMessage = 'Django 서버 연결을 확인해 주세요.'
      }
    },
  },
})
