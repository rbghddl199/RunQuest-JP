<script setup>
import BaseButton from '../components/common/BaseButton.vue'
import RunnerMark from '../components/common/RunnerMark.vue'
</script>

<template>
  <main class="mobile-shell welcome">
    <div class="welcome__atmosphere" aria-hidden="true">
      <span></span>
      <span></span>
      <span></span>
    </div>

    <section class="welcome__content" aria-labelledby="welcome-title">
      <div class="welcome__brand">
        <div class="welcome__brand-mark">
          <RunnerMark class="welcome__runner" />
        </div>
        <h1 id="welcome-title">RunQuest</h1>
        <p>오늘의 러닝을 퀘스트로 시작해요</p>
      </div>

      <div class="welcome__pulse" aria-hidden="true">
        <span></span>
        <span></span>
      </div>

      <nav class="welcome__actions" aria-label="시작 메뉴">
        <BaseButton to="/login">로그인</BaseButton>
        <BaseButton to="/signup" variant="outline">회원가입</BaseButton>
      </nav>
    </section>
  </main>
</template>

<style scoped>
.welcome {
  --welcome-navy: #020b22;
  --welcome-blue: #0875ff;
  position: relative;
  display: grid;
  min-height: var(--app-height);
  overflow: hidden;
  color: #fff;
  background:
    radial-gradient(circle at 50% 42%, rgba(8, 117, 255, 0.22), transparent 31%),
    radial-gradient(circle at 76% 18%, rgba(69, 244, 225, 0.16), transparent 24%),
    radial-gradient(ellipse at 50% 88%, rgba(0, 99, 255, 0.18), transparent 24%),
    linear-gradient(160deg, #030b22 0%, var(--welcome-navy) 52%, #010619 100%);
  isolation: isolate;
}

.welcome__atmosphere span {
  position: absolute;
  z-index: -1;
  border: 1px solid rgba(35, 121, 255, 0.12);
  border-radius: 50%;
}

.welcome__atmosphere span:first-child {
  top: -180px;
  left: -170px;
  width: 320px;
  height: 320px;
  box-shadow: 0 0 80px rgba(19, 126, 255, 0.12);
}

.welcome__atmosphere span:nth-child(2) {
  right: -210px;
  bottom: -170px;
  width: 390px;
  height: 390px;
  box-shadow: inset 0 0 80px rgba(19, 126, 255, 0.08);
}

.welcome__atmosphere span:last-child {
  top: 42%;
  left: 50%;
  width: 254px;
  height: 254px;
  border-color: rgba(69, 244, 225, 0.09);
  transform: translate(-50%, -50%);
}

.welcome__content {
  position: relative;
  z-index: 1;
  display: grid;
  min-height: inherit;
  grid-template-rows: minmax(0, 1fr) auto 70px;
  padding: 58px var(--content-padding) 0;
}

.welcome__brand {
  display: grid;
  align-self: center;
  justify-items: center;
  gap: 12px;
  text-align: center;
}

.welcome__brand-mark {
  display: grid;
  width: 86px;
  height: 86px;
  place-items: center;
  background:
    radial-gradient(circle at 36% 28%, rgba(255, 255, 255, 0.24), transparent 30%),
    linear-gradient(145deg, rgba(69, 244, 225, 0.18), rgba(8, 117, 255, 0.22));
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 50%;
  box-shadow:
    inset 0 0 22px rgba(69, 244, 225, 0.08),
    0 0 0 9px rgba(8, 117, 255, 0.08),
    0 24px 54px rgba(0, 0, 0, 0.38);
  animation: welcome-heartbeat 2.15s ease-in-out infinite;
  transform-origin: center;
}

.welcome__runner {
  width: 78px;
  height: 78px;
  color: #fff;
  filter:
    drop-shadow(0 0 7px rgba(69, 244, 225, 0.64))
    drop-shadow(0 0 14px rgba(8, 117, 255, 0.48));
}

@keyframes welcome-heartbeat {
  0%,
  42%,
  100% {
    box-shadow:
      inset 0 0 22px rgba(69, 244, 225, 0.08),
      0 0 0 9px rgba(8, 117, 255, 0.08),
      0 24px 54px rgba(0, 0, 0, 0.38);
    transform: scale(1);
  }

  12% {
    box-shadow:
      inset 0 0 24px rgba(69, 244, 225, 0.12),
      0 0 0 12px rgba(8, 117, 255, 0.1),
      0 28px 58px rgba(0, 0, 0, 0.4);
    transform: scale(1.065);
  }

  22% {
    transform: scale(0.985);
  }

  31% {
    transform: scale(1.035);
  }
}

.welcome__brand h1,
.welcome__brand p {
  margin: 0;
}

.welcome__brand h1 {
  color: transparent;
  background: linear-gradient(115deg, #fff 0%, #42efe0 38%, var(--welcome-blue) 88%);
  background-clip: text;
  -webkit-background-clip: text;
  font-size: 49px;
  font-style: italic;
  font-weight: 900;
  line-height: 0.95;
  letter-spacing: -2px;
  text-shadow: 0 16px 34px rgba(0, 61, 184, 0.2);
  transform: skewX(-6deg);
}

.welcome__brand p {
  max-width: 280px;
  color: rgba(227, 234, 247, 0.82);
  font-size: 15px;
  font-weight: 700;
  line-height: 1.55;
  letter-spacing: 0;
}

.welcome__pulse {
  position: absolute;
  top: 48%;
  left: 50%;
  width: min(68vw, 260px);
  aspect-ratio: 1;
  pointer-events: none;
  transform: translate(-50%, -50%);
}

.welcome__pulse span {
  position: absolute;
  inset: 0;
  border: 1px solid rgba(8, 117, 255, 0.2);
  border-radius: 50%;
  box-shadow: inset 0 0 36px rgba(8, 117, 255, 0.08);
}

.welcome__pulse span:last-child {
  inset: 20%;
  border-style: dashed;
  border-color: rgba(69, 244, 225, 0.16);
}

.welcome__actions {
  display: grid;
  align-self: end;
  gap: 12px;
  padding-bottom: 0;
}

.welcome__actions :deep(.base-button) {
  min-height: 52px;
  color: #fff;
  background: linear-gradient(135deg, #0b6cff 0%, #0757de 100%);
  border: 1px solid rgba(117, 170, 255, 0.48);
  border-radius: 18px;
  box-shadow: 0 18px 34px rgba(8, 73, 190, 0.36);
}

.welcome__actions :deep(.base-button--outline) {
  color: #dceaff;
  background: rgba(10, 27, 58, 0.56);
  border-color: rgba(111, 155, 229, 0.38);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(12px);
}

@media (max-height: 720px) {
  .welcome__content {
    grid-template-rows: minmax(0, 1fr) auto 44px;
    padding-top: 42px;
  }

  .welcome__brand-mark {
    width: 76px;
    height: 76px;
  }

  .welcome__brand h1 {
    font-size: 43px;
  }

  .welcome__brand p {
    font-size: 14px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .welcome__brand-mark {
    animation: none;
  }
}
</style>
