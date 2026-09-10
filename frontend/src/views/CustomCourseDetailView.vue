<script setup>
import { computed, onMounted } from 'vue'
import { ArrowLeft, Mountain, Play, Route, Trash2 } from '@lucide/vue'
import { useRoute, useRouter } from 'vue-router'

import KakaoCourseMap from '../components/maps/KakaoCourseMap.vue'
import { useCustomCourseStore } from '../stores/customCourses'

const route = useRoute()
const router = useRouter()
const store = useCustomCourseStore()
const course = computed(() => store.currentCourse)

async function removeCourse() {
  if (!course.value) return
  await store.deleteCourse(course.value.id)
  await router.replace('/my/courses')
}

onMounted(() => store.loadCourse(route.params.id))
</script>

<template>
  <main class="mobile-shell custom-detail">
    <header>
      <RouterLink to="/my/courses" aria-label="나의 코스로 돌아가기"><ArrowLeft /></RouterLink>
      <h1>나의 코스 상세</h1>
      <button type="button" aria-label="코스 삭제" @click="removeCourse"><Trash2 /></button>
    </header>
    <template v-if="course">
      <KakaoCourseMap
        :route-points="course.route_points"
        :start-latitude="course.start_latitude"
        :start-longitude="course.start_longitude"
      />
      <section>
        <small>{{ course.source === 'drawn' ? '직접 제작' : 'GPX' }} · {{ course.visibility === 'public' ? '공개' : '비공개' }}</small>
        <h2>{{ course.name }}</h2>
        <p>{{ course.description || (course.source === 'drawn' ? '지도에서 직접 만든 러닝 코스입니다.' : '저장된 GPX 러닝 코스입니다.') }}</p>
        <div class="stats">
          <span><Route :size="21" /><strong>{{ course.distance_km }}km</strong><small>거리</small></span>
          <span><Mountain :size="21" /><strong>{{ course.elevation_gain_m }}m</strong><small>상승 고도</small></span>
          <span><Route :size="21" /><strong>{{ course.route_points.length }}</strong><small>경로 포인트</small></span>
        </div>
        <RouterLink class="start-button" :to="`/run/start?custom=${course.id}`">
          <Play :size="20" fill="currentColor" /> 이 코스로 러닝 시작
        </RouterLink>
      </section>
    </template>
  </main>
</template>

<style scoped>
.custom-detail{background:#f7faff}.custom-detail>header{display:grid;grid-template-columns:44px 1fr 44px;align-items:center;padding:14px var(--content-padding);background:#fff;border-bottom:1px solid var(--color-border)}header a,header button{display:grid;width:42px;height:42px;place-items:center;background:transparent}header button{color:#e24559}header h1{margin:0;font-size:17px;text-align:center}.custom-detail>section{padding:22px var(--content-padding)}section>small{color:var(--color-primary);font-size:9px;font-weight:800}section>h2{margin:4px 0 8px;font-size:23px}section>p{margin:0;color:var(--color-muted);font-size:11px;line-height:1.7}.stats{display:grid;grid-template-columns:repeat(3,1fr);margin-top:20px;padding:16px 0;background:#fff;border:1px solid var(--color-border);border-radius:var(--radius-medium)}.stats span{display:grid;justify-items:center;gap:4px;color:var(--color-primary)}.stats span+span{border-left:1px solid var(--color-border)}.stats strong{color:var(--color-navy);font-size:13px}.stats small{color:var(--color-muted);font-size:8px}.start-button{display:flex;min-height:54px;align-items:center;justify-content:center;gap:7px;margin-top:18px;color:#fff;background:var(--color-primary);border-radius:var(--radius-medium);font-weight:700}
</style>
