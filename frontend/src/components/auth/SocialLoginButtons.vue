<script setup>
const providers = [
  { name: 'Google', label: 'G', className: 'google' },
  { name: 'Kakao', label: 'K', className: 'kakao' },
]
</script>

<template>
  <div class="social">
    <div class="social__divider"><span>또는</span></div>
    <div class="social__buttons">
      <button
        v-for="provider in providers"
        :key="provider.name"
        type="button"
        :class="provider.className"
        :aria-label="`${provider.name} 로그인은 준비 중입니다`"
        disabled
      >
        {{ provider.label }}
      </button>
    </div>
    <p>소셜 로그인은 외부 API 연결 단계에서 활성화됩니다.</p>
  </div>
</template>

<style scoped>
.social {
  margin-top: 0;
}

.social__divider {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--color-muted);
  font-size: 12px;
}

.social__divider::before,
.social__divider::after {
  height: 1px;
  flex: 1;
  background: var(--color-border);
  content: '';
}

.social__buttons {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 10px;
}

.social__buttons button {
  display: grid;
  width: 38px;
  height: 38px;
  place-items: center;
  color: var(--color-navy);
  font-size: 17px;
  font-weight: 900;
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: 50%;
}

.social__buttons .google {
  color: #4285f4;
}

.social__buttons .kakao {
  color: #302513;
  background: #fee500;
  border-color: #fee500;
}

.social__buttons button:disabled {
  cursor: not-allowed;
  opacity: 0.72;
}

.social > p {
  margin: 8px 0 0;
  color: #98a4b5;
  font-size: 9px;
  line-height: 1.45;
  text-align: center;
}
</style>
