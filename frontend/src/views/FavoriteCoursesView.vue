<script setup>
import { onMounted } from 'vue'
import { ArrowLeft } from '@lucide/vue'

import AppState from '../components/common/AppState.vue'
import FavoriteButton from '../components/courses/FavoriteButton.vue'
import { useCourseStore } from '../stores/courses'
import { useCustomCourseStore } from '../stores/customCourses'
import { getCourseImageForCourse } from '../utils/courseImages'

const customStore = useCustomCourseStore()
const courseStore = useCourseStore()

async function removeFavorite(course) {
  await courseStore.toggleFavorite(course)
  customStore.favoriteCourses = customStore.favoriteCourses.filter(
    (item) => item.slug !== course.slug,
  )
}

onMounted(() => customStore.loadFavorites())
</script>

<template>
  <main class="mobile-shell favorite-page">
    <header>
      <RouterLink to="/my" aria-label="마이페이지로 돌아가기"><ArrowLeft /></RouterLink>
      <h1>저장한 코스</h1><span></span>
    </header>
    <section>
      <article v-for="course in customStore.favoriteCourses" :key="course.slug">
        <RouterLink :to="`/courses/${course.slug}`">
          <img :src="getCourseImageForCourse(course)" :alt="course.name" />
          <div><small>{{ course.district }} · {{ course.course_type_label }}</small><h2>{{ course.name }}</h2><p>{{ course.distance_km }}km · {{ course.estimated_minutes }}분 · {{ course.difficulty_label }}</p></div>
        </RouterLink>
        <FavoriteButton :active="true" @toggle="removeFavorite(course)" />
      </article>
      <AppState
        v-if="customStore.isLoading"
        type="loading"
        title="저장한 코스를 불러오는 중입니다"
        message="찜한 코스를 확인하고 있어요."
      />
      <AppState
        v-else-if="customStore.errorMessage"
        type="error"
        title="저장한 코스를 불러오지 못했어요"
        :message="customStore.errorMessage"
        action-label="다시 시도"
        @action="customStore.loadFavorites"
      />
      <AppState
        v-else-if="!customStore.favoriteCourses.length"
        type="empty"
        title="저장한 코스가 없어요"
        message="마음에 드는 코스를 저장해 두고 다시 찾아보세요."
        action-label="코스 둘러보기"
        action-to="/courses"
      />
    </section>
  </main>
</template>

<style scoped>
.favorite-page{background:#f7faff}.favorite-page>header{display:grid;grid-template-columns:44px 1fr 44px;align-items:center;padding:15px var(--content-padding);background:#fff;border-bottom:1px solid var(--color-border)}header a{display:grid;width:42px;height:42px;place-items:center}header h1{margin:0;font-size:18px;text-align:center}.favorite-page>section{display:grid;gap:10px;padding:16px var(--content-padding)}article{position:relative;overflow:hidden;background:#fff;border:1px solid var(--color-border);border-radius:var(--radius-medium)}article>a{display:grid;grid-template-columns:92px minmax(0,1fr);min-height:86px}article img{width:92px;height:86px;object-fit:cover}article div{display:grid;min-width:0;align-content:center;padding:11px 54px 11px 12px}article small{color:var(--color-primary);font-size:8px;font-weight:700}article h2{margin:3px 0 5px;overflow:hidden;color:var(--color-navy);font-size:13px;text-overflow:ellipsis;white-space:nowrap}article p{margin:0;color:var(--color-muted);font-size:9px}article>:deep(.favorite-button){position:absolute;top:50%;right:10px;width:34px;height:34px;transform:translateY(-50%)}
</style>
