<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import {
  ArrowLeft,
  Bookmark,
  Heart,
  MessageCircle,
  MoreHorizontal,
  Send,
  X,
} from '@lucide/vue'
import { useRoute, useRouter } from 'vue-router'

import AppState from '../components/common/AppState.vue'
import { useAuthStore } from '../stores/auth'
import { useCommunityStore } from '../stores/community'
import { getCourseImageForCourse, getProfileImage } from '../utils/courseImages'
import { getStoredProfileAvatar } from '../utils/profileAvatar'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const communityStore = useCommunityStore()
const comment = ref('')
const mediaTrack = ref(null)
const pageScroll = ref(null)
const menuOpen = ref(false)
const editingPost = ref(false)
const editingCommentId = ref(null)
const editCommentContent = ref('')
const activeImageIndex = ref(0)
const mediaPress = reactive({
  startX: 0,
  moved: false,
})
const editPostForm = reactive({
  title: '',
  content: '',
})

const images = computed(() => communityStore.post?.images ?? [])
const returnTo = computed(() => String(route.query.returnTo || '/community'))

function showDetailImage(index) {
  if (!images.value.length) return
  const nextIndex = (index + images.value.length) % images.value.length
  activeImageIndex.value = nextIndex
  nextTick(() => {
    const track = mediaTrack.value
    if (!track) return
    track.scrollTo({ left: track.clientWidth * nextIndex, behavior: 'smooth' })
  })
}

function showNextImage() {
  showDetailImage(activeImageIndex.value + 1)
}

function startMediaPress(event) {
  mediaPress.startX = event.clientX
  mediaPress.moved = false
}

function moveMediaPress(event) {
  if (Math.abs(event.clientX - mediaPress.startX) > 8) {
    mediaPress.moved = true
  }
}

function handleMediaClick() {
  if (mediaPress.moved) {
    mediaPress.moved = false
    return
  }
  showNextImage()
}

function syncDetailImage() {
  const track = mediaTrack.value
  if (!track?.clientWidth) return
  activeImageIndex.value = Math.round(track.scrollLeft / track.clientWidth)
}

