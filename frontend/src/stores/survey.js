import { defineStore } from 'pinia'

import api from '../services/api'
import { useAuthStore } from './auth'

const DRAFT_KEY = 'runquest_survey_draft'

function loadDraft() {
  try {
    return JSON.parse(sessionStorage.getItem(DRAFT_KEY) ?? '{}')
  } catch {
    return {}
  }
}

export const useSurveyStore = defineStore('survey', {
  state: () => ({
    questions: [],
    answers: loadDraft(),
    isLoading: false,
    isSubmitting: false,
    errorMessage: '',
    result: null,
  }),
  getters: {
    answeredCount: (state) => Object.values(state.answers).filter(Boolean).length,
    isComplete() {
      return this.questions.length > 0 && this.answeredCount === this.questions.length
    },
  },
  actions: {
    async loadQuestions() {
      if (this.questions.length) return

      this.isLoading = true
      this.errorMessage = ''
      try {
        const { data } = await api.get('/survey/questions/')
        this.questions = data.questions
      } catch {
        this.errorMessage = '설문 문항을 불러오지 못했습니다.'
      } finally {
        this.isLoading = false
      }
    },
    selectAnswer(key, value) {
      this.answers[key] = value
      sessionStorage.setItem(DRAFT_KEY, JSON.stringify(this.answers))
    },
    async loadSavedResponse() {
      try {
        const { data } = await api.get('/survey/response/')
        const answerKeys = [
          'experience_level',
          'distance_range',
          'course_type',
          'preferred_time',
          'running_style',
          'running_goal',
        ]
        this.answers = Object.fromEntries(
          answerKeys.map((key) => [key, data[key]]),
        )
        this.result = data
        sessionStorage.setItem(DRAFT_KEY, JSON.stringify(this.answers))
      } catch (error) {
        if (error.response?.status !== 404) {
          this.errorMessage = '기존 설문 응답을 불러오지 못했습니다.'
        }
      }
    },
    async submit() {
      if (!this.isComplete) {
        this.errorMessage = '모든 문항에 답변해 주세요.'
        return null
      }

      this.isSubmitting = true
      this.errorMessage = ''
      try {
        const { data } = await api.post('/survey/response/', this.answers)
        this.result = data.survey
        const authStore = useAuthStore()
        authStore.user = data.user
        sessionStorage.removeItem(DRAFT_KEY)
        return data.survey
      } catch {
        this.errorMessage = '설문 저장 중 문제가 발생했습니다. 다시 시도해 주세요.'
        return null
      } finally {
        this.isSubmitting = false
      }
    },
  },
})
