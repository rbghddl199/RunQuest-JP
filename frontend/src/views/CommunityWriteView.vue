<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { Plus, X } from '@lucide/vue'
import { useRouter } from 'vue-router'

import { useCommunityStore } from '../stores/community'
import { useCourseStore } from '../stores/courses'
import { useProfileStore } from '../stores/profile'

const router = useRouter()
const communityStore = useCommunityStore()
const courseStore = useCourseStore()
const profileStore = useProfileStore()

const categories = [
  { value: 'course', label: '코스' },
  { value: 'tips', label: '러닝팁' },
  { value: 'together', label: '같이 뛰어요' },
  { value: 'log', label: '러닝로그' },
  { value: 'question', label: '질문' },
]

const form = reactive({
  category: 'course',
  title: '',
  content: '',
  related_course_slug: '',
  running_record_id: '',
})
const fileInput = ref(null)
const selectedPhotos = ref([])

const selectedCourse = computed(() => (
  courseStore.courses.find((course) => course.slug === form.related_course_slug)
))

const isValid = computed(() => (
  form.title.trim().length >= 2
  && form.content.trim().length >= 10
))

function selectRecord() {
  const record = profileStore.records.find(
    (item) => item.id === Number(form.running_record_id),
  )
  if (record?.course) form.related_course_slug = record.course.slug
}

function openFilePicker() {
  fileInput.value?.click()
}

function clearPhoto(index) {
  const [photo] = selectedPhotos.value.splice(index, 1)
  if (photo?.url) URL.revokeObjectURL(photo.url)
}

function selectPhotos(event) {
  const remainingSlots = Math.max(0, 8 - selectedPhotos.value.length)
  const files = Array.from(event.target.files ?? []).slice(0, remainingSlots)
  selectedPhotos.value.push(...files
    .filter((file) => file.type.startsWith('image/'))
    .map((file) => ({
      name: file.name,
      file,
      url: URL.createObjectURL(file),
    })))
  event.target.value = ''
}

function readPhoto(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(file)
  })
}

async function submit() {
  if (!isValid.value) return
  const payload = {
    category: form.category,
    title: form.title.trim(),
    content: form.content.trim(),
  }
  if (selectedPhotos.value.length) {
    payload.images = await Promise.all(
      selectedPhotos.value.map((photo) => readPhoto(photo.file)),
    )
  }
  if (form.related_course_slug) payload.related_course_slug = form.related_course_slug
  if (form.running_record_id) payload.running_record_id = Number(form.running_record_id)

  const post = await communityStore.createPost(payload)
  if (post) await router.replace(`/community/${post.id}`)
}

onMounted(() => {
  courseStore.loadCourses()
  profileStore.loadRecords()
})

onBeforeUnmount(() => {
  selectedPhotos.value.forEach((photo) => URL.revokeObjectURL(photo.url))
})
</script>

<template>
  <main class="mobile-shell write-page">
    <header class="write-header">
      <RouterLink to="/community" aria-label="닫기">
        <X :size="24" />
      </RouterLink>
      <div>
        <h1>게시글 작성</h1>
        <p>나가면 작성 중인 내용은 저장되지 않습니다.</p>
      </div>
      <span></span>
    </header>

    <form @submit.prevent="submit">
      <section>
        <label>카테고리 <b>*</b></label>
        <p class="help">게시글 성격에 맞는 주제를 선택해 주세요</p>
        <div class="chip-row">
          <button
            v-for="category in categories"
            :key="category.value"
            type="button"
            :class="{ active: form.category === category.value }"
            @click="form.category = category.value"
          >
            {{ category.label }}
          </button>
        </div>
      </section>

      <section>
        <label for="post-title">제목 <b>*</b></label>
        <div class="input-box">
          <input
            id="post-title"
            v-model="form.title"
            maxlength="60"
            placeholder="예: 엑스포 다리 야간 러닝 코스 추천해요"
          />
          <small>{{ form.title.length }}/60</small>
        </div>
      </section>

      <section>
        <label for="post-content">내용 <b>*</b></label>
        <div class="textarea-box">
          <textarea
            id="post-content"
            v-model="form.content"
            maxlength="5000"
            rows="6"
            placeholder="코스 분위기, 거리, 추천 시간대, 주의할 점 등을 자유롭게 공유해 주세요."
          ></textarea>
          <small>최소 10자 이상 · {{ form.content.length }}/5000</small>
        </div>
      </section>

      <section>
        <label>사진 추가 <span>(선택)</span></label>
        <p class="help">사진은 직접 선택한 파일만 미리보기로 표시돼요.</p>
        <input
          ref="fileInput"
          class="file-input"
          type="file"
          accept="image/*"
          multiple
          @change="selectPhotos"
        />
        <div class="photo-grid">
          <div v-for="(photo, index) in selectedPhotos" :key="photo.url" class="photo-preview">
            <img
              :src="photo.url"
              :alt="photo.name"
            />
            <button type="button" aria-label="사진 삭제" @click="clearPhoto(index)">
              <X :size="14" />
            </button>
          </div>
          <button
            v-for="index in Math.max(1, 8 - selectedPhotos.length)"
            :key="`empty-${index}`"
            type="button"
            class="photo-empty"
            @click="openFilePicker"
          >
            <Plus :size="20" />
          </button>
        </div>
      </section>

      <section>
        <label for="course-select">관련 코스 <span>(선택)</span></label>
        <div v-if="selectedCourse" class="selected-course">
          <div>
            <strong>{{ selectedCourse.name }}</strong>
            <small>{{ selectedCourse.distance_km }}km · {{ selectedCourse.district }} · {{ selectedCourse.difficulty_label }}</small>
          </div>
        </div>
        <select id="course-select" v-model="form.related_course_slug">
          <option value="">코스를 선택하지 않음</option>
          <option v-for="course in courseStore.courses" :key="course.slug" :value="course.slug">
            {{ course.name }} · {{ course.distance_km }}km
          </option>
        </select>
      </section>

      <section>
        <label for="record-select">러닝 기록 연결 <span>(선택)</span></label>
        <select id="record-select" v-model="form.running_record_id" @change="selectRecord">
          <option value="">연결하지 않음</option>
          <option v-for="record in profileStore.records" :key="record.id" :value="record.id">
            {{ new Date(record.completed_at).toLocaleDateString('ko-KR') }}
            · {{ record.distance_km }}km
            · {{ record.course?.name ?? record.custom_course?.name ?? '자유 러닝' }}
          </option>
        </select>
      </section>

      <p v-if="communityStore.errorMessage" class="error" role="alert">
        {{ communityStore.errorMessage }}
      </p>

      <button class="submit-button" type="submit" :disabled="!isValid || communityStore.isSubmitting">
        {{ communityStore.isSubmitting ? '게시 중...' : '게시하기' }}
      </button>
    </form>
  </main>
