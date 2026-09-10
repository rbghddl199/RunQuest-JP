import { defineStore } from 'pinia'

import api from '../services/api'
import { calculateDistanceKm } from '../utils/running'

const CACHE_KEY = 'runquest_active_run'

function normalizeRoutePoint(point) {
  if (Array.isArray(point)) {
    return {
      latitude: Number(point[0]),
      longitude: Number(point[1]),
    }
  }
  return {
    latitude: Number(point?.latitude),
    longitude: Number(point?.longitude),
  }
}

function interpolatePoint(points, progress) {
  const scaledIndex = Math.min(points.length - 1, Math.max(0, progress) * (points.length - 1))
  const startIndex = Math.floor(scaledIndex)
  const endIndex = Math.min(points.length - 1, startIndex + 1)
  const ratio = scaledIndex - startIndex
  const start = points[startIndex]
  const end = points[endIndex]

  return {
    latitude: start.latitude + (end.latitude - start.latitude) * ratio,
    longitude: start.longitude + (end.longitude - start.longitude) * ratio,
  }
}

function buildFallbackRoute(position) {
  const origin = position && Number.isFinite(Number(position.latitude)) && Number.isFinite(Number(position.longitude))
    ? {
      latitude: Number(position.latitude),
      longitude: Number(position.longitude),
    }
    : {
      latitude: 36.3504,
      longitude: 127.3845,
    }

  return [
    origin,
    { latitude: origin.latitude + 0.00045, longitude: origin.longitude + 0.00035 },
    { latitude: origin.latitude + 0.00082, longitude: origin.longitude + 0.00008 },
    { latitude: origin.latitude + 0.00045, longitude: origin.longitude - 0.00032 },
    origin,
  ]
}

function readCache() {
  try {
    return JSON.parse(localStorage.getItem(CACHE_KEY) ?? 'null')
  } catch {
    return null
  }
}

