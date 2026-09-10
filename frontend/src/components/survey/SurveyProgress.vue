<script setup>
defineProps({
  currentStep: {
    type: Number,
    required: true,
  },
  totalSteps: {
    type: Number,
    required: true,
  },
})
</script>

<template>
  <ol class="survey-progress" aria-label="설문 진행 단계">
    <li v-for="step in totalSteps" :key="step">
      <span
        :class="{
          'is-current': step === currentStep,
          'is-complete': step < currentStep,
        }"
        :aria-current="step === currentStep ? 'step' : undefined"
      >
        {{ step }}
      </span>
      <i v-if="step < totalSteps" aria-hidden="true"></i>
    </li>
  </ol>
</template>

<style scoped>
.survey-progress {
  display: flex;
  width: 100%;
  align-items: center;
  margin: 0;
  padding: 0;
  list-style: none;
}

.survey-progress li {
  display: flex;
  min-width: 0;
  flex: 1;
  align-items: center;
}

.survey-progress li:last-child {
  flex: 0 0 38px;
}

.survey-progress span {
  display: grid;
  width: 38px;
  height: 38px;
  flex: 0 0 38px;
  place-items: center;
  color: #65738a;
  font-size: 14px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 50%;
  transition: 180ms ease;
}

.survey-progress span.is-current {
  color: #03122a;
  font-weight: 700;
  background: #43f1e6;
  border-color: #43f1e6;
  box-shadow: 0 6px 18px rgba(67, 241, 230, 0.24);
}

.survey-progress span.is-complete {
  color: #43f1e6;
  background: rgba(67, 241, 230, 0.12);
  border-color: rgba(67, 241, 230, 0.5);
}

.survey-progress i {
  width: 100%;
  height: 1px;
  background: rgba(255, 255, 255, 0.22);
}

@media (max-width: 359px) {
  .survey-progress span {
    width: 34px;
    height: 34px;
    flex-basis: 34px;
  }

  .survey-progress li:last-child {
    flex-basis: 34px;
  }
}
</style>
