import { defineStore } from 'pinia'

import api from '../services/api'

function firstErrorMessage(response, fallback) {
  if (!response) return fallback
  if (typeof response.detail === 'string') return response.detail
  const first = Object.values(response).flat()[0]
  return typeof first === 'string' ? first : fallback
}

export const useCommunityStore = defineStore('community', {
  state: () => ({
    posts: [],
    post: null,
    isLoading: false,
    isSubmitting: false,
    errorMessage: '',
    postsRequestId: 0,
    hasLoadedPosts: false,
    hasMorePosts: false,
    nextOffset: 0,
    lastParams: {},
  }),
  actions: {
    async loadPosts(params = {}, options = {}) {
      const requestId = this.postsRequestId + 1
      this.postsRequestId = requestId
      const append = options.append === true
      this.isLoading = true
      this.errorMessage = ''
      try {
        const { data } = await api.get('/community/posts/', { params })
        if (requestId === this.postsRequestId) {
          const results = Array.isArray(data) ? data : data.results
          this.posts = append ? [...this.posts, ...results] : results
          this.hasMorePosts = Array.isArray(data) ? false : Boolean(data.has_more)
          this.nextOffset = Array.isArray(data) ? this.posts.length : data.next_offset
          this.lastParams = { ...params }
          this.hasLoadedPosts = true
        }
        return data
      } catch (error) {
        if (requestId === this.postsRequestId) {
          this.errorMessage = firstErrorMessage(
            error.response?.data,
            '게시글을 불러오지 못했습니다.',
          )
        }
        return []
      } finally {
        if (requestId === this.postsRequestId) {
          this.isLoading = false
        }
      }
    },
    loadMorePosts() {
      if (!this.hasMorePosts || this.isLoading) return Promise.resolve(null)
      return this.loadPosts(
        { ...this.lastParams, offset: this.nextOffset },
        { append: true },
      )
    },
    async loadPost(id) {
      this.isLoading = true
      this.errorMessage = ''
      try {
        const { data } = await api.get(`/community/posts/${id}/`)
        this.post = data
        return data
      } catch (error) {
        this.errorMessage = firstErrorMessage(
          error.response?.data,
          '게시글을 찾을 수 없습니다.',
        )
        return null
      } finally {
        this.isLoading = false
      }
    },
    async createPost(payload) {
      this.isSubmitting = true
      this.errorMessage = ''
      try {
        const { data } = await api.post('/community/posts/', payload)
        this.posts.unshift(data)
        return data
      } catch (error) {
        this.errorMessage = firstErrorMessage(
          error.response?.data,
          '게시글을 등록하지 못했습니다.',
        )
        return null
      } finally {
        this.isSubmitting = false
      }
    },
    async updatePost(id, payload) {
      this.isSubmitting = true
      this.errorMessage = ''
      try {
        const { data } = await api.patch(`/community/posts/${id}/`, payload)
        this.post = data
        const index = this.posts.findIndex((item) => item.id === data.id)
        if (index >= 0) this.posts[index] = data
        return data
      } catch (error) {
        this.errorMessage = firstErrorMessage(
          error.response?.data,
          '게시글을 수정하지 못했습니다.',
        )
        return null
      } finally {
        this.isSubmitting = false
      }
    },
    async deletePost(id) {
      this.errorMessage = ''
      try {
        await api.delete(`/community/posts/${id}/`)
        this.posts = this.posts.filter((item) => item.id !== id)
        if (this.post?.id === id) this.post = null
        return true
      } catch (error) {
        this.errorMessage = firstErrorMessage(
          error.response?.data,
          '게시글을 삭제하지 못했습니다.',
        )
        return false
      }
    },
    async toggleLike(post = this.post) {
      const { data } = await api.post(`/community/posts/${post.id}/like/`)
      post.is_liked = data.is_liked
      post.like_count = data.like_count
    },
    async toggleSave(post = this.post) {
      const { data } = await api.post(`/community/posts/${post.id}/save/`)
      post.is_saved = data.is_saved
    },
    async addComment(content) {
      const { data } = await api.post(
        `/community/posts/${this.post.id}/comments/`,
        { content },
      )
      this.post.comments.push(data)
      this.post.comment_count += 1
      return data
    },
    async updateComment(comment, content) {
      const { data } = await api.patch(`/community/comments/${comment.id}/`, {
        content,
      })
      const index = this.post.comments.findIndex((item) => item.id === comment.id)
      if (index >= 0) this.post.comments[index] = data
      return data
    },
    async toggleCommentLike(comment) {
      const { data } = await api.post(`/community/comments/${comment.id}/like/`)
      comment.is_liked = data.is_liked
      comment.like_count = data.like_count
    },
    async deleteComment(comment) {
      await api.delete(`/community/comments/${comment.id}/`)
      this.post.comments = this.post.comments.filter((item) => item.id !== comment.id)
      this.post.comment_count -= 1
    },
  },
})
