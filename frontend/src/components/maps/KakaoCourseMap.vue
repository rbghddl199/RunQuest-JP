<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { Coffee, LocateFixed, MapPinned } from '@lucide/vue'

import { loadKakaoMap } from '../../services/kakaoMap'

const props = defineProps({
  routePoints: { type: Array, default: () => [] },
  startLatitude: { type: [String, Number], default: null },
  startLongitude: { type: [String, Number], default: null },
  currentLatitude: { type: [String, Number], default: null },
  currentLongitude: { type: [String, Number], default: null },
  level: { type: Number, default: 5 },
  courseName: { type: String, default: '' },
  courseDistance: { type: [String, Number], default: null },
  courseMinutes: { type: [String, Number], default: null },
  courseDifficulty: { type: String, default: '' },
  showCourseCard: { type: Boolean, default: false },
  showFacilitiesToggle: { type: Boolean, default: false },
  focusStart: { type: Boolean, default: false },
})

const mapContainer = ref(null)
const mapStatus = ref('loading')
const facilitiesVisible = ref(false)
const facilitySearchStatus = ref('idle')

let map = null
let kakaoApi = null
let routePolyline = null
let routeOverlays = []
let currentOverlay = null
let facilityOverlays = []
let renderId = 0

const facilityQueries = [
  { keyword: '화장실', label: 'WC', tone: 'toilet' },
  { keyword: '편의점', label: '편의점', tone: 'store' },
  { keyword: '카페', label: '카페', tone: 'cafe' },
]

const hasRoute = computed(() => props.routePoints.length >= 2)
const hasStart = computed(() => (
  props.startLatitude !== null
  && props.startLongitude !== null
  && Number.isFinite(Number(props.startLatitude))
  && Number.isFinite(Number(props.startLongitude))
))
const hasCurrentLocation = computed(() => (
  props.currentLatitude !== null
  && props.currentLongitude !== null
  && Number.isFinite(Number(props.currentLatitude))
  && Number.isFinite(Number(props.currentLongitude))
))
const overlayTitle = computed(() => props.courseName || '러닝 코스')
const overlayMeta = computed(() => [
  props.courseDistance !== null ? `${props.courseDistance}km` : '',
  props.courseMinutes !== null ? `예상 ${props.courseMinutes}분` : '',
  props.courseDifficulty,
].filter(Boolean).join(' / '))

function clearOverlays(items) {
  items.forEach((overlay) => overlay.setMap(null))
  items.length = 0
}

function clearRoute() {
  if (routePolyline) {
    routePolyline.setMap(null)
    routePolyline = null
  }
  clearOverlays(routeOverlays)
}

function clearCurrent() {
  if (currentOverlay) {
    currentOverlay.setMap(null)
    currentOverlay = null
  }
}

function clearFacilityMarkers() {
  clearOverlays(facilityOverlays)
  facilitySearchStatus.value = 'idle'
}

function makeCurrentMarker(kakao, position) {
  return new kakao.maps.CustomOverlay({
    map,
    position,
    content: '<div class="rq-current-marker"><span></span></div>',
    yAnchor: 0.5,
    xAnchor: 0.5,
  })
}

function makeRouteMarker(kakao, position, label, tone = 'route') {
  if (tone === 'mid') return { setMap() {} }
  return new kakao.maps.CustomOverlay({
    map,
    position,
    content: `<div class="rq-route-marker rq-route-marker--${tone}"><span>${label}</span></div>`,
    yAnchor: 0.5,
    xAnchor: 0.5,
  })
}

function toLatLng(kakao, point) {
  const latitude = Array.isArray(point) ? Number(point[0]) : Number(point?.latitude)
  const longitude = Array.isArray(point) ? Number(point[1]) : Number(point?.longitude)
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return null
  return new kakao.maps.LatLng(latitude, longitude)
}

function makeRouteDot() {
  return { setMap() {} }
}

function makeFacilityMarker(kakao, position, label, tone) {
  const overlay = new kakao.maps.CustomOverlay({
    map,
    position,
    content: `<div class="rq-facility-marker rq-facility-marker--${tone}"><span>${label}</span></div>`,
    yAnchor: 0.5,
    xAnchor: 0.5,
  })
  facilityOverlays.push(overlay)
}

