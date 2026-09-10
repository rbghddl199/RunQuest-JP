<script setup>
import { computed } from 'vue'
import { ArrowLeft, Bell, Database, FileText, MapPin, ShieldCheck } from '@lucide/vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const sectionIds = ['service', 'privacy-collection', 'location', 'privacy-policy', 'notification']
const selectedSection = computed(() => (
  sectionIds.includes(route.query.section)
    ? route.query.section
    : 'service'
))

const sections = [
  {
    id: 'service',
    icon: ShieldCheck,
    title: '서비스 이용약관',
    summary: 'RunQuest 계정 생성과 맞춤 러닝 서비스 이용을 위한 필수 약관입니다.',
    items: [
      '회원은 정확한 계정 정보를 제공하고 본인의 계정을 안전하게 관리해야 합니다.',
      'RunQuest는 설문, 러닝 기록, 코스 저장 내역을 바탕으로 개인화된 러닝 경험을 제공합니다.',
      '커뮤니티에서 타인의 권리를 침해하거나 허위 기록을 등록하는 행위는 제한될 수 있습니다.',
      '약관에 동의하지 않으면 회원가입과 로그인 기반 기능을 이용할 수 없습니다.',
    ],
  },
  {
    id: 'privacy-collection',
    icon: Database,
    title: '개인정보 수집·이용 동의',
    summary: '회원 관리와 맞춤 추천을 위한 개인정보 수집·이용 동의입니다.',
    items: [
      '이메일, 닉네임, 비밀번호, 설문 응답, 러닝 기록, 저장 코스, 게시글·댓글 정보를 수집할 수 있습니다.',
      '수집한 정보는 계정 관리, 코스 추천, 러닝 기록 저장, 커뮤니티, 고객 지원에 사용됩니다.',
      '개인정보는 회원 탈퇴 시까지 보관하며, 법령상 보관이 필요한 정보는 해당 기간 동안 별도 보관될 수 있습니다.',
      '개인정보 수집·이용에 동의하지 않으면 RunQuest 회원가입을 완료할 수 없습니다.',
    ],
  },
  {
    id: 'location',
    icon: MapPin,
    title: '위치정보 수집·이용 동의',
    summary: '현재 위치 기반 코스 추천과 러닝 기록 측정을 위한 필수 위치 정보 동의입니다.',
    items: [
      '러닝 시작, 코스 추천, 주변 코스 탐색 시 현재 위치 또는 경로 정보가 사용될 수 있습니다.',
      '위치 정보는 거리, 페이스, 이동 경로, 맞춤 추천 결과를 계산하는 데 활용됩니다.',
      '위치 권한은 브라우저 또는 기기 설정에서 언제든 변경할 수 있습니다.',
      '위치정보 수집·이용에 동의하지 않으면 RunQuest의 핵심 러닝 기능을 이용할 수 없습니다.',
    ],
  },
  {
    id: 'privacy-policy',
    icon: FileText,
    title: '개인정보 처리방침',
    summary: '개인정보 보관, 삭제, 외부 서비스 이용 기준을 안내합니다.',
    items: [
      '사용자는 마이페이지 또는 고객 지원을 통해 개인정보 열람, 정정, 삭제, 처리 정지를 요청할 수 있습니다.',
      '지도, AI 추천, 서버 운영 등 서비스 제공을 위해 필요한 외부 API 또는 처리 위탁이 발생할 수 있습니다.',
      '보안, 장애 대응, 부정 이용 방지를 위해 접속 기록과 서비스 이용 기록이 일정 기간 보관될 수 있습니다.',
      '처리방침은 서비스 변경 또는 법령 개정에 따라 변경될 수 있으며, 중요한 변경은 사전에 안내합니다.',
    ],
  },
  {
    id: 'notification',
    icon: Bell,
    title: '혜택 및 활동 알림 수신 동의',
    summary: 'RunQuest 활동 소식을 받을지 선택하는 선택 동의입니다.',
    items: [
      '배지 획득, 추천 코스, 출석, 커뮤니티 반응 등 활동성 알림을 받을 수 있습니다.',
      '계정 보안, 서비스 운영, 중요 공지 등 필수 알림은 선택 동의와 무관하게 발송될 수 있습니다.',
      '알림 수신 동의는 가입 후 설정 화면에서 언제든 변경할 수 있습니다.',
      '선택 알림에 동의하지 않아도 RunQuest 회원가입과 기본 서비스 이용에는 제한이 없습니다.',
    ],
  },
]

const selectedTerm = computed(() => (
  sections.find((section) => section.id === selectedSection.value) ?? sections[0]
))
</script>

<template>
  <main class="mobile-shell terms-page">
    <header>
      <button type="button" class="back-button" aria-label="이전 화면" @click="router.back()">
        <ArrowLeft :size="24" />
      </button>
      <h1>약관 안내</h1>
      <span></span>
    </header>

    <section class="terms-summary">
      <span><FileText :size="20" /></span>
      <div>
        <strong>{{ selectedTerm.title }}</strong>
        <small>{{ selectedTerm.summary }}</small>
      </div>
    </section>

    <section class="terms-list">
      <article class="terms-card is-selected">
        <div class="terms-card__title">
          <span><component :is="selectedTerm.icon" :size="20" /></span>
          <div>
            <strong>{{ selectedTerm.title }}</strong>
            <p>{{ selectedTerm.summary }}</p>
          </div>
        </div>

        <ul>
          <li v-for="item in selectedTerm.items" :key="item">{{ item }}</li>
        </ul>
      </article>
    </section>
  </main>
</template>

<style scoped>
.terms-page { background: var(--color-background); }
.terms-page header { display:grid; height:64px; grid-template-columns:44px 1fr 44px; align-items:center; padding:0 14px; background:var(--color-surface); border-bottom:1px solid var(--color-border); }
.back-button { display:grid; width:40px; height:40px; place-items:center; color:var(--color-navy); background:transparent; }
header h1 { margin:0; font-size:18px; text-align:center; }
.terms-summary { display:flex; align-items:center; gap:10px; padding:18px var(--content-padding); background:var(--color-primary-soft); }
.terms-summary > span { display:grid; width:40px; height:40px; place-items:center; color:#fff; background:var(--color-primary); border-radius:50%; }
.terms-summary div { display:grid; gap:3px; }
.terms-summary strong { color:var(--color-navy); font-size:13px; }
.terms-summary small { color:var(--color-muted); font-size:9px; line-height:1.45; }
.terms-list { display:grid; gap:12px; padding:16px var(--content-padding) 30px; background:var(--color-surface); }
.terms-card { display:grid; gap:12px; padding:16px 0; border-bottom:1px solid var(--color-border); }
.terms-card.is-selected { padding-inline:12px; background:color-mix(in srgb, var(--color-primary-soft) 42%, var(--color-surface)); border:1px solid color-mix(in srgb, var(--color-primary) 18%, var(--color-border)); border-radius:var(--radius-medium); }
.terms-card__title { display:grid; grid-template-columns:42px 1fr; gap:10px; align-items:start; }
.terms-card__title > span { display:grid; width:40px; height:40px; place-items:center; color:var(--color-primary); background:var(--color-primary-soft); border-radius:50%; }
.terms-card__title div { display:grid; gap:4px; }
.terms-card strong { color:var(--color-navy); font-size:13px; }
.terms-card p { margin:0; color:var(--color-muted); font-size:10px; line-height:1.5; }
.terms-card ul { display:grid; gap:8px; margin:0; padding-left:18px; }
.terms-card li { color:var(--color-text); font-size:11px; line-height:1.55; }
</style>
