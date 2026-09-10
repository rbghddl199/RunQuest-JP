<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  ChevronDown,
  ChevronUp,
  Clock3,
  Cloud,
  CloudRain,
  FileUp,
  LocateFixed,
  Lock,
  MapPinned,
  Pause,
  Play,
  Route,
  Settings2,
  Square,
  Sun,
} from '@lucide/vue'
import { useRoute, useRouter } from 'vue-router'

import AppBottomNav from '../components/navigation/AppBottomNav.vue'
import KakaoCourseMap from '../components/maps/KakaoCourseMap.vue'
import api from '../services/api'
import { loadKakaoMap } from '../services/kakaoMap'
import { useCourseStore } from '../stores/courses'
import { useCustomCourseStore } from '../stores/customCourses'
import { useRunningStore } from '../stores/running'
import { formatDuration, formatPace } from '../utils/running'

const route = useRoute()
const router = useRouter()
const courseStore = useCourseStore()
const customCourseStore = useCustomCourseStore()
const runningStore = useRunningStore()
const trackingMode = ref('gps')
const modePanelOpen = ref(false)
const gpxPanelOpen = ref(false)
const locationPanelOpen = ref(true)
const mapRef = ref(null)
const weather = ref(null)
const weatherError = ref('')
const isActiveView = ref(false)
const isRunLocked = ref(false)
const unlockProgress = ref(0)
const currentPosition = ref(null)
const selectedCustomId = ref(null)
const appliedCourseOrigin = ref(null)
const gpxForm = ref({
  name: '',
  description: '',
  visibility: 'private',
  file: null,
})
const hasAppliedCourse = computed(() => Boolean(
  route.query.course
  || route.query.custom
  || selectedCustomId.value
  || runningStore.record?.course
  || runningStore.record?.custom_course,
))

const course = computed(() => (
  runningStore.record?.course
  ?? runningStore.record?.custom_course
  ?? (hasAppliedCourse.value && (route.query.custom || selectedCustomId.value) ? customCourseStore.currentCourse : null)
  ?? (hasAppliedCourse.value ? courseStore.currentCourse : null)
))

const weatherIcon = computed(() => {
  const code = weather.value?.weather_code ?? 800
  if ([200, 201, 202, 230, 231, 232, 500, 501, 502, 503, 504, 511, 520, 521, 522, 531].includes(code)) return CloudRain
  if ([801, 802, 803, 804, 701, 741].includes(code)) return Cloud
  return Sun
})

const weatherTemperature = computed(() => (
  weather.value ? `${Math.round(weather.value.temperature)}°C` : '--°C'
))

const paceText = computed(() => (
  runningStore.paceSeconds ? formatPace(runningStore.paceSeconds) : '--'
))
const lockedDistanceText = computed(() => runningStore.distanceKm.toFixed(2))
const lockedDurationText = computed(() => formatDuration(runningStore.elapsedSeconds))
const fineDustLabel = computed(() => weather.value?.fine_dust_label ?? '보통')
const fineDustHint = computed(() => {
  const label = fineDustLabel.value
  if (label.includes('좋음')) return '맑은 호흡, 가볍게 출발'
  if (label.includes('나쁨') || label.includes('매우')) return '짧게 천천히, 호흡 체크'
  return '편한 호흡으로 출발'
})
const expectedTime = computed(() => {
  if (course.value?.estimated_minutes) return `${course.value.estimated_minutes}분`
  if (weather.value?.running_status === 'poor') return '20분'
  if (weather.value?.running_status === 'good') return '35분'
  return '30분'
})
const mapCurrentPosition = computed(() => {
  const lastPoint = runningStore.points.at(-1)
  if (lastPoint) {
    return { latitude: lastPoint.latitude, longitude: lastPoint.longitude }
  }
  return currentPosition.value
})
const gpsStatusText = computed(() => {
  if (trackingMode.value === 'simulation') return '시뮬레이션'
  if (runningStore.trackingError) return 'GPS 확인 필요'
  if (mapCurrentPosition.value) return 'GPS 위치 수신됨'
  return 'GPS 준비됨'
})
const activeMapLevel = computed(() => (isActiveView.value ? 2 : 5))
const runModeLabel = computed(() => {
  if (route.query.course) return '추천 코스'
  if (route.query.custom || selectedCustomId.value) return course.value?.source === 'gpx' ? 'GPX 코스' : '나의 코스'
  return '자유 러닝'
})

async function loadWeather() {
  weatherError.value = ''
  try {
    const { data } = await api.get('/weather/current/')
    weather.value = data
  } catch {
    weatherError.value = '날씨 확인 불가'
  }
}

async function loadCourse() {
  if (route.query.custom) {
    selectedCustomId.value = Number(route.query.custom)
    appliedCourseOrigin.value = 'custom'
    courseStore.currentCourse = null
    await customCourseStore.loadCourse(route.query.custom)
  } else if (route.query.course) {
    selectedCustomId.value = null
    appliedCourseOrigin.value = 'favorite'
    customCourseStore.currentCourse = null
    await courseStore.loadCourse(route.query.course)
  } else {
    selectedCustomId.value = null
    appliedCourseOrigin.value = null
    customCourseStore.currentCourse = null
    courseStore.currentCourse = null
  }
}

