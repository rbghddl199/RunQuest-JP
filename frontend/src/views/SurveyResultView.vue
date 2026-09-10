<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { Check, MapPinned, Route, Sparkles } from '@lucide/vue'
import { useRouter } from 'vue-router'

import BaseButton from '../components/common/BaseButton.vue'
import { useSurveyStore } from '../stores/survey'

const router = useRouter()
const surveyStore = useSurveyStore()
const progress = ref(0)
let frame = null
let homeTimer = null

const targetDistance = computed(() => (
  surveyStore.result?.score_profile?.target_distance_km ?? '-'
))

onMounted(() => {
  if (!surveyStore.result) {
    surveyStore.loadSavedResponse()
  }

  const startedAt = performance.now()
  const duration = 2200
  const tick = (now) => {
    progress.value = Math.min(100, Math.round(((now - startedAt) / duration) * 100))
    if (progress.value < 100) {
      frame = window.requestAnimationFrame(tick)
    }
  }

  frame = window.requestAnimationFrame(tick)
  homeTimer = window.setTimeout(() => router.replace('/home'), 3400)
})

onUnmounted(() => {
  if (frame) window.cancelAnimationFrame(frame)
  if (homeTimer) window.clearTimeout(homeTimer)
})
</script>

<template>
  <main class="mobile-shell survey-result">
    <div class="result-atmosphere" aria-hidden="true">
      <span></span>
      <span></span>
      <span></span>
    </div>

    <section class="result-panel" aria-live="polite">
      <div class="recommendation-core" :style="{ '--progress': `${progress}%` }" aria-hidden="true">
        <div class="wave-ring wave-ring--outer"></div>
        <div class="wave-ring wave-ring--middle"></div>
        <div class="wave-ring wave-ring--inner"></div>
        <div class="flow-line flow-line--one"></div>
        <div class="flow-line flow-line--two"></div>
        <div class="core-orb">
          <Sparkles :size="42" />
        </div>
      </div>

      <div class="result-copy">
        <h1>답변을 추천 코스로<br />이어가고 있어요</h1>
        <p>
          러닝 성향과 선호 거리를 조합해 오늘 가장 잘 맞는 코스를 준비합니다.
        </p>
      </div>

      <div class="analysis-meter" :style="{ '--progress': `${progress}%` }" aria-label="추천 반영 진행률">
        <span></span>
      </div>

      <div class="result-steps">
        <article :class="{ done: progress >= 34 }">
          <Check :size="18" />
          <span>러닝 성향 분석</span>
        </article>
        <article :class="{ done: progress >= 68 }">
          <Route :size="18" />
          <span>코스 후보 연결</span>
        </article>
        <article :class="{ done: progress >= 96 }">
          <MapPinned :size="18" />
          <span>{{ targetDistance }}km 기준 반영</span>
        </article>
      </div>

      <BaseButton to="/home">추천 확인하기</BaseButton>
    </section>
  </main>
</template>

<style scoped>
.survey-result {
  position: relative;
  display: grid;
  min-height: var(--app-height);
  overflow: hidden;
  padding: 38px var(--content-padding);
  place-items: center;
  color: #fff;
  background:
    radial-gradient(circle at 50% 44%, rgba(8, 72, 186, 0.24), transparent 34%),
    radial-gradient(ellipse at 50% 86%, rgba(0, 99, 255, 0.22), transparent 25%),
    linear-gradient(160deg, #030b22 0%, #020b22 52%, #010619 100%);
  isolation: isolate;
}

.result-atmosphere span {
  position: absolute;
  z-index: -1;
  border: 1px solid rgba(35, 121, 255, 0.12);
  border-radius: 50%;
}

.result-atmosphere span:first-child {
  top: -190px;
  left: -170px;
  width: 320px;
  height: 320px;
  box-shadow: 0 0 80px rgba(19, 126, 255, 0.12);
}

.result-atmosphere span:nth-child(2) {
  right: -210px;
  bottom: -170px;
  width: 390px;
  height: 390px;
  box-shadow: inset 0 0 80px rgba(19, 126, 255, 0.08);
}

.result-atmosphere span:last-child {
  top: 47%;
  left: 50%;
  width: 270px;
  height: 270px;
  border-color: rgba(69, 244, 225, 0.1);
  transform: translate(-50%, -50%);
}

.result-panel {
  position: relative;
  display: grid;
  width: 100%;
  justify-items: center;
  text-align: center;
  transform: translateY(-24px);
}

.recommendation-core {
  position: relative;
  display: grid;
  width: min(82vw, 286px);
  aspect-ratio: 1;
  margin-bottom: 28px;
  place-items: center;
  transform: translateZ(0);
}

.wave-ring,
.flow-line {
  position: absolute;
  pointer-events: none;
}

.wave-ring {
  border: 1px solid rgba(75, 151, 255, 0.22);
  border-radius: 50%;
  box-shadow:
    inset 0 0 34px rgba(8, 117, 255, 0.1),
    0 0 46px rgba(0, 98, 255, 0.12);
}

.wave-ring--outer {
  inset: 0;
  animation: wave-pulse 2.7s ease-in-out infinite;
}

.wave-ring--middle {
  inset: 15%;
  border-style: dashed;
  border-color: rgba(69, 244, 225, 0.22);
  animation: wave-spin 6s linear infinite;
}

.wave-ring--inner {
  inset: 30%;
  background:
    radial-gradient(circle, rgba(69, 244, 225, 0.12), transparent 62%),
    rgba(4, 16, 45, 0.72);
  border-color: rgba(80, 167, 255, 0.32);
  animation: wave-breathe 1.8s ease-in-out infinite;
}

.flow-line {
  width: 178px;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(79, 241, 226, 0.86), rgba(11, 123, 255, 0.38), transparent);
  border-radius: 999px;
  filter: drop-shadow(0 0 9px rgba(69, 244, 225, 0.58));
  opacity: 0.78;
}

