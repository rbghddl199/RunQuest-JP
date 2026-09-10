<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import {
  ArrowLeft,
  BrainCircuit,
  Check,
  CircleAlert,
  Clock,
  Flame,
  MapPinned,
  Navigation,
  Target,
  Trophy,
} from '@lucide/vue'
import { useRoute, useRouter } from 'vue-router'

import LiveRunMap from '../components/maps/LiveRunMap.vue'
import api from '../services/api'
import { loadKakaoMap } from '../services/kakaoMap'
import { useRunningStore } from '../stores/running'
import { useSettingsStore } from '../stores/settings'
import { formatDuration, formatPace } from '../utils/running'
import { convertDistance, convertPaceSeconds, paceUnit } from '../utils/units'

const route = useRoute()
const router = useRouter()
const runningStore = useRunningStore()
const settingsStore = useSettingsStore()
const showCompletePopup = ref(true)
const showRecordContent = ref(false)
const completionProgress = ref(0)
const saveCourseState = ref('')
const savedCourse = ref(null)
const saveCourseForm = reactive({
  name: '',
  description: '',
  visibility: 'private',
})
let completionFrame = null
let completionHideTimer = null
const distanceUnit = computed(() => settingsStore.settings?.distance_unit ?? 'km')
const isHistoryView = computed(() => route.query.source === 'attendance' || Boolean(route.query.returnTo))
const pageTitle = computed(() => (isHistoryView.value ? '러닝 상세 기록' : '러닝 완료'))

const record = computed(() => runningStore.completedResult?.record ?? runningStore.record)
const feedback = computed(() => record.value?.ai_feedback)
const routeName = computed(() => (
  record.value?.course?.name
  ?? record.value?.custom_course?.name
  ?? '자유 러닝'
))
const completedDate = computed(() => {
  const value = record.value?.completed_at ?? record.value?.started_at
  if (!value) return ''
  return new Date(value).toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    weekday: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
})
const center = computed(() => {
  const point = record.value?.track_points?.[0]
  return point ? [point.latitude, point.longitude] : [36.3504, 127.3845]
})
const hasTrackedPath = computed(() => (record.value?.track_points?.length ?? 0) >= 2)
const summaryStats = computed(() => [
  {
    label: '총 시간',
    value: formatDuration(record.value?.duration_seconds ?? 0),
  },
  {
    label: '거리',
    value: convertDistance(record.value?.distance_km ?? 0, distanceUnit.value).toFixed(2),
    unit: distanceUnit.value,
  },
  {
    label: '평균 페이스',
    value: formatPace(convertPaceSeconds(record.value?.average_pace_seconds ?? 0, distanceUnit.value)),
    unit: paceUnit(distanceUnit.value),
  },
])
const detailStats = computed(() => [
  {
    icon: Flame,
    label: '소모 칼로리',
    value: `${record.value?.calories ?? 0} kcal`,
  },
  {
    icon: Clock,
    label: '정지 시간',
    value: formatDuration(record.value?.paused_seconds ?? 0),
  },
  {
    icon: Navigation,
    label: '기록 방식',
    value: record.value?.tracking_mode === 'gps' ? 'GPS' : '시뮬레이션',
  },
])
const canSaveAsCourse = computed(() => (
  !isHistoryView.value
  && record.value
  && !record.value.course
  && !record.value.custom_course
  && (record.value.track_points?.length ?? 0) >= 2
))
const courseSaveError = computed(() => {
  if (record.value?.course || record.value?.custom_course || savedCourse.value) return ''
  if ((record.value?.track_points?.length ?? 0) < 2) {
    return '코스로 저장하려면 최소 2개 이상의 위치 기록이 필요합니다.'
  }
  return ''
})

function goBack() {
  if (!isHistoryView.value) {
    router.replace('/run/start')
    return
  }
  if (route.query.returnTo) {
    router.push(String(route.query.returnTo))
    return
  }
  router.back()
}

