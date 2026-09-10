<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { Check, Eye, EyeOff, LockKeyhole, Mail, Smile } from '@lucide/vue'
import { useRouter } from 'vue-router'

import AuthShell from '../components/auth/AuthShell.vue'
import FormField from '../components/auth/FormField.vue'
import SocialLoginButtons from '../components/auth/SocialLoginButtons.vue'
import BaseButton from '../components/common/BaseButton.vue'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const PENDING_SIGNUP_KEY = 'runquest_pending_signup'
const submitted = ref(false)
const showPassword = ref(false)
const showPasswordConfirm = ref(false)
const nicknameStatus = reactive({
  checked: false,
  available: false,
  message: '',
  loading: false,
})

const form = reactive({
  email: '',
  password: '',
  passwordConfirm: '',
  nickname: '',
})

onMounted(() => {
  const pendingSignup = sessionStorage.getItem(PENDING_SIGNUP_KEY)
  if (!pendingSignup) return

  try {
    const parsed = JSON.parse(pendingSignup)
    form.email = parsed.email ?? ''
    form.password = parsed.password ?? ''
    form.passwordConfirm = parsed.password ?? ''
    form.nickname = parsed.nickname ?? ''
  } catch {
    sessionStorage.removeItem(PENDING_SIGNUP_KEY)
  }
})

watch(
  () => form.nickname,
  () => {
    nicknameStatus.checked = false
    nicknameStatus.available = false
    nicknameStatus.message = ''
  },
)

const emailError = computed(() => {
  if (!submitted.value) return ''
  if (!form.email) return '이메일을 입력해 주세요.'
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    return '올바른 이메일 형식으로 입력해 주세요.'
  }
  return ''
})

const passwordError = computed(() => {
  if (!submitted.value) return ''
  if (!form.password) return '비밀번호를 입력해 주세요.'
  if (form.password.length < 8) return '비밀번호는 8자 이상이어야 합니다.'
  if (
    !/[A-Za-z]/.test(form.password)
    || !/\d/.test(form.password)
    || !/[^A-Za-z0-9]/.test(form.password)
  ) {
    return '영문, 숫자, 특수문자를 모두 포함해 주세요.'
  }
  return ''
})

const passwordConfirmError = computed(() => {
  if (!submitted.value) return ''
  if (!form.passwordConfirm) return '비밀번호를 한 번 더 입력해 주세요.'
  if (form.passwordConfirm !== form.password) return '비밀번호가 일치하지 않아요.'
  return ''
})

const nicknameError = computed(() => {
  if (!submitted.value) return ''
  if (!form.nickname.trim()) return '닉네임을 입력해 주세요.'
  if (form.nickname.trim().length < 2 || form.nickname.trim().length > 12) {
    return '닉네임은 2~12자로 입력해 주세요.'
  }
  if (!nicknameStatus.available) return '닉네임 중복 확인이 필요합니다.'
  return ''
})

async function checkNickname() {
  if (form.nickname.trim().length < 2 || form.nickname.trim().length > 12) {
    nicknameStatus.checked = true
    nicknameStatus.message = '닉네임은 2~12자로 입력해 주세요.'
    return
  }

  nicknameStatus.loading = true
  try {
    const result = await authStore.checkNickname(form.nickname.trim())
    nicknameStatus.checked = true
    nicknameStatus.available = result.available
    nicknameStatus.message = result.message
  } catch {
    nicknameStatus.checked = true
    nicknameStatus.available = false
    nicknameStatus.message = '중복 확인 중 문제가 발생했습니다.'
  } finally {
    nicknameStatus.loading = false
  }
}

async function submitSignup() {
  submitted.value = true
  authStore.errorMessage = ''

  if (
    emailError.value
    || passwordError.value
    || passwordConfirmError.value
    || nicknameError.value
  ) return

  sessionStorage.setItem(PENDING_SIGNUP_KEY, JSON.stringify({
    email: form.email.trim().toLowerCase(),
    password: form.password,
    nickname: form.nickname.trim(),
  }))
  await router.push({ name: 'signup-terms-consent' })
}
</script>

