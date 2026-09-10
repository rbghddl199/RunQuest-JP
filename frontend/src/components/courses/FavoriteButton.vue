<script setup>
import { Bookmark } from '@lucide/vue'

defineProps({
  active: {
    type: Boolean,
    default: false,
  },
  label: {
    type: String,
    default: '코스 찜하기',
  },
})

defineEmits(['toggle'])
</script>

<template>
  <button
    type="button"
    class="favorite-button"
    :class="{ 'is-active': active }"
    :aria-label="active ? '코스 찜 해제' : label"
    :aria-pressed="active"
    @click.stop.prevent="$emit('toggle')"
  >
    <Bookmark :size="22" :fill="active ? 'currentColor' : 'none'" />
  </button>
</template>

<style scoped>
.favorite-button {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  padding: 0;
  color: #fff;
  background: rgba(12, 28, 52, 0.52);
  border-radius: 50%;
  cursor: pointer;
  backdrop-filter: blur(5px);
  line-height: 0;
}

.favorite-button.is-active {
  color: #fff;
  background: var(--color-primary);
}
</style>
