<script setup>
defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'outline', 'text'].includes(value),
  },
  to: {
    type: [String, Object],
    default: null,
  },
  nativeType: {
    type: String,
    default: 'button',
    validator: (value) => ['button', 'submit', 'reset'].includes(value),
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})
</script>

<template>
  <RouterLink v-if="to" class="base-button" :class="`base-button--${variant}`" :to="to">
    <slot />
  </RouterLink>
  <button
    v-else
    class="base-button"
    :class="`base-button--${variant}`"
    :type="nativeType"
    :disabled="disabled"
  >
    <slot />
  </button>
</template>

<style scoped>
.base-button {
  display: inline-flex;
  width: 100%;
  min-height: 56px;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 20px;
  color: var(--color-primary);
  font-size: 17px;
  font-weight: 700;
  line-height: 1.2;
  background: transparent;
  border-radius: var(--radius-medium);
  cursor: pointer;
  transition:
    transform 160ms ease,
    box-shadow 160ms ease,
    background-color 160ms ease;
}

.base-button:hover {
  transform: translateY(-1px);
}

.base-button:active {
  transform: translateY(0);
}

.base-button:disabled {
  cursor: wait;
  opacity: 0.65;
  transform: none;
}

.base-button:focus-visible {
  outline: 3px solid rgba(8, 102, 255, 0.24);
  outline-offset: 3px;
}

.base-button--primary {
  color: #fff;
  background: var(--color-primary);
  box-shadow: var(--shadow-button);
}

.base-button--primary:hover {
  background: var(--color-primary-dark);
}

.base-button--outline {
  background: rgba(255, 255, 255, 0.82);
  border: 2px solid var(--color-primary);
}

.base-button--outline:hover {
  background: var(--color-primary-soft);
}

.base-button--text {
  min-height: 44px;
  padding-block: 8px;
}

.base-button--text:hover {
  background: rgba(234, 243, 255, 0.8);
}
</style>
