import { defineStore } from 'pinia'

import api from '../services/api'

export const useProfileStore = defineStore('profile', {
  state: () => ({
    summary: null,
    records: [],
    attendance: null,
    badges: [],
    badge: null,
    isLoading: false,
    errorMessage: '',
  }),
  actions: {
    async request(callback) {
      this.isLoading = true
      this.errorMessage = ''
      try {
        return await callback()
      } catch (error) {
        this.errorMessage = error.response?.data?.detail
          ?? '정보를 불러오지 못했습니다.'
        throw error
      } finally {
        this.isLoading = false
      }
    },
    async loadSummary() {
      return this.request(async () => {
        const { data } = await api.get('/profile/summary/')
        this.summary = data
        return data
      })
    },
    async loadRecords() {
      return this.request(async () => {
        const { data } = await api.get('/profile/records/')
        this.records = data
        return data
      })
    },
    async deleteRecord(recordId) {
      return this.request(async () => {
        await api.delete(`/runs/${recordId}/`)
        this.records = this.records.filter((record) => record.id !== recordId)
        return true
      })
    },
    async loadAttendance(year, month) {
      return this.request(async () => {
        const { data } = await api.get('/profile/attendance/', {
          params: { year, month },
        })
        this.attendance = data
        return data
      })
    },
    async loadBadges() {
      return this.request(async () => {
        const { data } = await api.get('/profile/badges/')
        this.badges = data
        return data
      })
    },
    async loadBadge(code) {
      return this.request(async () => {
        const { data } = await api.get(`/profile/badges/${code}/`)
        this.badge = data
        return data
      })
    },
  },
})
