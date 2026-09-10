<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, MapPin, RotateCcw, Save, Undo2 } from '@lucide/vue'

import { loadKakaoMap } from '../services/kakaoMap'
import { useCustomCourseStore } from '../stores/customCourses'
import { calculateDistanceKm } from '../utils/running'

const router = useRouter()
const store = useCustomCourseStore()
const mapContainer = ref(null)
const points = ref([])
const mapStatus = ref('loading')
const name = ref('')
const description = ref('')
const visibility = ref('private')
const manualLatitude = ref('36.3504')
const manualLongitude = ref('127.3845')
let kakao = null
let map = null
let polyline = null
let markers = []

const distanceKm = computed(() => calculateDistanceKm(
  points.value.map(([latitude, longitude]) => ({ latitude, longitude })),
))
const canSave = computed(() => name.value.trim().length >= 2 && distanceKm.value >= 0.1)

function redraw() {
  if (!map || !kakao) return
  markers.forEach((marker) => marker.setMap(null))
  markers = points.value.map(([latitude, longitude], index) => new kakao.maps.Marker({
    map,
    position: new kakao.maps.LatLng(latitude, longitude),
    title: index === 0 ? '출발' : `경유지 ${index}`,
  }))
  polyline?.setMap(null)
  polyline = new kakao.maps.Polyline({
    map,
    path: points.value.map(([latitude, longitude]) => (
      new kakao.maps.LatLng(latitude, longitude)
    )),
    strokeWeight: 6,
    strokeColor: '#0866ff',
    strokeOpacity: 0.9,
  })
}

function addPoint(latitude, longitude) {
  const lat = Number(latitude)
  const lng = Number(longitude)
  if (lat < 36.1 || lat > 36.55 || lng < 127.2 || lng > 127.6) {
    store.errorMessage = '대전 지역 안의 지점만 추가할 수 있습니다.'
    return
  }
  store.errorMessage = ''
  points.value.push([Number(lat.toFixed(6)), Number(lng.toFixed(6))])
  redraw()
}

function undo() {
  points.value.pop()
  redraw()
}

function reset() {
  points.value = []
  redraw()
}

async function save() {
  try {
    const course = await store.createDrawnCourse({
      name: name.value.trim(),
      description: description.value.trim(),
      visibility: visibility.value,
      route_points: points.value,
    })
    router.replace(`/my/courses/${course.id}`)
  } catch {
    // Store displays validation details.
  }
}

onMounted(async () => {
  try {
    kakao = await loadKakaoMap()
    await nextTick()
    map = new kakao.maps.Map(mapContainer.value, {
      center: new kakao.maps.LatLng(36.3504, 127.3845),
      level: 6,
    })
    kakao.maps.event.addListener(map, 'click', (event) => {
      addPoint(event.latLng.getLat(), event.latLng.getLng())
    })
    mapStatus.value = 'ready'
  } catch {
    mapStatus.value = 'fallback'
  }
})
</script>