<template>
  <AuthShell mode="signup">
    <form class="auth-form signup-form" novalidate @submit.prevent="submitSignup">
      <div class="auth-form__heading">
        <span>RUNNER PROFILE</span>
        <h2>나만의 러너 프로필 만들기</h2>
        <p>기본 정보를 입력하면 성향 설문으로 이어집니다.</p>
      </div>

      <div class="auth-section-label">계정 정보</div>

      <FormField
        id="signup-email"
        v-model="form.email"
        label="이메일"
        type="email"
        placeholder="이메일 주소를 입력해 주세요"
        autocomplete="email"
        help="로그인과 주요 알림에 사용하는 이메일입니다."
        :error="emailError"
      >
        <template #icon><Mail :size="20" /></template>
      </FormField>

      <FormField
        id="signup-password"
        v-model="form.password"
        label="비밀번호"
        :type="showPassword ? 'text' : 'password'"
        placeholder="비밀번호를 입력해 주세요"
        autocomplete="new-password"
        help="영문, 숫자, 특수문자를 포함해 8자 이상 입력해 주세요."
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

      <FormField
        id="signup-password-confirm"
        v-model="form.passwordConfirm"
        label="비밀번호 확인"
        :type="showPasswordConfirm ? 'text' : 'password'"
        placeholder="비밀번호를 한 번 더 입력해 주세요"
        autocomplete="new-password"
        :error="passwordConfirmError"
      >
        <template #icon><LockKeyhole :size="20" /></template>
        <template #action>
          <button
            class="icon-action"
            type="button"
            :aria-label="showPasswordConfirm ? '비밀번호 확인 숨기기' : '비밀번호 확인 보기'"
            @click="showPasswordConfirm = !showPasswordConfirm"
          >
            <EyeOff v-if="showPasswordConfirm" :size="20" />
            <Eye v-else :size="20" />
          </button>
        </template>
      </FormField>

      <div class="auth-section-label">러너 이름</div>

      <FormField
        id="signup-nickname"
        v-model="form.nickname"
        label="닉네임"
        placeholder="사용할 닉네임을 입력해 주세요"
        autocomplete="nickname"
        help="2~12자, 다른 사용자와 겹치지 않게 설정해 주세요."
        :error="nicknameError"
      >
        <template #icon><Smile :size="20" /></template>
        <template #action>
          <button
            class="field-button"
            type="button"
            :disabled="nicknameStatus.loading"
            @click="checkNickname"
          >
            {{ nicknameStatus.loading ? '확인 중' : '중복확인' }}
          </button>
        </template>
      </FormField>

      <p
        v-if="nicknameStatus.checked"
        class="nickname-result"
        :class="{ 'nickname-result--success': nicknameStatus.available }"
      >
        <Check v-if="nicknameStatus.available" :size="15" />
        {{ nicknameStatus.message }}
      </p>

      <p v-if="authStore.errorMessage" class="form-error" role="alert">
        {{ authStore.errorMessage }}
      </p>

      <BaseButton native-type="submit" :disabled="authStore.isLoading">
        다음
      </BaseButton>

      <SocialLoginButtons />

      <p class="auth-form__switch">
        이미 계정이 있나요?
        <RouterLink to="/login">로그인</RouterLink>
      </p>
    </form>
  </AuthShell>
</template>

<style scoped>
@import '../assets/styles/auth-form.css';

.signup-form {
  gap: 10px;
}

.signup-form :deep(.base-button) {
  min-height: 50px;
  color: #fff;
  background: linear-gradient(135deg, #0b6cff 0%, #0757de 100%);
  border: 1px solid rgba(8, 82, 214, 0.24);
  border-radius: 16px;
  box-shadow: 0 16px 30px rgba(8, 73, 190, 0.26);
}

.signup-form :deep(.form-field p:not(.is-error)) {
  display: none;
}

.signup-form :deep(.social > p) {
  display: none;
}

.signup-form :deep(.social__buttons) {
  margin-top: 6px;
}

.signup-form :deep(.form-field) {
  gap: 5px;
}

.signup-form :deep(.form-field__control) {
  min-height: 44px;
  border-radius: 12px;
}

.signup-form :deep(.form-field input) {
  padding-block: 10px;
}

.signup-form :deep(.social__buttons button) {
  width: 34px;
  height: 34px;
  font-size: 15px;
}

.field-button {
  min-width: 68px;
  padding: 8px 9px;
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 800;
  background: var(--color-primary-soft);
  border-radius: var(--radius-small);
  cursor: pointer;
}

.field-button:disabled {
  cursor: wait;
  opacity: 0.6;
}

.nickname-result {
  display: flex;
  align-items: center;
  gap: 5px;
  margin: -5px 0 0;
  color: #d73c4e;
  font-size: 12px;
}

.nickname-result--success {
  color: var(--color-success);
}

.inline-error {
  margin: -8px 0 0;
  color: #d73c4e;
  font-size: 12px;
}
</style>
