<script setup>
import { onMounted } from 'vue'
import { ArrowLeft, Check, LockKeyhole } from '@lucide/vue'
import { useRoute } from 'vue-router'

import BadgeMark from '../components/profile/BadgeMark.vue'
import { useProfileStore } from '../stores/profile'

const route = useRoute()
const profileStore = useProfileStore()
onMounted(() => profileStore.loadBadge(route.params.code))
</script>

<template>
  <main class="mobile-shell badge-detail">
    <header class="sub-header">
      <RouterLink to="/my/badges" aria-label="배지 컬렉션으로 돌아가기"><ArrowLeft /></RouterLink>
      <h1>배지 상세</h1>
      <span></span>
    </header>
    <section v-if="profileStore.badge" class="badge-content">
      <BadgeMark :badge="profileStore.badge" :size="112" />
      <small>{{ profileStore.badge.earned ? 'BADGE UNLOCKED' : 'BADGE QUEST' }}</small>
      <h2>{{ profileStore.badge.name }}</h2>
      <p>{{ profileStore.badge.description }}</p>
      <div class="progress"><i :style="{ width: `${profileStore.badge.progress}%` }"></i></div>
      <strong>{{ profileStore.badge.progress }}%</strong>
      <div class="condition">
        <component :is="profileStore.badge.earned ? Check : LockKeyhole" :size="21" />
        <span>
          {{ profileStore.badge.earned ? '획득한 배지입니다.' : `현재 ${profileStore.badge.current_value} / 목표 ${profileStore.badge.condition_value}` }}
        </span>
      </div>
    </section>
  </main>
</template>

<style scoped>
.badge-detail { background:#f7faff; }
.sub-header { display:grid; grid-template-columns:42px 1fr 42px; align-items:center; padding:18px var(--content-padding); background:#fff; border-bottom:1px solid var(--color-border); }
.sub-header a { display:grid; width:40px; height:40px; place-items:center; }
.sub-header h1 { margin:0; font-size:18px; text-align:center; }
.badge-content { display:flex; align-items:center; flex-direction:column; padding:58px var(--content-padding); text-align:center; }
.badge-content > small { margin-top:25px; color:var(--color-primary); font-size:9px; font-weight:800; }
.badge-content h2 { margin:5px 0 8px; font-size:25px; }
.badge-content p { max-width:280px; margin:0; color:var(--color-muted); font-size:12px; line-height:1.7; }
.progress { width:100%; height:9px; margin-top:30px; overflow:hidden; background:#e2e8f1; border-radius:5px; }
.progress i { display:block; height:100%; background:var(--color-primary); border-radius:5px; }
.badge-content > strong { margin-top:7px; color:var(--color-primary); font-size:13px; }
.condition { display:flex; width:100%; align-items:center; gap:10px; margin-top:25px; padding:15px; color:var(--color-primary); background:#fff; border:1px solid var(--color-border); border-radius:var(--radius-medium); text-align:left; }
.condition span { color:var(--color-navy); font-size:12px; font-weight:600; }
</style>
