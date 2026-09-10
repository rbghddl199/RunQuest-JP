<script setup>
import { ArrowLeft, Construction } from '@lucide/vue'

defineProps({
  eyebrow: {
    type: String,
    required: true,
  },
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    required: true,
  },
})
</script>

<template>
  <main class="mobile-shell placeholder">
    <RouterLink class="placeholder__back" to="/welcome" aria-label="시작 화면으로 돌아가기">
      <ArrowLeft :size="25" />
    </RouterLink>

    <section>
      <span class="placeholder__icon"><Construction :size="30" /></span>
      <p>{{ eyebrow }}</p>
      <h1>{{ title }}</h1>
      <p class="placeholder__description">{{ description }}</p>
    </section>
  </main>
</template>

<style scoped>
.placeholder {
  padding: 28px var(--content-padding);
}

.placeholder__back {
  display: grid;
  width: 44px;
  height: 44px;
  place-items: center;
  color: var(--color-navy);
  border-radius: 50%;
}

.placeholder section {
  display: flex;
  min-height: calc(100svh - 110px);
  align-items: center;
  flex-direction: column;
  justify-content: center;
  text-align: center;
}

.placeholder__icon {
  display: grid;
  width: 64px;
  height: 64px;
  margin-bottom: 22px;
  place-items: center;
  color: var(--color-primary);
  background: var(--color-primary-soft);
  border-radius: var(--radius-medium);
}

.placeholder p,
.placeholder h1 {
  margin: 0;
}

.placeholder section > p:first-of-type {
  color: var(--color-primary);
  font-size: 13px;
  font-weight: 800;
}

.placeholder h1 {
  margin-top: 8px;
  color: var(--color-navy);
  font-size: 32px;
}

.placeholder .placeholder__description {
  max-width: 300px;
  margin-top: 14px;
  color: var(--color-muted);
  line-height: 1.7;
}
</style>
