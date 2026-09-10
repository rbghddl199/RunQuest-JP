<script setup>
import { computed, onBeforeUnmount, onMounted } from 'vue'
import { LockKeyhole, Pause, Play, Square } from '@lucide/vue'
import { useRouter } from 'vue-router'

import LiveRunMap from '../components/maps/LiveRunMap.vue'
import { useRunningStore } from '../stores/running'
import { useSettingsStore } from '../stores/settings'
import { formatDuration, formatPace } from '../utils/running'
import { convertDistance, convertPaceSeconds, paceUnit } from '../utils/units'

const router = useRouter()
const runningStore = useRunningStore()
const settingsStore = useSettingsStore()
const distanceUnit = computed(() => settingsStore.settings?.distance_unit ?? 'km')

const course = computed(() => (
  runningStore.record?.course ?? runningStore.record?.custom_course
))
const center = computed(() => {
  if (runningStore.points.length) {
    const point = runningStore.points[runningStore.points.length - 1]
    return [point.latitude, point.longitude]
  }
  return [
    Number(course.value?.start_latitude ?? 36.3504),
    Number(course.value?.start_longitude ?? 127.3845),
  ]
})
const calories = computed(() => Math.round(runningStore.distanceKm * 65))

onMounted(async () => {
  const record = await runningStore.restoreActive()
  if (!record) {
    await router.replace('/run/start')
    return
  }
  if (!runningStore.timerId) {
    runningStore.beginTracking(record.course ?? record.custom_course)
  }
})

onBeforeUnmount(() => {
  if (runningStore.isActive) {
    runningStore.syncProgress()
  }
})

async function finishRun() {
  const result = await runningStore.finish()
  if (result?.cancelled) {
    window.alert(result.detail ?? '100m 이상 이동한 러닝만 기록으로 저장됩니다.')
    await router.replace('/run/start')
    return
  }
  if (result) {
    await router.replace(`/run/completed/${result.record.id}`)
    return
  }
  if (runningStore.trackingError) {
    runningStore.reset()
    await router.replace('/run/start')
  }
}
</script>

<template>
  <main v-if="runningStore.record" class="mobile-shell active-run">
    <header>
      <span class="gps-status"><i></i> {{ runningStore.record.tracking_mode === 'gps' ? 'GPS 연결' : '시뮬레이션' }}</span>
      <strong>{{ course?.name ?? '자유 러닝' }}</strong>
      <LockKeyhole :size="20" />
    </header>

    <section class="primary-metrics">
      <p>시간</p>
      <strong>{{ formatDuration(runningStore.elapsedSeconds) }}</strong>
      <p>거리</p>
      <h1>{{ convertDistance(runningStore.distanceKm, distanceUnit).toFixed(2) }}<span>{{ distanceUnit }}</span></h1>
      <div>
        <span><small>페이스</small><strong>{{ formatPace(convertPaceSeconds(runningStore.paceSeconds, distanceUnit)) }}</strong><i>{{ paceUnit(distanceUnit) }}</i></span>
        <span><small>칼로리</small><strong>{{ calories }}</strong><i>kcal</i></span>
      </div>
    </section>

    <section class="active-map">
      <LiveRunMap
        :course-points="course?.route_points ?? []"
        :tracked-points="runningStore.points"
        :center="center"
      />
      <div v-if="runningStore.isPaused" class="paused-overlay">일시정지</div>
    </section>

    <p v-if="runningStore.trackingError" class="tracking-error" role="alert">
      {{ runningStore.trackingError }}
    </p>

    <footer class="run-controls">
      <button
        class="pause-button"
        type="button"
        :aria-label="runningStore.isPaused ? '러닝 재개' : '러닝 일시정지'"
        @click="runningStore.togglePause"
      >
        <Play v-if="runningStore.isPaused" :size="30" fill="currentColor" />
        <Pause v-else :size="30" fill="currentColor" />
      </button>
      <button
        class="finish-button"
        type="button"
        :disabled="runningStore.isFinishing"
        @click="finishRun"
      >
        <Square :size="23" fill="currentColor" />
        {{ runningStore.isFinishing ? '저장 중' : '완료' }}
      </button>
    </footer>
  </main>
</template>

<style scoped>
.active-run {
  display: grid;
  min-height: 100vh;
  grid-template-rows: auto auto minmax(260px, 1fr) auto auto;
  color: #fff;
  background: #081421;
}

header {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  padding: 20px 18px 10px;
  font-size: 11px;
}

header > strong {
  max-width: 180px;
  overflow: hidden;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

header > svg {
  justify-self: end;
}

.gps-status {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #85edb7;
}

.gps-status i {
  width: 8px;
  height: 8px;
  background: #2bd57f;
  border-radius: 50%;
}

.primary-metrics {
  padding: 8px 24px 20px;
  text-align: center;
}

.primary-metrics > p {
  margin: 9px 0 2px;
  color: #91a0b2;
  font-size: 10px;
}

.primary-metrics > strong {
  font-size: 28px;
  font-weight: 500;
}

.primary-metrics h1 {
  margin: 0;
  font-size: 54px;
  line-height: 1.1;
}

.primary-metrics h1 span {
  margin-left: 6px;
  color: #b7c3cf;
  font-size: 17px;
  font-weight: 400;
}

.primary-metrics > div {
  display: grid;
  grid-template-columns: 1fr 1fr;
  margin-top: 19px;
  padding-top: 16px;
  border-top: 1px solid #283747;
}

.primary-metrics > div > span {
  display: grid;
  grid-template-columns: auto auto;
  justify-content: center;
  gap: 3px;
}

.primary-metrics > div > span + span {
  border-left: 1px solid #283747;
}

.primary-metrics small {
  grid-column: 1 / -1;
  color: #91a0b2;
  font-size: 9px;
}

.primary-metrics div strong {
  font-size: 21px;
}

.primary-metrics div i {
  align-self: end;
  color: #91a0b2;
  font-size: 10px;
  font-style: normal;
}

.active-map {
  position: relative;
  min-height: 260px;
}

.paused-overlay {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  font-size: 28px;
  font-weight: 800;
  background: rgba(8, 20, 33, 0.64);
  backdrop-filter: blur(2px);
}

.run-controls {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  padding: 18px 24px max(22px, env(safe-area-inset-bottom));
  background: #081421;
}

.run-controls button {
  display: flex;
  min-height: 62px;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #fff;
  font-weight: 700;
  border-radius: var(--radius-medium);
}

.pause-button {
  background: var(--color-primary);
}

.finish-button {
  background: #ef4d5f;
}

.tracking-error {
  margin: 0;
  padding: 9px 18px;
  color: #ffd6da;
  font-size: 11px;
  background: #6c2430;
  text-align: center;
}
</style>
