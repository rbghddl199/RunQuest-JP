<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ArrowLeft, FileUp, MapPinned, X } from '@lucide/vue'
import { useRoute, useRouter } from 'vue-router'

import AppState from '../components/common/AppState.vue'
import KakaoCourseMap from '../components/maps/KakaoCourseMap.vue'
import { useCustomCourseStore } from '../stores/customCourses'

const store = useCustomCourseStore()
const route = useRoute()
const router = useRouter()
const uploadOpen = ref(false)
const activeCategory = ref('all')
const selectingForRun = computed(() => route.query.returnTo === '/run/start')
const form = reactive({
  name: '',
  description: '',
  visibility: 'private',
  file: null,
})
const selectableCourses = computed(() => [
  ...(selectingForRun.value
    ? store.favoriteCourses.map((course) => ({ ...course, selectionType: 'favorite' }))
    : []),
  ...store.courses
    .filter((course) => course.source !== 'gpx')
    .map((course) => ({ ...course, selectionType: 'drawn' })),
  ...store.courses
    .filter((course) => course.source === 'gpx')
    .map((course) => ({ ...course, selectionType: 'gpx' })),
])
const courseCategories = computed(() => [
  { value: 'all', label: '전체', count: selectableCourses.value.length },
  ...(selectingForRun.value ? [{
    value: 'favorite',
    label: '북마크',
    count: selectableCourses.value.filter((course) => course.selectionType === 'favorite').length,
  }] : []),
  {
    value: 'drawn',
    label: '직접 그린 코스',
    count: selectableCourses.value.filter((course) => course.selectionType === 'drawn').length,
  },
  {
    value: 'gpx',
    label: 'GPX 코스',
    count: selectableCourses.value.filter((course) => course.selectionType === 'gpx').length,
  },
])
const filteredCourses = computed(() => (
  activeCategory.value === 'all'
    ? selectableCourses.value
    : selectableCourses.value.filter((course) => course.selectionType === activeCategory.value)
))

function chooseFile(event) {
  form.file = event.target.files?.[0] ?? null
  if (form.file && !form.name) {
    form.name = form.file.name.replace(/\.gpx$/i, '')
  }
}

async function upload() {
  if (!form.name.trim() || !form.file) return
  const course = await store.uploadCourse({
    ...form,
    name: form.name.trim(),
    description: form.description.trim(),
  })
  if (course) {
    uploadOpen.value = false
    Object.assign(form, { name: '', description: '', visibility: 'private', file: null })
  }
}

function goBack() {
  if (route.query.returnTo) {
    router.push(String(route.query.returnTo))
    return
  }
  router.push('/my')
}

function courseTarget(course) {
  if (selectingForRun.value) {
    if (course.selectionType === 'favorite') {
      return { path: '/run/start', query: { course: course.slug } }
    }
    return { path: '/run/start', query: { custom: course.id } }
  }
  return `/my/courses/${course.id}`
}

function categoryDescription() {
  if (activeCategory.value === 'favorite') return '북마크한 기본 코스만 모아봤어요.'
  if (activeCategory.value === 'drawn') return '지도에서 직접 만든 코스만 보여드려요.'
  if (activeCategory.value === 'gpx') return 'GPX 파일로 가져온 코스만 정리했어요.'
  return selectingForRun.value
    ? '북마크, 직접 그린 코스, GPX 코스를 카테고리별로 찾을 수 있어요.'
    : '직접 만든 코스와 GPX 코스를 카테고리별로 찾을 수 있어요.'
}

function loadSelectableCourses() {
  if (selectingForRun.value) {
    return Promise.all([store.loadCourses(), store.loadFavorites()])
  }
  return store.loadCourses()
}

onMounted(() => loadSelectableCourses())
</script>

