<script setup>
import { computed, onMounted } from 'vue'
import { Activity, Check, RefreshCw, Server } from '@lucide/vue'

import { useSystemStore } from '../stores/system'

const systemStore = useSystemStore()

const statusText = computed(() => {
  const labels = {
    idle: '확인 전',
    loading: '연결 확인 중',
    connected: '정상 연결',
    error: '연결 실패',
  }

  return labels[systemStore.apiStatus]
})

onMounted(() => {
  systemStore.checkApi()
})
</script>

<template>
  <main class="mobile-shell system-check">
    <section class="brand" aria-labelledby="page-title">
      <div class="brand__mark" aria-hidden="true">
        <Activity :size="30" stroke-width="2.5" />
      </div>
      <div>
        <p class="brand__name">RunQuest</p>
        <p class="brand__caption">러닝의 새로운 시작</p>
      </div>
    </section>

    <section class="status-panel">
      <div class="status-panel__icon">
        <Server :size="28" />
      </div>
      <p class="eyebrow">STEP 1</p>
      <h1 id="page-title">개발 환경 준비 완료</h1>
      <p class="status-panel__description">
        Vue 화면과 Django REST API의 연결 상태를 확인합니다.
      </p>

      <div
        class="connection"
        :class="`connection--${systemStore.apiStatus}`"
        role="status"
        aria-live="polite"
      >
        <span class="connection__indicator">
          <Check v-if="systemStore.apiStatus === 'connected'" :size="16" />
        </span>
        <div>
          <strong>{{ statusText }}</strong>
          <p>{{ systemStore.serviceName || systemStore.errorMessage || 'API 상태 확인을 시작합니다.' }}</p>
        </div>
      </div>

      <button
        class="retry-button"
        type="button"
        :disabled="systemStore.apiStatus === 'loading'"
        @click="systemStore.checkApi"
      >
        <RefreshCw
          :size="19"
          :class="{ 'is-spinning': systemStore.apiStatus === 'loading' }"
        />
        다시 확인
      </button>
    </section>
  </main>
</template>

<style scoped>
.system-check {
  display: flex;
  flex-direction: column;
  padding: 34px 24px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand__mark {
  display: grid;
  width: 48px;
  height: 48px;
  place-items: center;
  color: #fff;
  background: var(--color-primary);
  border-radius: 8px;
}

.brand__name,
.brand__caption,
.connection p {
  margin: 0;
}

.brand__name {
  color: var(--color-primary);
  font-size: 24px;
  font-weight: 800;
}

.brand__caption {
  color: var(--color-muted);
  font-size: 13px;
}

.status-panel {
  display: flex;
  flex: 1;
  flex-direction: column;
  justify-content: center;
  padding-block: 40px;
}

.status-panel__icon {
  display: grid;
  width: 56px;
  height: 56px;
  margin-bottom: 24px;
  place-items: center;
  color: var(--color-primary);
  background: #e9f2ff;
  border-radius: 8px;
}

.eyebrow {
  margin: 0 0 8px;
  color: var(--color-primary);
  font-size: 13px;
  font-weight: 700;
}

h1 {
  margin: 0;
  color: var(--color-navy);
  font-size: 31px;
  line-height: 1.3;
  letter-spacing: 0;
}

.status-panel__description {
  margin: 14px 0 30px;
  color: var(--color-muted);
  line-height: 1.7;
}

.connection {
  display: grid;
  grid-template-columns: 22px 1fr;
  gap: 12px;
  min-height: 82px;
  padding: 18px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-surface);
  box-shadow: var(--shadow-soft);
}

.connection__indicator {
  display: grid;
  width: 22px;
  height: 22px;
  place-items: center;
  color: #fff;
  background: #aeb9ca;
  border-radius: 50%;
}

.connection--loading .connection__indicator {
  background: #ffb020;
}

.connection--connected .connection__indicator {
  background: #16a66a;
}

.connection--error .connection__indicator {
  background: #e04949;
}

.connection strong {
  display: block;
  margin-bottom: 3px;
  color: var(--color-navy);
}

.connection p {
  color: var(--color-muted);
  font-size: 13px;
  line-height: 1.5;
}

.retry-button {
  display: flex;
  width: 100%;
  min-height: 54px;
  margin-top: 14px;
  align-items: center;
  justify-content: center;
  gap: 9px;
  color: #fff;
  font-weight: 700;
  background: var(--color-primary);
  border-radius: 8px;
  cursor: pointer;
}

.retry-button:disabled {
  cursor: wait;
  opacity: 0.65;
}

.is-spinning {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
