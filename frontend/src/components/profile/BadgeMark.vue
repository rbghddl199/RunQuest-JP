<script setup>
import {
  CalendarCheck,
  Flame,
  Footprints,
  Medal,
  Moon,
  Route,
} from '@lucide/vue'
import { computed } from 'vue'

const props = defineProps({
  badge: {
    type: Object,
    required: true,
  },
  size: {
    type: Number,
    default: 58,
  },
})

const icons = {
  'calendar-check': CalendarCheck,
  flame: Flame,
  footprints: Footprints,
  medal: Medal,
  moon: Moon,
  route: Route,
}
const icon = computed(() => icons[props.badge.icon] ?? Medal)
</script>

<template>
  <span
    class="badge-mark"
    :class="{ 'is-locked': !badge.earned }"
    :style="{ '--badge-color': badge.color, width: `${size}px`, height: `${size}px` }"
  >
    <component :is="icon" :size="Math.round(size * 0.46)" stroke-width="2.2" />
  </span>
</template>

<style scoped>
.badge-mark {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  color: #fff;
  background: var(--badge-color);
  border: 4px solid color-mix(in srgb, var(--badge-color), white 55%);
  border-radius: 50%;
  box-shadow: 0 7px 16px color-mix(in srgb, var(--badge-color), transparent 72%);
}

.badge-mark.is-locked {
  color: #8793a6;
  background: #dce3ed;
  border-color: #eef2f7;
  box-shadow: none;
}
</style>
