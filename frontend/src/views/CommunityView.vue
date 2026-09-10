<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import {
  Bookmark,
  Heart,
  MessageCircle,
  Plus,
  Search,
  SlidersHorizontal,
  SquarePen,
  X,
} from '@lucide/vue'

import AppState from '../components/common/AppState.vue'
import AppBottomNav from '../components/navigation/AppBottomNav.vue'
import { useAuthStore } from '../stores/auth'
import { useCommunityStore } from '../stores/community'
import { getPostImages, getProfileImage } from '../utils/courseImages'
import { getStoredProfileAvatar } from '../utils/profileAvatar'

const PAGE_SIZE = 12

const authStore = useAuthStore()
const communityStore = useCommunityStore()
const searchOpen = ref(false)
const filterOpen = ref(false)
const categoryTabs = ref(null)
const categoryDrag = reactive({
  active: false,
  moved: false,
  startX: 0,
  scrollLeft: 0,
})
const draftFilters = reactive({ ordering: 'latest', period: '', region: 'all' })
const filters = reactive({
  category: '',
  ordering: 'latest',
  period: '',
  region: 'all',
  search: '',
})

const categories = [
  { value: '', label: '전체' },
  { value: 'course', label: '코스' },
  { value: 'tips', label: '러닝팁' },
  { value: 'together', label: '같이 뛰어요' },
  { value: 'log', label: '러닝로그' },
  { value: 'question', label: '질문' },
]
const sortOptions = [
  { value: 'latest', label: '최신순' },
  { value: 'popular', label: '인기순' },
]
const periodOptions = [
  { value: '', label: '전체' },
  { value: 'today', label: '오늘' },
  { value: 'week', label: '최근 7일' },
  { value: 'month', label: '최근 30일' },
]
const regionOptions = ['all', '대전 전체', '동구', '중구', '서구', '유성구', '대덕구']

const posts = computed(() => communityStore.posts)
const isInitialLoading = computed(() => communityStore.isLoading && !posts.value.length)
const postImageCache = new WeakMap()
const profileImageCache = new Map()

function postPreviewImage(post) {
  if (!postImageCache.has(post)) {
    postImageCache.set(post, getPostImages(post)[0] ?? '')
  }
  return postImageCache.get(post)
}

function authorProfileImage(author) {
  if (author?.id && authStore.user?.id === author.id) {
    return getStoredProfileAvatar(authStore.user.email)
      ?? getStoredProfileAvatar(authStore.user.id)
      ?? getProfileImage(author.id ?? author.nickname)
  }
  const key = author.id ?? author.nickname
  if (!profileImageCache.has(key)) {
    profileImageCache.set(key, getProfileImage(key))
  }
  return profileImageCache.get(key)
}

function postParams(offset = 0) {
  return {
    limit: PAGE_SIZE,
    offset,
    category: filters.category || undefined,
    ordering: filters.ordering,
    period: filters.period || undefined,
    region: filters.region === 'all' || filters.region === '대전 전체' ? undefined : filters.region,
    search: filters.search || undefined,
  }
}

function loadPosts() {
  return communityStore.loadPosts(postParams())
}

function loadMorePosts() {
  return communityStore.loadMorePosts()
}

function selectCategory(category) {
  if (categoryDrag.moved) return
  filters.category = category
  loadPosts()
}

function startCategoryDrag(event) {
  if (!categoryTabs.value) return
  categoryDrag.active = true
  categoryDrag.moved = false
  categoryDrag.startX = event.clientX
  categoryDrag.scrollLeft = categoryTabs.value.scrollLeft
}

function moveCategoryDrag(event) {
  if (!categoryDrag.active || !categoryTabs.value) return
  const deltaX = event.clientX - categoryDrag.startX
  if (Math.abs(deltaX) > 12) categoryDrag.moved = true
  categoryTabs.value.scrollLeft = categoryDrag.scrollLeft - deltaX
}

function endCategoryDrag() {
  if (!categoryTabs.value) return
  categoryDrag.active = false
  window.setTimeout(() => {
    categoryDrag.moved = false
  }, 80)
}

function openFilters() {
  draftFilters.ordering = filters.ordering
  draftFilters.period = filters.period
  draftFilters.region = filters.region
  filterOpen.value = true
}

function applyFilters() {
  filters.ordering = draftFilters.ordering
  filters.period = draftFilters.period
  filters.region = draftFilters.region
  filterOpen.value = false
  loadPosts()
}

function resetFilters() {
  draftFilters.ordering = 'latest'
  draftFilters.period = ''
  draftFilters.region = 'all'
}