function formatDate(value) {
  return new Date(value).toLocaleString('ko-KR', {
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function authorProfileImage(author) {
  if (author?.id && authStore.user?.id === author.id) {
    return getStoredProfileAvatar(authStore.user.email)
      ?? getStoredProfileAvatar(authStore.user.id)
      ?? getProfileImage(author.id ?? author.nickname)
  }
  return getProfileImage(author?.id ?? author?.nickname)
}

async function addComment() {
  if (!comment.value.trim()) return
  await communityStore.addComment(comment.value.trim())
  comment.value = ''
  await nextTick()
  if (pageScroll.value) {
    pageScroll.value.scrollTop = pageScroll.value.scrollHeight
  }
}

function startPostEdit() {
  if (!communityStore.post) return
  editPostForm.title = communityStore.post.title
  editPostForm.content = communityStore.post.content
  editingPost.value = true
  menuOpen.value = false
}

async function submitPostEdit() {
  if (!editPostForm.title.trim() || !editPostForm.content.trim()) return
  const updated = await communityStore.updatePost(communityStore.post.id, {
    title: editPostForm.title.trim(),
    content: editPostForm.content.trim(),
  })
  if (updated) editingPost.value = false
}

async function deletePost() {
  if (!window.confirm('게시글을 삭제할까요?')) return
  const deleted = await communityStore.deletePost(communityStore.post.id)
  if (deleted) await router.replace(returnTo.value)
}

function goBack() {
  router.push(returnTo.value)
}

function startCommentEdit(item) {
  editingCommentId.value = item.id
  editCommentContent.value = item.content
}

async function submitCommentEdit(item) {
  if (!editCommentContent.value.trim()) return
  await communityStore.updateComment(item, editCommentContent.value.trim())
  editingCommentId.value = null
  editCommentContent.value = ''
}

onMounted(() => communityStore.loadPost(route.params.id))
</script>

<template>
  <main class="mobile-shell detail-page">
    <header class="detail-header">
      <button type="button" aria-label="뒤로가기" @click="goBack">
        <ArrowLeft :size="22" />
      </button>
      <span></span>
      <button
        v-if="communityStore.post?.is_mine"
        type="button"
        aria-label="게시글 메뉴"
        @click="menuOpen = !menuOpen"
      >
        <MoreHorizontal :size="24" />
      </button>
      <span v-else></span>
      <div v-if="menuOpen" class="post-menu">
        <button type="button" @click="startPostEdit">게시글 수정</button>
        <button type="button" class="danger" @click="deletePost">게시글 삭제</button>
      </div>
    </header>

    <div ref="pageScroll" class="detail-scroll">
      <article v-if="communityStore.post" class="post-detail">
        <div class="author">
          <img
            v-if="authorProfileImage(communityStore.post.author)"
            class="author-avatar"
            :src="authorProfileImage(communityStore.post.author)"
            :alt="`${communityStore.post.author.nickname} 프로필`"
          />
          <div v-else class="author-avatar">{{ communityStore.post.author.nickname.slice(0, 1) }}</div>
          <p>
            <strong>{{ communityStore.post.author.nickname }}</strong>
            <small>{{ formatDate(communityStore.post.created_at) }}</small>
          </p>
        </div>

        <form v-if="editingPost" class="post-edit-form" @submit.prevent="submitPostEdit">
          <input v-model.trim="editPostForm.title" maxlength="60" aria-label="게시글 제목 수정" />
          <textarea v-model.trim="editPostForm.content" maxlength="5000" rows="5" aria-label="게시글 내용 수정"></textarea>
          <div>
            <button type="button" @click="editingPost = false">취소</button>
            <button type="submit" :disabled="communityStore.isSubmitting">저장</button>
          </div>
        </form>

        <template v-else>
          <h1>{{ communityStore.post.title }}</h1>
          <p class="content">{{ communityStore.post.content }}</p>
        </template>

        <div
          v-if="images.length"
          class="detail-media"
          @click="handleMediaClick"
          @pointerdown="startMediaPress"
          @pointermove="moveMediaPress"
        >
          <div
            ref="mediaTrack"
            class="detail-media__track"
            @scroll.passive="syncDetailImage"
          >
            <img
              v-for="(image, index) in images"
              :key="index"
              :src="image"
              :alt="`${communityStore.post.related_course?.name ?? communityStore.post.title} ${index + 1}`"
            />
          </div>
          <em v-if="images.length > 1">{{ activeImageIndex + 1 }}/{{ images.length }}</em>
        </div>

        <RouterLink
          v-if="communityStore.post.related_course"
          class="course-link"
          :to="`/courses/${communityStore.post.related_course.slug}`"
        >
          <strong>관련 코스</strong>
          <div>
            <img :src="getCourseImageForCourse(communityStore.post.related_course)" alt="" />
            <p>
              <b>{{ communityStore.post.related_course.name }}</b>
              <small>
                {{ communityStore.post.related_course.distance_km }}km ·
                {{ communityStore.post.related_course.difficulty_label }} ·
                소요시간 {{ communityStore.post.related_course.estimated_minutes }}분
              </small>
            </p>
            <span>코스 보기</span>
          </div>
        </RouterLink>

        <footer class="reactions">
          <button
            type="button"
            :class="{ active: communityStore.post.is_liked }"
            @click="communityStore.toggleLike()"
          >
            <Heart :size="21" :fill="communityStore.post.is_liked ? 'currentColor' : 'none'" />
            {{ communityStore.post.like_count }}
          </button>
          <span>
            <MessageCircle :size="21" />
            {{ communityStore.post.comment_count }}
          </span>
          <button
            type="button"
            :class="{ active: communityStore.post.is_saved }"
            aria-label="북마크"
            @click="communityStore.toggleSave()"
          >
            <Bookmark :size="21" :fill="communityStore.post.is_saved ? 'currentColor' : 'none'" />
          </button>
        </footer>
      </article>

      <section v-if="communityStore.post" class="comments">
        <h2>댓글 <span>{{ communityStore.post.comment_count }}</span></h2>
        <article v-for="item in communityStore.post.comments" :key="item.id">
          <img
            v-if="authorProfileImage(item.author)"
            class="comment-avatar"
            :src="authorProfileImage(item.author)"
            :alt="`${item.author.nickname} 프로필`"
          />
          <div v-else class="comment-avatar">{{ item.author.nickname.slice(0, 1) }}</div>
          <div>
            <strong>{{ item.author.nickname }}</strong>
            <small>{{ formatDate(item.created_at) }}</small>

            <form
              v-if="editingCommentId === item.id"
              class="comment-edit-form"
              @submit.prevent="submitCommentEdit(item)"
            >
              <input v-model.trim="editCommentContent" maxlength="500" aria-label="댓글 수정" />
              <button type="button" aria-label="수정 취소" @click="editingCommentId = null">
                <X :size="14" />
              </button>
              <button type="submit">저장</button>
            </form>
            <p v-else>{{ item.content }}</p>

            <div class="comment-actions">
              <button
                type="button"
                :class="{ active: item.is_liked }"
                @click="communityStore.toggleCommentLike(item)"
              >
                <Heart :size="14" :fill="item.is_liked ? 'currentColor' : 'none'" />
                {{ item.like_count }}
              </button>
              <button v-if="item.is_mine" type="button" @click="startCommentEdit(item)">수정</button>
              <button v-if="item.can_delete" type="button" class="danger" @click="communityStore.deleteComment(item)">삭제</button>
            </div>
          </div>
        </article>
        <p v-if="!communityStore.post.comments.length" class="no-comments">
          경험이나 팁을 댓글로 남겨보세요.
        </p>
      </section>

      <AppState
        v-else-if="communityStore.isLoading"
        compact
        type="loading"
        title="게시글을 불러오는 중입니다"
        message="러너의 이야기를 확인하고 있어요"
      />
      <AppState
        v-else
        compact
        type="error"
        title="게시글을 불러오지 못했어요"
        :message="communityStore.errorMessage || '잠시 후 다시 시도해 주세요.'"
        action-label="목록으로"
        @action="goBack"
      />
    </div>

    <form v-if="communityStore.post" class="comment-form" @submit.prevent="addComment">
      <input v-model="comment" maxlength="500" placeholder="경험이나 팁을 댓글로 남겨보세요" />
      <button type="submit" :disabled="!comment.trim()" aria-label="댓글 등록">
        <Send :size="20" />
      </button>
    </form>
  </main>
</template>

<style scoped>
.detail-page {
  position: relative;
  display: flex;
  height: var(--app-height);
  min-height: var(--app-height);
  flex-direction: column;
  overflow: hidden;
  padding-bottom: 0;
  background: #fff;
  border-radius: var(--app-radius);
}

.detail-header {
  position: relative;
  z-index: 10;
  display: grid;
  flex: 0 0 auto;
  grid-template-columns: 42px 1fr 42px;
  align-items: center;
  padding: 12px 18px 6px;
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(12px);
}

.detail-header > button {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  color: #111827;
  background: transparent;
}

.detail-scroll {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding-bottom: 86px;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
}

.detail-scroll::-webkit-scrollbar {
  display: none;
}

.post-menu {
  position: absolute;
  z-index: 20;
  top: 52px;
  right: 18px;
  display: grid;
  min-width: 128px;
  overflow: hidden;
  background: #fff;
  border: 1px solid #e6edf6;
  border-radius: 12px;
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.14);
}

.post-menu button {
  padding: 12px 14px;
  color: #111827;
  background: #fff;
  font-size: 12px;
  font-weight: 900;
  text-align: left;
}

.post-menu button + button {
  border-top: 1px solid #eef2f7;
}

.post-menu .danger {
  color: #e13b4b;
}

.post-detail {
  padding: 12px 22px 20px;
  background: #fff;
}

.author {
  display: grid;
  grid-template-columns: 34px 1fr;
  align-items: center;
  gap: 9px;
}

.author-avatar,
.comment-avatar {
  display: grid;
  place-items: center;
  color: #fff;
  background: linear-gradient(135deg, #0f172a, #0b6cff);
  border-radius: 50%;
  object-fit: cover;
  font-weight: 900;
}

.author-avatar {
  width: 34px;
  height: 34px;
  font-size: 12px;
}

.author p {
  display: grid;
  gap: 2px;
  margin: 0;
}

.author strong {
  color: #111827;
  font-size: 12px;
}

.author small {
  color: #8a94a6;
  font-size: 10px;
}

.post-detail h1 {
  margin: 16px 0 8px;
  color: #0f172a;
  font-size: 20px;
  letter-spacing: 0;
}

.content {
  margin: 0 0 16px;
  color: #2f3949;
  font-size: 13px;
  line-height: 1.65;
  white-space: pre-wrap;
}

.post-edit-form {
  display: grid;
  gap: 10px;
  margin-top: 16px;
}

.post-edit-form input,
.post-edit-form textarea,
.comment-edit-form input {
  width: 100%;
  color: #111827;
  background: #fff;
  border: 1px solid #dbe4f0;
  border-radius: 10px;
  outline: 0;
}

.post-edit-form input {
  min-height: 46px;
  padding: 0 12px;
  font-size: 16px;
  font-weight: 800;
}

.post-edit-form textarea {
  resize: vertical;
  padding: 12px;
  line-height: 1.55;
}

.post-edit-form div {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.post-edit-form button,
.comment-edit-form button {
  min-height: 34px;
  padding: 0 12px;
  color: #fff;
  background: #0b6cff;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 900;
}

.post-edit-form button[type='button'],
.comment-edit-form button[type='button'] {
  color: #596579;
  background: #f2f5f9;
}

.detail-media {
  position: relative;
  overflow: hidden;
  width: 100%;
  aspect-ratio: 1 / 1;
  background: #05070b;
  border-radius: 12px;
  cursor: pointer;
}

.detail-media__track {
  display: flex;
  width: 100%;
  height: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  scroll-snap-type: x mandatory;
  scroll-behavior: smooth;
  scrollbar-width: none;
  overscroll-behavior-x: contain;
  touch-action: pan-x;
  -webkit-overflow-scrolling: touch;
}

.detail-media__track::-webkit-scrollbar {
  display: none;
}

.detail-media img {
  flex: 0 0 100%;
  width: 100%;
  height: 100%;
  object-fit: cover;
  scroll-snap-align: start;
}

.detail-media em {
  position: absolute;
  top: 10px;
  right: 10px;
  padding: 5px 9px;
  color: #fff;
  background: rgba(0, 0, 0, 0.56);
  border-radius: 999px;
  font-size: 10px;
  font-style: normal;
  font-weight: 900;
  backdrop-filter: blur(8px);
}

.course-link {
  display: grid;
  gap: 9px;
  margin-top: 14px;
  padding: 13px;
  background: #fff;
  border: 1px solid #e6edf6;
  border-radius: 12px;
}

.course-link > strong {
  color: #111827;
  font-size: 12px;
}

.course-link div {
  display: grid;
  grid-template-columns: 66px 1fr auto;
  align-items: center;
  gap: 10px;
}

.course-link img {
  width: 66px;
  height: 46px;
  object-fit: cover;
  border-radius: 8px;
}

.course-link p {
  display: grid;
  gap: 3px;
  margin: 0;
}

.course-link b {
  color: #111827;
  font-size: 12px;
}

.course-link small {
  color: #8a94a6;
  font-size: 10px;
}

.course-link span {
  padding: 8px 11px;
  color: #0b6cff;
  border: 1px solid #0b6cff;
  border-radius: 9px;
  font-size: 11px;
  font-weight: 900;
}

.reactions {
  display: grid;
  grid-template-columns: auto auto 1fr;
  gap: 28px;
  margin-top: 16px;
  padding-top: 13px;
  border-top: 1px solid #eef2f7;
}

.reactions button,
.reactions span {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #2f3949;
  background: transparent;
  font-size: 12px;
}

.reactions button:last-child {
  justify-self: end;
}

.reactions .active {
  color: #ef3f64;
}

.comments {
  padding: 16px 22px 28px;
  background: #fff;
  border-top: 8px solid #f4f6fa;
}

.comments h2 {
  margin: 0 0 12px;
  color: #111827;
  font-size: 14px;
}

.comments h2 span {
  color: #8a94a6;
}

.comments article {
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr);
  gap: 9px;
  padding: 12px 0;
}

.comments article + article {
  border-top: 1px solid #eef2f7;
}

.comment-avatar {
  width: 34px;
  height: 34px;
  font-size: 11px;
}

.comments article > div:nth-child(2) {
  display: grid;
  min-width: 0;
  grid-template-columns: auto 1fr;
  gap: 2px 8px;
}

.comments article strong {
  color: #111827;
  font-size: 11px;
}

.comments article small {
  color: #8a94a6;
  font-size: 9px;
}

.comments article p {
  grid-column: 1 / -1;
  margin: 3px 0 0;
  color: #394456;
  font-size: 12px;
  line-height: 1.5;
}

.comment-actions {
  grid-column: 1 / -1;
  display: flex;
  gap: 10px;
  margin-top: 7px;
}

.comment-actions button {
  display: flex;
  align-items: center;
  gap: 3px;
  color: #7b8493;
  background: transparent;
  font-size: 10px;
  font-weight: 800;
}

.comment-actions button.active {
  color: #ef3f64;
}

.comment-actions button.danger {
  color: #e13b4b;
}

.comment-edit-form {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: 1fr 32px auto;
  gap: 6px;
  margin-top: 5px;
}

.comment-edit-form input {
  min-width: 0;
  min-height: 36px;
  padding: 0 10px;
  font-size: 12px;
}

.comment-edit-form button {
  min-height: 36px;
  padding: 0 9px;
}

.no-comments {
  padding: 26px 0;
  color: #8a94a6;
  font-size: 12px;
  text-align: center;
}

.comment-form {
  position: absolute;
  z-index: 20;
  right: 0;
  bottom: 0;
  left: 0;
  display: grid;
  grid-template-columns: 1fr 44px;
  gap: 8px;
  padding: 10px 18px max(10px, env(safe-area-inset-bottom));
  background: rgba(255, 255, 255, 0.98);
  border-top: 1px solid #eef2f7;
  border-radius: 0 0 var(--app-radius) var(--app-radius);
  backdrop-filter: blur(12px);
}

.comment-form input {
  min-width: 0;
  min-height: 44px;
  padding: 0 14px;
  border: 1px solid #dbe4f0;
  border-radius: 10px;
  outline: 0;
}

.comment-form button {
  display: grid;
  width: 44px;
  height: 44px;
  place-items: center;
  color: #fff;
  background: #0b6cff;
  border-radius: 50%;
}

.comment-form button:disabled {
  background: #b4c0d0;
}
</style>