<template>
  <main class="mobile-shell my-courses-page">
    <header class="sub-header">
      <button type="button" aria-label="마이페이지로 돌아가기" @click="goBack"><ArrowLeft /></button>
      <h1>{{ selectingForRun ? '코스 선택' : '나의 코스' }}</h1>
      <span aria-hidden="true"></span>
    </header>

    <section class="course-intro">
      <div><small>MY ROUTES</small><h2>{{ selectingForRun ? '내 코스와 북마크' : '직접 만든 러닝 코스' }}</h2></div>
      <div class="course-actions">
        <RouterLink to="/my/courses/new"><MapPinned :size="16" /> 직접 그리기</RouterLink>
        <button type="button" @click="uploadOpen = true"><FileUp :size="17" /> GPX</button>
      </div>
    </section>

    <section class="course-tabs" aria-label="코스 카테고리">
      <button
        v-for="category in courseCategories"
        :key="category.value"
        type="button"
        :class="{ active: activeCategory === category.value }"
        @click="activeCategory = category.value"
      >
        <strong>{{ category.label }}</strong>
        <span>{{ category.count }}</span>
      </button>
    </section>

    <p class="category-helper">{{ categoryDescription() }}</p>

    <section class="custom-list">
      <article v-for="course in filteredCourses" :key="`${course.selectionType}-${course.id}`">
        <RouterLink :to="courseTarget(course)">
          <div class="mini-map">
            <KakaoCourseMap
              :route-points="course.route_points"
              :start-latitude="course.start_latitude"
              :start-longitude="course.start_longitude"
            />
          </div>
          <div class="course-info">
            <span v-if="course.selectionType === 'favorite'">북마크 · {{ course.district }} · {{ course.course_type_label }}</span>
            <span v-else>{{ course.visibility === 'public' ? '공개' : '비공개' }} · {{ course.source === 'recorded' ? '러닝 기록 저장' : course.selectionType === 'drawn' ? '직접 그린 코스' : 'GPX 코스' }}</span>
            <h2>{{ course.name }}</h2>
            <p v-if="course.selectionType === 'favorite'">{{ course.distance_km }}km · {{ course.estimated_minutes }}분 · {{ course.difficulty_label }}</p>
            <p v-else>{{ course.distance_km }}km · 상승 {{ course.elevation_gain_m }}m · {{ course.route_points.length }}포인트</p>
          </div>
        </RouterLink>
      </article>
      <AppState
        v-if="store.isLoading"
        type="loading"
        title="나의 코스를 불러오는 중입니다"
        message="직접 만든 코스를 확인하고 있어요."
      />
      <AppState
        v-else-if="store.errorMessage"
        type="error"
        title="나의 코스를 불러오지 못했어요"
        :message="store.errorMessage"
        action-label="다시 시도"
        @action="loadSelectableCourses"
      />
      <AppState
        v-else-if="!selectableCourses.length"
        type="empty"
        title="저장한 코스가 없어요"
        message="기존 GPX 파일을 가져와 나만의 러닝 코스를 만들어보세요."
        action-label="첫 코스 만들기"
        @action="uploadOpen = true"
      />
      <AppState
        v-else-if="!filteredCourses.length"
        type="empty"
        title="이 카테고리에 코스가 없어요"
        message="다른 카테고리를 선택하거나 새 코스를 만들어보세요."
        action-label="전체 보기"
        @action="activeCategory = 'all'"
      />
    </section>

    <div v-if="uploadOpen" class="modal-backdrop" @click.self="uploadOpen = false">
      <section class="upload-modal" role="dialog" aria-modal="true" aria-labelledby="upload-title">
        <header><h2 id="upload-title">GPX 코스 가져오기</h2><button type="button" aria-label="닫기" @click="uploadOpen = false"><X /></button></header>
        <label>코스 이름<input v-model="form.name" maxlength="80" placeholder="예: 갑천 아침 러닝 코스" /></label>
        <label>코스 설명<textarea v-model="form.description" maxlength="300" rows="3" placeholder="코스 특징을 간단히 기록해 주세요."></textarea></label>
        <label>공개 설정<select v-model="form.visibility"><option value="private">비공개</option><option value="public">공개</option></select></label>
        <label class="file-drop">
          <FileUp :size="26" />
          <strong>{{ form.file?.name ?? 'GPX 파일 선택' }}</strong>
          <small>대전 지역 · 최대 2MB · 5,000포인트 이하</small>
          <input type="file" accept=".gpx,application/gpx+xml" @change="chooseFile" />
        </label>
        <p v-if="store.errorMessage" class="error" role="alert">{{ store.errorMessage }}</p>
        <button class="upload-button" type="button" :disabled="!form.name.trim() || !form.file || store.isUploading" @click="upload">
          <MapPinned :size="18" /> {{ store.isUploading ? '코스 분석 중' : '코스 저장하기' }}
        </button>
      </section>
    </div>
  </main>
