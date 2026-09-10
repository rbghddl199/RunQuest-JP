<script setup>
import { onMounted } from 'vue'
import { ArrowLeft, Award, Bell, Heart, MessageCircle, Sparkles } from '@lucide/vue'
import { useRouter } from 'vue-router'

import AppState from '../components/common/AppState.vue'
import { useNotificationStore } from '../stores/notifications'

const store = useNotificationStore()
const router = useRouter()
const icons = {
  badge: Award,
  like: Heart,
  comment: MessageCircle,
  recommendation: Sparkles,
  system: Bell,
}

async function openNotification(item) {
  await store.markRead(item)
  const target = store.targetLink(item)
  if (target) router.push(target)
}

onMounted(() => store.load())
</script>

<template>
  <main class="mobile-shell notification-page">
    <header>
      <button type="button" class="back-button" aria-label="이전 화면" @click="router.back()">
        <ArrowLeft :size="24" />
      </button>
      <h1>알림</h1>
      <button type="button" :disabled="!store.unreadCount" @click="store.markAllRead">
        모두 읽음
      </button>
    </header>

    <section class="notification-summary">
      <span><Bell :size="20" /></span>
      <div>
        <strong>{{ store.unreadCount }}개의 새 알림</strong>
        <small>최근 알림은 최대 50개까지 표시됩니다.</small>
      </div>
    </section>

    <section class="notification-list">
      <button
        v-for="item in store.notifications"
        :key="item.id"
        type="button"
        :class="{ unread: !item.is_read }"
        @click="openNotification(item)"
      >
        <span><component :is="icons[item.notification_type] ?? Bell" :size="20" /></span>
        <div>
          <strong>{{ item.title }}</strong>
          <p>{{ item.message }}</p>
          <small>{{ new Date(item.created_at).toLocaleString('ko-KR') }}</small>
        </div>
        <i v-if="!item.is_read" aria-label="읽지 않음"></i>
      </button>

      <AppState
        v-if="store.isLoading"
        compact
        type="loading"
        title="알림을 불러오는 중입니다"
        message="최근 활동 소식을 확인하고 있어요."
      />
      <AppState
        v-else-if="store.errorMessage"
        compact
        type="error"
        title="알림을 불러오지 못했어요"
        :message="store.errorMessage"
        action-label="다시 시도"
        @action="store.load"
      />
      <AppState
        v-else-if="!store.notifications.length"
        compact
        type="empty"
        title="새 알림이 없어요"
        message="러닝과 커뮤니티 활동 소식이 여기에 모입니다."
      />
    </section>
  </main>
</template>

<style scoped>
.notification-page { background: var(--color-background); }
.notification-page header { display:grid; height:64px; grid-template-columns:44px 1fr 72px; align-items:center; padding:0 14px; background:var(--color-surface); border-bottom:1px solid var(--color-border); }
.back-button { display:grid; width:40px; height:40px; place-items:center; color:var(--color-navy); background:transparent; }
header h1 { margin:0; font-size:18px; text-align:center; }
header button { color:var(--color-primary); background:transparent; font-size:10px; font-weight:700; }
.notification-summary { display:flex; align-items:center; gap:10px; padding:18px var(--content-padding); background:var(--color-primary-soft); }
.notification-summary > span { display:grid; width:40px; height:40px; place-items:center; color:#fff; background:var(--color-primary); border-radius:50%; }
.notification-summary div { display:grid; gap:3px; }
.notification-summary strong { color:var(--color-navy); font-size:13px; }
.notification-summary small { color:var(--color-muted); font-size:9px; }
.notification-list { padding:0 var(--content-padding) 30px; background:var(--color-surface); }
.notification-list > button { position:relative; display:grid; width:100%; grid-template-columns:42px 1fr 8px; align-items:start; gap:10px; padding:16px 0; color:var(--color-text); background:var(--color-surface); border-bottom:1px solid var(--color-border); text-align:left; }
.notification-list > button > span { display:grid; width:40px; height:40px; place-items:center; color:var(--color-primary); background:var(--color-primary-soft); border-radius:50%; }
.notification-list button div { display:grid; gap:4px; }
.notification-list strong { color:var(--color-navy); font-size:12px; }
.notification-list p { margin:0; color:var(--color-muted); font-size:10px; line-height:1.5; }
.notification-list small { color:var(--color-muted); font-size:8px; }
.notification-list i { width:7px; height:7px; margin-top:6px; background:var(--color-primary); border-radius:50%; }
.notification-list .unread { background:color-mix(in srgb, var(--color-primary-soft) 32%, var(--color-surface)); }
</style>
