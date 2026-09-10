<script setup>
import { onMounted } from 'vue'
import { ArrowLeft, CalendarDays, ChevronRight, Route } from '@lucide/vue'

import AppState from '../components/common/AppState.vue'
import { useProfileStore } from '../stores/profile'
import { formatDuration, formatPace } from '../utils/running'

const profileStore = useProfileStore()

async function deleteRecord(record) {
  if (!window.confirm('이 러닝 기록을 삭제할까요?')) return
  await profileStore.deleteRecord(record.id)
}

onMounted(() => profileStore.loadRecords())
</script>

<template>
  <main class="mobile-shell sub-page">
    <header class="sub-header">
      <RouterLink to="/my" aria-label="마이페이지로 돌아가기"><ArrowLeft /></RouterLink>
      <h1>러닝 기록</h1>
      <span></span>
    </header>

    <section class="records">
      <article
        v-for="record in profileStore.records"
        :key="record.id"
        class="run-record"
      >
        <RouterLink :to="{ path: `/run/completed/${record.id}`, query: { returnTo: '/my/records' } }">
          <span><Route :size="24" /></span>
          <div>
            <small><CalendarDays :size="13" /> {{ new Date(record.completed_at).toLocaleDateString('ko-KR') }}</small>
            <h2>{{ record.course?.name ?? record.custom_course?.name ?? '자유 러닝' }}</h2>
            <p>
              <strong>{{ record.distance_km }}km</strong>
              {{ formatDuration(record.duration_seconds) }}
              {{ formatPace(record.average_pace_seconds) }}/km
            </p>
          </div>
          <ChevronRight :size="19" />
        </RouterLink>
        <button type="button" class="delete-record" aria-label="러닝 기록 삭제" @click="deleteRecord(record)">
          🗑️
        </button>
      </article>

      <AppState
        v-if="profileStore.isLoading"
        type="loading"
        title="러닝 기록을 불러오는 중입니다"
        message="완료한 러닝을 정리하고 있어요."
      />
      <AppState
        v-else-if="profileStore.errorMessage"
        type="error"
        title="러닝 기록을 불러오지 못했어요"
        :message="profileStore.errorMessage"
        action-label="다시 시도"
        @action="profileStore.loadRecords"
      />
      <AppState
        v-else-if="!profileStore.records.length"
        type="empty"
        title="아직 완료한 러닝이 없어요"
        message="첫 러닝을 완료하면 기록이 여기에 쌓입니다."
        action-label="러닝 시작하기"
        action-to="/run/start"
      />
    </section>
  </main>
</template>

<style scoped>
.sub-page { background:#f7faff; }
.sub-header { display:grid; grid-template-columns:42px 1fr 42px; align-items:center; padding:18px var(--content-padding); background:#fff; border-bottom:1px solid var(--color-border); }
.sub-header a { display:grid; width:40px; height:40px; place-items:center; }
.sub-header h1 { margin:0; font-size:18px; text-align:center; }
.records { padding:18px var(--content-padding); }
.run-record { display:grid; grid-template-columns:minmax(0,1fr) 42px; align-items:center; gap:8px; margin-bottom:10px; padding:12px; background:#fff; border:1px solid var(--color-border); border-radius:var(--radius-medium); }
.run-record > a { display:grid; grid-template-columns:48px 1fr auto; align-items:center; gap:12px; min-width:0; }
.run-record span { display:grid; width:48px; height:48px; place-items:center; color:var(--color-primary); background:var(--color-primary-soft); border-radius:50%; }
.run-record div { min-width:0; }
.run-record small { display:flex; align-items:center; gap:4px; color:var(--color-muted); font-size:9px; }
.run-record h2 { overflow:hidden; margin:4px 0; font-size:14px; text-overflow:ellipsis; white-space:nowrap; }
.run-record p { display:flex; flex-wrap:wrap; gap:9px; margin:0; color:var(--color-muted); font-size:10px; }
.run-record p strong { color:var(--color-primary); }
.delete-record { display:grid; width:28px; height:28px; place-items:center; justify-self:end; color:#ef3f64; background:transparent; border-radius:50%; font-size:15px; font-weight:900; line-height:1; }
</style>
