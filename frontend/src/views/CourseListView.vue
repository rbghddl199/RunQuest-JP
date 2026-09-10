<script setup>
import { computed, onMounted, ref } from 'vue'
import { ChevronRight, MapPinned, SlidersHorizontal } from '@lucide/vue'

import AppState from '../components/common/AppState.vue'
import FavoriteButton from '../components/courses/FavoriteButton.vue'
import AppBottomNav from '../components/navigation/AppBottomNav.vue'
import { useCourseStore } from '../stores/courses'
import { getCourseImageForCourse } from '../utils/courseImages'

const courseStore = useCourseStore()
const activeType = ref('')

const filters = [
  { value: '', label: '전체' },
  { value: 'park', label: '공원' },
  { value: 'river', label: '강변' },
  { value: 'urban', label: '도심' },
  { value: 'trail', label: '트레일' },
]

const featured = computed(() => courseStore.featuredCourse)
const remainingCourses = computed(() => courseStore.courses.slice(1))

onMounted(() => courseStore.loadCourses())

function applyFilter(type) {
  activeType.value = type
  courseStore.loadCourses(type ? { type } : {})
}
</script>

<template>
  <main class="mobile-shell course-list-page">
    <div class="course-list-page__content">
      <header class="page-header">
        <div>
          <p>DAEJEON RUNNING</p>
          <h1>대전 러닝 코스</h1>
        </div>
        <button type="button" aria-label="필터 설정">
          <SlidersHorizontal :size="23" />
        </button>
      </header>

      <div class="filter-row" aria-label="코스 유형 필터">
        <button
          v-for="filter in filters"
          :key="filter.value"
          type="button"
          :class="{ 'is-active': activeType === filter.value }"
          @click="applyFilter(filter.value)"
        >
          {{ filter.label }}
        </button>
      </div>

      <AppState
        v-if="courseStore.isLoading"
        type="loading"
        title="코스를 불러오는 중입니다"
        message="오늘 달리기 좋은 코스를 준비하고 있어요."
      />
      <AppState
        v-else-if="courseStore.errorMessage"
        type="error"
        title="코스를 불러오지 못했어요"
        :message="courseStore.errorMessage"
        action-label="다시 시도"
        @action="applyFilter(activeType)"
      />
      <AppState
        v-else-if="!featured"
        type="empty"
        title="표시할 코스가 없어요"
        message="필터를 바꾸면 더 많은 코스를 찾을 수 있어요."
      />

      <template v-else>
        <section class="featured-section">
          <div class="section-heading">
            <div>
              <span>오늘의 추천</span>
              <h2>지금 달리기 좋은 코스</h2>
            </div>
            <MapPinned :size="23" />
          </div>

          <article class="featured-card">
            <RouterLink :to="`/courses/${featured.slug}`">
              <img :src="getCourseImageForCourse(featured)" :alt="featured.name" />
              <div class="featured-card__shade"></div>
              <span class="featured-card__badge">대전 인기 코스</span>
              <div class="featured-card__content">
                <h3>{{ featured.name }}</h3>
                <p>
                  {{ featured.distance_km }}km
                  <i></i>
                  {{ featured.estimated_minutes }}분
                  <i></i>
                  {{ featured.difficulty_label }}
                </p>
              </div>
            </RouterLink>
            <FavoriteButton
              class="featured-card__favorite"
              :active="featured.is_favorite"
              @toggle="courseStore.toggleFavorite(featured)"
            />
          </article>
        </section>

        <section class="course-section">
          <div class="section-heading">
            <div>
              <span>COURSES</span>
              <h2>다른 추천 코스</h2>
            </div>
            <button type="button">전체 보기 <ChevronRight :size="17" /></button>
          </div>

          <div class="course-grid">
            <article v-for="course in remainingCourses" :key="course.slug" class="course-card">
              <RouterLink :to="`/courses/${course.slug}`">
                <div class="course-card__image">
                  <img :src="getCourseImageForCourse(course)" :alt="course.name" />
                </div>
                <div class="course-card__body">
                  <span>{{ course.district }} · {{ course.course_type_label }}</span>
                  <h3>{{ course.name }}</h3>
                  <p>{{ course.distance_km }}km · {{ course.estimated_minutes }}분 · {{ course.difficulty_label }}</p>
                </div>
              </RouterLink>
              <FavoriteButton
                :active="course.is_favorite"
                @toggle="courseStore.toggleFavorite(course)"
              />
            </article>
          </div>
        </section>
      </template>
    </div>
    <AppBottomNav />
  </main>
