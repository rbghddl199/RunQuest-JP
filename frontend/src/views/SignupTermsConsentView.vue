<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ArrowLeft, Bell, ChevronRight, FileText } from '@lucide/vue'
import { useRouter } from 'vue-router'

import BaseButton from '../components/common/BaseButton.vue'
import { useAuthStore } from '../stores/auth'

const PENDING_SIGNUP_KEY = 'runquest_pending_signup'

const router = useRouter()
const authStore = useAuthStore()
const submitted = ref(false)
const pendingSignup = ref(null)

const agreements = reactive({
  service: false,
  privacyCollection: false,
  location: false,
  privacyPolicy: false,
  notification: false,
})

const requiredKeys = ['service', 'privacyCollection', 'location', 'privacyPolicy']
const requiredAgreed = computed(() => requiredKeys.every((key) => agreements[key]))
const allAgreed = computed({
  get: () => Object.values(agreements).every(Boolean),
  set: (value) => {
    Object.keys(agreements).forEach((key) => {
      agreements[key] = value
    })
  },
})

const terms = [
  {
    key: 'service',
    required: true,
    title: '서비스 이용약관',
    description: 'RunQuest 계정과 러닝 서비스 이용 규칙에 동의합니다.',
    section: 'service',
  },
  {
    key: 'privacyCollection',
    required: true,
    title: '개인정보 수집·이용 동의',
    description: '회원 관리와 맞춤 추천을 위한 개인정보 수집·이용에 동의합니다.',
    section: 'privacy-collection',
  },
  {
    key: 'location',
    required: true,
    title: '위치정보 수집·이용 동의',
    description: '코스 추천과 러닝 기록 측정을 위한 위치정보 이용에 동의합니다.',
    section: 'location',
  },
  {
    key: 'privacyPolicy',
    required: true,
    title: '개인정보 처리방침 확인',
    description: '보유 기간, 삭제, 외부 API 이용 기준을 확인했습니다.',
    section: 'privacy-policy',
  },
  {
    key: 'notification',
    required: false,
    title: '혜택 및 활동 알림 수신 동의',
    description: '배지, 추천 코스, 커뮤니티 반응 등 선택 알림을 받습니다.',
    section: 'notification',
  },
]

onMounted(() => {
  const stored = sessionStorage.getItem(PENDING_SIGNUP_KEY)
  if (!stored) return

  try {
    pendingSignup.value = JSON.parse(stored)
  } catch {
    sessionStorage.removeItem(PENDING_SIGNUP_KEY)
  }
})

async function completeSignup() {
  submitted.value = true
  authStore.errorMessage = ''

  if (!pendingSignup.value) {
    await router.replace({ name: 'signup' })
    return
  }

  if (!requiredAgreed.value) return

  try {
    await authStore.signup({
      ...pendingSignup.value,
      terms_agreed: true,
    })
    sessionStorage.removeItem(PENDING_SIGNUP_KEY)
    await router.push('/survey')
  } catch {
    // Store exposes the API error message in the form.
  }
}
</script>

<template>
  <main class="mobile-shell terms-consent-page">
    <header>
      <button type="button" class="back-button" aria-label="이전 화면" @click="router.back()">
        <ArrowLeft :size="24" />
      </button>
      <h1>약관 동의</h1>
      <span></span>
    </header>

    <section class="consent-summary">
      <span><FileText :size="20" /></span>
      <div>
        <strong>필수 약관 동의</strong>
        <small>RunQuest 이용을 위해 아래 항목을 확인해 주세요.</small>
      </div>
    </section>

    <form class="consent-form" novalidate @submit.prevent="completeSignup">
      <label class="agree-all">
        <input v-model="allAgreed" type="checkbox" />
        <span>전체 동의</span>
      </label>

      <section class="terms-check-list">
        <div v-for="term in terms" :key="term.key" class="terms-check-row">
          <label>
            <input v-model="agreements[term.key]" type="checkbox" />
            <span>
              <strong>
                <em>{{ term.required ? '필수' : '선택' }}</em>
                {{ term.title }}
              </strong>
              <small>{{ term.description }}</small>
            </span>
          </label>

          <RouterLink
            class="terms-detail-link"
            :to="{ name: 'signup-terms', query: { section: term.section } }"
            :aria-label="`${term.title} 보기`"
          >
            보기
            <ChevronRight :size="16" />
          </RouterLink>
        </div>
      </section>

      <p class="terms-note">
        필수 약관에 동의하지 않으면 RunQuest 회원가입을 완료할 수 없습니다.
        선택 알림은 가입 후 설정에서 언제든 변경할 수 있습니다.
      </p>

      <p v-if="submitted && !requiredAgreed" class="inline-error">
        필수 약관에 모두 동의해 주세요.
      </p>
      <p v-if="!pendingSignup" class="inline-error">
        계정 정보가 없습니다. 회원가입 정보를 먼저 입력해 주세요.
      </p>
      <p v-if="authStore.errorMessage" class="form-error" role="alert">
        {{ authStore.errorMessage }}
      </p>

      <BaseButton native-type="submit" :disabled="authStore.isLoading || !requiredAgreed || !pendingSignup">
        {{ authStore.isLoading ? '가입 중...' : '동의하고 가입하기' }}
      </BaseButton>

      <button type="button" class="text-action" @click="router.push({ name: 'signup' })">
        계정 정보 수정하기
      </button>
    </form>
  </main>