<template>
  <main class="mobile-shell builder-page">
    <header>
      <RouterLink to="/my/courses" aria-label="나의 코스로 돌아가기"><ArrowLeft :size="24" /></RouterLink>
      <h1>새 코스 만들기</h1>
      <button type="button" aria-label="경로 초기화" @click="reset"><RotateCcw :size="21" /></button>
    </header>

    <section class="map-editor">
      <div ref="mapContainer" class="map-canvas" aria-label="코스 편집 지도"></div>
      <div v-if="mapStatus === 'loading'" class="map-overlay">지도를 준비하고 있어요.</div>
      <div v-else-if="mapStatus === 'fallback'" class="map-overlay map-overlay--fallback">
        <MapPin :size="27" />
        <strong>좌표로 지점을 추가할 수 있어요</strong>
        <div>
          <input v-model="manualLatitude" aria-label="위도" inputmode="decimal" />
          <input v-model="manualLongitude" aria-label="경도" inputmode="decimal" />
        </div>
        <button type="button" @click="addPoint(manualLatitude, manualLongitude)">지점 추가</button>
      </div>
      <div class="map-toolbar">
        <span><strong>{{ distanceKm.toFixed(2) }}</strong>km · {{ points.length }}개 지점</span>
        <button type="button" :disabled="!points.length" aria-label="마지막 지점 취소" @click="undo"><Undo2 :size="18" /></button>
      </div>
    </section>

    <section class="builder-form">
      <p>지도를 눌러 출발점과 경유지를 순서대로 추가하세요.</p>
      <label>코스 이름<input v-model="name" maxlength="80" placeholder="예: 갑천 저녁 러닝 코스" /></label>
      <label>설명<textarea v-model="description" maxlength="300" placeholder="코스 특징과 주의점을 기록해 주세요."></textarea></label>
      <label>공개 설정
        <select v-model="visibility">
          <option value="private">비공개</option>
          <option value="public">공개</option>
        </select>
      </label>
      <p v-if="store.errorMessage" class="error">{{ store.errorMessage }}</p>
      <button class="save-button" type="button" :disabled="!canSave || store.isUploading" @click="save">
        <Save :size="19" /> {{ store.isUploading ? '저장 중...' : '코스 저장' }}
      </button>
    </section>
  </main>
</template>

<style scoped>
.builder-page { background:#f5f9ff; }
header { display:grid; height:64px; grid-template-columns:44px 1fr 44px; align-items:center; padding:0 14px; background:#fff; border-bottom:1px solid var(--color-border); }
header a,header button { display:grid; width:40px; height:40px; place-items:center; color:var(--color-navy); background:transparent; }
header h1 { margin:0; font-size:18px; text-align:center; }
.map-editor { position:relative; height:390px; background:#eaf2fb; }
.map-canvas { width:100%; height:100%; }
.map-overlay { position:absolute; inset:0; display:grid; place-items:center; color:var(--color-muted); background:#edf5ff; font-size:12px; }
.map-overlay--fallback { align-content:center; gap:10px; padding:24px; color:var(--color-primary); text-align:center; }
.map-overlay--fallback div { display:grid; width:100%; grid-template-columns:1fr 1fr; gap:7px; }
.map-overlay input { min-width:0; height:42px; padding:0 9px; border:1px solid var(--color-border); border-radius:6px; }
.map-overlay button { height:42px; padding:0 20px; color:#fff; background:var(--color-primary); border-radius:6px; }
.map-toolbar { position:absolute; right:14px; bottom:14px; left:14px; display:flex; height:52px; align-items:center; justify-content:space-between; padding:0 12px; background:rgba(255,255,255,.96); border:1px solid var(--color-border); border-radius:8px; box-shadow:var(--shadow-soft); }
.map-toolbar span { color:var(--color-muted); font-size:11px; }
.map-toolbar strong { color:var(--color-navy); font-size:17px; }
.map-toolbar button { display:grid; width:36px; height:36px; place-items:center; color:var(--color-primary); background:var(--color-primary-soft); border-radius:50%; }
.builder-form { display:grid; gap:15px; padding:20px var(--content-padding) 34px; }
.builder-form > p { margin:0; color:var(--color-muted); font-size:11px; }
.builder-form label { display:grid; gap:7px; color:var(--color-navy); font-size:11px; font-weight:700; }
.builder-form input,.builder-form textarea,.builder-form select { width:100%; padding:12px; background:#fff; border:1px solid var(--color-border); border-radius:6px; outline:none; }
.builder-form textarea { min-height:82px; resize:vertical; }
.builder-form .error { color:#b42318; }
.save-button { display:flex; height:50px; align-items:center; justify-content:center; gap:7px; color:#fff; font-weight:800; background:var(--color-primary); border-radius:7px; }
.save-button:disabled { opacity:.45; }
</style>