</template>

<style scoped>
.my-courses-page{background:#f7faff}.sub-header{display:grid;grid-template-columns:44px 1fr 44px;align-items:center;padding:15px var(--content-padding);background:#fff;border-bottom:1px solid var(--color-border)}.sub-header a,.sub-header>button{display:grid;width:42px;height:42px;place-items:center;background:transparent}.sub-header h1{margin:0;font-size:18px;text-align:center}.course-intro{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:22px var(--content-padding) 14px}.course-intro small{color:var(--color-primary);font-size:8px;font-weight:800}.course-intro h2{margin:3px 0 0;font-size:18px}.course-actions{display:flex;gap:6px}.course-actions a,.course-intro button{display:flex;min-height:38px;align-items:center;gap:5px;padding:0 10px;color:#fff;background:var(--color-primary);border-radius:var(--radius-small);font-size:9px}.course-actions button{color:var(--color-primary);background:#fff;border:1px solid var(--color-primary)}.course-tabs{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;padding:0 var(--content-padding)}.course-tabs button{display:grid;min-width:0;min-height:54px;align-content:center;justify-items:center;gap:3px;color:#536174;background:#fff;border:1px solid var(--color-border);border-radius:8px;font-size:11px;font-weight:900}.course-tabs button.active{color:var(--color-primary);background:var(--color-primary-soft);border-color:rgba(8,102,255,.35)}.course-tabs strong{max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.course-tabs span{display:grid;min-width:22px;height:22px;place-items:center;color:#fff;background:#8ba0b8;border-radius:999px;font-size:10px}.course-tabs button.active span{background:var(--color-primary)}.category-helper{margin:10px var(--content-padding) 14px;color:#64748b;font-size:11px;line-height:1.45}.custom-list{display:grid;gap:11px;padding:0 var(--content-padding) 30px}.custom-list article{overflow:hidden;background:#fff;border:1px solid var(--color-border);border-radius:var(--radius-medium)}.custom-list article>a{display:grid;grid-template-columns:125px 1fr;min-height:118px}.mini-map{height:118px;pointer-events:none}.mini-map :deep(.map-wrapper){height:100%;aspect-ratio:auto}.course-info{display:grid;align-content:center;padding:13px}.course-info span{color:var(--color-primary);font-size:8px;font-weight:700}.course-info h2{margin:4px 0 6px;font-size:14px}.course-info p{margin:0;color:var(--color-muted);font-size:9px;line-height:1.5}.modal-backdrop{position:fixed;z-index:100;inset:0;display:flex;align-items:flex-end;justify-content:center;padding:16px;background:rgba(7,20,39,.48)}.upload-modal{width:min(100%,448px);padding:20px;background:#fff;border-radius:8px}.upload-modal header{display:flex;align-items:center;justify-content:space-between}.upload-modal h2{margin:0;font-size:18px}.upload-modal header button{display:grid;width:38px;height:38px;place-items:center;background:transparent}.upload-modal label{display:grid;gap:7px;margin-top:14px;font-size:10px;font-weight:700}.upload-modal input,.upload-modal textarea,.upload-modal select{width:100%;padding:11px;border:1px solid var(--color-border);border-radius:var(--radius-small);outline:0}.file-drop{position:relative;place-items:center;padding:18px;color:var(--color-primary);background:#f5f9ff;border:1px dashed var(--color-primary);border-radius:var(--radius-medium);text-align:center}.file-drop small{color:var(--color-muted);font-weight:400}.file-drop input{position:absolute;inset:0;opacity:0;cursor:pointer}.upload-button{display:flex;width:100%;min-height:50px;align-items:center;justify-content:center;gap:7px;margin-top:16px;color:#fff;background:var(--color-primary);border-radius:var(--radius-medium);font-weight:700}.upload-button:disabled{background:#b5c1d1}.error{color:#d73c55;font-size:10px;text-align:center}@media(min-width:768px){.modal-backdrop{align-items:center}}
</style>
