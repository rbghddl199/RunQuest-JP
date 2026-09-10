<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import RunnerMark from '../components/common/RunnerMark.vue'

const ANIMATION_DURATION = 1400
const RING_RADIUS = 112
const RING_CIRCUMFERENCE = 2 * Math.PI * RING_RADIUS

const router = useRouter()
const progress = ref(0)
let animationFrame
let transitionTimer

const ringOffset = computed(
  () => RING_CIRCUMFERENCE * (1 - progress.value / 100),
)
const loaderStyle = computed(() => ({
  '--loader-angle': `${progress.value * 3.6}deg`,
  '--loader-progress': `${progress.value}%`,
}))

function moveToWelcome(delay = 90) {
  transitionTimer = window.setTimeout(
    () => router.replace({ name: 'welcome' }),
    delay,
  )
}

onMounted(() => {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (reduceMotion) {
    progress.value = 100
    moveToWelcome(220)
    return
  }

  const startedAt = performance.now()
  const animate = (now) => {
    const elapsed = Math.min(1, (now - startedAt) / ANIMATION_DURATION)
    progress.value = Math.round(elapsed * 100)

    if (elapsed < 1) {
      animationFrame = window.requestAnimationFrame(animate)
      return
    }
    moveToWelcome(180)
  }
  animationFrame = window.requestAnimationFrame(animate)
})

onBeforeUnmount(() => {
  window.cancelAnimationFrame(animationFrame)
  window.clearTimeout(transitionTimer)
})
</script>

<template>
  <main class="mobile-shell splash">
    <div class="splash__atmosphere" aria-hidden="true">
      <span></span>
      <span></span>
    </div>

    <section class="splash__content">
      <div class="splash__brand">
        <h1><span>Run</span><strong>Quest</strong></h1>
        <p>오늘의 퀘스트를 준비하고 있어요</p>
      </div>

      <div
        class="quest-loader"
        :style="loaderStyle"
        role="progressbar"
        aria-label="RunQuest 로딩 진행률"
        aria-valuemin="0"
        aria-valuemax="100"
        :aria-valuenow="progress"
      >
        <div class="quest-loader__halo" aria-hidden="true"></div>
        <div class="quest-loader__track" aria-hidden="true">
          <svg viewBox="0 0 260 260">
            <defs>
              <linearGradient
                id="splash-progress"
                gradientUnits="userSpaceOnUse"
                x1="35"
                y1="25"
                x2="225"
                y2="235"
              >
                <stop offset="0" stop-color="#4ff1e2" />
                <stop offset=".34" stop-color="#22c3f2" />
                <stop offset=".72" stop-color="#0b7bff" />
                <stop offset="1" stop-color="#0757de" />
              </linearGradient>
              <filter id="splash-glow" x="-40%" y="-40%" width="180%" height="180%">
                <feGaussianBlur stdDeviation="4.5" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>
            <circle class="quest-loader__rail-shadow" cx="130" cy="130" r="112" />
            <circle class="quest-loader__rail" cx="130" cy="130" r="112" />
            <circle
              class="quest-loader__progress"
              cx="130"
              cy="130"
              r="112"
              :stroke-dasharray="RING_CIRCUMFERENCE"
              :stroke-dashoffset="ringOffset"
            />
            <circle class="quest-loader__inner-dots" cx="130" cy="130" r="91" />
          </svg>
        </div>

        <div class="quest-loader__runner-orbit" aria-hidden="true">
          <span class="quest-loader__speed-line"></span>
          <span class="quest-loader__speed-line"></span>
          <span class="quest-loader__particle"></span>
          <span class="quest-loader__particle"></span>
          <RunnerMark class="quest-loader__runner" />
        </div>

        <div class="quest-loader__center">
          <strong>{{ progress }}<small>%</small></strong>
          <span>RUNNING TO YOUR<br />NEXT QUEST</span>
        </div>
      </div>

      <div class="splash__reflection" aria-hidden="true"></div>
    </section>
  </main>
</template>