function playCompletionIntro() {
  const duration = 320
  const holdAfterCheck = 120
  const startedAt = performance.now()

  const step = (timestamp) => {
    const elapsed = timestamp - startedAt
    completionProgress.value = Math.min(100, Math.round((elapsed / duration) * 100))
    if (completionProgress.value < 100) {
      completionFrame = window.requestAnimationFrame(step)
      return
    }
    completionHideTimer = window.setTimeout(() => {
      showCompletePopup.value = false
      showRecordContent.value = true
    }, holdAfterCheck)
  }

  completionFrame = window.requestAnimationFrame(step)
}

async function saveRecordedCourse() {
  if (!record.value || saveCourseState.value === 'saving') return
  const name = saveCourseForm.name.trim()
  if (!name) {
    saveCourseState.value = 'name-required'
    return
  }
  saveCourseState.value = 'saving'
  try {
    const { data } = await api.post(`/runs/${record.value.id}/save-course/`, {
      name,
      description: saveCourseForm.description.trim(),
      visibility: saveCourseForm.visibility,
    })
    savedCourse.value = data.course
    runningStore.record = data.record
    if (runningStore.completedResult) {
      runningStore.completedResult.record = data.record
    }
    saveCourseState.value = 'saved'
  } catch (error) {
    saveCourseState.value = error.response?.data?.detail
      ?? error.response?.data?.route?.[0]
      ?? error.response?.data?.name?.[0]
      ?? '코스를 저장하지 못했습니다.'
  }
}

onMounted(async () => {
  const kakaoMapWarmup = loadKakaoMap().catch(() => null)

  if (!record.value || Number(record.value.id) !== Number(route.params.id)) {
    const { data } = await api.get(`/runs/${route.params.id}/`)
    runningStore.record = data
  }
  saveCourseForm.name = `${routeName.value} 코스`
  kakaoMapWarmup.catch(() => {})
  if (isHistoryView.value) {
    showCompletePopup.value = false
    showRecordContent.value = true
  } else {
    playCompletionIntro()
  }
})

onUnmounted(() => {
  if (completionFrame) window.cancelAnimationFrame(completionFrame)
  if (completionHideTimer) window.clearTimeout(completionHideTimer)
})
</script>

