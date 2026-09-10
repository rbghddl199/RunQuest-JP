<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import {
  Bell,
  ChevronLeft,
  ChevronRight,
  Cloud,
  CloudFog,
  CloudRain,
  Droplets,
  Gauge,
  Home,
  MapPinned,
  Play,
  ShieldCheck,
  Snowflake,
  Sparkles,
  Sun,
  Target,
  Thermometer,
  ThermometerSun,
  TriangleAlert,
  Wind,
  Zap,
} from '@lucide/vue'
import { useRouter } from 'vue-router'

import AppBottomNav from '../components/navigation/AppBottomNav.vue'
import { useHomeStore } from '../stores/home'
import { useNotificationStore } from '../stores/notifications'
import { useSettingsStore } from '../stores/settings'
import { getCourseImageForCourse, getProfileImage } from '../utils/courseImages'
import { getStoredProfileAvatar } from '../utils/profileAvatar'
import { formatTemperature } from '../utils/units'

const homeStore = useHomeStore()
const notificationStore = useNotificationStore()
const settingsStore = useSettingsStore()
const router = useRouter()
const dashboard = computed(() => homeStore.dashboard)
const carouselIndex = ref(0)
const notificationOpen = ref(false)
let carouselTimer = null
const recentNotifications = computed(() => notificationStore.notifications.slice(0, 5))
const recommendedCourses = computed(() => (
  dashboard.value?.recommendations?.length
    ? dashboard.value.recommendations.slice(0, 5)
    : (dashboard.value?.recommendation ? [dashboard.value.recommendation] : [])
).filter((item) => item?.course))
const profileImage = computed(() => (
  getStoredProfileAvatar(dashboard.value?.user?.email)
  ?? getProfileImage(dashboard.value?.user?.id ?? dashboard.value?.user?.profile?.nickname)
))
const missionProgress = computed(() => {
  const mission = dashboard.value?.mission
  if (!mission) return 0
  if (typeof mission.progress === 'number') return mission.progress
  if (!mission.target) return 0
  return Math.min(Math.round((mission.current / mission.target) * 100), 100)
})
const missionUnit = computed(() => dashboard.value?.mission?.unit ?? '회')
const bonusMission = computed(() => dashboard.value?.mission?.bonus_mission ?? null)
const missionStepText = computed(() => {
  const mission = dashboard.value?.mission
  if (!mission?.total_missions) return ''
  return `${mission.level_label ?? '맞춤'} · ${mission.current_position}/${mission.total_missions}`
})
const weatherCode = computed(() => dashboard.value?.weather?.weather_code ?? 800)
const weatherMain = computed(() => dashboard.value?.weather?.main ?? '')
const weatherUiType = computed(() => {
  const weather = dashboard.value?.weather
  if (!weather) return 'sunny'
  const main = weatherMain.value
  const temperature = Number(weather.temperature ?? 0)
  const windSpeed = Number(weather.wind_speed ?? 0)
  if (['Thunderstorm', 'Squall', 'Tornado'].includes(main)) return 'storm'
  if (['Rain', 'Drizzle'].includes(main)) return 'rainy'
  if (main === 'Snow') return 'snowy'
  if (windSpeed >= 9) return 'windy'
  if (temperature >= 32) return 'hot'
  if (temperature <= -5) return 'cold'
  if (['Clouds', 'Mist', 'Fog', 'Haze', 'Smoke', 'Dust', 'Sand', 'Ash'].includes(main)) return 'cloudy'
  return 'sunny'
})
const weatherIcon = computed(() => {
  if (weatherUiType.value === 'storm') return Zap
  if (weatherUiType.value === 'snowy' || weatherUiType.value === 'cold') return Snowflake
  if (weatherUiType.value === 'windy') return Wind
  if (weatherUiType.value === 'hot') return ThermometerSun
  if (weatherUiType.value === 'cloudy') return CloudFog
  if ([200, 201, 202, 230, 231, 232, 500, 501, 502, 503, 504, 511, 520, 521, 522, 531, 61, 63, 65, 80, 81, 82, 95].includes(weatherCode.value)) return CloudRain
  if ([801, 802, 803, 804, 2, 3, 45, 48, 701, 741].includes(weatherCode.value)) return Cloud
  return Sun
})
const weatherMood = computed(() => {
  return weatherUiType.value
})
const weatherMessage = computed(() => {
  const weather = dashboard.value?.weather
  if (!weather) return ''
  if (weather.running_message) return weather.running_message
  if (weatherUiType.value === 'rainy') return '노면과 시야를 확인하고 짧은 회복주로 조절해요.'
  if (weatherUiType.value === 'cloudy') return '구름이 많은 날이에요. 체온을 지키며 가볍게 달려요.'
  return '햇살이 좋은 날이에요. 수분을 챙기고 산뜻하게 출발해요.'
})
const weatherLocationLabel = computed(() => dashboard.value?.weather?.location_label ?? '대전광역시')
const weatherBadges = computed(() => {
  const weather = dashboard.value?.weather
  if (!weather) return []
  const precipitation = weather.precipitation_probability ?? 0
  const windSpeed = Number(weather.wind_speed ?? 0)
  const apparentTemperature = formatTemperature(weather.apparent_temperature, settingsStore.settings?.temperature_unit)
  const temperature = formatTemperature(weather.temperature, settingsStore.settings?.temperature_unit)
  const windLabel = `바람 ${windSpeed.toFixed(1)}m/s`
  const base = {
    sunny: [
      { icon: ShieldCheck, label: '러닝 적합' },
      { icon: Droplets, label: '수분 체크' },
      { icon: Gauge, label: '페이스 업 가능' },
    ],
    cloudy: [
      { icon: CloudFog, label: '시야 체크' },
      { icon: Thermometer, label: `체감 ${apparentTemperature}` },
      { icon: Wind, label: windLabel },
    ],
    rainy: [
      { icon: Droplets, label: `강수 ${precipitation}%` },
      { icon: TriangleAlert, label: '노면 주의' },
      { icon: Gauge, label: '회복주 추천' },
    ],
    windy: [
      { icon: Wind, label: windLabel },
      { icon: Gauge, label: '강도 낮춤' },
      { icon: Thermometer, label: '체온 체크' },
    ],
    hot: [
      { icon: ThermometerSun, label: `기온 ${temperature}` },
      { icon: Droplets, label: '수분 체크' },
      { icon: MapPinned, label: '짧은 코스' },
    ],
    cold: [
      { icon: Snowflake, label: `기온 ${temperature}` },
      { icon: TriangleAlert, label: '미끄럼 주의' },
      { icon: Thermometer, label: '보온 체크' },
    ],
    snowy: [
      { icon: Snowflake, label: '눈길 주의' },
      { icon: TriangleAlert, label: '미끄럼 주의' },
      { icon: Home, label: '실내 운동' },
    ],
    storm: [
      { icon: Home, label: '실내 운동' },
      { icon: ShieldCheck, label: '안전 주의' },
      { icon: TriangleAlert, label: '러닝 보류' },
    ],
  }
  return base[weatherUiType.value] ?? base.sunny
})