function refreshMapSoon() {
  nextTick(() => {
    mapRef.value?.refreshLayout?.()
    window.setTimeout(() => mapRef.value?.refreshLayout?.(), 120)
    window.setTimeout(() => mapRef.value?.refreshLayout?.(), 440)
  })
}

function toggleLocationPanel() {
  locationPanelOpen.value = !locationPanelOpen.value
  refreshMapSoon()
}

function loadCurrentPosition() {
  if (!navigator.geolocation) return
  navigator.geolocation.getCurrentPosition(
    (position) => {
      currentPosition.value = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
      }
    },
    () => {
      currentPosition.value = null
    },
    { enableHighAccuracy: true, maximumAge: 60_000, timeout: 5000 },
  )
}

function refreshCurrentPosition() {
  if (!navigator.geolocation) return Promise.resolve(null)
  return new Promise((resolve) => {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const nextPosition = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        }
        currentPosition.value = nextPosition
        resolve(nextPosition)
      },
      () => {
        resolve(null)
      },
      { enableHighAccuracy: true, maximumAge: 0, timeout: 5000 },
    )
  })
}

onMounted(async () => {
  loadKakaoMap().catch(() => {})
  const active = await runningStore.restoreActive()
  loadCurrentPosition()
  await Promise.all([loadWeather(), loadCourse()])
  if (active) {
    isActiveView.value = true
    isRunLocked.value = false
    locationPanelOpen.value = false
    if (!runningStore.timerId) {
      runningStore.beginTracking(active.course ?? active.custom_course, currentPosition.value)
    }
  }
  refreshMapSoon()
})

watch(
  () => [locationPanelOpen.value, isActiveView.value],
  refreshMapSoon,
)

onBeforeUnmount(() => {
  if (runningStore.isActive) {
    runningStore.syncProgress()
  }
})

async function startRun() {
  await refreshCurrentPosition()
  const record = await runningStore.start(
    route.query.course ? course.value?.slug ?? null : null,
    trackingMode.value,
    route.query.custom ? Number(route.query.custom) : selectedCustomId.value,
  )
  if (!record) return
  isActiveView.value = true
  isRunLocked.value = false
  locationPanelOpen.value = false
  unlockProgress.value = 0
  runningStore.beginTracking(record.course ?? record.custom_course ?? course.value, currentPosition.value)
}

function lockRun() {
  unlockProgress.value = 0
  isRunLocked.value = true
}

function handleUnlockInput(event) {
  const value = Number(event.target.value)
  unlockProgress.value = value
  if (value >= 92) {
    isRunLocked.value = false
    unlockProgress.value = 0
  }
}

function resetUnlockProgress() {
  if (!isRunLocked.value) return
  unlockProgress.value = 0
}

async function applyCustomCourse(id, origin = 'custom') {
  selectedCustomId.value = Number(id)
  appliedCourseOrigin.value = origin
  courseStore.currentCourse = null
  await customCourseStore.loadCourse(id)
  gpxPanelOpen.value = false
  locationPanelOpen.value = true
  if (route.query.course || route.query.custom) {
    await router.replace('/run/start')
  }
  refreshMapSoon()
}

function clearAppliedCourse() {
  gpxPanelOpen.value = false
  selectedCustomId.value = null
  appliedCourseOrigin.value = null
  customCourseStore.currentCourse = null
  courseStore.currentCourse = null
  if (route.query.course || route.query.custom) {
    router.replace('/run/start')
  }
}

function chooseGpxFile(event) {
  const file = event.target.files?.[0] ?? null
  gpxForm.value.file = file
  if (file && !gpxForm.value.name) {
    gpxForm.value.name = file.name.replace(/\.gpx$/i, '')
  }
}

async function uploadGpxCourse() {
  if (!gpxForm.value.name.trim() || !gpxForm.value.file) return
  const uploaded = await customCourseStore.uploadCourse({
    name: gpxForm.value.name.trim(),
    description: gpxForm.value.description.trim(),
    visibility: gpxForm.value.visibility,
    file: gpxForm.value.file,
  })
  if (!uploaded) return
  await applyCustomCourse(uploaded.id, 'gpx')
  gpxForm.value = {
    name: '',
    description: '',
    visibility: 'private',
    file: null,
  }
}

async function finishRun() {
  const result = await runningStore.finish()
  if (result?.cancelled) {
    window.alert(result.detail ?? '100m 이상 이동한 러닝만 기록으로 저장됩니다.')
    isActiveView.value = false
    await router.replace('/run/start')
    return
  }
  if (result) {
    await router.replace(`/run/completed/${result.record.id}`)
    return
  }
  if (runningStore.trackingError) {
    runningStore.reset()
    isActiveView.value = false
    await router.replace('/run/start')
  }
}
</script>