<template>
  <main v-if="record" class="mobile-shell completed-page">
    <div
      v-if="showCompletePopup && !isHistoryView"
      class="completion-popup"
      :class="{ 'is-complete': completionProgress >= 100 }"
      :style="{ '--progress': `${completionProgress}%` }"
      role="status"
      aria-live="polite"
    >
      <div class="completion-gauge">
        <span>
          <Check v-if="completionProgress >= 100" :size="34" stroke-width="3.2" />
          <strong v-else>{{ completionProgress }}%</strong>
        </span>
      </div>
      <strong>{{ completionProgress >= 100 ? '러닝 기록 완료' : '기록을 정리하고 있어요' }}</strong>
    </div>

    <header v-show="showRecordContent" class="completed-header">
      <button type="button" aria-label="이전 화면" @click="goBack">
        <ArrowLeft :size="24" />
      </button>
      <h1>{{ pageTitle }}</h1>
      <span aria-hidden="true"></span>
    </header>

    <section v-show="showRecordContent" class="route-card">
      <div class="route-card__heading">
        <h2>{{ routeName }}</h2>
        <p>{{ completedDate }}</p>
      </div>
      <LiveRunMap
        v-if="showRecordContent"
        :course-points="[]"
        :tracked-points="record.track_points ?? []"
        :center="center"
        :follow-current="false"
      />
      <div v-if="!hasTrackedPath" class="route-card__empty" role="status">
        <CircleAlert :size="24" />
        <strong>이동 경로가 기록되지 않았어요</strong>
        <p>위치 기록이 2개 이상 저장되면 실제로 움직인 경로만 지도에 표시됩니다.</p>
      </div>
      <div class="route-card__shade"></div>
      <div class="summary-grid">
        <div v-for="stat in summaryStats" :key="stat.label">
          <span>{{ stat.label }}</span>
          <strong>{{ stat.value }}<small v-if="stat.unit">{{ stat.unit }}</small></strong>
        </div>
      </div>
    </section>

    <section v-show="showRecordContent" class="detail-grid">
      <article v-for="item in detailStats" :key="item.label">
        <component :is="item.icon" :size="26" />
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
      </article>
    </section>

    <section v-if="showRecordContent && feedback?.headline" class="ai-feedback">
      <header>
        <span><BrainCircuit :size="25" /></span>
        <div>
          <small>RUNQUEST AI COACH</small>
          <h2>러닝 피드백</h2>
        </div>
        <strong>{{ feedback.score }}<small>/100</small></strong>
      </header>

      <div class="ai-feedback__summary">
        <h3>{{ feedback.headline }}</h3>
        <p>{{ feedback.summary }}</p>
      </div>

      <div class="feedback-list">
        <article>
          <Trophy :size="24" />
          <div>
            <strong>잘한 점</strong>
            <p v-for="item in feedback.achievements" :key="item">{{ item }}</p>
          </div>
        </article>
        <article>
          <CircleAlert :size="24" />
          <div>
            <strong>회복 체크</strong>
            <p v-for="item in feedback.cautions" :key="item">{{ item }}</p>
          </div>
        </article>
        <article>
          <Target :size="24" />
          <div>
            <strong>다음 목표</strong>
            <p>{{ feedback.next_goal.message }}</p>
          </div>
        </article>
      </div>
    </section>

    <section
      v-if="showRecordContent && !isHistoryView && (canSaveAsCourse || savedCourse || courseSaveError)"
      class="save-course-card"
    >
      <header>
        <span><MapPinned :size="22" /></span>
        <div>
          <small>MY ROUTE</small>
          <h2>이 러닝을 코스로 저장</h2>
        </div>
      </header>
      <p v-if="savedCourse">
        {{ savedCourse.name }} 코스로 저장했어요. 이제 내 코스와 게시글 작성 기록 선택에서 다시 사용할 수 있어요.
      </p>
      <p v-else-if="courseSaveError">{{ courseSaveError }}</p>
      <template v-else>
        <label>
          <span>코스 이름</span>
          <input v-model="saveCourseForm.name" maxlength="80" placeholder="예: 갑천 저녁 자유 러닝" />
        </label>
        <label>
          <span>설명</span>
          <textarea v-model="saveCourseForm.description" maxlength="300" rows="2" placeholder="코스 분위기나 기억할 점을 남겨보세요."></textarea>
        </label>
        <label>
          <span>공개 설정</span>
          <select v-model="saveCourseForm.visibility">
            <option value="private">비공개</option>
            <option value="public">공개</option>
          </select>
        </label>
        <p v-if="saveCourseState && !['saving', 'saved'].includes(saveCourseState)" class="save-course-error">
          {{ saveCourseState === 'name-required' ? '코스 이름을 입력해 주세요.' : saveCourseState }}
        </p>
        <button type="button" :disabled="saveCourseState === 'saving'" @click="saveRecordedCourse">
          {{ saveCourseState === 'saving' ? '코스 저장 중' : '내 코스로 저장' }}
        </button>
      </template>
    </section>

    <footer v-if="showRecordContent && !isHistoryView" class="completed-actions">
      <button type="button" class="primary" @click="router.replace('/home')">
        기록 저장
      </button>
    </footer>
  </main>
</template>

<style scoped>
.completed-page {
  position: relative;
  min-height: var(--app-height);
  padding: 30px var(--content-padding) 28px;
  color: #f8fbff;
  background:
    radial-gradient(circle at 80% 0%, rgba(29, 130, 255, 0.18), transparent 36%),
    radial-gradient(circle at 12% 34%, rgba(63, 229, 255, 0.12), transparent 32%),
    #050912;
}