function searchKeyword(places, query, center) {
  return new Promise((resolve) => {
    places.keywordSearch(
      query.keyword,
      (results, status) => {
        if (status !== kakaoApi.maps.services.Status.OK) {
          resolve([])
          return
        }
        resolve(results.slice(0, 5).map((place) => ({ ...place, query })))
      },
      { location: center, radius: 1200, size: 5 },
    )
  })
}

async function renderFacilities() {
  if (!facilitiesVisible.value || !map || !kakaoApi?.maps?.services) return
  clearFacilityMarkers()
  facilitySearchStatus.value = 'loading'

  const places = new kakaoApi.maps.services.Places()
  const center = map.getCenter()
  const results = (await Promise.all(
    facilityQueries.map((query) => searchKeyword(places, query, center)),
  )).flat()

  results.forEach((place) => {
    makeFacilityMarker(
      kakaoApi,
      new kakaoApi.maps.LatLng(Number(place.y), Number(place.x)),
      place.query.label,
      place.query.tone,
    )
  })
  facilitySearchStatus.value = results.length ? 'ready' : 'empty'
}

function toggleFacilities() {
  facilitiesVisible.value = !facilitiesVisible.value
  if (!facilitiesVisible.value) {
    clearFacilityMarkers()
    return
  }
  renderFacilities()
}

function refreshLayout(afterRelayout) {
  if (!map) return
  map.relayout()
  if (afterRelayout) afterRelayout()
}

async function renderMap() {
  if (!mapContainer.value) return
  const currentRenderId = ++renderId
  if (!map && mapStatus.value !== 'error') {
    mapStatus.value = 'loading'
  }

  try {
    const kakao = await loadKakaoMap()
    if (currentRenderId !== renderId) return
    kakaoApi = kakao
    await nextTick()

    const fallback = new kakao.maps.LatLng(36.3504, 127.3845)
    const start = hasStart.value
      ? new kakao.maps.LatLng(Number(props.startLatitude), Number(props.startLongitude))
      : null
    const current = hasCurrentLocation.value
      ? new kakao.maps.LatLng(Number(props.currentLatitude), Number(props.currentLongitude))
      : null
    const initialCenter = current ?? start ?? fallback

    if (!map) {
      map = new kakao.maps.Map(mapContainer.value, { center: initialCenter, level: props.level })
    }

    clearRoute()
    clearCurrent()
    clearFacilityMarkers()

    const bounds = new kakao.maps.LatLngBounds()
    bounds.extend(initialCenter)
    const path = props.routePoints.map((point) => toLatLng(kakao, point)).filter(Boolean)

    if (path.length >= 2) {
      routePolyline = new kakao.maps.Polyline({
        map,
        path,
        strokeWeight: 7,
        strokeColor: '#2563eb',
        strokeOpacity: 0.96,
        strokeStyle: 'solid',
      })
      path.forEach((point) => {
        routeOverlays.push(makeRouteDot(kakao, point))
      })
      routeOverlays.push(makeRouteMarker(kakao, path[0], '출발', 'start'))
      routeOverlays.push(makeRouteMarker(kakao, path[Math.floor(path.length / 2)], '중간', 'mid'))
      routeOverlays.push(makeRouteMarker(kakao, path[path.length - 1], '도착', 'finish'))
      path.forEach((point) => bounds.extend(point))
    }

    if (current) {
      currentOverlay = makeCurrentMarker(kakao, current)
      bounds.extend(current)
    }

    refreshLayout(() => {
      if (props.focusStart && path.length >= 2) {
        map.panTo(path[0])
        map.setLevel(Math.min(props.level, 3), { anchor: path[0], animate: true })
      } else if (current && props.level <= 3) {
        map.panTo(current)
        map.setLevel(props.level, { anchor: current, animate: true })
      } else if (path.length >= 2) {
        map.setBounds(bounds, 44, 44, 118, 44)
        if (map.getLevel() < 4) map.setLevel(4)
        if (map.getLevel() > 6) map.setLevel(6)
      } else if (current) {
        map.setCenter(current)
        map.setLevel(props.level)
      } else {
        map.setCenter(initialCenter)
        map.setLevel(props.level)
      }
    })

    mapStatus.value = 'ready'
    if (facilitiesVisible.value) {
      window.setTimeout(renderFacilities, 120)
    }
  } catch {
    mapStatus.value = 'error'
  }
}

