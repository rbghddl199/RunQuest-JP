<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowLeft,
  Bell,
  CheckCircle2,
  ChevronRight,
  Eye,
  EyeOff,
  FileText,
  LockKeyhole,
  LogOut,
  UserRound,
} from '@lucide/vue'

import AppState from '../components/common/AppState.vue'
import { useAuthStore } from '../stores/auth'
import { useSettingsStore } from '../stores/settings'
import {
  clearStoredProfileAvatar,
  fileToProfileAvatar,
  getStoredProfileAvatar,
  saveStoredProfileAvatar,
} from '../utils/profileAvatar'

const router = useRouter()
const authStore = useAuthStore()
const settingsStore = useSettingsStore()

const form = reactive({
  nickname: '',
  push_notifications: true,
  recommendation_notifications: true,
  community_notifications: true,
  marketing_notifications: false,
  distance_unit: 'km',
  temperature_unit: 'c',
  profile_visibility: 'members',
  show_running_records: true,
})
const passwordForm = reactive({
  current_password: '',
  new_password: '',
  confirm_password: '',
})
const nicknameStatus = reactive({
  checked: false,
  available: false,
  loading: false,
  message: '',
})

const originalNickname = ref('')
const passwordOpen = ref(false)
const showCurrentPassword = ref(false)
const showNewPassword = ref(false)
const localError = ref('')
const profileImageInput = ref(null)
const profileImagePreview = ref('')
const openSection = ref('account')

const nicknameChanged = computed(() => form.nickname.trim() !== originalNickname.value)
const canSave = computed(() => {
  if (form.nickname.trim().length < 2) return false
  if (nicknameChanged.value && !nicknameStatus.available) return false
  return true
})

watch(
  () => form.nickname,
  () => {
    nicknameStatus.checked = false
    nicknameStatus.available = !nicknameChanged.value
    nicknameStatus.message = ''
  },
)

function applySettings(settings) {
  Object.keys(form).forEach((key) => {
    form[key] = settings[key]
  })
  originalNickname.value = settings.nickname
  nicknameStatus.available = true
}