<style scoped>
.splash {
  --splash-navy: #020b22;
  position: relative;
  display: grid;
  min-height: var(--app-height);
  overflow: hidden;
  place-items: center;
  color: #fff;
  background:
    radial-gradient(circle at 50% 46%, rgba(8, 72, 186, 0.24), transparent 34%),
    radial-gradient(ellipse at 50% 86%, rgba(0, 99, 255, 0.22), transparent 25%),
    linear-gradient(160deg, #030b22 0%, var(--splash-navy) 52%, #010619 100%);
  isolation: isolate;
}

.splash__atmosphere span {
  position: absolute;
  z-index: -1;
  width: 310px;
  height: 310px;
  border: 1px solid rgba(35, 121, 255, 0.12);
  border-radius: 50%;
}

.splash__atmosphere span:first-child {
  top: -190px;
  left: -170px;
  box-shadow: 0 0 80px rgba(19, 126, 255, 0.12);
}

.splash__atmosphere span:last-child {
  right: -210px;
  bottom: -170px;
  width: 390px;
  height: 390px;
  box-shadow: inset 0 0 80px rgba(19, 126, 255, 0.08);
}

.splash__content {
  position: relative;
  width: 100%;
  min-height: var(--app-height);
  animation: splash-enter 480ms ease-out both;
}

.splash__brand {
  position: absolute;
  top: clamp(112px, 15vh, 136px);
  left: 50%;
  display: grid;
  place-items: center;
  transform: translateX(-50%);
  white-space: nowrap;
}

.splash__brand h1 {
  margin: 0;
  font-size: clamp(52px, 15vw, 74px);
  font-style: italic;
  font-weight: 900;
  line-height: 0.9;
  letter-spacing: -5px;
  filter: drop-shadow(0 9px 22px rgba(0, 61, 184, 0.28));
  transform: skewX(-7deg);
}

.splash__brand h1 span {
  color: #fff;
}

.splash__brand h1 strong {
  color: transparent;
  background: linear-gradient(115deg, #42efe0 2%, #12aeea 42%, #0875ff 82%);
  background-clip: text;
  -webkit-background-clip: text;
}

.splash__brand p {
  margin: 26px 0 0;
  color: rgba(227, 234, 247, 0.78);
  font-size: clamp(15px, 4.1vw, 19px);
  font-weight: 600;
  letter-spacing: -0.5px;
}

.quest-loader {
  position: absolute;
  top: 57%;
  left: 50%;
  display: grid;
  width: min(94%, 340px);
  aspect-ratio: 1;
  place-items: center;
  transform: translate(-50%, -50%);
}

.quest-loader__halo,
.quest-loader__track {
  position: absolute;
  inset: 0;
}

.quest-loader__halo {
  border: 1px solid rgba(48, 137, 255, 0.22);
  border-radius: 50%;
  box-shadow:
    0 36px 66px rgba(0, 0, 0, 0.5),
    0 0 88px rgba(0, 98, 255, 0.24),
    inset 0 0 46px rgba(7, 112, 255, 0.1);
}

.quest-loader__track {
  inset: 5%;
  padding: 4px;
  background: linear-gradient(145deg, rgba(55, 128, 225, 0.24), rgba(0, 4, 15, 0.8));
  border: 1px solid rgba(73, 152, 255, 0.19);
  border-radius: 50%;
  box-shadow:
    inset 8px 10px 22px rgba(70, 143, 255, 0.09),
    inset -12px -16px 24px rgba(0, 0, 0, 0.72),
    0 10px 28px rgba(0, 0, 0, 0.48);
}

.quest-loader__track svg {
  width: 100%;
  height: 100%;
  overflow: visible;
  transform: rotate(-90deg);
}

.quest-loader__rail-shadow,
.quest-loader__rail,
.quest-loader__progress,
.quest-loader__inner-dots {
  fill: none;
}

.quest-loader__rail-shadow {
  stroke: #010611;
  stroke-width: 34;
  filter: drop-shadow(5px 7px 5px rgba(0, 0, 0, 0.72));
}

.quest-loader__rail {
  stroke: #11264f;
  stroke-width: 25;
  filter: drop-shadow(-2px -2px 2px rgba(83, 151, 255, 0.2));
}

.quest-loader__progress {
  stroke: url('#splash-progress');
  stroke-width: 25;
  stroke-linecap: round;
  filter: url('#splash-glow');
  transition: stroke-dashoffset 60ms linear;
}

.quest-loader__inner-dots {
  stroke: rgba(31, 128, 255, 0.57);
  stroke-width: 1.2;
  stroke-linecap: round;
  stroke-dasharray: 1 8;
}

.quest-loader__center {
  position: relative;
  z-index: 2;
  display: grid;
  justify-items: center;
  place-items: center;
  text-align: center;
}

.quest-loader__runner-orbit {
  position: absolute;
  inset: 0;
  z-index: 3;
  border-radius: 50%;
  transform: rotate(var(--loader-angle));
  transition: transform 60ms linear;
  will-change: transform;
}

.quest-loader__runner {
  position: absolute;
  top: -2px;
  left: 50%;
  z-index: 2;
  width: 52px;
  height: 52px;
  box-shadow:
    0 0 0 3px rgba(8, 117, 255, 0.14),
    0 0 30px rgba(69, 244, 225, 0.62);
  animation: runner-stride 210ms ease-in-out infinite alternate;
  transform: translateX(-50%) rotate(calc(var(--loader-angle) * -1));
}

.quest-loader__speed-line,
.quest-loader__particle {
  position: absolute;
  display: block;
  pointer-events: none;
}

.quest-loader__speed-line {
  top: 50%;
  left: 50%;
  width: 68px;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(69, 244, 225, 0.76));
  border-radius: 999px;
  transform-origin: -84px 50%;
}

.quest-loader__speed-line:nth-child(1) {
  transform: rotate(222deg) translateX(96px);
}

.quest-loader__speed-line:nth-child(2) {
  opacity: 0.72;
  transform: rotate(238deg) translateX(76px);
}

.quest-loader__particle {
  width: 6px;
  height: 6px;
  background: #45f4e1;
  border-radius: 50%;
  box-shadow: 0 0 14px rgba(69, 244, 225, 0.84);
}

.quest-loader__particle:nth-child(3) {
  top: 24%;
  left: 22%;
}

.quest-loader__particle:nth-child(4) {
  right: 18%;
  bottom: 28%;
  width: 4px;
  height: 4px;
}

.quest-loader__center strong {
  position: relative;
  display: inline-block;
  color: #fff;
  font-size: clamp(48px, 15vw, 68px);
  font-weight: 700;
  line-height: 0.95;
  letter-spacing: -2px;
  text-shadow: 0 8px 22px rgba(0, 24, 75, 0.68);
}

.quest-loader__center strong small {
  position: absolute;
  bottom: 0.08em;
  left: calc(100% + 8px);
  font-size: 0.42em;
  font-weight: 500;
  letter-spacing: -1px;
}

.quest-loader__center span {
  margin-top: 12px;
  color: #2b93ff;
  font-size: clamp(10px, 2.8vw, 13px);
  font-weight: 700;
  line-height: 1.55;
  letter-spacing: 2.1px;
}

.splash__reflection {
  position: absolute;
  top: 83%;
  left: 50%;
  width: min(62vw, 280px);
  height: 38px;
  background: radial-gradient(ellipse, rgba(0, 117, 255, 0.72), rgba(0, 74, 220, 0.16) 42%, transparent 72%);
  filter: blur(10px);
  border-radius: 50%;
  transform: translateX(-50%) scaleY(0.34);
}

@keyframes splash-enter {
  from {
    opacity: 0;
    transform: translateY(10px) scale(0.985);
  }
}

@keyframes runner-stride {
  from {
    translate: 0 -1px;
  }
  to {
    translate: 0 2px;
  }
}

@media (max-height: 700px) {
  .splash__brand {
    top: 48px;
  }

  .quest-loader {
    top: 58%;
    width: min(88%, 318px);
  }

  .splash__brand h1 {
    font-size: 46px;
    letter-spacing: -3px;
  }

  .splash__brand p {
    margin-top: 16px;
    font-size: 13px;
  }

  .quest-loader__runner {
    width: 54px;
    height: 54px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .splash__content,
  .quest-loader__runner-orbit,
  .quest-loader__runner {
    animation: none;
  }
}
</style>