.flow-line--one {
  top: 34%;
  left: -16%;
  transform: rotate(18deg);
  animation: flow-slide 2.2s ease-in-out infinite;
}

.flow-line--two {
  right: -16%;
  bottom: 30%;
  transform: rotate(198deg);
  animation: flow-slide 2.2s 0.55s ease-in-out infinite;
}

.core-orb {
  position: relative;
  z-index: 1;
  display: grid;
  width: 96px;
  height: 96px;
  place-items: center;
  color: #071222;
  background: linear-gradient(145deg, #4ff1e2 0%, #22c3f2 40%, #0b7bff 100%);
  border-radius: 50%;
  box-shadow:
    0 0 0 12px rgba(8, 117, 255, 0.08),
    0 0 42px rgba(69, 244, 225, 0.32),
    0 28px 56px rgba(0, 0, 0, 0.34);
  transform: scale(calc(0.96 + (var(--progress) / 100) * 0.04));
}

.result-copy {
  display: grid;
  justify-items: center;
}

.result-copy h1,
.result-copy p {
  margin: 0;
}

.result-copy h1 {
  color: #fff;
  font-size: 29px;
  line-height: 1.28;
  letter-spacing: 0;
  text-shadow: 0 10px 28px rgba(0, 24, 75, 0.58);
}

.result-copy p {
  max-width: 292px;
  margin-top: 14px;
  color: rgba(226, 242, 255, 0.78);
  font-size: 13px;
  line-height: 1.65;
}

.analysis-meter {
  width: 100%;
  height: 12px;
  margin-top: 28px;
  padding: 2px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(109, 154, 220, 0.24);
  border-radius: 999px;
  box-shadow: inset 0 0 18px rgba(0, 0, 0, 0.22);
}

.analysis-meter span {
  display: block;
  width: var(--progress);
  height: 100%;
  background: linear-gradient(90deg, #4ff1e2 0%, #22c3f2 34%, #0b7bff 72%, #0757de 100%);
  border-radius: inherit;
  box-shadow: 0 0 18px rgba(69, 244, 225, 0.32);
  transition: width 120ms linear;
}

.result-steps {
  display: grid;
  width: 100%;
  gap: 9px;
  margin: 18px 0 24px;
}

.result-steps article {
  display: grid;
  min-height: 48px;
  grid-template-columns: 34px 1fr;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  color: rgba(226, 242, 255, 0.64);
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  text-align: left;
  backdrop-filter: blur(10px);
  transition:
    color 160ms ease,
    border-color 160ms ease,
    background 160ms ease;
}

.result-steps svg {
  justify-self: center;
}

.result-steps .done {
  color: #fff;
  background: rgba(11, 123, 255, 0.16);
  border-color: rgba(69, 244, 225, 0.34);
}

.result-panel :deep(.base-button) {
  min-height: 52px;
  color: #fff;
  background: linear-gradient(135deg, #0b6cff 0%, #0757de 100%);
  border: 1px solid rgba(117, 170, 255, 0.42);
  border-radius: 16px;
  box-shadow: 0 16px 30px rgba(8, 73, 190, 0.3);
}

@keyframes wave-pulse {
  50% {
    border-color: rgba(69, 244, 225, 0.2);
    box-shadow:
      inset 0 0 44px rgba(8, 117, 255, 0.14),
      0 0 62px rgba(0, 98, 255, 0.18);
    transform: scale(1.035);
  }
}

@keyframes wave-spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes wave-breathe {
  50% {
    transform: scale(1.08);
  }
}

@keyframes flow-slide {
  0%,
  100% {
    opacity: 0.3;
    translate: -18px 0;
  }

  50% {
    opacity: 1;
    translate: 18px 0;
  }
}

@media (max-height: 720px) {
  .survey-result {
    padding-block: 24px;
  }

  .recommendation-core {
    width: min(70vw, 230px);
    margin-bottom: 18px;
  }

  .core-orb {
    width: 78px;
    height: 78px;
  }

  .result-copy h1 {
    font-size: 24px;
  }

  .result-copy p {
    margin-top: 10px;
    font-size: 12px;
  }

  .analysis-meter {
    margin-top: 20px;
  }

  .result-panel {
    transform: translateY(-14px);
  }
}

@media (prefers-reduced-motion: reduce) {
  .wave-ring,
  .flow-line,
  .core-orb {
    animation: none;
  }
}
</style>
