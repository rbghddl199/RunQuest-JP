import { defineStore } from 'pinia'

import api from '../services/api'

export const useNotificationStore = defineStore('notifications', {
  state: () => ({
    notifications: [],
    unreadCount: 0,
    isLoading: false,
    errorMessage: '',
  }),
  actions: {
    targetLink(notification) {
      if (notification?.link) return notification.link
      const metadata = notification?.metadata ?? {}
      if (metadata.post_id) return `/community/${metadata.post_id}`
      if (metadata.comment_id && metadata.post_id) return `/community/${metadata.post_id}`
      if (metadata.badge_code) return `/my/badges/${metadata.badge_code}`
      if (metadata.record_id) return `/run/completed/${metadata.record_id}`
      if (metadata.course_slug) return `/courses/${metadata.course_slug}`
      if (notification?.notification_type === 'recommendation') return '/recommendations'
      if (notification?.notification_type === 'comment' || notification?.notification_type === 'like') return '/community'
      if (notification?.notification_type === 'badge') return '/my/badges'
      return ''
    },
    async load() {
      this.isLoading = true
      this.errorMessage = ''
      try {
        const { data } = await api.get('/notifications/')
        this.notifications = data.notifications
        this.unreadCount = data.unread_count
      } catch (error) {
        this.errorMessage = error.response?.data?.detail
          ?? '알림을 불러오지 못했습니다.'
      } finally {
        this.isLoading = false
      }
    },
    async markRead(notification) {
      if (!notification.is_read) {
        const { data } = await api.post(`/notifications/${notification.id}/read/`)
        notification.is_read = true
        this.unreadCount = data.unread_count
      }
    },
    async markAllRead() {
      await api.post('/notifications/read-all/')
      this.notifications.forEach((item) => { item.is_read = true })
      this.unreadCount = 0
    },
  },
})