<template>
  <main class="mobile-shell run-start-page" :class="{ 'is-running': isActiveView }">
    <section class="map-stage" :class="{ 'is-map-focused': !locationPanelOpen }">
      <KakaoCourseMap
        ref="mapRef"
        class="map-background"
        :route-points="hasAppliedCourse ? course?.route_points ?? [] : []"
        :start-latitude="hasAppliedCourse ? course?.start_latitude : null"
        :start-longitude="hasAppliedCourse ? course?.start_longitude : null"
        :current-latitude="mapCurrentPosition?.latitude"
        :current-longitude="mapCurrentPosition?.longitude"
        :course-name="course?.name"
        :course-distance="course?.distance_km"
        :course-minutes="course?.estimated_minutes"
        :course-difficulty="course?.difficulty_label"
        :show-course-card="false"
        :show-facilities-toggle="false"
        :focus-start="hasAppliedCourse"
        :level="activeMapLevel"
      />
      <div class="top-controls">
        <span class="gps-status">
          <i></i>
          {{ gpsStatusText }}
        </span>
        <button
          type="button"
          class="mode-settings"
          aria-label="기록 방식 설정"
          :aria-expanded="modePanelOpen"
          @click="modePanelOpen = !modePanelOpen"
        >
          <Settings2 :size="20" />
        </button>
      </div>

      <section v-if="modePanelOpen && !isActiveView" class="mode-panel">
        <button
          type="button"
          :class="{ 'is-active': trackingMode === 'gps' }"
          @click="trackingMode = 'gps'; modePanelOpen = false"
        >
          <LocateFixed :size="19" />
          <span><strong>GPS 러닝</strong><small>실제 위치 기록</small></span>
        </button>
        <button
          type="button"
          :class="{ 'is-active': trackingMode === 'simulation' }"
          @click="trackingMode = 'simulation'; modePanelOpen = false"
        >
          <MapPinned :size="19" />
          <span><strong>시뮬레이션</strong><small>발표용 가상 기록</small></span>
        </button>
      </section>

      <button
        v-if="!isActiveView"
        class="start-button"
        type="button"
        :disabled="runningStore.isStarting"
        @click="startRun"
      >
        <span>{{ runningStore.isStarting ? '준비 중' : 'START' }}</span>
        <Play :size="25" fill="currentColor" />
      </button>

      <section v-else class="run-actions">
        <button
          type="button"
          class="pause-button"
          :aria-label="runningStore.isPaused ? '러닝 재개' : '러닝 일시정지'"
          @click="runningStore.togglePause"
        >
          <Play v-if="runningStore.isPaused" :size="24" fill="currentColor" />
          <Pause v-else :size="24" fill="currentColor" />
        </button>
        <button type="button" class="lock-button" aria-label="러닝 화면 잠금" @click="lockRun">
          <Lock :size="21" />
        </button>
        <button
          type="button"
          class="finish-button"
          :disabled="runningStore.isFinishing"
          :aria-label="runningStore.isFinishing ? '러닝 기록 저장 중' : '러닝 종료'"
          @click="finishRun"
        >
          <Square :size="20" fill="currentColor" />
        </button>
      </section>

      <section class="status-cards" :class="{ 'is-flipped': isActiveView }">
        <article>
          <div class="card-face card-front">
            <span>날씨</span>
            <div>
              <component :is="weatherIcon" :size="20" />
              <strong>{{ weatherError || weatherTemperature }}</strong>
            </div>
            <small>{{ weather?.label ?? '불러오는 중' }}</small>
          </div>
          <div class="card-face card-back">
            <span>거리</span>
            <strong>{{ runningStore.distanceKm.toFixed(2) }}</strong>
            <small>km</small>
          </div>
        </article>
        <article>
          <div class="card-face card-front">
            <span>미세먼지</span>
            <div>
              <span class="fine-dust-icon" aria-hidden="true"></span>
              <strong>{{ fineDustLabel }}</strong>
            </div>
            <small>{{ fineDustHint }}</small>
          </div>
          <div class="card-face card-back">
            <span>시간</span>
            <strong>{{ formatDuration(runningStore.elapsedSeconds) }}</strong>
            <small>진행 시간</small>
          </div>
        </article>
        <article>
          <div class="card-face card-front">
            <span>예상 시간</span>
            <Clock3 :size="20" />
            <strong>{{ expectedTime }}</strong>
          </div>
          <div class="card-face card-back">
            <span>페이스</span>
            <strong>{{ paceText }}</strong>
            <small>/km</small>
          </div>
        </article>
      </section>

      <div v-if="runningStore.isPaused" class="paused-badge">일시 정지</div>

      <p v-if="runningStore.trackingError" class="run-error">
        {{ runningStore.trackingError }}
      </p>
    </section>

    <section class="run-panel" :class="{ 'is-location-collapsed': !locationPanelOpen }">
      <div class="location-heading" :class="{ 'is-collapsed': !locationPanelOpen }">
        <div class="location-heading__top">
          <span><MapPinned :size="14" /> {{ hasAppliedCourse ? runModeLabel : '현재 위치' }}</span>
          <button
            type="button"
            class="location-toggle"
            :aria-expanded="locationPanelOpen"
            aria-label="현재 위치 정보 접기 펼치기"
            @click="toggleLocationPanel"
          >
            <ChevronUp v-if="locationPanelOpen" :size="17" />
            <ChevronDown v-else :size="17" />
          </button>
        </div>
        <div class="location-heading__body">
          <h1>{{ hasAppliedCourse ? (course?.name || '코스 불러오는 중') : '내 위치에서 시작' }}</h1>
          <p>{{ hasAppliedCourse ? `${course?.distance_km ?? '-'}km · ${course?.estimated_minutes ?? '-'}분 · ${course?.difficulty_label ?? '보통'}` : '지도는 현재 위치를 기준으로 두고, 원하는 방식으로 바로 시작할 수 있어요.' }}</p>
        </div>
      </div>

      <div class="run-panel__body">
        <section v-if="!isActiveView" class="route-selector" aria-label="러닝 방식 선택">
          <button type="button" :class="{ active: !hasAppliedCourse && !gpxPanelOpen }" @click="clearAppliedCourse">
            <LocateFixed :size="18" />
            <span><strong>자유 러닝</strong><small>현재 위치에서 바로 시작</small></span>
          </button>
          <button
            type="button"
            :class="{ active: Boolean((route.query.custom || selectedCustomId) && course?.source !== 'gpx' && appliedCourseOrigin !== 'gpx') }"
            @click="router.push({ path: '/my/courses', query: { returnTo: '/run/start' } })"
          >
            <Route :size="18" />
            <span><strong>내 코스</strong><small>저장한 코스 선택</small></span>
          </button>
          <button
            type="button"
            :class="{ active: gpxPanelOpen || Boolean((route.query.custom || selectedCustomId) && course?.source === 'gpx') || appliedCourseOrigin === 'gpx' }"
            @click="locationPanelOpen = true; gpxPanelOpen = !gpxPanelOpen"
          >
            <FileUp :size="18" />
            <span><strong>GPX</strong><small>파일 업로드 후 적용</small></span>
          </button>
        </section>

      </div>

    </section>

    <AppBottomNav />

    <div
      v-if="gpxPanelOpen && !isActiveView"
      class="route-sheet-backdrop"
      @click.self="gpxPanelOpen = false"
    >
      <section class="route-sheet" aria-label="GPX 코스 가져오기">
        <header>
          <div>
            <small>GPX IMPORT</small>
            <h2>GPX 코스 가져오기</h2>
          </div>
          <button type="button" aria-label="선택창 닫기" @click="gpxPanelOpen = false">
            <ChevronDown :size="20" />
          </button>
        </header>

        <div class="gpx-panel">
          <label>
            <span>코스 이름</span>
            <input v-model="gpxForm.name" maxlength="80" placeholder="예: 갑천 퇴근 러닝" />
          </label>
          <label class="gpx-file-field">
            <FileUp :size="22" />
            <span>
              <strong>{{ gpxForm.file?.name ?? 'GPX 파일 선택' }}</strong>
              <small>외부 러닝 경로를 RunQuest 코스로 가져와요.</small>
            </span>
            <input type="file" accept=".gpx,application/gpx+xml" @change="chooseGpxFile" />
          </label>
          <button
            type="button"
            :disabled="!gpxForm.name.trim() || !gpxForm.file || customCourseStore.isUploading"
            @click="uploadGpxCourse"
          >
            {{ customCourseStore.isUploading ? '분석 중' : 'GPX 코스 적용' }}
          </button>
          <p v-if="customCourseStore.errorMessage" class="run-error-inline">{{ customCourseStore.errorMessage }}</p>
        </div>
      </section>
    </div>

    <section v-if="isActiveView && isRunLocked" class="run-lock-screen" aria-label="러닝 잠금 화면">
      <div class="lock-scrim"></div>
      <div class="lock-content">
        <span class="lock-status">
          <i></i>
          {{ runningStore.isPaused ? '일시 정지 중' : '러닝 기록 중' }}
        </span>
        <div class="lock-primary">
          <small>시간</small>
          <strong>{{ lockedDurationText }}</strong>
          <span>잠금화면</span>
        </div>
        <div class="lock-metrics">
          <div>
            <small>거리</small>
            <strong>{{ lockedDistanceText }}</strong>
            <span>km</span>
          </div>
          <div>
            <small>페이스</small>
            <strong>{{ paceText }}</strong>
            <span>/km</span>
          </div>
        </div>
        <label
          class="unlock-slider"
          :style="{ '--unlock-progress': `${unlockProgress}%` }"
        >
          <span>밀어서 잠금 해제</span>
          <b aria-hidden="true"></b>
          <input
            type="range"
            min="0"
            max="100"
            :value="unlockProgress"
            aria-label="밀어서 잠금 해제"
            @input="handleUnlockInput"
            @change="resetUnlockProgress"
          />
          <i aria-hidden="true">
            <img src="/runquest-runner-badge.png" alt="" />
          </i>
        </label>
      </div>
    </section>
  </main>