</template>

<style scoped>
.terms-consent-page { background: var(--color-background); }
.terms-consent-page header { display:grid; height:64px; grid-template-columns:44px 1fr 44px; align-items:center; padding:0 14px; background:var(--color-surface); border-bottom:1px solid var(--color-border); }
.back-button { display:grid; width:40px; height:40px; place-items:center; color:var(--color-navy); background:transparent; }
header h1 { margin:0; font-size:18px; text-align:center; }
.consent-summary { display:flex; align-items:center; gap:10px; padding:18px var(--content-padding); background:var(--color-primary-soft); }
.consent-summary > span { display:grid; width:40px; height:40px; place-items:center; color:#fff; background:var(--color-primary); border-radius:50%; }
.consent-summary div { display:grid; gap:3px; }
.consent-summary strong { color:var(--color-navy); font-size:13px; }
.consent-summary small { color:var(--color-muted); font-size:9px; line-height:1.45; }
.consent-form { display:grid; gap:12px; padding:16px var(--content-padding) 28px; background:var(--color-surface); }
.agree-all { display:flex; align-items:center; gap:10px; padding:14px; color:var(--color-navy); background:var(--color-primary-soft); border:1px solid color-mix(in srgb, var(--color-primary) 18%, var(--color-border)); border-radius:var(--radius-medium); cursor:pointer; }
.agree-all input,
.terms-check-row input { width:18px; height:18px; flex:0 0 auto; margin:0; accent-color:var(--color-primary); }
.agree-all span { display:flex; align-items:center; gap:6px; font-size:13px; font-weight:900; }
.terms-check-list { display:grid; background:var(--color-surface); border-top:1px solid var(--color-border); }
.terms-check-row { display:grid; grid-template-columns:minmax(0, 1fr) auto; align-items:center; gap:10px; padding:13px 0; border-bottom:1px solid var(--color-border); }
.terms-check-row label { display:flex; min-width:0; align-items:flex-start; gap:10px; cursor:pointer; }
.terms-check-row label > span { display:grid; min-width:0; gap:4px; }
.terms-check-row strong { color:var(--color-navy); font-size:12px; line-height:1.35; }
.terms-check-row em { display:inline-flex; margin-right:4px; color:var(--color-primary); font-style:normal; font-weight:900; text-decoration:underline; text-underline-offset:3px; }
.terms-check-row small { color:var(--color-muted); font-size:9px; line-height:1.45; }
.terms-detail-link { display:inline-flex; align-items:center; gap:1px; padding:7px 0 7px 8px; color:var(--color-primary); font-size:11px; font-weight:900; text-decoration:underline; text-underline-offset:3px; }
.terms-note { margin:0; color:var(--color-muted); font-size:10px; line-height:1.55; }
.inline-error { margin:-4px 0 0; color:#d73c4e; font-size:12px; }
.form-error { margin:-4px 0 0; padding:10px 12px; color:#b52e3e; font-size:12px; line-height:1.45; background:#fff0f2; border-radius:var(--radius-small); }
.text-action { justify-self:center; padding:8px; color:var(--color-primary); font-size:12px; font-weight:800; background:transparent; }
</style>
