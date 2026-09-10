<script setup>
import { House, Play, Sparkles, UserRound, UsersRound } from '@lucide/vue'

import { preloadKakaoMap } from '../../services/kakaoMap'
import { useCommunityStore } from '../../stores/community'

const COMMUNITY_PRELOAD_LIMIT = 12
const communityStore = useCommunityStore()
const items = [
  { label: '홈', to: '/home', icon: House },
  { label: '추천', to: '/recommendations', icon: Sparkles },
  { label: '시작', to: '/run/start', icon: Play, primary: true },
  { label: '커뮤니티', to: '/community', icon: UsersRound },
  { label: '마이페이지', to: '/my', icon: UserRound },
]

function handleNavIntent(item) {
  if (item.to === '/run/start') {
    preloadKakaoMap()
  }
  if (item.to === '/community' && !communityStore.hasLoadedPosts && !communityStore.isLoading) {
    communityStore.loadPosts({
      limit: COMMUNITY_PRELOAD_LIMIT,
      offset: 0,
      ordering: 'latest',
    })
  }
}
</script>

<template>
  <nav class="bottom-nav" aria-label="주요 메뉴">
    <RouterLink
      v-for="item in items"
      :key="item.label"
      :to="item.to"
      :class="{ 'bottom-nav__primary': item.primary }"
      @focus="handleNavIntent(item)"
      @pointerenter="handleNavIntent(item)"
      @touchstart.passive="handleNavIntent(item)"
    >
      <span>
        <component :is="item.icon" :size="item.primary ? 23 : 22" fill="none" />
      </span>
      <small>{{ item.label }}</small>
    </RouterLink>
  </nav>
</template>

<style scoped>
.bottom-nav {
  position: sticky;
  z-index: 20;
  left: auto;
  bottom: 0;
  display: grid;
  flex: 0 0 var(--bottom-nav-height);
  width: min(100%, var(--app-width));
  margin-top: auto;
  height: var(--bottom-nav-height);
  min-height: var(--bottom-nav-height);
  grid-template-columns: repeat(5, minmax(0, 1fr));
  align-items: center;
  padding: 6px 10px;
  background: color-mix(in srgb, var(--color-surface) 94%, transparent);
  border-top: 1px solid var(--color-border);
  box-shadow: 0 -10px 26px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(16px);
  transform: none;
}

.bottom-nav a {
  display: flex;
  min-width: 0;
  min-height: 46px;
  align-items: center;
  flex-direction: column;
  justify-content: center;
  gap: 3px;
  color: var(--color-text);
}

.bottom-nav a > span {
  display: grid;
  width: 24px;
  height: 24px;
  place-items: center;
}

.bottom-nav svg {
  display: block;
  flex-shrink: 0;
}

.bottom-nav small {
  overflow: hidden;
  max-width: 100%;
  font-size: 8px;
  font-weight: 800;
  line-height: 1.1;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bottom-nav a.router-link-active {
  color: var(--color-primary);
}

.bottom-nav .bottom-nav__primary {
  color: var(--color-text);
}

.bottom-nav .bottom-nav__primary > span {
  width: 40px;
  height: 40px;
  color: #fff;
  background: linear-gradient(145deg, var(--color-primary), var(--color-primary-dark));
  border-radius: 50%;
  box-shadow: 0 8px 18px rgba(8, 102, 255, 0.26);
}

.bottom-nav .bottom-nav__primary small {
  color: var(--color-text);
}
</style>
