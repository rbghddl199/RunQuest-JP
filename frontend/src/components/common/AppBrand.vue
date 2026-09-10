<script setup>
defineProps({
  size: {
    type: String,
    default: 'medium',
  },
  light: {
    type: Boolean,
    default: false,
  },
  showName: {
    type: Boolean,
    default: true,
  },
})
</script>

<template>
  <div class="app-brand" :class="[`app-brand--${size}`, { 'app-brand--light': light }]">
    <span class="app-brand__mark" aria-hidden="true">
      <img src="/runner.png" alt="" />
    </span>
    <span v-if="showName" class="app-brand__name">RunQuest</span>
  </div>
</template>

<style scoped>
.app-brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.app-brand__mark {
  position: relative;
  display: grid;
  width: 44px;
  height: 44px;
  place-items: center;
  overflow: hidden;
  background: #031335;
  border: 0;
  border-radius: 50%;
  box-shadow:
    0 0 0 1px rgba(69, 244, 225, 0.16),
    0 0 18px rgba(21, 151, 255, 0.28);
}

.app-brand__mark img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scale(1.14);
}

.app-brand__name {
  color: transparent;
  background: linear-gradient(115deg, #fff 0%, #42efe0 38%, #0875ff 88%);
  background-clip: text;
  -webkit-background-clip: text;
  font-size: 28px;
  font-style: italic;
  font-weight: 900;
  line-height: 0.95;
  letter-spacing: -1px;
  filter: drop-shadow(0 9px 22px rgba(0, 61, 184, 0.22));
  transform: skewX(-6deg);
}

.app-brand--small {
  gap: 8px;
}

.app-brand--small .app-brand__mark {
  width: 34px;
  height: 34px;
}

.app-brand--small .app-brand__name {
  font-size: 22px;
}

.app-brand--large .app-brand__mark {
  width: 58px;
  height: 58px;
}

.app-brand--large .app-brand__name {
  font-size: 38px;
}

.app-brand--light .app-brand__name {
  background: linear-gradient(115deg, #fff 0%, #42efe0 38%, #0875ff 88%);
  background-clip: text;
  -webkit-background-clip: text;
}
</style>