function getCurrentLocation() {
  if (!navigator.geolocation) return Promise.resolve(null)
  return new Promise((resolve) => {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        })
      },
      () => resolve(null),
      {
        enableHighAccuracy: false,
        timeout: 3500,
        maximumAge: 1000 * 60 * 10,
      },
    )
  })
}

function courseCategory(item) {
  const targetCourse = item?.course
  if (!targetCourse) return '맞춤'
  const tags = targetCourse.tags ?? []
  if (targetCourse.difficulty === 'easy' || tags.some((tag) => String(tag).includes('초보자'))) return '초보자'
  if (tags.some((tag) => ['안전', '야간', '조명'].some((word) => String(tag).includes(word)))) return '안전'
  return targetCourse.course_type_label?.replace(' 코스', '') ?? '맞춤'
}

function courseReason(item) {
  if (item?.reasons?.length) return item.reasons[0]
  const category = courseCategory(item)
  if (category === '안전') return '안전을 중요하게 보는 러너들이 선호하는 코스예요.'
  if (category === '초보자') return '초보 러너들이 부담 없이 선택하는 코스예요.'
  return `${category} 유형 러너들이 선호하는 코스예요.`
}

function stopCarousel() {
  if (!carouselTimer) return
  window.clearInterval(carouselTimer)
  carouselTimer = null
}

