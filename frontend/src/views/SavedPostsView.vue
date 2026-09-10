<script setup>
import { onMounted } from 'vue'
import { ArrowLeft, Bookmark, Heart, MessageCircle } from '@lucide/vue'

import AppState from '../components/common/AppState.vue'
import { useCommunityStore } from '../stores/community'
import { getProfileImage } from '../utils/courseImages'

const communityStore = useCommunityStore()

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

async function unsave(post) {
  await communityStore.toggleSave(post)
  if (!post.is_saved) {
    communityStore.posts = communityStore.posts.filter((item) => item.id !== post.id)
  }
}

onMounted(() => communityStore.loadPosts({ saved: 'true' }))
</script>

<template>
  <main class="mobile-shell saved-posts-page">
    <header>
      <RouterLink to="/my" aria-label="마이페이지로 돌아가기"><ArrowLeft /></RouterLink>
      <h1>저장한 게시글</h1>
      <span></span>
    </header>

    <section class="saved-list">
      <article v-for="post in communityStore.posts" :key="post.id">
        <RouterLink :to="{ path: `/community/${post.id}`, query: { returnTo: '/my/saved-posts' } }">
          <div class="author-row">
            <img
              v-if="getProfileImage(post.author.id ?? post.author.nickname)"
              class="author-avatar"
              :src="getProfileImage(post.author.id ?? post.author.nickname)"
              :alt="`${post.author.nickname} 프로필`"
            />
            <div v-else class="author-avatar">{{ post.author.nickname.slice(0, 1) }}</div>
            <p>
              <strong>{{ post.author.nickname }}</strong>
              <small>{{ formatDate(post.created_at) }}</small>
            </p>
            <span>{{ post.category_label }}</span>
          </div>
          <h2>{{ post.title }}</h2>
          <p>{{ post.content }}</p>
        </RouterLink>

        <footer>
          <span><Heart :size="18" /> {{ post.like_count }}</span>
          <span><MessageCircle :size="18" /> {{ post.comment_count }}</span>
          <button type="button" aria-label="저장 해제" @click="unsave(post)">
            <Bookmark :size="18" fill="currentColor" />
          </button>
        </footer>
      </article>

      <AppState
        v-if="communityStore.isLoading"
        type="loading"
        title="저장한 게시글을 불러오는 중입니다"
        message="북마크한 글을 확인하고 있어요."
      />
      <AppState
        v-else-if="communityStore.errorMessage"
        type="error"
        title="저장한 게시글을 불러오지 못했어요"
        :message="communityStore.errorMessage"
        action-label="다시 시도"
        @action="communityStore.loadPosts({ saved: 'true' })"
      />
      <AppState
        v-else-if="!communityStore.posts.length"
        type="empty"
        title="저장한 게시글이 없어요"
        message="커뮤니티에서 북마크한 글이 여기에 모입니다."
        action-label="커뮤니티 둘러보기"
        action-to="/community"
      />
    </section>
  </main>
</template>

<style scoped>
.saved-posts-page { min-height:100vh; background:#f7faff; }
.saved-posts-page > header { display:grid; grid-template-columns:44px 1fr 44px; align-items:center; padding:15px var(--content-padding); background:#fff; border-bottom:1px solid var(--color-border); }
header a { display:grid; width:42px; height:42px; place-items:center; }
header h1 { margin:0; color:var(--color-navy); font-size:18px; text-align:center; }
.saved-list { display:grid; gap:12px; padding:18px var(--content-padding) 28px; }
article { overflow:hidden; background:#fff; border:1px solid var(--color-border); border-radius:var(--radius-medium); box-shadow:var(--shadow-soft); }
article > a { display:block; padding:14px; }
.author-row { display:grid; grid-template-columns:32px 1fr auto; align-items:center; gap:8px; }
.author-avatar { display:grid; width:32px; height:32px; place-items:center; color:#fff; background:linear-gradient(135deg,#0f172a,#0b6cff); border-radius:50%; object-fit:cover; font-size:11px; font-weight:900; }
.author-row p { display:grid; gap:1px; min-width:0; margin:0; }
.author-row strong { color:var(--color-navy); font-size:12px; }
.author-row small { color:var(--color-muted); font-size:9px; }
.author-row span { padding:4px 8px; color:var(--color-primary); background:var(--color-primary-soft); border-radius:999px; font-size:9px; font-weight:900; }
article h2 { margin:12px 0 5px; color:var(--color-navy); font-size:16px; }
article p { display:-webkit-box; overflow:hidden; margin:0; color:var(--color-text); font-size:12px; line-height:1.5; -webkit-box-orient:vertical; -webkit-line-clamp:2; }
article footer { display:grid; grid-template-columns:auto auto 1fr; gap:18px; padding:9px 14px 13px; border-top:1px solid var(--color-divider); }
article footer span,
article footer button { display:flex; align-items:center; gap:5px; color:#313847; background:transparent; font-size:11px; }
article footer button { justify-self:end; color:var(--color-primary); }
</style>
