import { defineStore } from 'pinia'

import api from '../services/api'

export const useCourseStore = defineStore('courses', {
  state: () => ({
    courses: [],
    currentCourse: null,
    isLoading: false,
    errorMessage: '',
  }),
  getters: {
    featuredCourse: (state) => state.courses[0] ?? null,
  },
  actions: {
    async loadCourses(params = {}) {
      this.isLoading = true
      this.errorMessage = ''
      try {
        const { data } = await api.get('/courses/', { params })
        this.courses = data.courses
      } catch {
        this.errorMessage = '대전 러닝 코스를 불러오지 못했습니다.'
      } finally {
        this.isLoading = false
      }
    },
    async loadCourse(slug) {
      this.isLoading = true
      this.errorMessage = ''
      try {
        const { data } = await api.get(`/courses/${slug}/`)
        this.currentCourse = data
        return data
      } catch {
        this.errorMessage = '코스 상세 정보를 불러오지 못했습니다.'
        return null
      } finally {
        this.isLoading = false
      }
    },
    async toggleFavorite(course) {
      const nextValue = !course.is_favorite
      course.is_favorite = nextValue

      try {
        if (nextValue) {
          await api.post(`/courses/${course.slug}/favorite/`)
        } else {
          await api.delete(`/courses/${course.slug}/favorite/`)
        }
      } catch {
        course.is_favorite = !nextValue
        this.errorMessage = '찜 상태를 변경하지 못했습니다.'
      }
    },
  },
})
