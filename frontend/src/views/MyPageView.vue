<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  Award,
  Bell,
  Bookmark,
  CalendarDays,
  ChevronRight,
  Clock3,
  Droplets,
  Flame,
  Heart,
  Leaf,
  MapPinned,
  Moon,
  Route,
  Settings,
  Sparkles,
  Target,
  Zap,
} from '@lucide/vue'
import { useRouter } from 'vue-router'

import AppState from '../components/common/AppState.vue'
import AppBottomNav from '../components/navigation/AppBottomNav.vue'
import { useNotificationStore } from '../stores/notifications'
import { useProfileStore } from '../stores/profile'
import { useSettingsStore } from '../stores/settings'
import { formatDuration } from '../utils/running'
import { formatDistance } from '../utils/units'
import { getProfileImage } from '../utils/courseImages'
import { getStoredProfileAvatar } from '../utils/profileAvatar'

const profileStore = useProfileStore()
const notificationStore = useNotificationStore()
const settingsStore = useSettingsStore()
const router = useRouter()
const streakNoticeOpen = ref(false)
const notificationOpen = ref(false)
const summary = computed(() => profileStore.summary)
const stats = computed(() => summary.value?.stats ?? {})
const recentNotifications = computed(() => notificationStore.notifications.slice(0, 5))
const avatarImage = computed(() => (
  getStoredProfileAvatar(summary.value?.user?.email)
  ?? getProfileImage(summary.value?.user?.id ?? summary.value?.user?.profile?.nickname)
))
const hasAttendanceEffect = computed(() => Number(summary.value?.profile_style?.streak_days ?? 0) >= 7)
const styleIcon = computed(() => ({
  ember: Flame,
  moon: Moon,
  speed: Zap,
  wave: Droplets,
  nature: Leaf,
})[summary.value?.profile_style.style_code] ?? Flame)
const runningProfile = computed(() => summary.value?.running_profile ?? {})
const profileTags = computed(() => (
  runningProfile.value.tags
  ?? runningProfile.value.secondary_types?.map((item) => item.name)
  ?? []
))
const profileReasons = computed(() => runningProfile.value.reasons ?? [])
const primaryProfileType = computed(() => (
  runningProfile.value.primary_type
  ?? runningProfile.value.type
  ?? '균형형 러너'
))
const profileBackgroundType = computed(() => {
  const type = primaryProfileType.value
  if (type.includes('공원')) return 'park'
  if (type.includes('리버사이드')) return 'riverside'
  if (type.includes('도심')) return 'urban'
  if (type.includes('트레일')) return 'trail'
  return 'balanced'
})
const profileCategoryLabel = computed(() => (
  runningProfile.value.category ? `AI 러닝 프로필 · ${runningProfile.value.category}` : 'AI 러닝 프로필'
))
const toggleStreakNotice = () => {
  streakNoticeOpen.value = !streakNoticeOpen.value
  if (streakNoticeOpen.value) notificationOpen.value = false
}

const toggleNotifications = async () => {
  notificationOpen.value = !notificationOpen.value
  if (notificationOpen.value) {
    streakNoticeOpen.value = false
    if (!notificationStore.notifications.length) {
      await notificationStore.load()
    }
  }
}