</template>

<style scoped>
.write-page {
  min-height: 100vh;
  background: var(--color-background);
}

.write-header {
  display: grid;
  grid-template-columns: 42px 1fr 42px;
  align-items: start;
  padding: 18px 18px 8px;
}

.write-header a {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  color: var(--color-navy);
}

.write-header h1 {
  margin: 0;
  color: var(--color-navy);
  font-size: 18px;
  text-align: center;
}

.write-header p {
  margin: 8px 0 0;
  color: var(--color-muted);
  font-size: 11px;
  text-align: center;
}

form {
  padding: 8px 22px 28px;
}

section {
  padding: 14px 0;
}

label {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--color-navy);
  font-size: 13px;
  font-weight: 900;
}

label b {
  color: #f04455;
}

label span,
.help {
  color: var(--color-muted);
  font-size: 11px;
  font-weight: 600;
}

.help {
  margin: 4px 0 10px;
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
}

.chip-row button {
  min-height: 36px;
  padding: 0 17px;
  color: var(--color-text);
  background: var(--color-subtle);
  border-radius: 999px;
  font-size: 12px;
  font-weight: 900;
}

.chip-row button.active {
  color: #fff;
  background: #0b6cff;
}

.input-box,
.textarea-box {
  position: relative;
  margin-top: 9px;
}

input,
textarea,
select {
  width: 100%;
  color: var(--color-navy);
  background: var(--color-input);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  outline: 0;
}

input,
select {
  min-height: 48px;
  padding: 0 13px;
}

textarea {
  resize: vertical;
  padding: 13px;
  line-height: 1.55;
}

input:focus,
textarea:focus,
select:focus {
  border-color: #0b6cff;
  box-shadow: 0 0 0 3px rgba(11, 108, 255, 0.1);
}

.input-box small,
.textarea-box small {
  position: absolute;
  right: 12px;
  bottom: 9px;
  color: var(--color-muted);
  font-size: 10px;
}

.input-box input,
.textarea-box textarea {
  padding-right: 72px;
}

.textarea-box textarea {
  padding-bottom: 28px;
}

.file-input {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
}

.photo-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.photo-preview,
.photo-empty {
  position: relative;
  display: grid;
  aspect-ratio: 1;
  place-items: center;
  overflow: hidden;
  color: var(--color-muted);
  background: var(--color-surface);
  border: 1px dashed var(--color-border);
  border-radius: 10px;
}

.photo-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.photo-preview button {
  position: absolute;
  top: 5px;
  right: 5px;
  display: grid;
  width: 24px;
  height: 24px;
  place-items: center;
  color: #fff;
  background: rgba(17, 24, 39, 0.76);
  border-radius: 50%;
}

.selected-course {
  display: grid;
  gap: 10px;
  margin: 10px 0;
  padding: 10px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
}

.selected-course div {
  display: grid;
  align-content: center;
  gap: 3px;
}

.selected-course strong {
  color: var(--color-navy);
  font-size: 12px;
}

.selected-course small {
  color: #7b8493;
  font-size: 10px;
}

.submit-button {
  width: 100%;
  min-height: 54px;
  margin-top: 12px;
  color: #fff;
  background: #0b6cff;
  border-radius: 10px;
  font-weight: 900;
}

.submit-button:disabled {
  background: #b8c4d4;
}

.error {
  color: #d83c55;
  font-size: 12px;
  text-align: center;
}
</style>
