<script setup>
import {
  Activity,
  BarChart3,
  Dumbbell,
  HeartPulse,
  Medal,
  Scale,
  Smile,
  Sprout,
  Trophy,
  UserRound,
} from '@lucide/vue'

const iconMap = {
  sprout: Sprout,
  runner: UserRound,
  medal: Medal,
  heart: HeartPulse,
  scale: Scale,
  dumbbell: Dumbbell,
  smile: Smile,
  chart: BarChart3,
  trophy: Trophy,
}

defineProps({
  option: {
    type: Object,
    required: true,
  },
  selected: {
    type: Boolean,
    default: false,
  },
  name: {
    type: String,
    required: true,
  },
})

defineEmits(['select'])
</script>

<template>
  <label class="survey-option" :class="{ 'is-selected': selected }">
    <input
      type="radio"
      :name="name"
      :value="option.value"
      :checked="selected"
      @change="$emit('select', option.value)"
    />
    <span class="survey-option__radio" aria-hidden="true"></span>
    <component
      :is="iconMap[option.icon] ?? Activity"
      v-if="option.icon"
      class="survey-option__icon"
      :size="28"
      stroke-width="2.2"
    />
    <span class="survey-option__label">{{ option.label }}</span>
  </label>
</template>

<style scoped>
.survey-option {
  display: grid;
  min-height: 68px;
  grid-template-columns: 28px auto 1fr;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  color: #edf7ff;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  cursor: pointer;
  transition:
    border-color 160ms ease,
    background-color 160ms ease,
    box-shadow 160ms ease;
}

.survey-option:hover {
  border-color: rgba(67, 241, 230, 0.58);
}

.survey-option.is-selected {
  background: rgba(67, 241, 230, 0.13);
  border-color: #43f1e6;
  box-shadow: 0 10px 24px rgba(67, 241, 230, 0.12);
}

.survey-option input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
}

.survey-option__radio {
  display: grid;
  width: 24px;
  height: 24px;
  place-items: center;
  border: 2px solid rgba(210, 232, 244, 0.68);
  border-radius: 50%;
}

.survey-option__radio::after {
  width: 12px;
  height: 12px;
  background: transparent;
  border-radius: 50%;
  content: '';
}

.is-selected .survey-option__radio {
  border-color: #43f1e6;
}

.is-selected .survey-option__radio::after {
  background: #43f1e6;
}

.survey-option__icon {
  color: #43f1e6;
}

.survey-option__label {
  overflow: hidden;
  font-size: 15px;
  line-height: 1.4;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
