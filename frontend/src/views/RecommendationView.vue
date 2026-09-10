<script setup>
import { computed, onMounted } from 'vue'
import {
  Bot,
  MapPinned,
  RefreshCw,
  ShieldCheck,
  Sparkles,
} from '@lucide/vue'

import AppState from '../components/common/AppState.vue'
import FavoriteButton from '../components/courses/FavoriteButton.vue'
import AppBottomNav from '../components/navigation/AppBottomNav.vue'
import { useCourseStore } from '../stores/courses'
import { useRecommendationStore } from '../stores/recommendations'
import { getCourseImageForCourse } from '../utils/courseImages'

const recommendationStore = useRecommendationStore()
const courseStore = useCourseStore()

const course = computed(() => recommendationStore.course)
const session = computed(() => recommendationStore.session)
const recommendation = computed(() => recommendationStore.recommendation)

const userStateLabels = {
  new: '신규 러너',
  active: '기존 러너',
  returning: '복귀 러너',
  chat: '챗봇 대화',
}

const locationDistance = computed(
  () => recommendation.value?.score_details?.location?.distance_km,
)

onMounted(() => {
  if (!recommendationStore.loadChatRecommendation()) {
    recommendationStore.loadCurrent()
  }
})
</script>

<template>
  <main class="mobile-shell recommendation-page">
    <div class="recommendation-page__content">
      <header class="recommendation-header">
        <div>
          <p>RUNQUEST AI</p>
          <h1>AI 맞춤 추천</h1>
        </div>
        <span><Bot :size="25" /></span>
      </header>

      <nav class="recommendation-tabs" aria-label="추천 메뉴">
        <button type="button" class="is-active">맞춤 추천</button>
        <RouterLink to="/chat">AI 챗봇</RouterLink>
      </nav>

      <AppState
        v-if="recommendationStore.isLoading && !course"
        type="loading"
        title="러닝 성향을 분석하고 있어요"
        message="최근 기록과 선호도를 바탕으로 코스를 고르고 있어요."
      />
      <AppState
        v-else-if="recommendationStore.errorMessage && !course"
        type="error"
        title="추천을 불러오지 못했어요"
        :message="recommendationStore.errorMessage"
        :action-label="recommendationStore.errorMessage.includes('설문') ? '설문 작성하기' : '다시 시도'"
        :action-to="recommendationStore.errorMessage.includes('설문') ? '/survey' : ''"
        @action="recommendationStore.loadCurrent"
      />
      <AppState
        v-else-if="!course"
        type="empty"
        title="아직 준비된 AI 추천이 없어요"
        message="AI 재추천을 눌렀을 때만 새로운 코스를 추천해 드릴게요."
        action-label="AI 추천 받기"
        @action="recommendationStore.recommendAgain"
      />

      <template v-else-if="course && session && recommendation">
        <section class="recommendation-intro">
          <div>
            <div class="recommendation-intro__title">
              <h2>오늘의 AI 추천</h2>
              <span>AI Pick</span>
            </div>
            <p>
              {{ userStateLabels[session.user_state] ?? '맞춤 러너' }} 기준으로 지금 가장 어울리는 코스 1개를 골랐어요.
            </p>
            <p class="location-status" :class="{ 'is-applied': session.location.applied }">
              <MapPinned :size="14" />
              <span v-if="session.location.applied">
                현재 위치 우선 추천
                <template v-if="locationDistance != null">
                  · 코스까지 {{ locationDistance }}km
                </template>
              </span>
              <span v-else>위치 없이 개인 데이터로 추천</span>
              <button
                v-if="!session.location.applied"
                type="button"
                class="location-retry"
                :disabled="recommendationStore.locationStatus === 'loading'"
                @click="recommendationStore.requestLocationAndRegenerate"
              >
                위치 다시 요청
              </button>
            </p>
          </div>
          <button
            type="button"
            :disabled="recommendationStore.isLoading || recommendationStore.isAdvancing"
            @click="recommendationStore.recommendAgain"
          >
            <RefreshCw
              :size="18"
              :class="{ 'is-spinning': recommendationStore.isLoading || recommendationStore.isAdvancing }"
            />
            AI 재추천
          </button>
        </section>

        <article class="recommendation-card">
          <RouterLink :to="`/courses/${course.slug}`" aria-label="코스 상세 보기">
            <div class="recommendation-card__image">
              <img :src="getCourseImageForCourse(course)" :alt="course.name" />
              <div class="recommendation-card__shade"></div>
              <span><Sparkles :size="14" /> AI 추천 코스</span>
            </div>
            <div class="recommendation-card__body">
              <div class="recommendation-card__heading">
                <div>
                  <small>{{ course.district }} · {{ course.course_type_label }}</small>
                  <h2>{{ course.name }}</h2>
                </div>
                <FavoriteButton
                  class="recommendation-card__favorite"
                  :active="course.is_favorite"
                  @toggle="courseStore.toggleFavorite(course)"
                />
              </div>
              <p class="recommendation-card__meta">
                {{ course.distance_km }}km · {{ course.estimated_minutes }}분 · {{ course.difficulty_label }}
              </p>
              <p class="recommendation-card__summary">{{ course.summary }}</p>
            </div>
          </RouterLink>
        </article>

        <section class="reason-panel">
          <div class="reason-panel__heading">
            <Sparkles :size="20" />
            <h2>이 코스를 추천한 이유</h2>
          </div>
          <ul>
            <li v-for="reason in recommendation.reasons" :key="reason">
              <ShieldCheck :size="17" />
              <span>{{ reason }}</span>
            </li>
          </ul>
        </section>

        <p v-if="recommendationStore.errorMessage" class="inline-error">
          {{ recommendationStore.errorMessage }}
        </p>
      </template>
    </div>
    <AppBottomNav />
  </main>
