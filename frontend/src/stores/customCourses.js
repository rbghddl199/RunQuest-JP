import { defineStore } from 'pinia'

import api from '../services/api'

export const useCustomCourseStore = defineStore('customCourses', {
  state: () => ({
    courses: [],
    currentCourse: null,
    favoriteCourses: [],
    isLoading: false,
    isUploading: false,
    errorMessage: '',
  }),
  actions: {
    async loadCourses() {
      this.isLoading = true
      this.errorMessage = ''
      try {
        const { data } = await api.get('/custom-courses/')
        this.courses = data
      } catch {
        this.errorMessage = '나의 코스를 불러오지 못했습니다.'
      } finally {
        this.isLoading = false
      }
    },
    async loadCourse(id) {
      this.isLoading = true
      try {
        const { data } = await api.get(`/custom-courses/${id}/`)
        this.currentCourse = data
        return data
      } catch {
        this.errorMessage = '나의 코스를 찾을 수 없습니다.'
        return null
      } finally {
        this.isLoading = false
      }
    },
    async uploadCourse(payload) {
      this.isUploading = true
      this.errorMessage = ''
      try {
        const body = new FormData()
        body.append('name', payload.name)
        body.append('description', payload.description)
        body.append('visibility', payload.visibility)
        body.append('gpx_file', payload.file)
        const { data } = await api.post('/custom-courses/', body, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
        this.courses.unshift(data)
        return data
      } catch (error) {
        const response = error.response?.data
        this.errorMessage = response
          ? Object.values(response).flat()[0]
          : 'GPX 코스를 저장하지 못했습니다.'
        return null
      } finally {
        this.isUploading = false
      }
    },
    async createDrawnCourse(payload) {
      this.isUploading = true
      this.errorMessage = ''
      try {
        const { data } = await api.post('/custom-courses/', payload)
        this.courses.unshift(data)
        return data
      } catch (error) {
        this.errorMessage = error.response?.data?.route?.[0]
          ?? error.response?.data?.name?.[0]
          ?? '코스를 저장하지 못했습니다.'
        throw error
      } finally {
        this.isUploading = false
      }
    },
    async deleteCourse(id) {
      await api.delete(`/custom-courses/${id}/`)
      this.courses = this.courses.filter((course) => course.id !== id)
    },
    async loadFavorites() {
      this.isLoading = true
      try {
        const { data } = await api.get('/courses/favorites/')
        this.favoriteCourses = data
      } catch {
        this.errorMessage = '찜한 코스를 불러오지 못했습니다.'
      } finally {
        this.isLoading = false
      }
    },
  },
})