.completion-popup {
  position: absolute;
  z-index: 90;
  top: 50%;
  left: 50%;
  display: grid;
  width: 188px;
  height: 188px;
  align-items: center;
  align-content: center;
  justify-content: center;
  justify-items: center;
  gap: 10px;
  color: #fff;
  background:
    radial-gradient(circle at 50% 28%, rgba(69, 244, 225, 0.24), transparent 34%),
    rgba(8, 17, 33, 0.96);
  border: 1px solid rgba(88, 166, 255, 0.46);
  border-radius: 50%;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.42);
  text-align: center;
  transform: translate(-50%, -50%);
  backdrop-filter: blur(18px);
  transition: transform 260ms ease, border-color 260ms ease, box-shadow 260ms ease;
}

.completion-popup.is-complete {
  border-color: rgba(69, 244, 225, 0.88);
  box-shadow:
    0 20px 50px rgba(0, 0, 0, 0.42),
    0 0 34px rgba(69, 244, 225, 0.26);
  transform: translate(-50%, -50%) scale(1.04);
}

.completion-gauge {
  position: relative;
  display: grid;
  width: 86px;
  height: 86px;
  place-items: center;
  background:
    conic-gradient(#45f4e1 var(--progress), rgba(117, 157, 210, 0.24) 0),
    rgba(255, 255, 255, 0.08);
  border-radius: 50%;
}

.completion-gauge::before {
  position: absolute;
  inset: 8px;
  content: '';
  background: #081121;
  border-radius: 50%;
  box-shadow: inset 0 0 18px rgba(69, 244, 225, 0.12);
}

.completion-gauge span {
  position: relative;
  z-index: 1;
  display: grid;
  width: 58px;
  height: 58px;
  color: #071222;
  place-items: center;
  background: linear-gradient(145deg, #45f4e1, #7dfff0);
  border-radius: 50%;
  transition: transform 220ms ease;
}

.completion-popup.is-complete .completion-gauge span {
  animation: completion-pop 360ms cubic-bezier(.2, 1.4, .38, 1) both;
}

.completion-gauge span > strong {
  color: #071222;
  font-size: 15px;
  font-weight: 950;
}

.completion-popup strong {
  max-width: 118px;
  font-size: 14px;
  line-height: 1.35;
}

.completed-header {
  display: grid;
  grid-template-columns: 54px 1fr 54px;
  align-items: center;
  gap: 10px;
  margin-bottom: 22px;
}

.completed-header button,
.share-chip {
  display: inline-flex;
  min-height: 48px;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(159, 189, 230, 0.22);
  border-radius: 999px;
}

.completed-header button:first-child {
  width: 48px;
}

.share-chip {
  gap: 7px;
  padding: 0 15px;
  font-size: 14px;
  font-weight: 800;
}

.completed-header h1 {
  margin: 0;
  font-size: 22px;
  text-align: center;
}

.route-card {
  position: relative;
  min-height: 318px;
  overflow: hidden;
  background: #e8f1fb;
  border: 1px solid rgba(112, 150, 204, 0.22);
  border-radius: 8px;
  box-shadow: 0 18px 42px rgba(0, 0, 0, 0.24);
}

.route-card :deep(.live-map) {
  min-height: 318px;
  height: 318px;
  background: #e8f1fb;
  filter: none;
}

.route-card :deep(.live-map__state) {
  color: #49d8ff;
  background: #e8f1fb;
}

.route-card__shade {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(180deg, rgba(7, 13, 24, 0.22), rgba(7, 13, 24, 0.01) 34%, rgba(7, 13, 24, 0.38));
}

.route-card__empty {
  position: absolute;
  z-index: 3;
  top: 92px;
  right: 24px;
  left: 24px;
  display: grid;
  justify-items: center;
  gap: 7px;
  padding: 16px 14px;
  color: #fff;
  background: rgba(5, 15, 30, 0.74);
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 8px;
  text-align: center;
  backdrop-filter: blur(10px);
}

.route-card__empty svg {
  color: #49d8ff;
}

.route-card__empty strong,
.route-card__empty p {
  margin: 0;
}

.route-card__empty strong {
  font-size: 14px;
  line-height: 1.25;
}

.route-card__empty p {
  max-width: 230px;
  color: rgba(233, 240, 250, 0.74);
  font-size: 11px;
  line-height: 1.45;
}

.route-card__heading {
  position: absolute;
  z-index: 2;
  top: 14px;
  left: 50%;
  display: grid;
  width: min(72%, 236px);
  justify-items: center;
  gap: 2px;
  padding: 7px 10px;
  overflow: hidden;
  background: rgba(5, 15, 30, 0.68);
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 8px;
  box-shadow: 0 9px 18px rgba(0, 0, 0, 0.16);
  text-align: center;
  transform: translateX(-50%);
  backdrop-filter: blur(10px);
}

.route-card__heading h2,
.route-card__heading p {
  margin: 0;
}

.route-card__heading h2 {
  width: 100%;
  overflow: hidden;
  color: #fff;
  font-size: 16px;
  line-height: 1.16;
  text-overflow: ellipsis;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.36);
  white-space: nowrap;
}

.route-card__heading p {
  color: rgba(255, 235, 241, 0.82);
  font-size: 10px;
  line-height: 1.15;
}

.summary-grid {
  position: absolute;
  z-index: 2;
  right: 18px;
  bottom: 18px;
  left: 18px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.summary-grid div {
  position: relative;
  display: grid;
  box-sizing: border-box;
  justify-items: center;
  align-content: center;
  min-height: 58px;
  min-width: 0;
  padding: 8px 4px;
  background: rgba(7, 13, 24, 0.68);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  text-align: center;
  backdrop-filter: blur(8px);
}

.summary-grid span {
  display: block;
  color: rgba(233, 240, 250, 0.72);
  font-size: 12px;
}

.summary-grid strong {
  display: block;
  width: 100%;
  margin-top: 6px;
  overflow: hidden;
  font-size: clamp(13px, 3.25vw, 18px);
  font-variant-numeric: tabular-nums;
  line-height: 1.08;
  text-align: center;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.summary-grid small {
  margin-left: 3px;
  font-size: 9px;
  white-space: nowrap;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin: 12px 19px 0;
}

.detail-grid article {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  min-height: 88px;
  align-content: center;
  justify-items: center;
  gap: 4px;
  box-sizing: border-box;
  padding: 12px 6px;
  color: #1e88ff;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(139, 171, 215, 0.2);
  border-radius: 8px;
  text-align: center;
}

.detail-grid article > svg {
  justify-self: center;
}

.detail-grid span {
  display: block;
  width: 100%;
  color: rgba(233, 240, 250, 0.64);
  font-size: 11px;
  line-height: 1.25;
  text-align: center;
}

.detail-grid strong {
  display: block;
  width: 100%;
  color: #fff;
  font-size: clamp(13px, 3.35vw, 15px);
  font-variant-numeric: tabular-nums;
  line-height: 1.25;
  text-align: center;
  white-space: nowrap;
}

.ai-feedback__summary {
  text-align: center;
}

.ai-feedback {
  margin-top: 14px;
  padding: 18px;
  background: rgba(16, 27, 42, 0.84);
  border: 1px solid rgba(17, 132, 255, 0.54);
  border-radius: 8px;
}

.ai-feedback header {
  display: grid;
  grid-template-columns: 48px 1fr auto;
  align-items: center;
  gap: 11px;
}

.ai-feedback header > span {
  display: grid;
  width: 48px;
  height: 48px;
  place-items: center;
  background: linear-gradient(145deg, #2f8bff, #0866ff);
  border-radius: 50%;
}

.ai-feedback small {
  color: #45f4e1;
  font-size: 10px;
  font-weight: 900;
}

.ai-feedback h2,
.ai-feedback h3,
.ai-feedback p {
  margin: 0;
}

.ai-feedback h2 {
  font-size: 20px;
}

.ai-feedback header > strong {
  color: #1e88ff;
  font-size: 34px;
}

.ai-feedback header > strong small {
  color: rgba(233, 240, 250, 0.82);
  font-size: 15px;
}

.ai-feedback__summary {
  margin-top: 14px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
}

.ai-feedback__summary h3 {
  font-size: 15px;
}

.ai-feedback__summary p {
  margin-top: 8px;
  color: rgba(233, 240, 250, 0.68);
  font-size: 12px;
  line-height: 1.6;
}

.feedback-list {
  display: grid;
  gap: 8px;
  margin-top: 12px;
}

.feedback-list article {
  display: grid;
  grid-template-columns: 34px 1fr;
  gap: 10px;
  padding: 13px;
  color: #1e88ff;
  background: rgba(255, 255, 255, 0.035);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
}

.feedback-list article:nth-child(2) {
  color: #ffac3d;
}

.feedback-list strong {
  display: block;
  color: #fff;
  font-size: 13px;
}

.feedback-list p {
  position: relative;
  margin-top: 5px;
  padding-left: 10px;
  color: rgba(233, 240, 250, 0.72);
  font-size: 11px;
  line-height: 1.45;
}

.feedback-list p::before {
  position: absolute;
  top: 7px;
  left: 0;
  width: 4px;
  height: 4px;
  content: '';
  background: #32d8ff;
  border-radius: 50%;
}

.memo-card {
  display: grid;
  grid-template-columns: 34px 1fr 28px;
  align-items: center;
  gap: 12px;
  margin-top: 14px;
  padding: 16px;
  color: #d9e8ff;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(139, 171, 215, 0.22);
  border-radius: 8px;
}

.memo-card h2,
.memo-card p {
  margin: 0;
}

.memo-card h2 {
  font-size: 15px;
}

.memo-card p {
  margin-top: 4px;
  color: rgba(233, 240, 250, 0.72);
  font-size: 12px;
  line-height: 1.5;
}

.save-course-card {
  display: grid;
  gap: 12px;
  margin-top: 14px;
  padding: 16px;
  color: #f8fbff;
  background: rgba(16, 27, 42, 0.86);
  border: 1px solid rgba(69, 244, 225, 0.3);
  border-radius: 8px;
}

.save-course-card header {
  display: grid;
  grid-template-columns: 42px 1fr;
  align-items: center;
  gap: 10px;
}

.save-course-card header > span {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  color: #071222;
  background: #45f4e1;
  border-radius: 50%;
}

.save-course-card h2,
.save-course-card p {
  margin: 0;
}

.save-course-card h2 {
  font-size: 16px;
}

.save-course-card small {
  color: #45f4e1;
  font-size: 10px;
  font-weight: 900;
}

.save-course-card p {
  color: rgba(233, 240, 250, 0.72);
  font-size: 12px;
  line-height: 1.55;
}

.save-course-card label {
  display: grid;
  gap: 6px;
  color: rgba(233, 240, 250, 0.78);
  font-size: 11px;
  font-weight: 900;
}

.save-course-card input,
.save-course-card textarea,
.save-course-card select {
  width: 100%;
  padding: 11px;
  color: #f8fbff;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(139, 171, 215, 0.24);
  border-radius: 8px;
  outline: 0;
}

.save-course-card textarea {
  resize: vertical;
}

.save-course-card button {
  min-height: 50px;
  color: #071222;
  background: #45f4e1;
  border-radius: 8px;
  font-weight: 950;
}

.save-course-card button:disabled {
  opacity: 0.64;
}

.save-course-error {
  color: #ffd6da !important;
}

.completed-actions {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
  margin-top: 16px;
}

.completed-actions button {
  display: inline-flex;
  min-height: 56px;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #fff;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 900;
}

.completed-actions .primary {
  background: linear-gradient(145deg, #177dff, #0866ff);
}

.completed-actions .secondary {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(122, 169, 232, 0.64);
}

@keyframes completion-pop {
  0% { transform: scale(0.72); opacity: 0.72; }
  72% { transform: scale(1.12); opacity: 1; }
  100% { transform: scale(1); opacity: 1; }
}
</style>