</template>

<style scoped>
.recommendation-page { display:flex; min-height:100vh; flex-direction:column; background:#f8fbff; }
.recommendation-page__content { flex:0 0 auto; padding:var(--page-top-padding) var(--content-padding) var(--page-bottom-padding); }
.recommendation-header { display:flex; align-items:center; justify-content:space-between; }
.recommendation-header p,.recommendation-header h1 { margin:0; }
.recommendation-header p { color:var(--color-primary); font-size:10px; font-weight:800; }
.recommendation-header h1 { margin-top:2px; color:var(--color-navy); font-size:var(--title-font-size); }
.recommendation-header > span { display:grid; width:40px; height:40px; place-items:center; color:var(--color-primary); background:var(--color-primary-soft); border-radius:50%; }
.recommendation-tabs { display:grid; grid-template-columns:1fr 1fr; margin:var(--page-gap) 0 var(--section-gap); border-bottom:1px solid var(--color-border); }
.recommendation-tabs button,.recommendation-tabs a { min-height:38px; color:var(--color-muted); font-size:13px; font-weight:600; background:transparent; text-align:center; }
.recommendation-tabs a { display:grid; place-items:center; }
.recommendation-tabs .is-active { color:var(--color-primary); border-bottom:2px solid var(--color-primary); }
.recommendation-intro { display:flex; align-items:flex-start; justify-content:space-between; gap:10px; }
.recommendation-intro__title { display:flex; align-items:center; gap:9px; }
.recommendation-intro h2,.recommendation-intro p { margin:0; }
.recommendation-intro .location-status { display:flex; align-items:center; gap:5px; color:#78889e; }
.recommendation-intro .location-status.is-applied { color:var(--color-primary); font-weight:700; }
.location-retry { min-height:26px; margin-left:4px; padding:0 7px; color:var(--color-primary); background:#fff; border:1px solid rgba(11,108,255,.25); border-radius:999px; font-size:9px; font-weight:800; }
.location-retry:disabled { color:#94a3b8; border-color:#d8e1ee; }
.recommendation-intro h2 { color:var(--color-navy); font-size:var(--section-title-size); }
.recommendation-intro__title span { padding:3px 6px; color:var(--color-primary); font-size:10px; font-weight:700; background:var(--color-primary-soft); border-radius:999px; }
.recommendation-intro p { margin-top:5px; color:var(--color-muted); font-size:11px; line-height:1.45; }
.recommendation-intro > button { display:flex; min-width:84px; min-height:34px; align-items:center; justify-content:center; gap:5px; color:var(--color-primary); font-size:11px; font-weight:700; background:#fff; border:1px solid var(--color-primary); border-radius:var(--radius-small); }
.recommendation-card { position:relative; margin-top:var(--page-gap); overflow:hidden; background:#fff; border:1px solid #e3ebf5; border-radius:var(--card-radius); box-shadow:0 10px 24px rgba(15,23,42,.08); }
.recommendation-card__image { position:relative; aspect-ratio:16/7.4; overflow:hidden; }
.recommendation-card__image img { width:100%; height:100%; object-fit:cover; }
.recommendation-card__shade { position:absolute; inset:0; background:linear-gradient(180deg,rgba(5,22,48,.04),rgba(5,22,48,.55)); }
.recommendation-card__image > span { position:absolute; top:10px; left:10px; display:flex; align-items:center; gap:4px; padding:5px 8px; color:#fff; font-size:9px; font-weight:700; background:var(--color-primary); border-radius:999px; }
.recommendation-card__body { padding:var(--card-padding); }
.recommendation-card__heading { display:grid; grid-template-columns:minmax(0,1fr) 34px; align-items:start; gap:9px; }
.recommendation-card__heading > div { min-width:0; }
.recommendation-card small { color:var(--color-primary); font-weight:700; }
.recommendation-card h2 { margin:3px 0 0; color:var(--color-navy); font-size:var(--title-font-size); }
.recommendation-card__meta { margin:6px 0 0; color:var(--color-navy); font-size:11px; font-weight:600; }
.recommendation-card__summary { display:-webkit-box; overflow:hidden; margin:8px 0 0; color:var(--color-muted); font-size:var(--caption-font-size); line-height:1.45; -webkit-box-orient:vertical; -webkit-line-clamp:2; }
.recommendation-card__favorite { align-self:start; }
.recommendation-card__favorite:deep(.favorite-button),
.recommendation-card__heading :deep(.favorite-button) { width:34px; height:34px; color:var(--color-primary); background:var(--color-primary-soft); backdrop-filter:none; }
.recommendation-card__favorite:deep(.favorite-button.is-active),
.recommendation-card__heading :deep(.favorite-button.is-active) { color:#fff; background:var(--color-primary); }
.reason-panel { margin-top:var(--page-gap); padding:var(--card-padding); background:#f0f7ff; border-radius:var(--card-radius); }
.reason-panel__heading { display:flex; align-items:center; gap:7px; color:var(--color-primary); }
.reason-panel h2 { margin:0; color:var(--color-navy); font-size:var(--section-title-size); }
.reason-panel ul { display:grid; gap:7px; margin:10px 0 0; padding:0; list-style:none; }
.reason-panel li { display:grid; grid-template-columns:18px 1fr; align-items:center; gap:5px; color:#425572; font-size:11px; line-height:1.35; }
.reason-panel li svg { color:var(--color-success); }
.inline-error { margin:12px 0 0; color:#d73c4e; font-size:12px; text-align:center; }
.is-spinning { animation:spin .8s linear infinite; }
@keyframes spin { to { transform:rotate(360deg); } }
</style>
