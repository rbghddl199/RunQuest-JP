<script setup>
import { computed, onMounted } from 'vue'
import { ArrowLeft } from '@lucide/vue'

import BadgeMark from '../components/profile/BadgeMark.vue'
import { useProfileStore } from '../stores/profile'

const profileStore = useProfileStore()
const earnedCount = computed(() => profileStore.badges.filter((badge) => badge.earned).length)
onMounted(() => profileStore.loadBadges())
</script>

<template>
  <main class="mobile-shell badge-page">
    <header class="sub-header">
      <RouterLink to="/my" aria-label="마이페이지로 돌아가기"><ArrowLeft /></RouterLink>
      <h1>배지 컬렉션</h1>
      <span></span>
    </header>
    <section class="badge-intro">
      <small>COLLECTION</small>
      <h2>{{ earnedCount }} / {{ profileStore.badges.length }} 획득</h2>
      <p>러닝 퀘스트를 완료하고 새로운 배지를 모아보세요.</p>
    </section>
    <section class="badge-grid">
      <RouterLink
        v-for="badge in profileStore.badges"
        :key="badge.code"
        :to="`/my/badges/${badge.code}`"
        class="badge-item"
      >
        <BadgeMark :badge="badge" />
        <strong>{{ badge.name }}</strong>
        <small>{{ badge.earned ? '획득 완료' : `${badge.progress}% 달성` }}</small>
        <div><i :style="{ width: `${badge.progress}%` }"></i></div>
      </RouterLink>
    </section>
  </main>
</template>

<style scoped>
.badge-page { background:#f7faff; }
.sub-header { display:grid; grid-template-columns:42px 1fr 42px; align-items:center; padding:18px var(--content-padding); background:#fff; border-bottom:1px solid var(--color-border); }
.sub-header a { display:grid; width:40px; height:40px; place-items:center; }
.sub-header h1 { margin:0; font-size:18px; text-align:center; }
.badge-intro { padding:24px var(--content-padding); color:#fff; background:var(--color-primary); }
.badge-intro small { font-size:9px; font-weight:800; opacity:.8; }
.badge-intro h2 { margin:3px 0 7px; font-size:24px; }
.badge-intro p { margin:0; font-size:11px; opacity:.85; }
.badge-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; padding:18px var(--content-padding); }
.badge-item { display:flex; min-height:176px; align-items:center; flex-direction:column; justify-content:center; padding:16px 12px; background:#fff; border:1px solid var(--color-border); border-radius:var(--radius-medium); text-align:center; }
.badge-item strong { margin-top:11px; font-size:13px; }
.badge-item small { margin-top:3px; color:var(--color-muted); font-size:9px; }
.badge-item > div { width:100%; height:5px; margin-top:12px; overflow:hidden; background:#e8edf5; border-radius:3px; }
.badge-item i { display:block; height:100%; background:var(--color-primary); border-radius:3px; }
</style>