function formatDate(value) {
  const date = new Date(value)
  const diff = Date.now() - date.getTime()
  const minutes = Math.floor(diff / 60_000)
  const hours = Math.floor(diff / 3_600_000)
  if (minutes < 1) return '방금 전'
  if (hours < 1) return `${minutes}분 전`
  if (hours < 24) return `${hours}시간 전`
  return date.toLocaleDateString('ko-KR')
}

onMounted(() => {
  if (!communityStore.hasLoadedPosts && !communityStore.isLoading) {
    loadPosts()
  }
})
</script>

<template>
  <main class="mobile-shell community-page">
    <div class="community-content">
      <header class="community-header">
        <span aria-hidden="true"></span>
        <h1>RunQuest</h1>
        <button type="button" class="icon-tool" aria-label="검색" @click="searchOpen = !searchOpen">
          <Search :size="20" />
        </button>
      </header>

      <section class="tools" :class="{ 'is-searching': searchOpen }">
        <form class="search-bar" @submit.prevent="loadPosts">
          <Search :size="18" />
          <input v-model.trim="filters.search" type="search" placeholder="제목, 내용, 러너 검색" />
          <button type="submit">검색</button>
        </form>
        <div
          ref="categoryTabs"
          class="category-tabs"
          :class="{ 'is-dragging': categoryDrag.active }"
          aria-label="게시글 카테고리"
          @pointerdown="startCategoryDrag"
          @pointermove="moveCategoryDrag"
          @pointerup="endCategoryDrag"
          @pointercancel="endCategoryDrag"
          @pointerleave="endCategoryDrag"
        >
          <button
            v-for="category in categories"
            :key="category.value"
            type="button"
            :class="{ 'is-active': filters.category === category.value }"
            @click.stop="selectCategory(category.value)"
          >
            {{ category.label }}
          </button>
        </div>
        <button type="button" class="filter-button" aria-label="필터" @click="openFilters">
          <SlidersHorizontal :size="19" />
        </button>
      </section>

      <section class="post-list">
        <article v-for="post in posts" :key="post.id" class="post-card">
          <RouterLink :to="`/community/${post.id}`" class="post-card__main">
            <div class="author-row">
              <img
                v-if="authorProfileImage(post.author)"
                class="author-avatar"
                :src="authorProfileImage(post.author)"
                :alt="`${post.author.nickname} 프로필`"
                loading="lazy"
                decoding="async"
              />
              <div v-else class="author-avatar">{{ post.author.nickname.slice(0, 1) }}</div>
              <p>
                <strong>{{ post.author.nickname }}</strong>
                <small>{{ formatDate(post.created_at) }}</small>
              </p>
              <span>{{ post.category_label }}</span>
            </div>
            <h2>{{ post.title }}</h2>
            <p class="post-excerpt">{{ post.content }}</p>
            <div v-if="postPreviewImage(post)" class="post-media">
              <img
                :src="postPreviewImage(post)"
                :alt="post.related_course?.name ?? post.title"
                loading="lazy"
                decoding="async"
              />
            </div>
          </RouterLink>
          <footer>
            <button type="button" :class="{ active: post.is_liked }" @click="communityStore.toggleLike(post)">
              <Heart :size="19" :fill="post.is_liked ? 'currentColor' : 'none'" />
              {{ post.like_count }}
            </button>
            <RouterLink :to="`/community/${post.id}`">
              <MessageCircle :size="19" />
              {{ post.comment_count }}
            </RouterLink>
            <button
              type="button"
              :class="{ active: post.is_saved }"
              aria-label="북마크"
              @click="communityStore.toggleSave(post)"
            >
              <Bookmark :size="19" :fill="post.is_saved ? 'currentColor' : 'none'" />
            </button>
          </footer>
        </article>

        <button
          v-if="communityStore.hasMorePosts && posts.length"
          type="button"
          class="load-more-button"
          :disabled="communityStore.isLoading"
          @click="loadMorePosts"
        >
          {{ communityStore.isLoading ? '불러오는 중' : '더 보기' }}
        </button>

        <AppState
          v-if="isInitialLoading"
          compact
          type="loading"
          title="게시글을 불러오는 중입니다"
          message="러너들의 이야기를 모으고 있어요"
        />
        <AppState
          v-else-if="communityStore.errorMessage"
          compact
          type="error"
          title="게시글을 불러오지 못했어요"
          :message="communityStore.errorMessage"
          action-label="다시 시도"
          @action="loadPosts"
        />
        <AppState
          v-else-if="!posts.length"
          compact
          type="empty"
          title="조건에 맞는 게시글이 없어요"
          message="검색어나 필터를 바꿔 다시 확인해 보세요"
        />
      </section>
    </div>

    <RouterLink to="/community/write" class="write-fab" aria-label="게시글 작성">
      <SquarePen :size="27" />
      <Plus :size="15" />
    </RouterLink>

    <div v-if="filterOpen" class="filter-backdrop" @click.self="filterOpen = false">
      <section class="filter-sheet" aria-label="게시글 필터">
        <header>
          <h2>필터</h2>
          <button type="button" aria-label="닫기" @click="filterOpen = false">
            <X :size="22" />
          </button>
        </header>

        <div class="filter-group">
          <strong>정렬</strong>
          <div>
            <button
              v-for="option in sortOptions"
              :key="option.value"
              type="button"
              :class="{ active: draftFilters.ordering === option.value }"
              @click="draftFilters.ordering = option.value"
            >
              {{ option.label }}
            </button>
          </div>
        </div>

        <div class="filter-group">
          <strong>기간</strong>
          <div>
            <button
              v-for="option in periodOptions"
              :key="option.value"
              type="button"
              :class="{ active: draftFilters.period === option.value }"
              @click="draftFilters.period = option.value"
            >
              {{ option.label }}
            </button>
          </div>
        </div>

        <div class="filter-group">
          <strong>지역</strong>
          <div>
            <button
              v-for="region in regionOptions"
              :key="region"
              type="button"
              :class="{ active: draftFilters.region === region }"
              @click="draftFilters.region = region"
            >
              {{ region === 'all' ? '내 주변' : region }}
            </button>
          </div>
        </div>

        <footer>
          <button type="button" class="reset" @click="resetFilters">초기화</button>
          <button type="button" class="apply" @click="applyFilters">적용하기</button>
        </footer>
      </section>
    </div>

    <AppBottomNav />
  </main>