</template>

<style scoped>
.run-start-page {
  position: relative;
  display: flex;
  height: var(--app-height);
  min-height: var(--app-height);
  flex-direction: column;
  padding-bottom: 0;
  overflow: hidden;
  background: #edf5ff;
  border-radius: var(--app-radius);
}

.map-stage {
  position: relative;
  flex: 0 0 auto;
  height: 520px;
  overflow: hidden;
  background: #dfeaf7;
  border-radius: inherit;
  transition: height 420ms cubic-bezier(.2, .8, .2, 1);
}

.map-stage.is-map-focused {
  flex: 1 1 auto;
  height: 610px;
}

.map-background,
.map-background :deep(.map-wrapper) {
  width: 100%;
  height: 100%;
  aspect-ratio: auto;
}

.top-controls {
  position: absolute;
  z-index: 2;
  top: 24px;
  right: var(--content-padding);
  left: var(--content-padding);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.gps-status,
.mode-settings {
  min-height: 42px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 8px 24px rgba(24, 63, 117, 0.14);
  backdrop-filter: blur(12px);
}

.gps-status {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 0 14px;
  color: #31455f;
  border-radius: 22px;
  font-size: 12px;
  font-weight: 700;
}

.gps-status i {
  width: 8px;
  height: 8px;
  background: #28c75f;
  border-radius: 50%;
  box-shadow: 0 0 0 4px rgba(40, 199, 95, 0.14);
}

.mode-settings {
  display: grid;
  width: 42px;
  place-items: center;
  color: var(--color-navy);
  border-radius: 50%;
}

.run-panel {
  position: relative;
  z-index: 2;
  display: grid;
  gap: var(--page-gap);
  margin-top: 0;
  padding: var(--section-gap) var(--content-padding) 22px;
  background: var(--color-background);
  border-radius: var(--card-radius) var(--card-radius) 0 0;
  box-shadow: 0 -10px 26px rgba(24, 63, 117, 0.08);
}

.run-panel__body {
  display: grid;
  gap: var(--page-gap);
  overflow: visible;
  max-height: 520px;
  opacity: 1;
  transform: translateY(0);
  transition:
    max-height 420ms cubic-bezier(.2,.8,.2,1),
    opacity 240ms ease,
    transform 320ms cubic-bezier(.2,.8,.2,1);
}

.run-panel.is-location-collapsed {
  gap: 0;
  padding-top: 10px;
  padding-bottom: 10px;
}

.run-panel.is-location-collapsed .run-panel__body {
  max-height: 0;
  opacity: 0;
  overflow: hidden;
  pointer-events: none;
  transform: translateY(-8px);
}

.location-heading {
  overflow: hidden;
  text-align: left;
  transition:
    opacity 360ms ease,
    transform 420ms cubic-bezier(.2,.8,.2,1),
    max-height 420ms cubic-bezier(.2,.8,.2,1),
    margin 420ms cubic-bezier(.2,.8,.2,1);
  max-height: 112px;
}

.location-heading.is-collapsed {
  max-height: 38px;
}

.location-heading__top {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 30px;
  align-items: center;
  gap: 8px;
  min-height: 32px;
}

.location-heading__body {
  overflow: hidden;
  opacity: 1;
  transform: translateY(0);
  transition:
    opacity 260ms ease,
    transform 320ms cubic-bezier(.2,.8,.2,1);
}

.location-heading.is-collapsed .location-heading__body {
  opacity: 0;
  pointer-events: none;
  transform: translateY(-8px);
}

.location-toggle {
  display: grid;
  width: 30px;
  height: 30px;
  place-items: center;
  justify-self: end;
  color: var(--color-primary);
  background: var(--color-primary-soft);
  border: 1px solid color-mix(in srgb, var(--color-primary) 18%, transparent);
  border-radius: 50%;
}

.run-start-page.is-running .location-heading {
  max-height: 0;
  margin: -6px 0 -13px;
  opacity: 0;
  pointer-events: none;
  transform: translateY(-12px);
}

.location-heading span {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 5px;
  color: var(--color-primary);
  font-size: 11px;
  font-weight: 800;
}

.location-heading h1 {
  margin: 5px 0 0;
  color: var(--color-navy);
  font-size: var(--title-font-size);
  line-height: 1.25;
}

.location-heading p {
  margin: 5px 0 0;
  color: var(--color-muted);
  font-size: var(--body-font-size);
  line-height: 1.5;
}

.route-selector {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.route-selector button {
  display: grid;
  min-width: 0;
  min-height: 76px;
  align-content: center;
  justify-items: center;
  gap: 5px;
  padding: 10px 6px;
  color: #64748b;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-medium);
  text-align: center;
  box-shadow: 0 8px 18px rgba(20, 61, 118, 0.06);
}

.route-selector button.active {
  color: var(--color-primary);
  border-color: rgba(8, 102, 255, 0.38);
  background: var(--color-primary-soft);
}

.route-selector strong,
.route-selector small {
  display: block;
  overflow: hidden;
  max-width: 100%;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.route-selector strong {
  color: var(--color-navy);
  font-size: 11px;
}

.route-selector small {
  font-size: 9px;
}

.route-sheet-backdrop {
  position: absolute;
  z-index: 70;
  inset: 0;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 0 var(--content-padding) calc(var(--bottom-nav-height) + 10px);
  background: linear-gradient(180deg, transparent 42%, rgba(9, 20, 43, 0.22));
  pointer-events: auto;
}

.route-sheet {
  display: grid;
  width: 100%;
  max-height: 332px;
  gap: 12px;
  overflow: hidden;
  padding: var(--card-padding);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px 8px var(--card-radius) var(--card-radius);
  box-shadow:
    0 -18px 42px rgba(15, 23, 42, 0.18),
    0 0 0 1px rgba(255, 255, 255, 0.68);
  animation: route-sheet-up 220ms cubic-bezier(.2, .8, .2, 1);
}

.route-sheet header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.route-sheet header small,
.route-sheet header h2 {
  margin: 0;
}

.route-sheet header small {
  color: var(--color-primary);
  font-size: 9px;
  font-weight: 900;
}

.route-sheet header h2 {
  margin-top: 2px;
  color: var(--color-navy);
  font-size: 16px;
}

.route-sheet header button {
  display: grid;
  width: 34px;
  height: 34px;
  flex: 0 0 auto;
  place-items: center;
  color: var(--color-muted);
  background: var(--color-subtle);
  border-radius: 50%;
}

.gpx-panel {
  display: grid;
  gap: 8px;
}

.gpx-panel label {
  display: grid;
  gap: 6px;
  color: var(--color-navy);
  font-size: 10px;
  font-weight: 900;
}

.gpx-panel input {
  width: 100%;
  min-height: 42px;
  padding: 0 12px;
  color: var(--color-navy);
  background: var(--color-input);
  border: 1px solid var(--color-border);
  border-radius: 6px;
}

.gpx-panel button {
  min-height: 42px;
  color: #fff;
  background: var(--color-primary);
  border-radius: 6px;
  font-size: 12px;
  font-weight: 900;
}

.gpx-file-field {
  position: relative;
  grid-template-columns: 30px 1fr;
  align-items: center;
  gap: 8px;
  min-height: 64px;
  padding: 12px;
  color: var(--color-primary);
  background: var(--color-primary-soft);
  border: 1px dashed rgba(8, 102, 255, 0.42);
  border-radius: 8px;
}

.gpx-file-field strong,
.gpx-file-field small {
  display: block;
}

.gpx-file-field strong {
  color: var(--color-navy);
  font-size: 12px;
}

.gpx-file-field small {
  margin-top: 2px;
  color: var(--color-muted);
  font-size: 9px;
  font-weight: 700;
}

.gpx-file-field input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.gpx-panel button:disabled {
  color: #e2e8f0;
  background: #94a3b8;
}

.mode-panel {
  position: absolute;
  z-index: 5;
  top: 76px;
  right: var(--content-padding);
  display: grid;
  width: 210px;
  gap: 6px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.98);
  border-radius: 14px;
  box-shadow: 0 15px 34px rgba(22, 61, 116, 0.2);
}

.mode-panel button {
  display: grid;
  grid-template-columns: 28px 1fr;
  align-items: center;
  gap: 6px;
  padding: 10px;
  color: #66758a;
  background: transparent;
  border-radius: 9px;
  text-align: left;
}

.mode-panel button.is-active {
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.mode-panel span {
  display: grid;
  gap: 2px;
}

.mode-panel strong {
  color: var(--color-navy);
  font-size: 12px;
}

.mode-panel small {
  font-size: 9px;
}

.start-button {
  position: absolute;
  z-index: 6;
  bottom: 138px;
  left: 50%;
  display: grid;
  width: 112px;
  height: 112px;
  place-items: center;
  align-content: center;
  align-items: center;
  justify-content: center;
  gap: 3px;
  color: #fff;
  background: linear-gradient(145deg, #4674ff, #0068e9);
  border: 8px solid rgba(236, 246, 255, 0.92);
  border-radius: 50%;
  box-shadow:
    0 18px 38px rgba(8, 102, 255, 0.38),
    inset 0 0 26px rgba(255, 255, 255, 0.14);
  transform: translateX(-50%);
  animation: start-heartbeat 1.8s ease-in-out infinite;
}

.start-button span {
  font-size: 18px;
  font-weight: 800;
}

.start-button:disabled {
  opacity: 0.64;
  animation: none;
}

.run-actions {
  position: absolute;
  z-index: 6;
  right: var(--content-padding);
  bottom: 128px;
  left: var(--content-padding);
  display: grid;
  grid-template-columns: repeat(3, 58px);
  justify-content: center;
  gap: 14px;
}

.run-actions button {
  display: grid;
  width: 58px;
  height: 58px;
  min-height: 58px;
  align-items: center;
  justify-content: center;
  color: #fff;
  border-radius: 50%;
  font-weight: 900;
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.2);
}

.pause-button {
  background: linear-gradient(145deg, #0b6cff, #004bd6);
}

.lock-button {
  background: linear-gradient(145deg, #101c36, #293f69);
}

.finish-button {
  background: linear-gradient(145deg, #ff5a6b, #e7324a);
}

.status-cards {
  position: absolute;
  z-index: 5;
  right: var(--content-padding);
  bottom: 20px;
  left: var(--content-padding);
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.status-cards article {
  position: relative;
  min-width: 0;
  min-height: 104px;
  transform-style: preserve-3d;
  transition: transform 700ms cubic-bezier(.2, .8, .2, 1);
}

.status-cards.is-flipped article {
  transform: rotateY(180deg);
}

.status-cards article:nth-child(2) {
  transition-delay: 60ms;
}

.status-cards article:nth-child(3) {
  transition-delay: 120ms;
}

.card-face {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 6px;
  padding: 12px 8px;
  background: rgba(255, 255, 255, 0.97);
  border: 1px solid rgba(219, 232, 248, 0.96);
  border-radius: var(--radius-medium);
  box-shadow: 0 8px 22px rgba(27, 62, 112, 0.13);
  text-align: center;
  backface-visibility: hidden;
  backdrop-filter: blur(12px);
}

.card-back {
  transform: rotateY(180deg);
  background: rgba(8, 17, 38, 0.88);
}

.card-face > span,
.card-face small {
  overflow: hidden;
  max-width: 100%;
  color: #516074;
  font-size: 10px;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: normal;
  line-height: 1.25;
}

.card-back > span,
.card-back small {
  color: #b8c8e4;
}

.card-face > div {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #ffae18;
}

.fine-dust-icon {
  display: block;
  width: 22px;
  height: 22px;
  flex: 0 0 auto;
  background: currentColor;
  mask: url('../assets/icons/fine-dust.svg') center / contain no-repeat;
  -webkit-mask: url('../assets/icons/fine-dust.svg') center / contain no-repeat;
}

.card-face strong {
  color: var(--color-navy);
  font-size: 17px;
  line-height: 1.1;
}

.card-back strong {
  color: #fff;
  font-size: 20px;
}

.card-face > svg {
  color: var(--color-primary);
}

.paused-badge {
  position: absolute;
  z-index: 7;
  top: 50%;
  left: 50%;
  padding: 10px 18px;
  color: #fff;
  background: rgba(8, 17, 38, 0.64);
  border-radius: 999px;
  font-size: 18px;
  font-weight: 900;
  text-align: center;
  transform: translate(-50%, -50%);
  backdrop-filter: blur(5px);
}

.run-lock-screen {
  position: absolute;
  z-index: 80;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 64px var(--content-padding) 30px;
  overflow: hidden;
  color: #fff;
  border-radius: inherit;
}

.lock-scrim {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background:
    radial-gradient(circle at 50% 18%, rgba(67, 135, 255, 0.32), transparent 34%),
    linear-gradient(180deg, rgba(7, 15, 35, 0.64), rgba(5, 11, 24, 0.9));
  backdrop-filter: blur(8px);
}

.lock-content {
  position: relative;
  z-index: 1;
  display: grid;
  width: min(100%, 328px);
  max-width: 100%;
  align-content: center;
  gap: 16px;
  overflow: hidden;
  text-align: center;
}

.lock-status {
  justify-self: center;
  display: inline-flex;
  min-height: 36px;
  align-items: center;
  gap: 7px;
  padding: 0 13px;
  color: rgba(255, 255, 255, 0.92);
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 999px;
  font-size: 12px;
  font-weight: 900;
  backdrop-filter: blur(10px);
}

.lock-status i {
  width: 8px;
  height: 8px;
  background: #43e87d;
  border-radius: 50%;
  box-shadow: 0 0 0 5px rgba(67, 232, 125, 0.16);
}

.lock-primary {
  display: grid;
  width: 100%;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  justify-items: center;
  gap: 2px;
}

.lock-primary small,
.lock-metrics small {
  color: rgba(225, 235, 255, 0.76);
  font-size: 12px;
  font-weight: 900;
}

.lock-primary strong {
  display: block;
  max-width: 100%;
  overflow: hidden;
  color: #fff;
  font-size: clamp(48px, 13.5vw, 72px);
  line-height: 0.98;
  letter-spacing: 0;
  text-overflow: clip;
  white-space: nowrap;
  text-shadow: 0 12px 34px rgba(0, 0, 0, 0.32);
}

.lock-primary span {
  color: rgba(229, 239, 255, 0.86);
  font-size: 18px;
  font-weight: 900;
}

.lock-metrics {
  display: grid;
  width: 100%;
  min-width: 0;
  max-width: 100%;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  overflow: hidden;
}

.lock-metrics div {
  display: grid;
  min-width: 0;
  min-height: 78px;
  align-content: center;
  gap: 5px;
  padding: 10px 8px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 8px;
  box-shadow: 0 14px 26px rgba(0, 0, 0, 0.16);
  backdrop-filter: blur(12px);
}

.lock-metrics strong {
  overflow: hidden;
  color: #fff;
  font-size: 24px;
  line-height: 1;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.lock-metrics span {
  color: rgba(225, 235, 255, 0.74);
  font-size: 11px;
  font-weight: 900;
}

.unlock-slider {
  --unlock-progress: 0%;
  position: relative;
  display: grid;
  width: 100%;
  min-width: 0;
  max-width: 100%;
  min-height: 62px;
  align-items: center;
  margin-top: 2px;
  overflow: hidden;
  color: rgba(255, 255, 255, 0.78);
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.18), rgba(83, 161, 255, 0.18)),
    rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 22px;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(12px);
}

.unlock-slider::before {
  content: "";
  position: absolute;
  right: 18px;
  bottom: 16px;
  left: 18px;
  height: 2px;
  background:
    linear-gradient(90deg, rgba(255,255,255,.3), rgba(255,255,255,.78)),
    repeating-linear-gradient(90deg, transparent 0 12px, rgba(255,255,255,.22) 12px 18px);
  border-radius: 999px;
}

.unlock-slider > span {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 0 20px 15px;
  color: rgba(235, 244, 255, 0.82);
  font-size: 12px;
  font-weight: 900;
  text-align: center;
}

.unlock-slider b {
  position: absolute;
  bottom: 15px;
  left: 18px;
  width: calc(var(--unlock-progress) * 0.82);
  height: 4px;
  background: linear-gradient(90deg, #43e87d, #86f5ff);
  border-radius: 999px;
  box-shadow: 0 0 16px rgba(90, 230, 255, 0.42);
  pointer-events: none;
  transition: width 120ms ease;
}

.unlock-slider input {
  position: absolute;
  z-index: 3;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.unlock-slider i {
  position: absolute;
  z-index: 2;
  bottom: 6px;
  left: clamp(7px, calc(var(--unlock-progress) * 0.82 + 7px), calc(100% - 55px));
  display: grid;
  width: 50px;
  height: 50px;
  place-items: center;
  overflow: hidden;
  padding: 0;
  background: rgba(2, 11, 34, 0.72);
  border: 1px solid rgba(255, 255, 255, 0.42);
  border-radius: 50%;
  box-shadow:
    0 8px 18px rgba(0, 0, 0, 0.26),
    0 0 18px rgba(91, 210, 255, 0.28),
    inset 0 0 0 1px rgba(255, 255, 255, 0.2);
  pointer-events: none;
  transition: left 120ms ease;
  backdrop-filter: blur(8px);
}

.unlock-slider i::before {
  content: "";
  position: absolute;
  inset: auto 6px 2px;
  height: 14px;
  background: rgba(0, 0, 0, 0.22);
  filter: blur(8px);
  border-radius: 50%;
}

.unlock-slider img {
  position: absolute;
  inset: -1px;
  z-index: 1;
  display: block;
  width: calc(100% + 2px);
  height: calc(100% + 2px);
  object-fit: cover;
  border-radius: 50%;
  filter:
    saturate(1.16)
    contrast(1.04)
    drop-shadow(0 4px 8px rgba(0, 0, 0, 0.26))
    drop-shadow(0 0 8px rgba(92, 185, 255, 0.22));
}

.run-error {
  position: absolute;
  z-index: 7;
  right: 28px;
  bottom: 228px;
  left: 28px;
}

.run-error,
.run-error-inline {
  margin: 0;
  padding: 9px 12px;
  color: #b52c3a;
  background: rgba(255, 239, 241, 0.96);
  border-radius: 8px;
  font-size: 10px;
  text-align: center;
}

.loading-state {
  display: grid;
  flex: 1;
  place-items: center;
  align-content: center;
  gap: 10px;
  color: var(--color-primary);
}

.loading-state p {
  margin: 0;
  color: var(--color-muted);
  font-size: 12px;
}

.run-start-page :deep(.bottom-nav) {
  position: sticky;
  bottom: 0;
  margin-top: auto;
}

@keyframes slide-up {
  from {
    opacity: 0;
    transform: translateY(18px);
  }
}

@keyframes route-sheet-up {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
}

@keyframes start-heartbeat {
  0%, 26%, 52%, 100% {
    transform: translateX(-50%) scale(1);
  }
  12% {
    transform: translateX(-50%) scale(1.035);
  }
  38% {
    transform: translateX(-50%) scale(1.018);
  }
}

@keyframes unlock-runner-stride {
  from {
    transform: translateY(2px) rotate(-4deg);
  }

  to {
    transform: translateY(-2px) rotate(5deg);
  }
}

@media (max-height: 720px) {
  .map-stage { height: 500px; }
  .map-stage.is-map-focused { height: 570px; }
  .run-panel { gap: 10px; padding-top: 14px; }
  .start-button { bottom: 124px; width: 102px; height: 102px; }
  .status-cards article {
    min-height: 84px;
  }
}
</style>