</template>

<style scoped>
.course-list-page {
  display: flex;
  min-height: 100vh;
  flex-direction: column;
  background: #f8fbff;
}

.course-list-page__content {
  flex: 0 0 auto;
  padding: var(--page-top-padding) var(--content-padding) var(--page-bottom-padding);
}

.page-header,
.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.page-header p,
.page-header h1,
.section-heading span,
.section-heading h2 {
  margin: 0;
}

.page-header p,
.section-heading span {
  color: var(--color-primary);
  font-size: 11px;
  font-weight: 800;
}

.page-header h1 {
  margin-top: 3px;
  color: var(--color-navy);
  font-size: 25px;
}

.page-header > button {
  display: grid;
  width: 44px;
  height: 44px;
  place-items: center;
  color: var(--color-navy);
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: 50%;
}

.filter-row {
  display: flex;
  gap: 8px;
  margin: 22px 0 26px;
  overflow-x: auto;
  scrollbar-width: none;
}

.filter-row button {
  flex: 0 0 auto;
  min-height: 38px;
  padding: 8px 17px;
  color: #627188;
  font-size: 13px;
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: 999px;
}

.filter-row button.is-active {
  color: #fff;
  background: var(--color-primary);
  border-color: var(--color-primary);
}

.section-heading h2 {
  margin-top: 3px;
  color: var(--color-navy);
  font-size: 19px;
}

.section-heading > button {
  display: flex;
  align-items: center;
  color: var(--color-muted);
  font-size: 12px;
  background: transparent;
}

.featured-card {
  position: relative;
  display: block;
  min-height: 245px;
  margin-top: 14px;
  overflow: hidden;
  color: #fff;
  border-radius: var(--radius-medium);
  box-shadow: var(--shadow-soft);
}

.featured-card > a,
.featured-card > a > img,
.featured-card > a > .featured-card__shade {
  position: absolute;
  inset: 0;
}

.featured-card > a > img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.featured-card__shade {
  background: linear-gradient(180deg, rgba(6, 20, 43, 0.05) 30%, rgba(6, 20, 43, 0.86));
}

.featured-card__badge {
  position: absolute;
  top: 16px;
  left: 16px;
  padding: 7px 10px;
  font-size: 11px;
  font-weight: 700;
  background: var(--color-primary);
  border-radius: 999px;
}

.featured-card__favorite {
  position: absolute;
  top: 14px;
  right: 14px;
}

.featured-card__content {
  position: absolute;
  right: 18px;
  bottom: 18px;
  left: 18px;
}

.featured-card h3 {
  margin: 0;
  font-size: 25px;
}

.featured-card p {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 7px 0 0;
  color: rgba(255, 255, 255, 0.9);
  font-size: 13px;
}

.featured-card i {
  width: 3px;
  height: 3px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 50%;
}

.course-section {
  margin-top: 30px;
}

.course-grid {
  display: grid;
  gap: 12px;
  margin-top: 14px;
}

.course-card {
  position: relative;
  overflow: hidden;
  background: #fff;
  border: 1px solid #e4ebf5;
  border-radius: var(--radius-medium);
}

.course-card > a {
  display: grid;
  grid-template-columns: 118px minmax(0, 1fr);
}

.course-card__image {
  position: relative;
  min-height: 116px;
}

.course-card__image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.course-card > :deep(.favorite-button) {
  position: absolute;
  top: 8px;
  left: 76px;
  width: 34px;
  height: 34px;
}

.course-card__body {
  align-self: center;
  min-width: 0;
  padding: 14px;
}

.course-card__body span {
  color: var(--color-primary);
  font-size: 11px;
  font-weight: 700;
}

.course-card__body h3 {
  margin: 5px 0;
  overflow: hidden;
  color: var(--color-navy);
  font-size: 15px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.course-card__body p {
  margin: 0;
  color: var(--color-muted);
  font-size: 11px;
}

</style>
