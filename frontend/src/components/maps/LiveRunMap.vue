<script setup>
import { nextTick, onMounted, ref, watch } from 'vue'
import { MapPinned } from '@lucide/vue'

import { loadKakaoMap } from '../../services/kakaoMap'

const props = defineProps({
  coursePoints: {
    type: Array,
    default: () => [],
  },
  trackedPoints: {
    type: Array,
    default: () => [],
  },
  center: {
    type: Array,
    required: true,
  },
  followCurrent: {
    type: Boolean,
    default: true,
  },
})

const container = ref(null)
const status = ref('loading')
let map
let courseLine
let trackHaloLine
let trackLine
let currentMarker
let kakaoApi

function toLatLng(kakao, point) {
  const latitude = Array.isArray(point) ? Number(point[0]) : Number(point?.latitude)
  const longitude = Array.isArray(point) ? Number(point[1]) : Number(point?.longitude)
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return null
  return new kakao.maps.LatLng(latitude, longitude)
}

function fitVisiblePath() {
  if (!map || !kakaoApi) return
  const visiblePoints = [...props.coursePoints, ...props.trackedPoints]
  if (!visiblePoints.length) return
  const bounds = new kakaoApi.maps.LatLngBounds()
  const path = visiblePoints.map((point) => toLatLng(kakaoApi, point)).filter(Boolean)
  if (!path.length) return
  path.forEach((point) => bounds.extend(point))
  map.relayout()
  if (path.length === 1) {
    map.setCenter(path[0])
    map.setLevel(4)
    return
  }
  map.setBounds(bounds, 34, 34, props.followCurrent ? 34 : 120, 34)
}

async function initialize() {
  try {
    const kakao = await loadKakaoMap()
    kakaoApi = kakao
    await nextTick()
    map = new kakao.maps.Map(container.value, {
      center: new kakao.maps.LatLng(props.center[0], props.center[1]),
      level: 5,
    })
    courseLine = new kakao.maps.Polyline({
      map,
      path: props.coursePoints.map((point) => toLatLng(kakao, point)).filter(Boolean),
      strokeWeight: 5,
      strokeColor: '#8eb8ff',
      strokeOpacity: 0.8,
    })
    trackHaloLine = new kakao.maps.Polyline({
      map,
      path: [],
      strokeWeight: 1,
      strokeColor: '#8eb8ff',
      strokeOpacity: 0,
    })
    trackLine = new kakao.maps.Polyline({
      map,
      path: [],
      strokeWeight: 7,
      strokeColor: '#0866ff',
      strokeOpacity: 1,
    })
    status.value = 'ready'
    updateTrack()
    if (!props.followCurrent || !props.trackedPoints.length) {
      fitVisiblePath()
    }
  } catch {
    status.value = 'error'
  }
}

async function updateTrack() {
  if (!map || status.value !== 'ready' || !props.trackedPoints.length) return
  const kakao = kakaoApi ?? window.kakao
  const path = props.trackedPoints.map((point) => toLatLng(kakao, point)).filter(Boolean)
  if (!path.length) return
  trackHaloLine?.setPath(path)
  trackLine.setPath(path)
  const currentPosition = path[path.length - 1]
  if (!currentMarker) {
    currentMarker = new kakao.maps.Marker({
      map,
      position: currentPosition,
      title: '현재 위치',
    })
  } else {
    currentMarker.setPosition(currentPosition)
  }
  if (props.followCurrent) {
    map.panTo(currentPosition)
  } else {
    fitVisiblePath()
  }
}

onMounted(initialize)
watch(() => props.trackedPoints.length, updateTrack)
watch(() => props.coursePoints.length, fitVisiblePath)
</script>

<template>
  <div class="live-map">
    <div ref="container" class="live-map__canvas"></div>
    <div v-if="status !== 'ready'" class="live-map__state">
      <MapPinned :size="25" />
      <span>{{ status === 'error' ? '지도를 표시하지 못했습니다.' : '지도를 준비 중입니다.' }}</span>
    </div>
  </div>
</template>

<style scoped>
.live-map {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 260px;
  overflow: hidden;
  background: #e8f1fb;
}

.live-map__canvas {
  width: 100%;
  height: 100%;
}

.live-map__state {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  flex-direction: column;
  justify-content: center;
  gap: 8px;
  color: var(--color-primary);
  background: #edf5ff;
}

.live-map__state span {
  color: var(--color-muted);
  font-size: 12px;
}
</style>
