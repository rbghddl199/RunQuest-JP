<script setup>
import { computed, reactive, ref } from 'vue'
import { Eye, EyeOff, LockKeyhole, Mail } from '@lucide/vue'
import { useRouter } from 'vue-router'

import AuthShell from '../components/auth/AuthShell.vue'
import FormField from '../components/auth/FormField.vue'
import SocialLoginButtons from '../components/auth/SocialLoginButtons.vue'
import BaseButton from '../components/common/BaseButton.vue'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const showPassword = ref(false)
const remember = ref(Boolean(authStore.rememberedEmail))
const submitted = ref(false)

const form = reactive({
  email: authStore.rememberedEmail,
  password: '',
})

const emailError = computed(() => {
  if (!submitted.value) return ''
  if (!form.email) return '이메일을 입력해 주세요.'
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    return '올바른 이메일 형식으로 입력해 주세요.'
  }
  return ''
})

const passwordError = computed(() => {
  if (!submitted.value || form.password) return ''
  return '비밀번호를 입력해 주세요.'
})

async function submitLogin() {
  submitted.value = true
  authStore.errorMessage = ''
  if (emailError.value || passwordError.value) return

  try {
    const user = await authStore.login(
      {
        email: form.email.trim().toLowerCase(),
        password: form.password,
      },
      remember.value,
    )
    await router.push(user.profile.survey_completed ? '/home' : '/survey')
  } catch {
    // Store exposes the API error message in the form.
  }
}
</script>

<template>
  <AuthShell mode="login">
    <form class="auth-form" novalidate @submit.prevent="submitLogin">
      <div class="auth-form__heading">
        <span>RUNNER CHECK-IN</span>
        <h2>다시 달릴 준비됐나요?</h2>
        <p>러닝 기록과 오늘의 추천 코스를 이어서 확인해 보세요.</p>
      </div>

      <FormField
        id="login-email"
        v-model="form.email"
        label="이메일"
        type="email"
        placeholder="이메일 주소"
        autocomplete="email"
        :error="emailError"
      >
        <template #icon><Mail :size="20" /></template>
      </FormField>

      <FormField
        id="login-password"
        v-model="form.password"
        label="비밀번호"
        :type="showPassword ? 'text' : 'password'"
        placeholder="비밀번호"
        autocomplete="current-password"
        :error="passwordError"
      >
        <template #icon><LockKeyhole :size="20" /></template>
        <template #action>
          <button
            class="icon-action"
            type="button"
            :aria-label="showPassword ? '비밀번호 숨기기' : '비밀번호 보기'"
            @click="showPassword = !showPassword"
          >
            <EyeOff v-if="showPassword" :size="20" />
            <Eye v-else :size="20" />
          </button>
        </template>
      </FormField>

      <div class="auth-form__options">
        <label class="check-control">
          <input v-model="remember" type="checkbox" />
          <span>로그인 상태 유지</span>
        </label>
        <button type="button" class="link-button" disabled>비밀번호 찾기</button>
      </div>

      <p v-if="authStore.errorMessage" class="form-error" role="alert">
        {{ authStore.errorMessage }}
      </p>

      <BaseButton native-type="submit" :disabled="authStore.isLoading">
        {{ authStore.isLoading ? '로그인 중...' : '로그인' }}
      </BaseButton>

      <SocialLoginButtons />

      <p class="auth-form__switch">
        처음 오셨나요?
        <RouterLink to="/signup">회원가입</RouterLink>
      </p>
    </form>
  </AuthShell>
</template>

<style scoped>
@import '../assets/styles/auth-form.css';

.auth-form :deep(.base-button) {
  min-height: 50px;
  color: #fff;
  background: linear-gradient(135deg, #0b6cff 0%, #0757de 100%);
  border: 1px solid rgba(8, 82, 214, 0.24);
  border-radius: 16px;
  box-shadow: 0 16px 30px rgba(8, 73, 190, 0.26);
}
</style>
