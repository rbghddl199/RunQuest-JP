<script setup>
import { computed } from 'vue'
import { ArrowLeft } from '@lucide/vue'

import AppBrand from '../common/AppBrand.vue'

const props = defineProps({
  showBack: {
    type: Boolean,
    default: true,
  },
  mode: {
    type: String,
    default: 'login',
  },
})

const heroCopy = computed(() => {
  if (props.mode === 'signup') {
    return {
      eyebrow: 'RUNQUEST START',
      title: '오늘부터 나만의 러닝 루틴을 만들어요.',
      description: '가볍게 질문을 마치면 성향에 맞는 코스와 미션을 바로 받을 수 있어요.',
    }
  }

  return {
    eyebrow: 'RUNQUEST CHECK-IN',
    title: '오늘의 러닝을 이어서 시작해요.',
    description: '기록, 추천 코스, 미션을 한 화면에서 확인하고 바로 달릴 수 있어요.',
  }
})
</script>

<template>
  <main class="mobile-shell auth-shell" :class="`auth-shell--${mode}`">
    <div class="auth-shell__visual">
      <div class="auth-shell__overlay"></div>
      <div class="auth-shell__track" aria-hidden="true"></div>

      <RouterLink
        v-if="showBack"
        class="auth-shell__back"
        to="/welcome"
        aria-label="시작 화면으로 돌아가기"
      >
        <ArrowLeft :size="25" />
      </RouterLink>

      <div class="auth-shell__brand">
        <AppBrand />
        <span>{{ heroCopy.eyebrow }}</span>
        <h1>{{ heroCopy.title }}</h1>
        <p>{{ heroCopy.description }}</p>
      </div>
    </div>

    <section class="auth-shell__panel">
      <slot />
    </section>
  </main>
</template>

<style scoped>
.auth-shell {
  position: relative;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  background:
    radial-gradient(circle at 50% 42%, rgba(8, 117, 255, 0.16), transparent 31%),
    radial-gradient(circle at 76% 18%, rgba(69, 244, 225, 0.12), transparent 24%),
    linear-gradient(160deg, #030b22 0%, #020b22 52%, #010619 100%);
}

.auth-shell__visual {
  position: relative;
  flex: 0 0 auto;
  min-height: 226px;
  overflow: hidden;
  padding: 20px var(--content-padding) 46px;
  background:
    radial-gradient(circle at 78% 12%, rgba(69, 244, 225, 0.16), transparent 26%),
    radial-gradient(circle at 22% 76%, rgba(8, 117, 255, 0.26), transparent 34%),
    linear-gradient(160deg, #030b22 0%, #020b22 56%, #010619 100%);
  isolation: isolate;
}

.auth-shell__visual::before,
.auth-shell__visual::after {
  position: absolute;
  z-index: -1;
  content: '';
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 50%;
}

.auth-shell__visual::before {
  top: -154px;
  right: -118px;
  width: 300px;
  height: 300px;
  box-shadow: 0 0 90px rgba(8, 117, 255, 0.24);
}

.auth-shell__visual::after {
  bottom: -178px;
  left: -156px;
  width: 360px;
  height: 360px;
  box-shadow: inset 0 0 80px rgba(69, 244, 225, 0.12);
}

.auth-shell__overlay {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(115deg, transparent 0 54%, rgba(255, 255, 255, 0.08) 54% 55%, transparent 55%),
    linear-gradient(180deg, transparent 58%, rgba(244, 249, 255, 0.96) 100%);
}

.auth-shell__track {
  position: absolute;
  right: -32px;
  bottom: 42px;
  width: 260px;
  height: 96px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-left: 0;
  border-radius: 999px;
  opacity: 0.7;
  transform: rotate(-15deg);
}

.auth-shell__track::before,
.auth-shell__track::after {
  position: absolute;
  right: 18px;
  left: 18px;
  height: 1px;
  content: '';
  background: rgba(255, 255, 255, 0.18);
}

.auth-shell__track::before {
  top: 32px;
}

.auth-shell__track::after {
  bottom: 32px;
}

.auth-shell__back,
.auth-shell__brand {
  position: relative;
  z-index: 1;
}

.auth-shell__back {
  display: grid;
  width: 38px;
  height: 38px;
  margin: -4px 0 8px -6px;
  place-items: center;
  color: #fff;
  background: rgba(255, 255, 255, 0.12);
  border-radius: 50%;
}

.auth-shell__brand {
  display: grid;
  gap: 7px;
}

.auth-shell__brand > span {
  width: fit-content;
  margin-top: 4px;
  padding: 5px 8px;
  color: #7dfff0;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 999px;
  font-size: 9px;
  font-weight: 900;
  letter-spacing: 0.4px;
}

.auth-shell__brand h1,
.auth-shell__brand p {
  margin: 0;
}

.auth-shell__brand h1 {
  max-width: none;
  color: #fff;
  font-size: 20px;
  line-height: 1.25;
  letter-spacing: 0;
  white-space: nowrap;
}

.auth-shell__brand p {
  max-width: none;
  color: rgba(227, 236, 250, 0.84);
  font-size: 10.5px;
  line-height: 1.5;
  white-space: nowrap;
}

.auth-shell__panel {
  position: relative;
  z-index: 2;
  width: 100%;
  flex: 1 0 auto;
  margin: -24px 0 0;
  padding: 18px 18px max(22px, env(safe-area-inset-bottom));
  background: rgba(255, 255, 255, 0.97);
  border: 0;
  border-bottom: 0;
  border-radius: 24px 24px 0 0;
  box-shadow: 0 -14px 34px rgba(35, 78, 140, 0.12);
}

.auth-shell--signup .auth-shell__visual {
  min-height: 210px;
  padding-bottom: 38px;
}

.auth-shell--signup .auth-shell__brand h1 {
  font-size: 18px;
}

.auth-shell--signup .auth-shell__brand p {
  display: none;
}

.auth-shell--signup .auth-shell__panel {
  margin-top: -20px;
  padding-top: 16px;
}

@media (max-width: 359px) {
  .auth-shell__panel {
    padding-inline: 16px;
  }
}

@media (max-height: 720px) {
  .auth-shell__visual {
    min-height: 196px;
    padding-top: 18px;
    padding-bottom: 32px;
  }

  .auth-shell--signup .auth-shell__visual {
    min-height: 180px;
  }

  .auth-shell__brand h1 {
    font-size: 18px;
  }

  .auth-shell__brand p {
    font-size: 10px;
  }
}
</style>