const formatNotificationTime = (value) => {
  if (!value) return ''
  const created = new Date(value)
  const diffMinutes = Math.floor((Date.now() - created.getTime()) / 60000)
  if (diffMinutes < 1) return '방금 전'
  if (diffMinutes < 60) return `${diffMinutes}분 전`
  if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}시간 전`
  return created.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })
}

const readNotification = async (notification) => {
  await notificationStore.markRead(notification)
  notificationOpen.value = false
  const target = notificationStore.targetLink(notification)
  if (target) await router.push(target)
}

const menuItems = [
  { label: '러닝 기록', to: '/my/records', icon: Route },
  { label: '배지 컬렉션', to: '/my/badges', icon: Award },
  { label: '출석 현황', to: '/my/attendance', icon: CalendarDays },
  { label: '나의 코스', to: '/my/courses', icon: MapPinned },
  { label: '저장한 코스', to: '/my/favorites', icon: Heart },
  { label: '저장한 게시글', to: '/my/saved-posts', icon: Bookmark },
  { label: '설정', to: '/my/settings', icon: Settings },
]

onMounted(() => {
  profileStore.loadSummary()
  notificationStore.load()
})
</script>

<template>
  <main class="mobile-shell my-page">
    <div v-if="summary" class="my-page__content">
      <header class="profile-header">
        <div class="avatar-wrap" :style="{ '--accent': summary.profile_style.accent_color }">
          <div class="avatar" :class="hasAttendanceEffect ? `avatar--${summary.profile_style.style_code}` : ''">
            <img v-if="avatarImage" :src="avatarImage" :alt="`${summary.user.profile.nickname} 프로필`" />
            <span v-else>{{ summary.user.profile.nickname.slice(0, 1) }}</span>
          </div>
          <img
            v-if="hasAttendanceEffect && summary.profile_style.frame_url"
            class="avatar-frame"
            :src="summary.profile_style.frame_url"
            :alt="`${summary.profile_style.style_name} ${summary.profile_style.stage_name} 프로필 프레임`"
          />
        </div>
        <div class="runner-info">
          <p>RUNQUEST RUNNER</p>
          <h1>{{ summary.user.profile.nickname }}</h1>
          <span>{{ primaryProfileType }}</span>
        </div>
        <div class="profile-actions">
          <button
            type="button"
            class="notice-button"
            aria-label="알림"
            @click="toggleNotifications"
          >
            <Bell :size="18" />
            <i v-if="notificationStore.unreadCount">{{ notificationStore.unreadCount }}</i>
          </button>
          <button type="button" class="streak" @click="toggleStreakNotice">
            <Flame :size="18" fill="currentColor" />
            <strong>{{ stats.streak_days }}</strong>
            <small>{{ summary.profile_style.stage_name }}</small>
          </button>
          <div v-if="streakNoticeOpen" class="streak-popover" role="status">
            <strong>{{ stats.streak_days }}일 연속 출석 중</strong>
            <span v-if="summary.profile_style.next_stage">
              연속 {{ summary.profile_style.next_stage.days }}일에 {{ summary.profile_style.next_stage.name }} 단계가 열려요.
            </span>
            <span v-else>최고 성장 단계에 도달했어요.</span>
          </div>
          <div v-if="notificationOpen" class="notification-popover" role="dialog" aria-label="알림 상세">
            <header>
              <strong>알림</strong>
              <span>{{ notificationStore.unreadCount }}개 읽지 않음</span>
            </header>
            <div v-if="recentNotifications.length" class="notification-list">
              <button
                v-for="notification in recentNotifications"
                :key="notification.id"
                type="button"
                :class="{ unread: !notification.is_read }"
                @click="readNotification(notification)"
              >
                <span>
                  <strong>{{ notification.title }}</strong>
                  <small>{{ formatNotificationTime(notification.created_at) }}</small>
                </span>
                <p>{{ notification.message }}</p>
              </button>
            </div>
            <p v-else class="notification-empty">새 알림이 없어요.</p>
            <RouterLink to="/notifications">전체 알림 보기</RouterLink>
          </div>
        </div>
      </header>

      <section class="style-band" :style="{ '--accent': summary.profile_style.accent_color }">
        <div>
          <component :is="styleIcon" :size="20" />
          <span>
            <small>PROFILE STYLE</small>
            <strong>{{ summary.profile_style.style_name }} · {{ summary.profile_style.stage_name }}</strong>
          </span>
        </div>
        <p v-if="summary.profile_style.next_stage">
          연속 {{ summary.profile_style.next_stage.days }}일에 {{ summary.profile_style.next_stage.name }} 단계가 열려요.
        </p>
        <p v-else>최고 성장 단계에 도달했어요.</p>
      </section>

      <section class="goal-band">
        <div class="section-title">
          <span><Target :size="20" /></span>
          <div>
            <small>이번 달 목표</small>
            <h2>
              {{ formatDistance(summary.monthly_goal.current_km, settingsStore.settings?.distance_unit) }}
              /
              {{ formatDistance(summary.monthly_goal.target_km, settingsStore.settings?.distance_unit) }}
            </h2>
          </div>
          <strong>{{ summary.monthly_goal.progress }}%</strong>
        </div>
        <div class="progress"><i :style="{ width: `${summary.monthly_goal.progress}%` }"></i></div>
      </section>

      <section class="stats-band">
        <h2>나의 러닝 현황</h2>
        <div>
          <span><Route :size="22" /><strong>{{ formatDistance(stats.total_distance, settingsStore.settings?.distance_unit) }}</strong><small>누적 거리</small></span>
          <span><Flame :size="22" /><strong>{{ stats.run_count }}회</strong><small>총 러닝</small></span>
          <span><Clock3 :size="22" /><strong>{{ formatDuration(stats.total_duration) }}</strong><small>총 시간</small></span>
        </div>
      </section>

      <section class="ai-profile" :class="`ai-profile--${profileBackgroundType}`">
        <div class="ai-profile__glow" aria-hidden="true"></div>
        <div class="ai-profile__header">
          <span><Sparkles :size="21" /></span>
          <div>
            <small>{{ profileCategoryLabel }}</small>
            <h2>{{ primaryProfileType }}</h2>
          </div>
        </div>
        <p>{{ summary.running_profile.description }}</p>
        <div class="profile-tags">
          <span v-for="tag in profileTags" :key="tag">#{{ tag }}</span>
        </div>
        <div v-if="profileReasons.length" class="ai-profile__reasons">
          <strong>나타난 이유</strong>
          <span v-for="reason in profileReasons" :key="reason">{{ reason }}</span>
        </div>
      </section>

      <nav class="profile-menu" aria-label="마이페이지 상세 메뉴">
        <RouterLink v-for="item in menuItems" :key="item.label" :to="item.to">
          <component :is="item.icon" :size="21" />
          <span>{{ item.label }}</span>
          <ChevronRight :size="19" />
        </RouterLink>
      </nav>
    </div>

    <AppState
      v-else-if="profileStore.isLoading"
      type="loading"
      title="러닝 프로필을 불러오는 중입니다"
      message="기록, 목표, 프로필 정보를 정리하고 있어요."
    />
    <AppState
      v-else
      type="error"
      title="러닝 프로필을 불러오지 못했어요"
      :message="profileStore.errorMessage"
      action-label="다시 시도"
      @action="profileStore.loadSummary"
    />
    <AppBottomNav />
  </main>
</template>

<style scoped>
.my-page { display:flex; min-height:100vh; flex-direction:column; background:#f6f9fe; }
.my-page__content { flex:0 0 auto; padding:var(--page-top-padding) var(--content-padding) var(--page-bottom-padding); }
.profile-header { display:grid; grid-template-columns:92px minmax(0,1fr) 98px; align-items:center; gap:12px; min-width:0; }
.avatar-wrap { position:relative; display:grid; width:92px; height:92px; place-items:center; overflow:visible; }
.avatar { position:relative; z-index:1; display:grid; width:66px; height:66px; overflow:hidden; place-items:center; color:#fff; font-size:24px; font-weight:800; background:var(--color-primary); border:3px solid rgba(255,255,255,.95); border-radius:50%; box-shadow:0 5px 14px color-mix(in srgb,var(--accent) 32%,transparent); }
.avatar img { width:100%; height:100%; object-fit:cover; }
.avatar-frame { position:absolute; z-index:2; inset:50% auto auto 50%; width:88px; height:88px; max-width:none; object-fit:contain; pointer-events:none; transform:translate(-50%,-50%); animation:frame-pulse 2.8s ease-in-out infinite; }
.avatar--moon { background:#7257e8; }.avatar--speed { background:#087cff; }.avatar--nature { background:#23a55a; }.avatar--wave { background:#00a8cc; }.avatar--ember { background:#ff6b35; }
.runner-info { min-width:0; }
.runner-info p,.runner-info h1 { margin:0; }
.runner-info p { color:var(--color-primary); font-size:9px; font-weight:800; }
.runner-info h1 { overflow:hidden; margin-top:2px; font-size:var(--title-font-size); text-overflow:ellipsis; white-space:nowrap; }
.runner-info span { display:block; overflow:hidden; color:var(--color-muted); font-size:11px; text-overflow:ellipsis; white-space:nowrap; }
.profile-actions { position:relative; display:grid; grid-template-columns:34px 58px; align-items:center; justify-content:end; gap:6px; }
.streak { display:grid; grid-template-columns:auto auto; align-items:center; justify-content:center; gap:2px; min-width:0; padding:8px 6px; color:#f47a22; background:#fff; border:1px solid #ffe0c8; border-radius:16px; text-align:center; box-shadow:0 8px 20px rgba(244,122,34,.1); }
.streak strong { font-size:22px; line-height:1; }
.streak small { grid-column:1/-1; overflow:hidden; max-width:48px; color:var(--color-muted); font-size:8px; text-overflow:ellipsis; white-space:nowrap; }
.notice-button { position:relative; display:grid; width:34px; height:34px; place-items:center; color:var(--color-primary); background:#fff; border:1px solid var(--color-border); border-radius:50%; box-shadow:0 8px 18px rgba(8,102,255,.1); }
.notice-button i { position:absolute; top:-4px; right:-4px; display:grid; min-width:15px; height:15px; padding:0 4px; place-items:center; color:#fff; background:#ef4444; border:2px solid #fff; border-radius:999px; font-size:8px; font-style:normal; font-weight:900; line-height:1; }
.streak-popover { position:absolute; z-index:8; top:48px; right:0; display:grid; width:178px; gap:4px; padding:12px; color:var(--color-navy); background:#fff; border:1px solid #dbe8f8; border-radius:12px; box-shadow:0 14px 30px rgba(15,23,42,.14); text-align:left; }
.streak-popover strong { font-size:12px; }
.streak-popover span { color:var(--color-muted); font-size:10px; line-height:1.45; }
.notification-popover { position:absolute; z-index:9; top:48px; right:0; display:grid; width:min(278px,calc(100vw - 32px)); gap:10px; padding:14px; color:var(--color-navy); background:#fff; border:1px solid #dbe8f8; border-radius:18px; box-shadow:0 18px 38px rgba(15,23,42,.18); text-align:left; }
.notification-popover header { display:flex; align-items:center; justify-content:space-between; gap:8px; }
.notification-popover header strong { font-size:14px; }
.notification-popover header span { color:var(--color-muted); font-size:10px; font-weight:700; }
.notification-list { display:grid; gap:8px; max-height:260px; overflow:auto; }
.notification-list button { display:grid; gap:5px; width:100%; padding:11px; color:var(--color-navy); background:#f7faff; border:1px solid var(--color-border); border-radius:var(--card-radius); text-align:left; }
.notification-list button.unread { background:#eef6ff; border-color:#bcd9ff; }
.notification-list button > span { display:flex; align-items:flex-start; justify-content:space-between; gap:8px; }
.notification-list strong { min-width:0; font-size:12px; line-height:1.3; }
.notification-list small { flex:0 0 auto; color:var(--color-muted); font-size:9px; font-weight:700; }
.notification-list p { margin:0; color:var(--color-muted); font-size:10px; line-height:1.45; }
.notification-empty { margin:0; padding:18px 8px; color:var(--color-muted); font-size:11px; text-align:center; }
.notification-popover a { justify-self:center; color:var(--color-primary); font-size:11px; font-weight:800; }
.style-band { display:none; }
.style-band>div { display:flex; align-items:center; gap:9px; color:var(--accent); }
.style-band span { display:grid; gap:2px; }
.style-band small { font-size:8px; font-weight:800; }
.style-band strong { color:var(--color-navy); font-size:13px; }
.style-band p { margin:9px 0 0; color:var(--color-muted); font-size:10px; line-height:1.5; }
.goal-band,.stats-band,.profile-menu { margin-top:var(--page-gap); padding:var(--card-padding); background:#fff; border:1px solid var(--color-border); border-radius:var(--card-radius); }
.section-title { display:flex; align-items:center; gap:10px; }
.section-title > span { display:grid; width:32px; height:32px; flex:0 0 auto; place-items:center; color:var(--color-primary); background:var(--color-primary-soft); border-radius:50%; }
.section-title div { flex:1; min-width:0; }
.section-title small { color:var(--color-muted); font-size:9px; }
.section-title h2 { margin:0; font-size:var(--section-title-size); }
.section-title > strong { color:var(--color-primary); font-size:14px; }
.progress { height:6px; margin-top:11px; overflow:hidden; background:#e7edf6; border-radius:4px; }
.progress i { display:block; height:100%; background:linear-gradient(90deg,var(--color-primary),#21d5e8); border-radius:4px; }
.stats-band h2 { margin:0 0 10px; font-size:var(--section-title-size); }
.stats-band > div { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); }
.stats-band span { display:grid; min-width:0; justify-items:center; gap:2px; color:var(--color-primary); text-align:center; }
.stats-band span + span { border-left:1px solid var(--color-border); }
.stats-band strong { overflow:hidden; max-width:100%; color:var(--color-navy); font-size:12px; text-overflow:ellipsis; white-space:nowrap; }
.stats-band small { color:var(--color-muted); font-size:9px; }
.ai-profile { position:relative; isolation:isolate; overflow:hidden; margin-top:var(--page-gap); min-height:218px; padding:var(--card-padding); color:#fff; background:#0b3f9f; border-radius:var(--card-radius); box-shadow:0 18px 36px rgba(8,102,255,.24); }
.ai-profile::before { content:""; position:absolute; z-index:1; inset:0; background:linear-gradient(90deg,rgba(8,45,120,.86) 0%,rgba(20,90,190,.68) 45%,rgba(20,180,220,.34) 100%),linear-gradient(180deg,rgba(2,14,42,.06),rgba(2,14,42,.18)); pointer-events:none; }
.ai-profile::after { content:""; position:absolute; z-index:0; inset:-6px; background:var(--profile-bg) center/cover no-repeat; filter:blur(2px) saturate(.9); transform:scale(1.02); pointer-events:none; }
.ai-profile > * { position:relative; z-index:2; }
.ai-profile--park { --profile-bg:url('../assets/images/profile-types/ai-profile-park.webp'); }
.ai-profile--riverside { --profile-bg:url('../assets/images/profile-types/ai-profile-riverside.webp'); }
.ai-profile--urban { --profile-bg:url('../assets/images/profile-types/ai-profile-urban.webp'); }
.ai-profile--trail { --profile-bg:url('../assets/images/profile-types/ai-profile-trail.webp'); }
.ai-profile--balanced { --profile-bg:url('../assets/images/profile-types/ai-profile-balanced.webp'); }
.ai-profile__glow { position:absolute; z-index:1; right:-42px; top:-46px; width:150px; height:150px; background:radial-gradient(circle,rgba(255,255,255,.22),transparent 64%); border-radius:50%; animation:profile-glow 3s ease-in-out infinite; }
.ai-profile__header { position:relative; display:flex; align-items:center; gap:9px; }
.ai-profile__header > span { display:grid; width:34px; height:34px; place-items:center; color:#0b6cff; background:#fff; border-radius:13px; box-shadow:0 10px 24px rgba(3,12,34,.18); }
.ai-profile__header small { color:rgba(255,255,255,.72); font-size:8px; font-weight:900; }
.ai-profile__header h2 { margin:1px 0 0; font-size:19px; letter-spacing:0; }
.ai-profile p { position:relative; margin:10px 0 0; color:rgba(255,255,255,.88); font-size:11px; line-height:1.45; }
.profile-tags { position:relative; display:flex; flex-wrap:wrap; gap:6px; margin-top:10px; }
.profile-tags span { padding:5px 7px; color:#eaf6ff; background:rgba(255,255,255,.14); border:1px solid rgba(255,255,255,.16); border-radius:999px; font-size:9px; font-weight:800; backdrop-filter:blur(8px); }
.ai-profile__reasons { position:relative; display:grid; max-width:405px; gap:4px; margin-top:10px; padding:10px; background:rgba(8,74,174,.42); border:1px solid rgba(255,255,255,.18); border-radius:var(--card-radius); backdrop-filter:blur(8px); }
.ai-profile__reasons strong { font-size:11px; }
.ai-profile__reasons span { color:rgba(255,255,255,.82); font-size:9px; line-height:1.35; }
.profile-menu { padding:4px 18px; }
.profile-menu a { display:grid; grid-template-columns:26px 1fr auto; align-items:center; gap:9px; min-height:51px; color:var(--color-navy); }
.profile-menu a + a { border-top:1px solid var(--color-border); }
.profile-menu a > svg:first-child { color:var(--color-primary); }
.profile-menu span { font-size:13px; font-weight:600; }
@keyframes frame-pulse { 0%,100% { transform:translate(-50%,-50%) scale(.98); } 50% { transform:translate(-50%,-50%) scale(1.02); } }
@keyframes profile-glow { 0%,100% { transform:scale(.92); opacity:.7; } 50% { transform:scale(1.08); opacity:1; } }
:global(:root[data-theme='dark']) .my-page { background:var(--color-background); }
:global(:root[data-theme='dark']) .streak,
:global(:root[data-theme='dark']) .notice-button,
:global(:root[data-theme='dark']) .streak-popover,
:global(:root[data-theme='dark']) .notification-popover,
:global(:root[data-theme='dark']) .goal-band,
:global(:root[data-theme='dark']) .stats-band,
:global(:root[data-theme='dark']) .profile-menu { color:var(--color-text); background:var(--color-surface); border-color:var(--color-border); box-shadow:0 14px 34px rgba(0,0,0,.34); }
:global(:root[data-theme='dark']) .streak { color:#ffb36b; }
:global(:root[data-theme='dark']) .streak small,
:global(:root[data-theme='dark']) .streak-popover span,
:global(:root[data-theme='dark']) .notification-popover header span,
:global(:root[data-theme='dark']) .notification-list small,
:global(:root[data-theme='dark']) .notification-list p,
:global(:root[data-theme='dark']) .notification-empty,
:global(:root[data-theme='dark']) .runner-info span,
:global(:root[data-theme='dark']) .stats-band small,
:global(:root[data-theme='dark']) .section-title small { color:var(--color-muted); }
:global(:root[data-theme='dark']) .notice-button { color:#7cb7ff; }
:global(:root[data-theme='dark']) .notice-button i { border-color:var(--color-surface); }
:global(:root[data-theme='dark']) .notification-list button { color:var(--color-text); background:var(--color-elevated); border-color:var(--color-border); }
:global(:root[data-theme='dark']) .notification-list button.unread { background:#12233d; border-color:#2f6fc3; }
:global(:root[data-theme='dark']) .runner-info h1,
:global(:root[data-theme='dark']) .section-title h2,
:global(:root[data-theme='dark']) .stats-band h2,
:global(:root[data-theme='dark']) .stats-band strong,
:global(:root[data-theme='dark']) .profile-menu a { color:var(--color-text); }
:global(:root[data-theme='dark']) .ai-profile { color:#fff !important; background:#0b3f9f !important; border:1px solid rgba(255,255,255,.14); box-shadow:0 18px 36px rgba(0,0,0,.42); }
:global(:root[data-theme='dark']) .ai-profile__header h2,
:global(:root[data-theme='dark']) .ai-profile__header small,
:global(:root[data-theme='dark']) .ai-profile p,
:global(:root[data-theme='dark']) .ai-profile__reasons span { color:rgba(255,255,255,.9) !important; }
:global(:root[data-theme='dark']) .ai-profile__header > span { color:#0b6cff; background:#f8fbff; }
@media (max-width:350px) {
  .profile-header { grid-template-columns:82px minmax(0,1fr) 90px; gap:8px; }
  .avatar-wrap { width:82px; height:82px; }
  .avatar { width:60px; height:60px; }
  .avatar-frame { width:80px; height:80px; }
}
@media (prefers-reduced-motion:reduce) { .avatar-frame,.ai-profile__glow { animation:none; } }
</style>