defineExpose({
  refreshLayout,
})

onMounted(renderMap)
watch(
  () => [
    props.routePoints,
    props.startLatitude,
    props.startLongitude,
    props.currentLatitude,
    props.currentLongitude,
    props.level,
    props.courseName,
    props.focusStart,
  ],
  renderMap,
  { deep: true },
)
</script>

<template>
  <div class="map-wrapper" :class="{ 'is-loading': mapStatus === 'loading' }">
    <div ref="mapContainer" class="kakao-map" aria-label="코스 경로 지도"></div>

    <section v-if="showCourseCard && (courseName || overlayMeta)" class="course-map-card">
      <strong>{{ overlayTitle }}</strong>
      <span>{{ overlayMeta }}</span>
    </section>

    <button
      v-if="showFacilitiesToggle"
      type="button"
      class="facility-toggle"
      :class="{ 'is-active': facilitiesVisible }"
      @click="toggleFacilities"
    >
      <Coffee :size="15" />
      {{ facilitiesVisible ? '편의시설 숨기기' : '주변 편의시설 보기' }}
    </button>

    <p v-if="facilitiesVisible" class="facility-note">
      <span v-if="facilitySearchStatus === 'loading'">주변 편의시설을 찾는 중입니다.</span>
      <span v-else-if="facilitySearchStatus === 'empty'">주변 1.2km 안에서 표시할 편의시설을 찾지 못했어요.</span>
      <span v-else>화장실, 편의점, 카페만 지도에 표시합니다.</span>
    </p>

    <div v-if="mapStatus !== 'ready'" class="fallback-map" aria-label="코스 지도 대체 화면">
      <i class="fallback-map__river"></i>
      <i class="fallback-map__road fallback-map__road--one"></i>
      <i class="fallback-map__road fallback-map__road--two"></i>
      <i class="fallback-map__road fallback-map__road--three"></i>
      <span class="fallback-map__pin"><MapPinned :size="23" /></span>
      <span v-if="hasCurrentLocation" class="fallback-map__current"><LocateFixed :size="18" /></span>
      <small>{{ mapStatus === 'loading' ? '지도 준비 중' : '카카오맵 연결 대기 중' }}</small>
    </div>

    <div v-if="mapStatus === 'loading'" class="map-state">
      <MapPinned :size="17" />
      <span>지도를 준비하는 중</span>
    </div>
  </div>
</template>

