<script setup>
import { computed, onMounted, ref } from 'vue'
import { ArrowLeft } from '@lucide/vue'
import { useRouter } from 'vue-router'

import AppState from '../components/common/AppState.vue'
import BaseButton from '../components/common/BaseButton.vue'
import SurveyOption from '../components/survey/SurveyOption.vue'
import SurveyProgress from '../components/survey/SurveyProgress.vue'
import { useAuthStore } from '../stores/auth'
import { useSurveyStore } from '../stores/survey'

const router = useRouter()
const authStore = useAuthStore()
const surveyStore = useSurveyStore()
const currentStep = ref(1)
const validationMessage = ref('')

const currentQuestion = computed(
  () => surveyStore.questions[currentStep.value - 1] ?? null,
)
const selectedValue = computed(() => (
  currentQuestion.value
    ? surveyStore.answers[currentQuestion.value.key]
    : ''
))

onMounted(async () => {
  await surveyStore.loadQuestions()
  if (authStore.user?.profile?.survey_completed) {
    await surveyStore.loadSavedResponse()
  }
})

function selectOption(value) {
  surveyStore.selectAnswer(currentQuestion.value.key, value)
  validationMessage.value = ''
}

function goBack() {
  if (currentStep.value > 1) {
    currentStep.value -= 1
    validationMessage.value = ''
    window.scrollTo({ top: 0, behavior: 'smooth' })
    return
  }
  router.back()
}

async function goNext() {
  if (!selectedValue.value) {
    validationMessage.value = '답변을 하나 선택해 주세요.'
    return
  }

  if (currentStep.value < surveyStore.questions.length) {
    currentStep.value += 1
    validationMessage.value = ''
    window.scrollTo({ top: 0, behavior: 'smooth' })
    return
  }

  const result = await surveyStore.submit()
  if (result) {
    await router.push('/survey/result')
  }
}
</script>

<template>
  <main class="mobile-shell survey-page">
    <header class="survey-header">
      <button type="button" aria-label="이전 화면" @click="goBack">
        <ArrowLeft :size="26" />
      </button>
      <h1>맞춤 추천 설문</h1>
      <span aria-hidden="true"></span>
    </header>

    <AppState
      v-if="surveyStore.isLoading"
      type="loading"
      tone="dark"
      title="설문을 준비하고 있어요"
      message="맞춤 추천에 필요한 질문을 불러오는 중입니다."
    />

    <AppState
      v-else-if="surveyStore.errorMessage && !currentQuestion"
      type="error"
      tone="dark"
      title="설문을 불러오지 못했어요"
      :message="surveyStore.errorMessage"
      action-label="다시 불러오기"
      @action="surveyStore.loadQuestions"
    />

    <template v-else-if="currentQuestion">
      <SurveyProgress
        :current-step="currentStep"
        :total-steps="surveyStore.questions.length"
      />

      <p class="survey-guide">
        한 가지씩 답변해 주시면 맞춤 코스와 크루를 추천해 드려요.
      </p>

      <section class="survey-card" :aria-labelledby="`question-${currentStep}`">
        <h2 :id="`question-${currentStep}`">
          <strong>Q{{ currentStep }}.</strong>
          {{ currentQuestion.title }}
        </h2>

        <div class="survey-options">
          <SurveyOption
            v-for="option in currentQuestion.options"
            :key="option.value"
            :name="currentQuestion.key"
            :option="option"
            :selected="selectedValue === option.value"
            @select="selectOption"
          />
        </div>
      </section>

      <p v-if="validationMessage || surveyStore.errorMessage" class="survey-error" role="alert">
        {{ validationMessage || surveyStore.errorMessage }}
      </p>

      <footer class="survey-actions">
        <BaseButton variant="outline" @click="goBack">이전</BaseButton>
        <BaseButton
          :disabled="surveyStore.isSubmitting"
          @click="goNext"
        >
          {{
            surveyStore.isSubmitting
              ? '저장 중...'
              : currentStep === surveyStore.questions.length
                ? '완료'
                : '다음'
          }}
        </BaseButton>
      </footer>
    </template>
  </main>
</template>

<style scoped>
.survey-page {
  min-height: max(100svh, 720px);
  padding: 24px var(--content-padding) 28px;
  color: #eaf6ff;
  background:
    radial-gradient(circle at 78% 8%, rgba(69, 244, 225, 0.24), transparent 28%),
    radial-gradient(circle at 12% 38%, rgba(8, 102, 255, 0.28), transparent 32%),
    linear-gradient(160deg, #030b22 0%, #020b22 56%, #061a35 100%);
}

.survey-header {
  display: grid;
  grid-template-columns: 44px 1fr 44px;
  align-items: center;
  margin-bottom: 28px;
}

.survey-header button {
  display: grid;
  width: 44px;
  height: 44px;
  margin-left: -10px;
  place-items: center;
  color: #d9f4ff;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 50%;
  cursor: pointer;
}

.survey-header h1 {
  margin: 0;
  color: #ffffff;
  font-size: 21px;
  text-align: center;
}

.survey-guide {
  margin: 28px 4px 24px;
  color: rgba(226, 242, 255, 0.78);
  font-size: 13px;
  line-height: 1.65;
}

.survey-card {
  padding: 25px 20px 22px;
  background: rgba(255, 255, 255, 0.09);
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 8px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.22);
  backdrop-filter: blur(18px);
}

.survey-card h2 {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin: 0 0 24px;
  color: #ffffff;
  font-size: 18px;
  line-height: 1.5;
  white-space: nowrap;
}

.survey-card h2 strong {
  flex: 0 0 auto;
  color: #43f1e6;
}

.survey-options {
  display: grid;
  gap: 12px;
}

.survey-error {
  margin: 14px 0 0;
  color: #ffb4c0;
  font-size: 12px;
  text-align: center;
}

.survey-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 18px;
}

.survey-actions :deep(.base-button) {
  min-height: 52px;
  border-radius: 16px;
}

.survey-actions :deep(.base-button--primary) {
  color: #03122d;
  background: linear-gradient(135deg, #55f5e6 0%, #1fc6f5 46%, #0b7bff 100%);
  box-shadow: 0 18px 34px rgba(8, 117, 255, 0.28);
}

.survey-actions :deep(.base-button--outline) {
  color: #eaf8ff;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(93, 225, 255, 0.28);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(12px);
}

.is-spinning {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-height: 700px) {
  .survey-page {
    padding-top: 14px;
  }

  .survey-header {
    margin-bottom: 18px;
  }

  .survey-guide {
    margin-block: 18px;
  }
}
</style>
