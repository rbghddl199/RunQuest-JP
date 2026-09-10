<script setup>
import { computed } from 'vue'
import { AlertTriangle, Inbox, RefreshCw } from '@lucide/vue'

import RunnerMark from './RunnerMark.vue'

const props = defineProps({
  type: {
    type: String,
    default: 'empty',
    validator: (value) => ['loading', 'empty', 'error'].includes(value),
  },
  title: {
    type: String,
    required: true,
  },
  message: {
    type: String,
    default: '',
  },
  actionLabel: {
    type: String,
    default: '',
  },
  actionTo: {
    type: [String, Object],
    default: '',
  },
  compact: {
    type: Boolean,
    default: false,
  },
  tone: {
    type: String,
    default: 'light',
    validator: (value) => ['light', 'dark'].includes(value),
  },
})

const emit = defineEmits(['action'])

const iconComponent = computed(() => {
  if (props.type === 'error') return AlertTriangle
  if (props.type === 'loading') return RefreshCw
  return Inbox
})
</script>

<template>
  <section
    class="app-state"
    :class="[
      `app-state--${type}`,
      `app-state--${tone}`,
      { 'app-state--compact': compact },
    ]"
    :aria-live="type === 'loading' ? 'polite' : undefined"
    :role="type === 'error' ? 'alert' : undefined"
  >
    <div class="app-state__mark" aria-hidden="true">
      <RunnerMark v-if="type === 'loading'" class="app-state__runner" />
      <component
        :is="iconComponent"
        v-else
        class="app-state__icon"
        :size="28"
        stroke-width="2.2"
      />
    </div>

    <div class="app-state__copy">
      <h2>{{ title }}</h2>
      <p v-if="message">{{ message }}</p>
    </div>

    <slot name="action">
      <RouterLink v-if="actionTo && actionLabel" class="app-state__action" :to="actionTo">
        {{ actionLabel }}
      </RouterLink>
      <button
        v-else-if="actionLabel"
        class="app-state__action"
        type="button"
        @click="emit('action')"
      >
        {{ actionLabel }}
      </button>
    </slot>
  </section>
</template>

<style scoped>
.app-state {
  display: grid;
  min-height: 360px;
  align-content: center;
  justify-items: center;
  gap: 12px;
  padding: 44px 18px;
  color: var(--color-muted);
  text-align: center;
}

.app-state--compact {
  min-height: 180px;
  padding: 28px 16px;
}

.app-state__mark {
  position: relative;
  display: grid;
  width: 58px;
  height: 58px;
  place-items: center;
  color: var(--color-primary);
  background:
    radial-gradient(circle at 34% 28%, rgba(255, 255, 255, 0.9), transparent 31%),
    linear-gradient(145deg, rgba(8, 102, 255, 0.14), rgba(19, 198, 200, 0.16));
  border: 1px solid color-mix(in srgb, var(--color-primary) 18%, var(--color-border));
  border-radius: 50%;
  box-shadow:
    inset 0 0 18px rgba(8, 102, 255, 0.08),
    0 14px 34px rgba(32, 83, 156, 0.12);
}

.app-state--error .app-state__mark {
  color: #d73c4e;
  background:
    radial-gradient(circle at 34% 28%, rgba(255, 255, 255, 0.9), transparent 31%),
    linear-gradient(145deg, rgba(255, 240, 242, 0.9), rgba(255, 232, 221, 0.9));
  border-color: rgba(215, 60, 78, 0.18);
}

.app-state__runner {
  width: 44px;
  height: 44px;
  animation: app-state-pulse 1.1s ease-in-out infinite;
}

.app-state--loading .app-state__mark::after {
  position: absolute;
  inset: -5px;
  content: "";
  border: 2px solid rgba(8, 102, 255, 0.12);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: app-state-spin 0.9s linear infinite;
}

.app-state__copy {
  display: grid;
  gap: 6px;
  max-width: 270px;
}

.app-state__copy h2 {
  margin: 0;
  color: var(--color-navy);
  font-size: 16px;
  font-weight: 900;
  letter-spacing: 0;
}

.app-state__copy p {
  margin: 0;
  color: var(--color-muted);
  font-size: 12px;
  line-height: 1.55;
}

.app-state__action {
  display: inline-grid;
  min-height: 38px;
  align-items: center;
  justify-content: center;
  margin-top: 2px;
  padding: 0 15px;
  color: #fff;
  background: var(--color-primary);
  border-radius: var(--radius-small);
  box-shadow: var(--shadow-button);
  font-size: 12px;
  font-weight: 800;
}

.app-state--dark {
  color: rgba(226, 242, 255, 0.76);
}

.app-state--dark .app-state__mark {
  color: #43f1e6;
  background:
    radial-gradient(circle at 34% 28%, rgba(255, 255, 255, 0.24), transparent 31%),
    linear-gradient(145deg, rgba(69, 244, 225, 0.14), rgba(8, 117, 255, 0.18));
  border-color: rgba(255, 255, 255, 0.16);
  box-shadow:
    inset 0 0 22px rgba(69, 244, 225, 0.08),
    0 22px 52px rgba(0, 0, 0, 0.28);
}

.app-state--dark .app-state__copy h2 {
  color: #fff;
}

.app-state--dark .app-state__copy p {
  color: rgba(226, 242, 255, 0.76);
}

@keyframes app-state-spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes app-state-pulse {
  50% {
    transform: scale(1.04);
  }
}
</style>
