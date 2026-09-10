<script setup>
import { computed, onMounted, ref } from 'vue'
import { ArrowLeft, ChevronLeft, ChevronRight, Flame, Route } from '@lucide/vue'
import { useRoute, useRouter } from 'vue-router'

import { useProfileStore } from '../stores/profile'
import { formatDuration, formatPace } from '../utils/running'

const profileStore = useProfileStore()
const route = useRoute()
const router = useRouter()
const cursor = ref(new Date())
const selectedDate = ref(null)
const weekdayLabels = ['일', '월', '화', '수', '목', '금', '토']
const todayKey = computed(() => {
  const parts = new Intl.DateTimeFormat('en', {
    timeZone: 'Asia/Seoul',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(new Date())
  const value = Object.fromEntries(parts.map((part) => [part.type, part.value]))
  return `${value.year}-${value.month}-${value.day}`
})

const attendanceMap = computed(() => new Map(
  (profileStore.attendance?.attendances ?? []).map((item) => [item.date, item]),
))
const recordsByDate = computed(() => profileStore.attendance?.records_by_date ?? {})
const title = computed(() => `${cursor.value.getFullYear()}년 ${cursor.value.getMonth() + 1}월`)
const selectedRecords = computed(() => recordsByDate.value[selectedDate.value] ?? [])
const selectedLabel = computed(() => {
  if (!selectedDate.value) return ''
  return new Date(`${selectedDate.value}T00:00:00`).toLocaleDateString('ko-KR', {
    month: 'long',
    day: 'numeric',
    weekday: 'short',
  })
})
const days = computed(() => {
  const year = cursor.value.getFullYear()
  const month = cursor.value.getMonth()
  const firstDay = new Date(year, month, 1).getDay()
  const lastDate = new Date(year, month + 1, 0).getDate()
  return [
    ...Array.from({ length: firstDay }, () => null),
    ...Array.from({ length: lastDate }, (_, index) => {
      const day = index + 1
      const key = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
      const records = recordsByDate.value[key] ?? []
      return {
        day,
        key,
        attendance: attendanceMap.value.get(key),
        records,
      }
    }),
  ]
})

function load() {
  const queryDate = typeof route.query.date === 'string' ? route.query.date : null
  if (queryDate) {
    const [year, month] = queryDate.split('-').map(Number)
    if (year && month) {
      cursor.value = new Date(year, month - 1, 1)
    }
  }
  selectedDate.value = queryDate
  return profileStore.loadAttendance(
    cursor.value.getFullYear(),
    cursor.value.getMonth() + 1,
  )
}

function moveMonth(offset) {
  cursor.value = new Date(
    cursor.value.getFullYear(),
    cursor.value.getMonth() + offset,
    1,
  )
  load()
}

function selectDay(item) {
  if (!item) return
  selectedDate.value = item.key
  router.replace({ path: '/my/attendance', query: { date: item.key } })
}

function goBack() {
  router.push('/my')
}

function recordTitle(record) {
  return record.course?.name ?? record.custom_course?.name ?? '자유 러닝'
}

function recordTime(record) {
  if (!record.completed_at) return '완료 시간 없음'
  return new Date(record.completed_at).toLocaleTimeString('ko-KR', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(load)
</script>

<template>
  <main class="mobile-shell attendance-page">
    <header class="sub-header">
      <button type="button" aria-label="이전 화면" @click="goBack">
        <ArrowLeft />
      </button>
      <h1>출석 현황</h1>
      <span></span>
    </header>

    <template v-if="!selectedDate">
      <section class="attendance-summary">
        <span><Flame :size="25" fill="currentColor" /></span>
        <div>
          <small>현재 연속 출석</small>
          <strong>{{ profileStore.attendance?.streak_days ?? 0 }}일</strong>
        </div>
        <div>
          <small>이번 달 러닝</small>
          <strong>{{ profileStore.attendance?.count ?? 0 }}회</strong>
        </div>
      </section>

      <section class="calendar">
        <header>
          <button type="button" aria-label="이전 달" @click="moveMonth(-1)"><ChevronLeft /></button>
          <h2>{{ title }}</h2>
          <button type="button" aria-label="다음 달" @click="moveMonth(1)"><ChevronRight /></button>
        </header>
        <div class="weekdays"><span v-for="label in weekdayLabels" :key="label">{{ label }}</span></div>
        <div class="days">
          <button
            v-for="(item, index) in days"
            :key="item?.key ?? `blank-${index}`"
            type="button"
            :disabled="!item"
            :class="{ 'has-records': item?.records.length, 'is-today': item?.key === todayKey }"
            @click="selectDay(item)"
          >
            <template v-if="item">
              <span>{{ item.day }}</span>
              <i v-if="item.attendance"><Flame :size="16" fill="currentColor" /></i>
              <small v-if="item.records.length > 1">{{ item.records.length }}회</small>
            </template>
          </button>
        </div>
        <p><Flame :size="16" fill="currentColor" /> 날짜를 누르면 그날의 러닝 기록을 볼 수 있어요.</p>
      </section>
    </template>

    <section v-else class="date-records">
      <div class="date-records__title">
        <small>러닝 기록</small>
        <h2>{{ selectedLabel }}</h2>
        <p>{{ selectedRecords.length ? `${selectedRecords.length}개의 기록이 있어요` : '이날 완료한 기록이 없어요' }}</p>
      </div>

      <div v-if="selectedRecords.length" class="record-list">
        <RouterLink
          v-for="record in selectedRecords"
          :key="record.id"
          class="record-card"
          :to="{ path: `/run/completed/${record.id}`, query: { source: 'attendance', returnTo: `/my/attendance?date=${selectedDate}` } }"
        >
          <span><Route :size="22" /></span>
          <div>
            <strong>{{ recordTitle(record) }}</strong>
            <small>{{ recordTime(record) }}</small>
            <p>
              {{ record.distance_km }}km ·
              {{ formatDuration(record.duration_seconds) }} ·
              {{ formatPace(record.average_pace_seconds) }}/km
            </p>
          </div>
          <ChevronRight :size="19" />
        </RouterLink>
      </div>

      <div v-else class="empty-records">
        <Flame :size="28" />
        <p>출석 기록이 없는 날짜예요.</p>
      </div>
    </section>
  </main>
</template>

<style scoped>
.attendance-page { min-height:100vh; background:var(--color-background); }
.sub-header { display:grid; grid-template-columns:42px 1fr 42px; align-items:center; padding:18px var(--content-padding); background:var(--color-surface); border-bottom:1px solid var(--color-border); }
.sub-header button { display:grid; width:40px; height:40px; place-items:center; color:var(--color-navy); background:transparent; }
.sub-header h1 { margin:0; color:var(--color-navy); font-size:18px; text-align:center; }
.attendance-summary { display:grid; grid-template-columns:48px 1fr 1fr; align-items:center; gap:12px; margin:18px var(--content-padding); padding:17px; color:#f27a22; background:#fff4e9; border:1px solid #ffd9b9; border-radius:var(--radius-medium); }
.attendance-summary > span { display:grid; width:45px; height:45px; place-items:center; background:#fff; border-radius:50%; }
.attendance-summary div { display:grid; gap:2px; }
.attendance-summary div + div { padding-left:12px; border-left:1px solid #f3c9a8; }
.attendance-summary small { color:#8c715d; font-size:9px; }
.attendance-summary strong { color:#10213d; font-size:18px; }
.calendar { margin:0 var(--content-padding); padding:18px 14px; background:var(--color-surface); border:1px solid var(--color-border); border-radius:var(--radius-medium); }
.calendar > header { display:grid; grid-template-columns:40px 1fr 40px; align-items:center; }
.calendar header button { display:grid; width:38px; height:38px; place-items:center; color:var(--color-navy); background:transparent; }
.calendar h2 { margin:0; color:var(--color-navy); font-size:17px; text-align:center; }
.weekdays,.days { display:grid; grid-template-columns:repeat(7,minmax(0,1fr)); }
.weekdays { margin-top:18px; color:var(--color-muted); font-size:10px; text-align:center; }
.days { margin-top:8px; gap:2px; }
.days > button { position:relative; display:grid; min-height:56px; place-items:center; align-content:center; gap:2px; color:var(--color-text); background:transparent; border-radius:14px; font-size:11px; }
.days > button:disabled { opacity:0; pointer-events:none; }
.days > button.has-records { background:#fff7ed; box-shadow:inset 0 0 0 1px #ffd9b9; }
.days > button.is-today { box-shadow:inset 0 0 0 1px var(--color-primary); }
.days i { display:grid; width:25px; height:25px; place-items:center; color:#fff; background:#ff7a22; border-radius:50%; }
.days small { position:absolute; right:3px; bottom:3px; padding:1px 5px; color:#f47a22; background:#fff; border-radius:999px; font-size:8px; font-weight:800; }
.calendar > p { display:flex; align-items:center; justify-content:center; gap:5px; margin:16px 0 0; color:var(--color-muted); font-size:9px; }
.calendar > p svg { color:#ff7a22; }
.date-records { margin:18px var(--content-padding) 96px; }
.date-records__title { padding:20px; color:#fff; background:linear-gradient(135deg,#0b6cff,#19c9e6); border-radius:22px; box-shadow:0 16px 30px rgba(8,102,255,.22); }
.date-records__title small { font-size:10px; opacity:.82; }
.date-records__title h2 { margin:4px 0; font-size:24px; }
.date-records__title p { margin:0; font-size:12px; opacity:.9; }
.record-list { display:grid; gap:10px; margin-top:14px; }
.record-card { display:grid; grid-template-columns:42px 1fr 20px; align-items:center; gap:10px; padding:14px; color:var(--color-navy); background:var(--color-surface); border:1px solid var(--color-border); border-radius:16px; box-shadow:0 8px 18px rgba(15,23,42,.05); }
.record-card > span { display:grid; width:42px; height:42px; place-items:center; color:var(--color-primary); background:var(--color-primary-soft); border-radius:50%; }
.record-card div { display:grid; gap:3px; min-width:0; }
.record-card strong { overflow:hidden; font-size:13px; text-overflow:ellipsis; white-space:nowrap; }
.record-card small { color:var(--color-muted); font-size:10px; }
.record-card p { margin:0; color:var(--color-muted); font-size:11px; }
.empty-records { display:grid; place-items:center; gap:8px; margin-top:18px; padding:46px 18px; color:var(--color-muted); background:var(--color-surface); border:1px dashed var(--color-border); border-radius:18px; }
.empty-records p { margin:0; font-size:12px; }
</style>