export const useRunningStore = defineStore('running', {
  state: () => ({
    record: readCache(),
    points: readCache()?.track_points ?? [],
    elapsedSeconds: readCache()?.duration_seconds ?? 0,
    pausedSeconds: readCache()?.paused_seconds ?? 0,
    isPaused: readCache()?.status === 'paused',
    isStarting: false,
    isFinishing: false,
    trackingError: '',
    completedResult: null,
    watchId: null,
    timerId: null,
    simulationId: null,
    simulationIndex: 0,
    lastSyncPointCount: 0,
  }),
  getters: {
    distanceKm: (state) => calculateDistanceKm(state.points),
    paceSeconds() {
      return this.distanceKm > 0
        ? Math.round(this.elapsedSeconds / this.distanceKm)
        : 0
    },
    isActive: (state) => Boolean(
      state.record
      && ['active', 'paused'].includes(state.record.status),
    ),
  },
  actions: {
    cache() {
      if (!this.record) {
        localStorage.removeItem(CACHE_KEY)
        return
      }
      localStorage.setItem(
        CACHE_KEY,
        JSON.stringify({
          ...this.record,
          track_points: this.points,
          duration_seconds: this.elapsedSeconds,
          paused_seconds: this.pausedSeconds,
          status: this.isPaused ? 'paused' : 'active',
        }),
      )
    },
    async restoreActive() {
      try {
        const { data } = await api.get('/runs/active/')
        this.record = data
        this.points = data.track_points ?? []
        this.elapsedSeconds = data.duration_seconds
        this.pausedSeconds = data.paused_seconds
        this.isPaused = data.status === 'paused'
        this.lastSyncPointCount = this.points.length
        this.cache()
        return data
      } catch (error) {
        if (error.response?.status === 404) {
          this.reset()
        }
        return null
      }
    },
    async start(courseSlug, trackingMode, customCourseId = null) {
      this.isStarting = true
      this.trackingError = ''
      try {
        const { data } = await api.post('/runs/start/', {
          course_slug: courseSlug || null,
          custom_course_id: customCourseId,
          tracking_mode: trackingMode,
        })
        this.record = data
        this.points = data.track_points ?? []
        this.elapsedSeconds = data.duration_seconds
        this.pausedSeconds = data.paused_seconds
        this.isPaused = data.status === 'paused'
        this.lastSyncPointCount = this.points.length
        this.cache()
        return data
      } catch {
        this.trackingError = '러닝을 시작하지 못했습니다.'
        return null
      } finally {
        this.isStarting = false
      }
    },
    beginTracking(course, fallbackPosition = null) {
      this.stopTracking()
      this.startTimer()
      if (this.record.tracking_mode === 'simulation') {
        this.startSimulation(
          course?.route_points ?? [],
          course?.estimated_minutes ?? 30,
          fallbackPosition,
        )
      } else {
        this.startGps()
      }
    },
    startTimer() {
      this.timerId = window.setInterval(() => {
        if (this.isPaused) {
          this.pausedSeconds += 1
        } else if (this.record?.tracking_mode !== 'simulation') {
          this.elapsedSeconds += 1
        }
        this.cache()
      }, 1000)
    },
    startGps() {
      if (!navigator.geolocation) {
        this.trackingError = '이 브라우저는 GPS 위치 추적을 지원하지 않습니다.'
        return
      }
      this.watchId = navigator.geolocation.watchPosition(
        (position) => {
          if (this.isPaused || position.coords.accuracy > 50) return
          this.points.push({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            timestamp: position.timestamp,
          })
          this.cache()
          if (this.points.length - this.lastSyncPointCount >= 5) {
            this.syncProgress()
          }
        },
        (error) => {
          const messages = {
            1: '위치 권한이 거부되었습니다. 브라우저 설정에서 허용해 주세요.',
            2: '현재 위치를 확인할 수 없습니다.',
            3: '위치 확인 시간이 초과되었습니다.',
          }
          this.trackingError = messages[error.code] ?? 'GPS 연결에 실패했습니다.'
        },
        {
          enableHighAccuracy: true,
          maximumAge: 3000,
          timeout: 10000,
        },
      )
    },
    startSimulation(routePoints, estimatedMinutes, fallbackPosition = null) {
      const rawPoints = routePoints.length >= 2
        ? routePoints
        : buildFallbackRoute(fallbackPosition)
      const points = rawPoints
        .map(normalizeRoutePoint)
        .filter((point) => Number.isFinite(point.latitude) && Number.isFinite(point.longitude))

      if (points.length < 2) {
        this.trackingError = '시뮬레이션 경로를 만들 수 없습니다. 코스 좌표를 확인해 주세요.'
        return
      }

      const totalSeconds = Math.max(60, Math.round(Number(estimatedMinutes || 30) * 60))
      if (!this.points.length) {
        this.points.push({
          ...points[0],
          accuracy: 5,
          timestamp: Date.now(),
        })
        this.cache()
      }
      this.simulationId = window.setInterval(() => {
        if (this.isPaused) return
        if (this.elapsedSeconds >= totalSeconds) {
          window.clearInterval(this.simulationId)
          this.simulationId = null
          return
        }
        this.elapsedSeconds += 1
        const progress = Math.min(1, this.elapsedSeconds / totalSeconds)
        const { latitude, longitude } = interpolatePoint(points, progress)
        this.points.push({
          latitude,
          longitude,
          accuracy: 5,
          timestamp: Date.now(),
        })
        this.cache()
        if (this.points.length - this.lastSyncPointCount >= 5) {
          this.syncProgress()
        }
      }, 1000)
    },
    async syncProgress() {
      if (!this.record) return
      try {
        await api.patch(`/runs/${this.record.id}/progress/`, {
          track_points: this.points.slice(this.lastSyncPointCount),
          duration_seconds: this.elapsedSeconds,
          paused_seconds: this.pausedSeconds,
          status: this.isPaused ? 'paused' : 'active',
        })
        this.lastSyncPointCount = this.points.length
      } catch {
        this.trackingError = '기록을 서버에 임시 저장하지 못했습니다.'
      }
    },
    async togglePause() {
      this.isPaused = !this.isPaused
      this.record.status = this.isPaused ? 'paused' : 'active'
      this.cache()
      await this.syncProgress()
    },
    async finish() {
      if (!this.record || this.isFinishing) return null
      this.isFinishing = true
      this.stopTracking()
      try {
        const { data } = await api.post(`/runs/${this.record.id}/finish/`, {
          track_points: this.points.slice(this.lastSyncPointCount),
          duration_seconds: this.elapsedSeconds,
          paused_seconds: this.pausedSeconds,
        })
        if (data.cancelled) {
          this.trackingError = data.detail ?? '100m 이상 이동한 러닝만 기록으로 저장됩니다.'
          this.record = null
          this.completedResult = null
          localStorage.removeItem(CACHE_KEY)
          return data
        }
        this.completedResult = data
        this.record = data.record
        localStorage.removeItem(CACHE_KEY)
        return data
      } catch (error) {
        this.trackingError = error.response?.data?.detail ?? '러닝 완료 기록을 저장하지 못했습니다.'
        if (typeof window !== 'undefined' && error.response?.status === 400) {
          window.alert(this.trackingError)
        }
        return null
      } finally {
        this.isFinishing = false
      }
    },
    stopTracking() {
      if (this.watchId !== null) {
        navigator.geolocation?.clearWatch(this.watchId)
      }
      window.clearInterval(this.timerId)
      window.clearInterval(this.simulationId)
      this.watchId = null
      this.timerId = null
      this.simulationId = null
    },
    reset() {
      this.stopTracking()
      this.record = null
      this.points = []
      this.elapsedSeconds = 0
      this.pausedSeconds = 0
      this.isPaused = false
      this.trackingError = ''
      this.completedResult = null
      this.lastSyncPointCount = 0
      localStorage.removeItem(CACHE_KEY)
    },
  },
})