async function checkNickname() {
  localError.value = ''
  const nickname = form.nickname.trim()
  if (!nicknameChanged.value) {
    nicknameStatus.checked = true
    nicknameStatus.available = true
    nicknameStatus.message = '현재 사용 중인 닉네임이에요.'
    return
  }
  if (nickname.length < 2 || nickname.length > 12) {
    nicknameStatus.checked = true
    nicknameStatus.available = false
    nicknameStatus.message = '닉네임은 2~12자로 입력해 주세요.'
    return
  }
  nicknameStatus.loading = true
  try {
    const result = await authStore.checkNickname(nickname)
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

async function save() {
  localError.value = ''
  if (nicknameChanged.value && !nicknameStatus.available) {
    localError.value = '닉네임 중복 확인을 먼저 진행해 주세요.'
    return
  }
  try {
    const saved = await settingsStore.saveSettings({
      ...form,
      nickname: form.nickname.trim(),
    })
    applySettings(saved)
  } catch {
    // Store exposes the server message.
  }
}

async function chooseProfileImage(event) {
  localError.value = ''
  const file = event.target.files?.[0]
  if (!file) return
  try {
    const dataUrl = await fileToProfileAvatar(file)
    const key = settingsStore.settings?.email ?? authStore.user?.email
    saveStoredProfileAvatar(key, dataUrl)
    if (authStore.user?.id) saveStoredProfileAvatar(authStore.user.id, dataUrl)
    profileImagePreview.value = dataUrl
  } catch (error) {
    localError.value = error.message
  } finally {
    event.target.value = ''
  }
}

function removeProfileImage() {
  const key = settingsStore.settings?.email ?? authStore.user?.email
  clearStoredProfileAvatar(key)
  if (authStore.user?.id) clearStoredProfileAvatar(authStore.user.id)
  profileImagePreview.value = ''
}

async function changePassword() {
  localError.value = ''
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    localError.value = '새 비밀번호가 서로 일치하지 않습니다.'
    return
  }
  try {
    await settingsStore.changePassword({
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password,
    })
    passwordForm.current_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
    passwordOpen.value = false
  } catch {
    // Store exposes the server message.
  }
}

async function logout() {
  await authStore.logout()
  router.replace('/login')
}

onMounted(async () => {
  try {
    const settings = await settingsStore.loadSettings()
    applySettings(settings)
    profileImagePreview.value = getStoredProfileAvatar(settings.email) ?? ''
  } catch {
    // The page state renders the store error.
  }
})
</script>

<template>
  <main class="mobile-shell settings-page">
    <header class="settings-header">
      <RouterLink to="/my" aria-label="마이페이지로 돌아가기">
        <ArrowLeft :size="23" />
      </RouterLink>
      <h1>설정</h1>
      <span aria-hidden="true"></span>
    </header>

    <AppState
      v-if="settingsStore.isLoading"
      type="loading"
      title="설정을 불러오는 중입니다"
      message="프로필과 알림 설정을 확인하고 있어요."
    />

    <form v-else-if="settingsStore.settings" class="settings-content" @submit.prevent="save">
      <section class="settings-card" :class="{ 'is-open': openSection === 'account' }">
        <button type="button" class="section-heading" @click="openSection = openSection === 'account' ? '' : 'account'">
          <UserRound :size="19" />
          <div>
            <h2>계정</h2>
            <p>프로필과 로그인 정보를 관리해요.</p>
          </div>
          <ChevronRight :size="18" />
        </button>

        <div v-show="openSection === 'account'" class="settings-card__body">
        <div class="profile-image-field">
          <div class="profile-image-preview">
            <img v-if="profileImagePreview" :src="profileImagePreview" alt="프로필 이미지" />
            <UserRound v-else :size="30" />
          </div>
          <div>
            <strong>프로필 이미지</strong>
            <small>홈과 마이페이지에 표시돼요.</small>
            <div class="profile-image-actions">
              <button type="button" @click="profileImageInput?.click()">이미지 변경</button>
              <button type="button" :disabled="!profileImagePreview" @click="removeProfileImage">삭제</button>
            </div>
          </div>
          <input
            ref="profileImageInput"
            class="profile-image-input"
            type="file"
            accept="image/*"
            @change="chooseProfileImage"
          />
        </div>

        <label class="field">
          <span>이메일</span>
          <input :value="settingsStore.settings.email" disabled />
        </label>

        <div class="nickname-field">
          <label class="field">
            <span>닉네임</span>
            <input v-model="form.nickname" maxlength="12" placeholder="2~12자 닉네임" />
            <small>{{ form.nickname.length }}/12</small>
          </label>
          <button type="button" :disabled="nicknameStatus.loading || !nicknameChanged" @click="checkNickname">
            {{ nicknameStatus.loading ? '확인 중' : '중복확인' }}
          </button>
        </div>
        <p
          v-if="nicknameStatus.checked"
          class="nickname-result"
          :class="{ 'nickname-result--success': nicknameStatus.available }"
        >
          <CheckCircle2 v-if="nicknameStatus.available" :size="14" />
          {{ nicknameStatus.message }}
        </p>

        <div class="account-actions">
          <button type="button" @click="passwordOpen = !passwordOpen">
            <LockKeyhole :size="18" />
            <span>비밀번호 변경</span>
            <ChevronRight :size="17" :class="{ rotated: passwordOpen }" />
          </button>

          <div v-if="passwordOpen" class="password-form">
            <label class="field">
              <span>현재 비밀번호</span>
              <div class="password-input">
                <input
                  v-model="passwordForm.current_password"
                  :type="showCurrentPassword ? 'text' : 'password'"
                  autocomplete="current-password"
                />
                <button
                  type="button"
                  :aria-label="showCurrentPassword ? '현재 비밀번호 숨기기' : '현재 비밀번호 보기'"
                  @click="showCurrentPassword = !showCurrentPassword"
                >
                  <EyeOff v-if="showCurrentPassword" :size="18" />
                  <Eye v-else :size="18" />
                </button>
              </div>
            </label>
            <label class="field">
              <span>새 비밀번호</span>
              <div class="password-input">
                <input
                  v-model="passwordForm.new_password"
                  :type="showNewPassword ? 'text' : 'password'"
                  autocomplete="new-password"
                />
                <button
                  type="button"
                  :aria-label="showNewPassword ? '새 비밀번호 숨기기' : '새 비밀번호 보기'"
                  @click="showNewPassword = !showNewPassword"
                >
                  <EyeOff v-if="showNewPassword" :size="18" />
                  <Eye v-else :size="18" />
                </button>
              </div>
            </label>
            <label class="field">
              <span>새 비밀번호 확인</span>
              <input v-model="passwordForm.confirm_password" type="password" autocomplete="new-password" />
            </label>
            <button class="secondary-button" type="button" :disabled="settingsStore.isSaving" @click="changePassword">
              비밀번호 변경
            </button>
          </div>

          <button class="logout-button" type="button" @click="logout">
            <LogOut :size="18" />
            <span>로그아웃</span>
            <ChevronRight :size="17" />
          </button>
        </div>
        </div>
      </section>

      <section class="settings-card" :class="{ 'is-open': openSection === 'notifications' }">
        <button type="button" class="section-heading" @click="openSection = openSection === 'notifications' ? '' : 'notifications'">
          <Bell :size="19" />
          <div>
            <h2>알림</h2>
            <p>필요한 소식만 받을 수 있어요.</p>
          </div>
          <ChevronRight :size="18" />
        </button>
        <div v-show="openSection === 'notifications'" class="settings-card__body">
        <div class="switch-list">
          <label class="switch-row">
            <span><strong>전체 알림</strong><small>RunQuest 알림을 허용합니다.</small></span>
            <input v-model="form.push_notifications" type="checkbox" />
            <i aria-hidden="true"></i>
          </label>
          <label class="switch-row">
            <span><strong>맞춤 추천</strong><small>오늘의 코스와 주간 미션 알림</small></span>
            <input v-model="form.recommendation_notifications" type="checkbox" :disabled="!form.push_notifications" />
            <i aria-hidden="true"></i>
          </label>
          <label class="switch-row">
            <span><strong>커뮤니티</strong><small>댓글, 좋아요, 저장 반응 알림</small></span>
            <input v-model="form.community_notifications" type="checkbox" :disabled="!form.push_notifications" />
            <i aria-hidden="true"></i>
          </label>
          <label class="switch-row">
            <span><strong>이벤트 정보</strong><small>업데이트와 챌린지 소식</small></span>
            <input v-model="form.marketing_notifications" type="checkbox" :disabled="!form.push_notifications" />
            <i aria-hidden="true"></i>
          </label>
        </div>
        </div>
      </section>

      <section class="settings-card" :class="{ 'is-open': openSection === 'terms' }">
        <button type="button" class="section-heading" @click="openSection = openSection === 'terms' ? '' : 'terms'">
          <FileText :size="19" />
          <div>
            <h2>이용약관</h2>
            <p>서비스 이용에 필요한 기준을 확인해요.</p>
          </div>
          <ChevronRight :size="18" />
        </button>
        <div v-show="openSection === 'terms'" class="settings-card__body">
        <div class="terms-card">
          <article>
            <strong>서비스 이용</strong>
            <p>RunQuest는 러닝 기록, 코스 추천, 커뮤니티 기능을 제공해요. 실제 러닝 전 안전과 건강 상태는 직접 확인해야 합니다.</p>
          </article>
          <article>
            <strong>위치 및 러닝 기록</strong>
            <p>위치 정보와 러닝 기록은 코스 추천, 기록 저장, 통계 계산에 사용돼요. 브라우저 권한에 따라 일부 기능이 제한될 수 있습니다.</p>
          </article>
          <article>
            <strong>커뮤니티 이용</strong>
            <p>게시글과 댓글은 다른 러너에게 공개될 수 있어요. 개인정보, 부적절한 표현, 타인의 권리를 침해하는 내용은 등록하지 않아야 합니다.</p>
          </article>
          <article>
            <strong>알림 및 마케팅</strong>
            <p>추천, 커뮤니티, 이벤트 알림은 설정에서 언제든지 켜고 끌 수 있어요.</p>
          </article>
        </div>
        </div>
      </section>

      <p v-if="localError || settingsStore.errorMessage" class="message message--error">
        {{ localError || settingsStore.errorMessage }}
      </p>
      <p v-else-if="settingsStore.successMessage" class="message message--success">
        {{ settingsStore.successMessage }}
      </p>

      <button class="primary-button" type="submit" :disabled="!canSave || settingsStore.isSaving">
        {{ settingsStore.isSaving ? '저장 중...' : '변경사항 저장' }}
      </button>
    </form>

    <AppState
      v-else
      type="error"
      title="설정을 불러오지 못했어요"
      :message="settingsStore.errorMessage"
      action-label="다시 시도"
      @action="settingsStore.loadSettings"
    />
  </main>
</template>

<style scoped>
.settings-page { display:flex; height:var(--app-height); min-height:var(--app-height); flex-direction:column; overflow:hidden; background:#f5f9ff; }
.settings-header { position:sticky; z-index:5; top:0; display:grid; height:64px; flex:0 0 auto; grid-template-columns:44px 1fr 44px; align-items:center; padding:0 14px; background:rgba(255,255,255,.97); border-bottom:1px solid var(--color-border); }
.settings-header a { display:grid; width:40px; height:40px; place-items:center; color:var(--color-navy); }
.settings-header h1 { margin:0; color:var(--color-navy); font-size:18px; text-align:center; }
.settings-content { flex:1 1 auto; min-height:0; padding:14px var(--content-padding) 18px; overflow-y:auto; scrollbar-width:none; }
.settings-content::-webkit-scrollbar { display:none; }
.settings-card { display:grid; gap:0; margin-bottom:10px; padding:0; overflow:hidden; background:#fff; border:1px solid var(--color-border); border-radius:var(--card-radius); box-shadow:0 10px 24px rgba(15,23,42,.05); }
.settings-card.is-open { gap:12px; padding-bottom:var(--card-padding); }
.settings-card__body { display:grid; gap:13px; padding:0 var(--card-padding); }
.section-heading { display:grid; width:100%; grid-template-columns:22px minmax(0,1fr) 18px; align-items:flex-start; gap:10px; padding:var(--card-padding); color:inherit; background:transparent; text-align:left; }
.section-heading > svg { flex:0 0 auto; margin-top:2px; color:var(--color-primary); }
.section-heading > svg:last-child { margin-top:1px; color:var(--color-muted); transition:transform 180ms ease; }
.settings-card.is-open .section-heading > svg:last-child { transform:rotate(90deg); }
.section-heading h2,.section-heading p { margin:0; }
.section-heading h2 { color:var(--color-navy); font-size:var(--section-title-size); }
.section-heading p { margin-top:3px; color:var(--color-muted); font-size:10px; }
.profile-image-field { position:relative; display:grid; grid-template-columns:60px 1fr; gap:12px; align-items:center; padding:11px; background:#f7faff; border:1px solid var(--color-border); border-radius:var(--card-radius); }
.profile-image-preview { display:grid; width:60px; height:60px; overflow:hidden; place-items:center; color:var(--color-primary); background:var(--color-primary-soft); border-radius:50%; }
.profile-image-preview img { width:100%; height:100%; object-fit:cover; }
.profile-image-field strong { display:block; color:var(--color-navy); font-size:13px; }
.profile-image-field small { display:block; margin-top:3px; color:var(--color-muted); font-size:10px; }
.profile-image-actions { display:flex; flex-wrap:wrap; gap:6px; margin-top:9px; }
.profile-image-actions button { min-height:31px; padding:0 9px; color:#fff; background:var(--color-primary); border-radius:7px; font-size:10px; font-weight:800; }
.profile-image-actions button + button { color:var(--color-muted); background:#eef3fa; }
.profile-image-actions button:disabled { opacity:.45; }
.profile-image-input { position:absolute; width:1px; height:1px; opacity:0; pointer-events:none; }
.field { position:relative; display:grid; gap:6px; }
.field > span { color:var(--color-text); font-size:11px; font-weight:800; }
.field input { width:100%; height:43px; padding:0 12px; color:var(--color-navy); background:#fff; border:1px solid var(--color-border); border-radius:8px; outline:none; }
.field input:focus { border-color:var(--color-primary); box-shadow:0 0 0 3px var(--color-primary-soft); }
.field input:disabled { color:var(--color-muted); background:#edf2f8; }
.field > small { position:absolute; right:10px; bottom:13px; color:var(--color-muted); font-size:9px; }
.nickname-field { display:grid; grid-template-columns:minmax(0,1fr) 78px; align-items:end; gap:8px; }
.nickname-field button { height:43px; color:#fff; background:var(--color-primary); border-radius:8px; font-size:11px; font-weight:900; }
.nickname-field button:disabled { color:var(--color-muted); background:#edf2f8; }
.nickname-result { display:flex; align-items:center; gap:5px; margin:-5px 0 0; color:#d64545; font-size:10px; font-weight:800; }
.nickname-result--success { color:#0a8a58; }
.account-actions { overflow:hidden; background:#f8fbff; border:1px solid var(--color-border); border-radius:var(--card-radius); }
.account-actions > button { display:grid; width:100%; min-height:50px; grid-template-columns:24px 1fr auto; align-items:center; gap:8px; padding:0 13px; color:var(--color-navy); background:transparent; text-align:left; }
.account-actions > button + button { border-top:1px solid var(--color-border); }
.account-actions > button svg:first-child { color:var(--color-primary); }
.account-actions .rotated { transform:rotate(90deg); }
.account-actions .logout-button { color:#c53b3b; }
.account-actions .logout-button svg:first-child { color:#c53b3b; }
.password-form { display:grid; gap:10px; padding:0 13px 14px; border-top:1px solid var(--color-border); }
.password-input { position:relative; }
.password-input input { padding-right:42px; }
.password-input button { position:absolute; top:2px; right:2px; display:grid; width:39px; height:39px; place-items:center; color:var(--color-muted); background:transparent; }
.switch-list { overflow:hidden; border:1px solid var(--color-border); border-radius:var(--card-radius); }
.switch-row { position:relative; display:flex; min-height:57px; align-items:center; justify-content:space-between; gap:13px; padding:0 12px; background:#fff; }
.switch-row + .switch-row { border-top:1px solid var(--color-border); }
.switch-row > span { display:grid; gap:3px; min-width:0; }
.switch-row strong { color:var(--color-navy); font-size:12px; }
.switch-row small { color:var(--color-muted); font-size:10px; line-height:1.35; }
.switch-row input { position:absolute; width:1px; height:1px; opacity:0; }
.switch-row i { position:relative; width:42px; height:24px; flex:0 0 42px; background:#cbd5e3; border-radius:12px; transition:.2s; }
.switch-row i::after { position:absolute; top:3px; left:3px; width:18px; height:18px; content:''; background:#fff; border-radius:50%; box-shadow:0 1px 4px rgba(16,33,61,.22); transition:.2s; }
.switch-row input:checked + i { background:var(--color-primary); }
.switch-row input:checked + i::after { transform:translateX(18px); }
.switch-row input:disabled + i { opacity:.45; }
.terms-card { display:grid; gap:0; overflow:hidden; background:#f8fbff; border:1px solid var(--color-border); border-radius:var(--card-radius); }
.terms-card article { display:grid; gap:4px; padding:12px; }
.terms-card article + article { border-top:1px solid var(--color-border); }
.terms-card strong { color:var(--color-navy); font-size:12px; }
.terms-card p { margin:0; color:var(--color-muted); font-size:10px; line-height:1.55; }
.message { margin:10px 0 0; padding:11px 13px; font-size:11px; border-radius:8px; }
.message--error { color:#b42318; background:#fff0ef; }
.message--success { color:#087a4f; background:#eaf9f2; }
.primary-button,.secondary-button { width:100%; height:48px; color:#fff; font-weight:900; background:var(--color-primary); border-radius:9px; }
.primary-button { margin:2px 0 10px; }
.primary-button:disabled,.secondary-button:disabled { opacity:.55; }
.secondary-button { height:43px; }
:global(:root[data-theme='dark']) .settings-card,
:global(:root[data-theme='dark']) .profile-image-field,
:global(:root[data-theme='dark']) .account-actions,
:global(:root[data-theme='dark']) .switch-list,
:global(:root[data-theme='dark']) .switch-row,
:global(:root[data-theme='dark']) .terms-card {
  color:var(--color-text);
  background:var(--color-surface);
  border-color:var(--color-border);
}
:global(:root[data-theme='dark']) .field input,
:global(:root[data-theme='dark']) .nickname-field button:disabled {
  color:var(--color-text);
  background:var(--color-input);
  border-color:var(--color-border);
}
</style>