function startCarousel() {
  stopCarousel()
  if (recommendedCourses.value.length <= 1) return
  carouselTimer = window.setInterval(() => {
    carouselIndex.value = (carouselIndex.value + 1) % recommendedCourses.value.length
  }, 4200)
}

function moveCarousel(offset) {
  const total = recommendedCourses.value.length
  if (!total) return
  carouselIndex.value = (carouselIndex.value + offset + total) % total
  startCarousel()
}

function goToSlide(index) {
  carouselIndex.value = index
  startCarousel()
}

async function toggleNotifications() {
  notificationOpen.value = !notificationOpen.value
  if (notificationOpen.value && !notificationStore.notifications.length) {
    await notificationStore.load()
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

async function readNotification(notification) {
  await notificationStore.markRead(notification)
  notificationOpen.value = false
  const target = notificationStore.targetLink(notification)
  if (target) await router.push(target)
}

watch(
  () => recommendedCourses.value.length,
  (length) => {
    carouselIndex.value = Math.min(carouselIndex.value, Math.max(length - 1, 0))
    startCarousel()
  },
)

onMounted(async () => {
  const location = await getCurrentLocation()
  await Promise.all([
    homeStore.loadDashboard(location),
    notificationStore.load(),
  ])
  startCarousel()
})
onUnmounted(stopCarousel)
</script>

<template>
  <main class="mobile-shell home-page">
    <div v-if="dashboard" class="home-content">
      <header class="home-header">
        <div>
          <small>RUNQUEST</small>
          <h1>안녕하세요, {{ dashboard.user.profile.nickname }}님</h1>
          <p>오늘의 러닝 브리핑을 준비했어요.</p>
        </div>
        <div class="header-actions">
          <button type="button" class="notice-button" aria-label="알림" @click="toggleNotifications">
            <Bell :size="18" />
            <i v-if="notificationStore.unreadCount">{{ notificationStore.unreadCount }}</i>
          </button>
          <RouterLink to="/my" class="profile-link" aria-label="마이페이지">
            <img v-if="profileImage" :src="profileImage" alt="" />
            <span v-else>{{ dashboard.user.profile.nickname.slice(0, 1) }}</span>
          </RouterLink>
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

      <section class="weather-band" :class="`weather-band--${weatherMood}`">
        <div class="weather-effect" aria-hidden="true">
          <span v-if="weatherUiType === 'sunny'" class="sun-layer"></span>
          <span v-if="weatherUiType === 'cloudy'" class="cloud-layer"></span>
          <span v-if="weatherUiType === 'rainy'" class="rain-layer"></span>
          <span v-if="weatherUiType === 'windy'" class="wind-layer"></span>
          <span v-if="weatherUiType === 'hot'" class="heat-layer"></span>
          <span v-if="['cold', 'snowy'].includes(weatherUiType)" class="snow-layer"></span>
          <span v-if="weatherUiType === 'storm'" class="storm-layer"></span>
        </div>
        <div class="weather-main">
          <span><component :is="weatherIcon" :size="32" /></span>
          <div>
            <small>{{ weatherLocationLabel }} · {{ dashboard.weather.label }}</small>
            <strong>{{ formatTemperature(dashboard.weather.temperature, settingsStore.settings?.temperature_unit) }}</strong>
          </div>
        </div>
        <p>{{ weatherMessage }}</p>
        <div class="weather-details">
          <span v-for="badge in weatherBadges" :key="badge.label">
            <component :is="badge.icon" :size="14" /> {{ badge.label }}
          </span>
        </div>
      </section>

      <RouterLink v-if="dashboard.active_run" to="/run/active" class="active-run-banner">
        <span><Play :size="22" fill="currentColor" /></span>
        <div>
          <small>진행 중인 러닝</small>
          <strong>{{ dashboard.active_run.course?.name ?? dashboard.active_run.custom_course?.name ?? '자유 러닝' }}</strong>
        </div>
        <ChevronRight :size="20" />
      </RouterLink>

      <section v-if="recommendedCourses.length" class="today-course">
        <div class="section-heading">
          <div><small>오늘의 추천 코스</small><h2>지금 달리기 좋은 Top 5</h2></div>
        </div>
        <div class="course-carousel" aria-label="추천 코스 Top 5">
          <button
            type="button"
            class="carousel-arrow carousel-arrow--prev"
            aria-label="이전 추천 코스"
            :disabled="recommendedCourses.length <= 1"
            @click="moveCarousel(-1)"
          >
            <ChevronLeft :size="20" />
          </button>

          <div class="course-window">
            <div
              class="course-track"
              :style="{ transform: `translateX(-${carouselIndex * 100}%)` }"
            >
              <article
                v-for="(item, index) in recommendedCourses"
                :key="item.course.slug"
                class="course-slide"
              >
                <RouterLink :to="`/courses/${item.course.slug}`" class="course-image">
                  <img :src="getCourseImageForCourse(item.course)" :alt="item.course.name" />
                  <span>TOP {{ index + 1 }}</span>
                  <div>
                    <h3>{{ item.course.name }}</h3>
                    <p>{{ item.course.distance_km }}km · {{ item.course.estimated_minutes }}분 · {{ item.course.difficulty_label }}</p>
                  </div>
                </RouterLink>
                <div class="course-reason">
                  <Sparkles :size="18" />
                  <p>{{ courseReason(item) }}</p>
                </div>
                <RouterLink class="course-start" :to="`/run/start?course=${item.course.slug}`">
                  <MapPinned :size="18" /> 이 코스로 러닝 시작
                </RouterLink>
              </article>
            </div>
          </div>

          <button
            type="button"
            class="carousel-arrow carousel-arrow--next"
            aria-label="다음 추천 코스"
            :disabled="recommendedCourses.length <= 1"
            @click="moveCarousel(1)"
          >
            <ChevronRight :size="20" />
          </button>
        </div>

        <div class="course-dots" aria-label="추천 코스 순서">
          <button
            v-for="(item, index) in recommendedCourses"
            :key="`dot-${item.course.slug}`"
            type="button"
            :class="{ active: index === carouselIndex }"
            :aria-label="`${index + 1}번째 추천 코스로 이동`"
            @click="goToSlide(index)"
          ></button>
        </div>
      </section>

      <div class="home-grid">
        <section class="mission-panel">
          <div class="section-heading">
            <div>
              <small>
                이번 주 미션<span v-if="missionStepText"> · {{ missionStepText }}</span>
              </small>
              <h2>{{ dashboard.mission.title }}</h2>
            </div>
            <Target :size="22" />
          </div>
          <div class="mission-progress"><i :style="{ width: `${missionProgress}%` }"></i></div>
          <p class="mission-count">
            <strong>{{ dashboard.mission.current }}</strong>
            / {{ dashboard.mission.target }}{{ missionUnit }} 완료
          </p>
          <p v-if="dashboard.mission.description" class="mission-description">
            {{ dashboard.mission.description }}
          </p>
          <p v-if="dashboard.mission.next_title" class="mission-next">
            다음 미션 {{ dashboard.mission.next_title }}
          </p>
          <div v-if="bonusMission" class="bonus-mission" :class="{ completed: bonusMission.completed }">
            <small>보너스 활동</small>
            <strong>{{ bonusMission.title }}</strong>
            <span>
              {{ bonusMission.completed ? '완료' : `${bonusMission.current}/${bonusMission.target}${bonusMission.unit}` }}
            </span>
          </div>
        </section>
      </div>
    </div>

    <div v-else class="home-state">
      {{ homeStore.errorMessage || '오늘의 러닝 정보를 준비하고 있어요.' }}
    </div>
    <AppBottomNav />
  </main>
</template>

<style scoped>
.home-page { display:flex; min-height:100vh; flex-direction:column; background:#f6f9fe; }
.home-content { flex:0 0 auto; padding:var(--page-top-padding) var(--content-padding) calc(var(--bottom-nav-height) + 18px); }
.home-header { display:flex; align-items:center; justify-content:space-between; gap:16px; }
.home-header small { color:var(--color-primary); font-size:9px; font-weight:800; }
.home-header h1 { margin:3px 0 2px; font-size:var(--title-font-size); }
.home-header p { margin:0; color:var(--color-muted); font-size:var(--caption-font-size); }
.header-actions { position:relative; display:flex; align-items:center; gap:8px; }
.notice-button { position:relative; display:grid; width:36px; height:36px; place-items:center; color:var(--color-primary); background:#fff; border:1px solid var(--color-border); border-radius:50%; box-shadow:0 8px 18px rgba(8,102,255,.1); }
.notice-button i { position:absolute; top:-4px; right:-4px; display:grid; min-width:15px; height:15px; padding:0 4px; place-items:center; color:#fff; background:#ef4444; border:2px solid #fff; border-radius:999px; font-size:8px; font-style:normal; font-weight:900; line-height:1; }
.notification-popover { position:absolute; z-index:24; top:46px; right:0; display:grid; width:min(278px,calc(100vw - 32px)); gap:10px; padding:14px; color:var(--color-navy); background:#fff; border:1px solid #dbe8f8; border-radius:18px; box-shadow:0 18px 38px rgba(15,23,42,.18); text-align:left; }
.notification-popover header { display:flex; align-items:center; justify-content:space-between; gap:8px; }
.notification-popover header strong { font-size:14px; }
.notification-popover header span { color:var(--color-muted); font-size:10px; font-weight:700; }
.notification-list { display:grid; gap:8px; max-height:260px; overflow:auto; }
.notification-list button { display:grid; gap:5px; width:100%; padding:11px; color:var(--color-navy); background:#f7faff; border:1px solid var(--color-border); border-radius:14px; text-align:left; }
.notification-list button.unread { background:#eef6ff; border-color:#bcd9ff; }
.notification-list button > span { display:flex; align-items:flex-start; justify-content:space-between; gap:8px; }
.notification-list strong { min-width:0; font-size:12px; line-height:1.3; }
.notification-list small { flex:0 0 auto; color:var(--color-muted); font-size:9px; font-weight:700; }
.notification-list p { margin:0; color:var(--color-muted); font-size:10px; line-height:1.45; }
.notification-empty { margin:0; padding:18px 8px; color:var(--color-muted); font-size:11px; text-align:center; }
.notification-popover a { justify-self:center; color:var(--color-primary); font-size:11px; font-weight:800; }
.profile-link { display:grid; width:46px; height:46px; overflow:hidden; flex:0 0 auto; place-items:center; color:#fff; font-weight:800; background:var(--color-primary); border-radius:50%; }
.profile-link img { width:100%; height:100%; object-fit:cover; }
.weather-band { position:relative; overflow:hidden; margin-top:var(--section-gap); padding:var(--card-padding); color:#fff; border-radius:var(--card-radius); box-shadow:0 18px 34px rgba(8,102,255,.24); isolation:isolate; }
.weather-band--sunny { background:linear-gradient(135deg,#1686f4 0%,#4ebbf7 50%,#ffd36d 100%); }
.weather-band--cloudy { background:linear-gradient(135deg,#2f6fb6 0%,#70b9ef 58%,#a9d9ff 100%); }
.weather-band--rainy { background:linear-gradient(135deg,#082c59 0%,#14538b 54%,#4b8fc3 100%); box-shadow:0 18px 34px rgba(8,42,89,.28); }
.weather-band--windy { background:linear-gradient(135deg,#1677df 0%,#39c1e7 48%,#8be6d0 100%); }
.weather-band--hot { background:linear-gradient(135deg,#1290f4 0%,#f7b45d 58%,#ff823e 100%); box-shadow:0 18px 34px rgba(244,121,45,.24); }
.weather-band--cold,.weather-band--snowy { color:#113457; background:linear-gradient(135deg,#eaf8ff 0%,#9ddaff 48%,#5ea6e7 100%); box-shadow:0 18px 34px rgba(68,154,218,.2); }
.weather-band--storm { background:linear-gradient(135deg,#071b40 0%,#17215f 55%,#4d2a91 100%); box-shadow:0 18px 34px rgba(16,24,69,.32); }
.weather-effect,.weather-effect span { position:absolute; inset:0; z-index:-1; pointer-events:none; }
.sun-layer::before { position:absolute; top:-46px; right:22px; width:154px; height:154px; content:''; background:radial-gradient(circle,rgba(255,255,255,.95) 0 14%,rgba(255,229,140,.65) 18%,rgba(255,218,105,.26) 38%,transparent 67%); border-radius:50%; animation:sun-glow 3.4s ease-in-out infinite; }
.sun-layer::after { position:absolute; inset:0; content:''; background:linear-gradient(115deg,transparent 0 48%,rgba(255,255,255,.28) 50%,transparent 53%); animation:sun-sweep 5s ease-in-out infinite; }
.cloud-layer::before,.cloud-layer::after { position:absolute; content:''; background:rgba(255,255,255,.22); filter:blur(.2px); border-radius:999px; animation:cloud-drift 8s ease-in-out infinite alternate; }
.cloud-layer::before { right:-18px; bottom:28px; width:180px; height:54px; box-shadow:-42px -18px 0 rgba(255,255,255,.16),26px -22px 0 rgba(255,255,255,.2); }
.cloud-layer::after { right:36px; top:32px; width:118px; height:36px; opacity:.55; animation-delay:-2s; }
.rain-layer { background-image:repeating-linear-gradient(115deg,rgba(255,255,255,.36) 0 1px,transparent 1px 14px); opacity:.42; animation:rain-move .75s linear infinite; }
.rain-layer::after { position:absolute; right:0; bottom:-28px; left:0; height:70px; content:''; background:linear-gradient(transparent,rgba(178,219,255,.28)); filter:blur(8px); }
.wind-layer::before,.wind-layer::after { position:absolute; right:-24px; width:190px; height:58px; content:''; border:1px solid rgba(255,255,255,.32); border-left:0; border-radius:999px; animation:wind-flow 2.8s ease-in-out infinite; }
.wind-layer::before { top:30px; }
.wind-layer::after { top:80px; right:24px; width:145px; opacity:.8; animation-delay:.55s; }
.wind-layer { background:linear-gradient(112deg,transparent 0 42%,rgba(255,255,255,.28) 48%,transparent 54%); animation:wind-sheen 2.6s ease-in-out infinite; }
.heat-layer::before { position:absolute; top:-58px; right:-12px; width:180px; height:180px; content:''; background:radial-gradient(circle,rgba(255,255,255,.98) 0 12%,rgba(255,226,119,.8) 18%,rgba(255,115,61,.34) 46%,transparent 68%); border-radius:50%; animation:heat-pulse 2.4s ease-in-out infinite; }
.heat-layer::after { position:absolute; inset:0; content:''; background:repeating-linear-gradient(90deg,rgba(255,255,255,.11) 0 1px,transparent 1px 18px); filter:blur(8px); opacity:.44; animation:heat-wave 2.2s ease-in-out infinite; }
.snow-layer { background-image:radial-gradient(circle,rgba(255,255,255,.85) 0 1.5px,transparent 2px),radial-gradient(circle,rgba(255,255,255,.65) 0 1px,transparent 1.5px); background-position:0 0,34px 24px; background-size:46px 46px,58px 58px; opacity:.74; animation:snow-fall 5s linear infinite; }
.snow-layer::after { position:absolute; inset:auto 0 0; height:34px; content:''; background:linear-gradient(transparent,rgba(255,255,255,.38)); }
.storm-layer::before { position:absolute; top:-12px; right:72px; width:72px; height:160px; content:''; background:linear-gradient(160deg,transparent 0 30%,rgba(255,255,255,.95) 31% 36%,transparent 37% 48%,rgba(198,166,255,.95) 49% 54%,transparent 55%); filter:drop-shadow(0 0 14px rgba(207,180,255,.9)); animation:lightning-flash 3.1s steps(1,end) infinite; }
.storm-layer::after { position:absolute; inset:0; content:''; background:radial-gradient(circle at 78% 18%,rgba(130,94,217,.44),transparent 32%),radial-gradient(circle at 62% 0,rgba(255,255,255,.16),transparent 25%); animation:storm-cloud 4s ease-in-out infinite alternate; }
.weather-main { display:flex; align-items:center; gap:11px; }
.weather-main > span { display:grid; width:52px; height:52px; place-items:center; background:rgba(255,255,255,.18); border:1px solid rgba(255,255,255,.16); border-radius:50%; box-shadow:inset 0 1px 0 rgba(255,255,255,.3); }
.weather-main div { display:grid; }
.weather-main small { font-size:9px; opacity:.86; }
.weather-main strong { font-size:30px; line-height:1.05; }
.weather-band > p { margin:12px 0; font-size:var(--body-font-size); font-weight:800; line-height:1.45; }
.weather-details { display:flex; flex-wrap:wrap; gap:8px; }
.weather-details span { display:flex; align-items:center; gap:4px; padding:6px 8px; background:rgba(255,255,255,.14); border-radius:999px; font-size:9px; backdrop-filter:blur(8px); }
.active-run-banner { display:grid; grid-template-columns:42px 1fr auto; align-items:center; gap:10px; margin-top:var(--page-gap); padding:var(--card-padding); background:#fff; border:1px solid var(--color-border); border-radius:var(--card-radius); }
.active-run-banner > span { display:grid; width:42px; height:42px; place-items:center; color:#fff; background:var(--color-primary); border-radius:50%; }
.active-run-banner div { display:grid; gap:2px; min-width:0; }
.active-run-banner small { color:var(--color-muted); font-size:9px; }
.active-run-banner strong { overflow:hidden; font-size:12px; text-overflow:ellipsis; white-space:nowrap; }
.today-course,.mission-panel { margin-top:var(--section-gap); }
.section-heading { display:flex; align-items:center; justify-content:space-between; gap:10px; }
.section-heading small { color:var(--color-primary); font-size:8px; font-weight:800; }
.section-heading h2 { margin:2px 0 0; font-size:var(--section-title-size); }
.section-heading a { display:flex; align-items:center; color:var(--color-muted); font-size:9px; }
.course-carousel { position:relative; margin-top:10px; }
.course-window { overflow:hidden; background:#fff; border:1px solid var(--color-border); border-radius:var(--card-radius); }
.course-track { display:flex; transition:transform 520ms cubic-bezier(.2,.82,.22,1); will-change:transform; }
.course-slide { flex:0 0 100%; min-width:0; overflow:hidden; background:#fff; }
.carousel-arrow { position:absolute; top:38%; z-index:5; display:grid; width:34px; height:34px; place-items:center; color:#10213d; background:rgba(255,255,255,.92); border:1px solid rgba(214,224,238,.9); border-radius:50%; box-shadow:0 8px 18px rgba(15,23,42,.12); transform:translateY(-50%); }
.carousel-arrow:disabled { opacity:.35; }
.carousel-arrow--prev { left:8px; }
.carousel-arrow--next { right:8px; }
.course-image { position:relative; display:block; aspect-ratio:16/8.7; overflow:hidden; color:#fff; }
.course-image img { width:100%; height:100%; object-fit:cover; }
.course-image::after { position:absolute; inset:35% 0 0; content:''; background:linear-gradient(transparent,rgba(4,20,43,.82)); }
.course-image > span { position:absolute; z-index:2; top:11px; left:11px; padding:5px 7px; background:var(--color-primary); border-radius:var(--radius-small); font-size:8px; font-weight:700; }
.course-image > div { position:absolute; z-index:2; right:13px; bottom:12px; left:13px; }
.course-image h3 { margin:0; font-size:20px; }
.course-image p { margin:4px 0 0; font-size:10px; }
.course-reason { display:grid; grid-template-columns:25px 1fr; align-items:center; gap:7px; padding:11px 13px; color:var(--color-primary); }
.course-reason p { margin:0; color:#52627b; font-size:9px; line-height:1.5; }
.course-start { display:flex; min-height:43px; align-items:center; justify-content:center; gap:6px; margin:0 13px 13px; color:#fff; background:var(--color-primary); border-radius:var(--radius-small); font-size:10px; font-weight:700; }
.course-dots { display:flex; align-items:center; justify-content:center; gap:6px; margin-top:10px; }
.course-dots button { width:6px; height:6px; padding:0; background:#c6d2e4; border-radius:999px; transition:width 220ms ease, background 220ms ease; }
.course-dots button.active { width:18px; background:var(--color-primary); }
.home-grid { display:grid; grid-template-columns:1fr; }
.mission-panel { padding:var(--card-padding); background:#fff; border:1px solid var(--color-border); border-radius:var(--card-radius); }
.mission-panel .section-heading svg { color:var(--color-primary); }
.mission-panel h2 { font-size:var(--section-title-size); }
.mission-progress { height:7px; margin-top:14px; overflow:hidden; background:#e6ecf4; border-radius:4px; }
.mission-progress i { display:block; height:100%; background:linear-gradient(90deg,var(--color-primary),#20d3e8); border-radius:4px; }
.mission-panel > p { margin:8px 0 0; color:var(--color-muted); font-size:9px; }
.mission-panel > p strong { color:var(--color-primary); font-size:12px; }
.mission-count { white-space:nowrap; }
.mission-description { line-height:1.45; }
.mission-next { overflow:hidden; color:#6e7f97 !important; text-overflow:ellipsis; white-space:nowrap; }
.bonus-mission { display:grid; grid-template-columns:1fr auto; align-items:center; gap:2px 8px; margin-top:10px; padding-top:10px; border-top:1px solid var(--color-border); }
.bonus-mission small { grid-column:1 / -1; color:#7b8da6; font-size:8px; font-weight:900; }
.bonus-mission strong { overflow:hidden; color:var(--color-navy); font-size:10px; text-overflow:ellipsis; white-space:nowrap; }
.bonus-mission span { padding:4px 6px; color:var(--color-primary); background:var(--color-primary-soft); border-radius:999px; font-size:8px; font-weight:900; white-space:nowrap; }
.bonus-mission.completed span { color:#fff; background:var(--color-success); }
.home-state { display:grid; min-height:calc(100vh - 72px); place-items:center; padding:24px; color:var(--color-muted); }
@keyframes sun-glow { 0%,100% { transform:scale(.94); opacity:.78; } 50% { transform:scale(1.06); opacity:1; } }
@keyframes sun-sweep { 0%,100% { transform:translateX(34px); opacity:.16; } 50% { transform:translateX(-22px); opacity:.36; } }
@keyframes cloud-drift { from { transform:translateX(16px); } to { transform:translateX(-22px); } }
@keyframes rain-move { from { transform:translateY(-14px); } to { transform:translateY(14px); } }
@keyframes wind-flow { 0% { transform:translateX(24px); opacity:.16; } 50% { opacity:.48; } 100% { transform:translateX(-38px); opacity:.1; } }
@keyframes wind-sheen { 0%,100% { background-position:60px 0; opacity:.24; } 50% { background-position:-40px 0; opacity:.48; } }
@keyframes heat-pulse { 0%,100% { transform:scale(.95); opacity:.75; } 50% { transform:scale(1.08); opacity:1; } }
@keyframes heat-wave { 0%,100% { transform:translateX(-8px) skewX(-4deg); } 50% { transform:translateX(9px) skewX(4deg); } }
@keyframes snow-fall { from { background-position:0 -46px,34px -34px; } to { background-position:0 46px,34px 82px; } }
@keyframes lightning-flash { 0%,72%,100% { opacity:0; } 73%,76% { opacity:1; } 77%,84% { opacity:.08; } 85%,87% { opacity:.9; } }
@keyframes storm-cloud { from { transform:translateX(10px); } to { transform:translateX(-16px); } }
@media (prefers-reduced-motion:reduce) { .weather-effect,.weather-effect span,.weather-effect span::before,.weather-effect span::after { animation:none; } }
</style>