</template>

<style scoped>
.community-page { position:relative; display:flex; height:var(--app-height); min-height:var(--app-height); flex-direction:column; overflow:hidden; background:#fff; }
.community-content { display:flex; min-height:0; flex:1 1 auto; flex-direction:column; padding:var(--page-padding) var(--content-padding) 0; overflow:hidden; }
.community-header { display:grid; grid-template-columns:42px 1fr 42px; align-items:center; }
.community-header h1 { margin:0; color:#05070b; font-size:16px; font-style:italic; font-weight:900; letter-spacing:0; text-align:center; }
.community-header > span,.community-header button,.icon-tool { display:grid; width:38px; height:38px; place-items:center; color:#111827; background:transparent; }
.tools { position:relative; display:grid; grid-template-columns:minmax(0,1fr) 38px; min-height:44px; align-items:center; gap:6px; overflow:hidden; margin-top:16px; }
.category-tabs { display:flex; gap:8px; overflow-x:auto; padding:0 0 4px; cursor:grab; scrollbar-width:none; touch-action:pan-x; transition:transform 560ms cubic-bezier(.18,.95,.22,1), opacity 320ms ease; user-select:none; -webkit-overflow-scrolling:touch; }
.category-tabs.is-dragging { cursor:grabbing; }
.category-tabs::-webkit-scrollbar { display:none; }
.category-tabs button,.filter-group button { flex:0 0 auto; min-height:32px; padding:0 13px; color:#5f6674; background:#f2f3f5; border-radius:999px; font-size:11px; font-weight:800; }
.category-tabs button.is-active,.filter-group button.active { color:#fff; background:#0b6cff; }
.filter-button { display:grid; width:36px; height:36px; place-items:center; color:#111827; background:#f4f6f9; border-radius:50%; transition:transform 460ms cubic-bezier(.18,.95,.22,1), opacity 260ms ease; }
.search-bar { position:absolute; z-index:2; top:0; bottom:2px; left:0; display:grid; width:100%; grid-template-columns:auto 1fr auto; align-items:center; gap:8px; min-height:42px; padding:0 8px 0 13px; background:#171719; border-radius:999px; box-shadow:inset 0 0 0 1px rgba(255,255,255,.06), 0 12px 26px rgba(15,23,42,.12); opacity:0; pointer-events:none; transform:translateX(-76%); transition:transform 560ms cubic-bezier(.18,.95,.22,1), opacity 220ms ease; }
.search-bar svg { color:#fff; }
.search-bar input { min-width:0; border:0; outline:0; background:transparent; font-size:12px; }
.search-bar input,
.search-bar input::placeholder { color:#fff; }
.search-bar input::placeholder { opacity:.62; }
.search-bar button { min-height:30px; padding:0 13px; color:#111827; background:#fff; border-radius:999px; font-size:11px; font-weight:900; box-shadow:0 2px 8px rgba(255,255,255,.16); }
.tools.is-searching .search-bar { opacity:1; pointer-events:auto; transform:translateX(0); }
.tools.is-searching .category-tabs { opacity:.2; transform:translateX(72%); }
.tools.is-searching .filter-button { opacity:0; pointer-events:none; transform:translateX(48px) scale(.82); }
.post-list { display:flex; flex:1 1 auto; flex-direction:column; gap:var(--page-gap); min-height:0; margin-top:10px; padding-bottom:12px; overflow-y:auto; scrollbar-width:none; -webkit-overflow-scrolling:touch; }
.post-list::-webkit-scrollbar { display:none; }
.post-card { flex:0 0 auto; overflow:hidden; background:#fff; border:1px solid #edf0f5; border-radius:var(--card-radius); box-shadow:0 8px 24px rgba(15,23,42,.06); }
.post-card__main { display:block; padding:0; }
.author-row { display:grid; grid-template-columns:30px 1fr auto; align-items:center; gap:8px; }
.author-row,
.post-card h2,
.post-excerpt { margin-right:10px; margin-left:10px; }
.author-row { margin-top:10px; }
.author-avatar { display:grid; width:30px; height:30px; place-items:center; color:#fff; background:linear-gradient(135deg,#0f172a,#0b6cff); border-radius:50%; object-fit:cover; font-size:11px; font-weight:900; }
.author-row p { display:flex; min-width:0; align-items:center; gap:6px; margin:0; }
.author-row strong { color:#111827; font-size:11px; }
.author-row small,.author-row span { color:#7b8493; font-size:9px; }
.author-row span { padding:3px 8px; background:#f3f6fb; border-radius:999px; font-weight:800; }
.post-card h2 { margin-top:9px; margin-bottom:4px; color:#0f172a; font-size:16px; letter-spacing:0; }
.post-excerpt { display:-webkit-box; overflow:hidden; margin-top:0; margin-bottom:10px; color:#3f4b5f; font-size:12px; line-height:1.45; -webkit-box-orient:vertical; -webkit-line-clamp:2; }
.post-media { position:relative; overflow:hidden; width:100%; aspect-ratio:1/1; margin:0 0 10px; background:#05070b; border-radius:0; }
.post-media img { display:block; width:100%; height:100%; object-fit:cover; }
.post-card footer { display:grid; grid-template-columns:auto auto 1fr; gap:22px; padding:8px 14px 12px; }
.post-card footer button,.post-card footer a { display:flex; align-items:center; gap:5px; color:#313847; background:transparent; font-size:11px; }
.post-card footer button:last-child { justify-self:end; }
.post-card footer .active { color:#ef3f64; }
.load-more-button { min-height:44px; color:#0b6cff; background:#f3f7ff; border:1px solid rgba(11,108,255,.16); border-radius:10px; font-size:13px; font-weight:900; }
.load-more-button:disabled { color:#8aa4c7; background:#f5f7fb; }
.write-fab { position:absolute; z-index:21; right:18px; bottom:calc(var(--bottom-nav-height) + 18px); display:grid; width:54px; height:54px; place-items:center; color:#fff; background:linear-gradient(145deg,#2d7dff,#0866ff); border:1px solid rgba(255,255,255,.5); border-radius:50%; box-shadow:0 12px 24px rgba(8,102,255,.26); }
.write-fab svg:first-child { transform:translate(-1px,-1px); }
.write-fab svg:last-child { position:absolute; right:13px; bottom:13px; padding:2px; color:#0866ff; background:#fff; border-radius:50%; box-shadow:0 3px 8px rgba(15,23,42,.16); }
.filter-backdrop { position:absolute; z-index:50; inset:0; display:flex; align-items:flex-end; justify-content:center; background:rgba(15,23,42,.28); }
.filter-sheet { width:100%; max-height:calc(var(--app-height) - 84px); overflow-y:auto; padding:18px var(--content-padding) max(24px,env(safe-area-inset-bottom)); background:#fff; border-radius:22px 22px 0 0; box-shadow:0 -20px 40px rgba(15,23,42,.18); }
.filter-sheet header { display:flex; align-items:center; justify-content:space-between; }
.filter-sheet h2 { margin:0; font-size:20px; }
.filter-sheet header button { display:grid; width:36px; height:36px; place-items:center; background:transparent; }
.filter-group { display:grid; gap:10px; margin-top:22px; }
.filter-group strong { color:#111827; font-size:13px; }
.filter-group div { display:flex; flex-wrap:wrap; gap:10px; }
.filter-sheet footer { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:28px; }
.filter-sheet footer button { min-height:54px; border-radius:10px; font-size:15px; font-weight:900; }
.filter-sheet .reset { color:#0b6cff; background:#fff; border:1px solid #0b6cff; }
.filter-sheet .apply { color:#fff; background:#0b6cff; }
</style>
