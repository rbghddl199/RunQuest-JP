<script setup>
import { computed, onMounted } from 'vue'
import {
  ArrowLeft,
  Clock3,
  MapPin,
  Mountain,
  SunMedium,
  Users,
} from '@lucide/vue'
import { useRoute, useRouter } from 'vue-router'

import AppState from '../components/common/AppState.vue'
import FavoriteButton from '../components/courses/FavoriteButton.vue'
import KakaoCourseMap from '../components/maps/KakaoCourseMap.vue'
import BaseButton from '../components/common/BaseButton.vue'
import { useCourseStore } from '../stores/courses'

const route = useRoute()
const router = useRouter()
const courseStore = useCourseStore()

const course = computed(() => courseStore.currentCourse)

const timeLabels = {
  morning: '아침',
  afternoon: '오후',
  evening: '저녁',
  night: '야간',
}

const recommendedTime = computed(() => (
  course.value?.recommended_times
    ?.map((time) => timeLabels[time] ?? time)
    .join('/')
))

onMounted(() => courseStore.loadCourse(route.params.slug))
</script>

<template>
  <main class="mobile-shell course-detail-page">
    <header class="detail-header">
      <button type="button" aria-label="이전 화면" @click="router.back()">
        <ArrowLeft :size="25" />
      </button>
      <h1>코스 상세</h1>
      <span aria-hidden="true"></span>
    </header>

    <AppState
      v-if="courseStore.isLoading"
      type="loading"
      title="코스를 불러오는 중입니다"
      message="지도와 코스 정보를 함께 준비하고 있어요."
    />
    <AppState
      v-else-if="courseStore.errorMessage || !course"
      :type="courseStore.errorMessage ? 'error' : 'empty'"
      :title="courseStore.errorMessage ? '코스 정보를 불러오지 못했어요' : '코스를 찾을 수 없어요'"
      :message="courseStore.errorMessage || '다른 코스를 선택해 주세요.'"
      action-label="코스 목록으로"
      action-to="/courses"
    />

    <template v-else>
      <KakaoCourseMap
        :route-points="course.route_points"
        :start-latitude="course.start_latitude"
        :start-longitude="course.start_longitude"
        :course-name="course.name"
        :course-distance="course.distance_km"
        :course-minutes="course.estimated_minutes"
        :course-difficulty="course.difficulty_label"
        :level="5"
        show-course-card
        show-facilities-toggle
      />

      <section class="course-info">
        <div class="course-info__title">
          <div>
            <span>{{ course.district }} · {{ course.course_type_label }}</span>
            <h2>{{ course.name }}</h2>
          </div>
          <FavoriteButton
            :active="course.is_favorite"
            @toggle="courseStore.toggleFavorite(course)"
          />
        </div>

        <p class="course-info__summary">{{ course.summary }}</p>

        <div class="course-stats">
          <div><strong>{{ course.distance_km }}km</strong><span>거리</span></div>
          <div><strong>{{ course.estimated_minutes }}분</strong><span>예상 시간</span></div>
          <div><strong>{{ course.difficulty_label }}</strong><span>난이도</span></div>
        </div>

        <p class="course-description">{{ course.description }}</p>

        <div class="course-features">
          <div><Mountain :size="20" /><span>고도 상승</span><strong>{{ course.elevation_gain_m }}m</strong></div>
          <div><SunMedium :size="20" /><span>추천 시간</span><strong>{{ recommendedTime }}</strong></div>
          <div><Users :size="20" /><span>혼잡도</span><strong>{{ course.crowd_level }}</strong></div>
          <div><MapPin :size="20" /><span>지역</span><strong>대전 {{ course.district }}</strong></div>
        </div>

        <div class="course-tags">
          <span v-for="tag in course.tags" :key="tag">#{{ tag }}</span>
        </div>

        <div class="safety-panel">
          <Clock3 :size="21" />
          <div>
            <strong>러닝 전 확인해 주세요</strong>
            <p v-for="note in course.safety_notes" :key="note">{{ note }}</p>
          </div>
        </div>

        <BaseButton :to="{ path: '/run/start', query: { course: course.slug } }">
          이 코스 지도에 적용하기
        </BaseButton>
      </section>
    </template>
  </main>
</template>

<style scoped>
.course-detail-page {
  background: #f8fbff;
}

.detail-header {
  display: grid;
  min-height: 66px;
  grid-template-columns: 46px 1fr 46px;
  align-items: center;
  padding: 10px 14px;
  background: #fff;
  border-bottom: 1px solid var(--color-border);
}

.detail-header button {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  color: var(--color-navy);
  background: transparent;
  border-radius: 50%;
}

.detail-header h1 {
  margin: 0;
  color: var(--color-navy);
  font-size: 18px;
  text-align: center;
}

.course-info {
  position: relative;
  z-index: 2;
  margin-top: -8px;
  padding: 25px var(--content-padding) 34px;
  background: #fff;
  border-radius: 8px 8px 0 0;
}

.course-info__title {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.course-info__title span {
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 700;
}

.course-info__title h2 {
  margin: 5px 0 0;
  color: var(--color-navy);
  font-size: 24px;
  line-height: 1.35;
}

.course-info__title :deep(.favorite-button) {
  flex: 0 0 auto;
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.course-info__summary {
  margin: 14px 0 20px;
  color: var(--color-muted);
  font-size: 14px;
  line-height: 1.6;
}

.course-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  padding: 17px 0;
  border-block: 1px solid var(--color-border);
}

.course-stats div {
  display: grid;
  gap: 4px;
  text-align: center;
}

.course-stats div + div {
  border-left: 1px solid var(--color-border);
}

.course-stats strong {
  color: var(--color-navy);
  font-size: 16px;
}

.course-stats span {
  color: var(--color-muted);
  font-size: 11px;
}

.course-description {
  margin: 22px 0;
  color: #425572;
  font-size: 13px;
  line-height: 1.75;
}

.course-features {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.course-features div {
  display: grid;
  grid-template-columns: 26px 1fr;
  align-items: center;
  padding: 13px;
  color: var(--color-primary);
  background: #f5f9ff;
  border-radius: var(--radius-medium);
}

.course-features span,
.course-features strong {
  grid-column: 2;
}

.course-features span {
  color: var(--color-muted);
  font-size: 10px;
}

.course-features strong {
  color: var(--color-navy);
  font-size: 12px;
}

.course-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin: 20px 0;
}

.course-tags span {
  padding: 7px 9px;
  color: var(--color-primary);
  font-size: 11px;
  background: var(--color-primary-soft);
  border-radius: 999px;
}

.safety-panel {
  display: grid;
  grid-template-columns: 25px 1fr;
  gap: 10px;
  margin-bottom: 18px;
  padding: 15px;
  color: #ef8b17;
  background: #fff8eb;
  border-radius: var(--radius-medium);
}

.safety-panel strong {
  color: var(--color-navy);
  font-size: 12px;
}

.safety-panel p {
  margin: 4px 0 0;
  color: #7a6548;
  font-size: 11px;
  line-height: 1.5;
}

</style>