<style scoped>
.map-wrapper { position:relative; width:100%; aspect-ratio:16/11; overflow:hidden; background:#eaf2fb; }
.kakao-map { width:100%; height:100%; }
.course-map-card { position:absolute; z-index:4; right:14px; bottom:14px; left:14px; display:grid; gap:4px; padding:13px 14px; color:#0f172a; background:rgba(255,255,255,.86); border:1px solid rgba(255,255,255,.68); border-radius:14px; box-shadow:0 14px 32px rgba(15,23,42,.16); backdrop-filter:blur(12px); }
.course-map-card strong { font-size:14px; }
.course-map-card span { color:#475569; font-size:11px; font-weight:700; }
.facility-toggle { position:absolute; z-index:5; top:14px; right:14px; display:flex; min-height:36px; align-items:center; gap:6px; padding:0 11px; color:#2563eb; background:rgba(255,255,255,.9); border:1px solid rgba(37,99,235,.18); border-radius:999px; box-shadow:0 10px 24px rgba(15,23,42,.12); font-size:11px; font-weight:900; backdrop-filter:blur(10px); }
.facility-toggle.is-active { color:#fff; background:#2563eb; }
.facility-note { position:absolute; z-index:5; top:56px; right:14px; max-width:210px; margin:0; padding:8px 10px; color:#334155; background:rgba(255,255,255,.88); border-radius:10px; font-size:10px; line-height:1.45; box-shadow:0 10px 24px rgba(15,23,42,.12); }
.map-state { position:absolute; z-index:3; top:16px; left:50%; display:flex; align-items:center; gap:7px; padding:9px 12px; color:var(--color-primary); background:rgba(255,255,255,.9); border:1px solid rgba(255,255,255,.72); border-radius:999px; box-shadow:0 10px 24px rgba(15,23,42,.12); text-align:center; transform:translateX(-50%); backdrop-filter:blur(10px); }
.map-state span { color:#334155; font-size:11px; line-height:1.35; font-weight:900; white-space:nowrap; }
.fallback-map { position:absolute; inset:0; overflow:hidden; background:linear-gradient(30deg,transparent 48%,rgba(199,215,230,.54) 49%,rgba(199,215,230,.54) 52%,transparent 53%),linear-gradient(125deg,transparent 46%,rgba(255,255,255,.92) 47%,rgba(255,255,255,.92) 52%,transparent 53%),#eaf1ec; }
.map-wrapper.is-loading .fallback-map { opacity:.96; }
.fallback-map::before,.fallback-map::after { position:absolute; width:130%; height:14px; content:''; background:rgba(255,255,255,.9); box-shadow:0 0 0 2px rgba(208,219,226,.42); transform:rotate(-18deg); }
.fallback-map::before { top:28%; left:-14%; }
.fallback-map::after { right:-12%; bottom:22%; transform:rotate(22deg); }
.fallback-map__river { position:absolute; top:-18%; left:45%; width:64px; height:140%; background:#cfe9f5; border:7px solid rgba(255,255,255,.55); border-radius:48% 52% 42% 58%; transform:rotate(15deg); }
.fallback-map__road { position:absolute; display:block; height:7px; background:#fff; border-radius:6px; box-shadow:0 0 0 1px rgba(205,217,225,.55); }
.fallback-map__road--one { top:18%; left:6%; width:54%; transform:rotate(38deg); }
.fallback-map__road--two { top:58%; right:8%; width:62%; transform:rotate(-31deg); }
.fallback-map__road--three { bottom:12%; left:-5%; width:72%; transform:rotate(10deg); }
.fallback-map__pin,.fallback-map__current { position:absolute; z-index:2; display:grid; place-items:center; color:#fff; border:5px solid #fff; border-radius:50%; box-shadow:0 7px 18px rgba(8,102,255,.3); transform:translate(-50%,-50%); }
.fallback-map__pin { top:36%; left:52%; width:42px; height:42px; background:var(--color-primary); }
.fallback-map__current { top:54%; left:38%; width:36px; height:36px; background:#21c06b; }
.fallback-map small { position:absolute; z-index:2; right:12px; bottom:12px; padding:5px 8px; color:#64748b; background:rgba(255,255,255,.82); border-radius:10px; font-size:8px; }
:deep(.rq-current-marker) { position:relative; width:30px; height:30px; border-radius:50%; background:rgba(16,185,129,.2); box-shadow:0 0 0 8px rgba(16,185,129,.14); }
:deep(.rq-current-marker span) { position:absolute; inset:8px; background:#10b981; border:3px solid #fff; border-radius:50%; box-shadow:0 5px 14px rgba(16,185,129,.32); }
:deep(.rq-route-marker) { display:grid; min-width:38px; height:30px; place-items:center; padding:0 8px; color:#fff; background:#2563eb; border:3px solid #fff; border-radius:999px; box-shadow:0 10px 22px rgba(37,99,235,.35); font-size:10px; font-weight:900; white-space:nowrap; }
:deep(.rq-route-marker--start) { background:#16a34a; }
:deep(.rq-route-marker--mid) { background:#2563eb; }
:deep(.rq-route-marker--finish) { background:#ef4444; }
:deep(.rq-route-dot) { width:11px; height:11px; background:#fff; border:3px solid #2563eb; border-radius:50%; box-shadow:0 4px 10px rgba(37,99,235,.28), 0 0 0 3px rgba(255,255,255,.62); }
:deep(.rq-facility-marker) { display:grid; min-width:34px; height:26px; place-items:center; padding:0 7px; color:#fff; border:2px solid #fff; border-radius:999px; box-shadow:0 8px 18px rgba(15,23,42,.22); font-size:9px; font-weight:900; white-space:nowrap; }
:deep(.rq-facility-marker--toilet) { background:#0f766e; }
:deep(.rq-facility-marker--store) { background:#7c3aed; }
:deep(.rq-facility-marker--cafe) { background:#b45309; }
</style>
