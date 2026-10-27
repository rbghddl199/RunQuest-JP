<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { Bot, ChevronRight, MapPinned, Send, Sparkles } from '@lucide/vue'

import AppBottomNav from '../components/navigation/AppBottomNav.vue'
import { useChatStore } from '../stores/chat'
import { useRecommendationStore } from '../stores/recommendations'
import { getCourseImageForCourse } from '../utils/courseImages'

const chatStore = useChatStore()
const recommendationStore = useRecommendationStore()
const message = ref('')
const conversation = ref(null)
const hasTyped = ref(false)
const inputFocused = ref(false)

const quickPrompts = [
  { icon: '🌙', label: '야간에 안전한 코스', prompt: '야간에도 안전하게 뛸 수 있는 코스 추천해줘' },
  { icon: '🏃', label: '5km 코스 추천', prompt: '5km 정도로 달리기 좋은 코스 추천해줘' },
  { icon: '🌳', label: '조용한 공원 코스', prompt: '사람이 적고 조용한 공원 코스 있을까?' },
  { icon: '🔥', label: '운동 강도 높은 코스', prompt: '운동 강도를 높일 수 있는 코스 추천해줘' },
  { icon: '☺️', label: '가볍게 뛰고 싶어요', prompt: '오늘은 가볍게 3km만 뛰고 싶어' },
  { icon: '💪', label: '초보자에게 좋은 코스', prompt: '초보자가 뛰기 좋은 쉬운 코스 알려줘' },
]

const exampleQuestions = [
  '오늘은 가볍게 3km만 뛰고 싶어',
  '야간에도 안전한 코스 추천해줘',
  '사람이 적은 공원 코스 없을까?',
  '초보자가 뛰기 좋은 코스 알려줘',
]

const showStarter = computed(() => (
  !hasTyped.value
  && !inputFocused.value
  && !message.value.trim()
  && chatStore.messages.filter((item) => item.role === 'user').length === 0
))

async function scrollToBottom() {
  await nextTick()
  if (conversation.value) conversation.value.scrollTop = conversation.value.scrollHeight
}

async function send(content = message.value) {
  const trimmed = content.trim()
  if (!trimmed) return
  hasTyped.value = true
  message.value = ''
  const pendingReply = chatStore.send(trimmed)
  await scrollToBottom()
  const assistantMessage = await pendingReply
  if (assistantMessage?.recommended_course) {
    recommendationStore.applyChatRecommendation(assistantMessage)
  }
  await scrollToBottom()
}

function handleInput() {
  if (message.value.trim()) hasTyped.value = true
}

function providerNotice(item) {
  const provider = item.metadata?.provider
  if (provider === 'local_fallback') {
    return 'AI 연결이 지연되어 기본 추천 로직으로 안내했어요.'
  }
  if (provider === 'llm') {
    return ''
  }
  return ''
}

onMounted(async () => {
  await chatStore.loadConversation()
  await scrollToBottom()
})
</script>

<template>
  <main class="mobile-shell chat-page">
    <header class="chat-header">
      <RouterLink to="/recommendations">맞춤 추천</RouterLink>
      <span>AI 챗봇</span>
    </header>

    <section ref="conversation" class="conversation" aria-live="polite">
      <div class="bot-intro">
        <span><Bot :size="22" /></span>
        <div>
          <strong>RunQuest AI 챗봇</strong>
          <p>
            오늘 컨디션이나 원하는 러닝 스타일을 알려주시면
            맞춤 코스를 추천해드릴게요!
          </p>
          <small>
            <MapPinned :size="14" />
            추천 코스는 상세 페이지에서 지도 확인 후 적용할 수 있어요.
          </small>
        </div>
      </div>

      <section v-if="showStarter" class="starter-panel">
        <h2>무엇을 찾고 계신가요?</h2>
        <div class="quick-grid">
          <button
            v-for="prompt in quickPrompts"
            :key="prompt.label"
            type="button"
            @click="send(prompt.prompt)"
          >
            <span>{{ prompt.icon }}</span>
            {{ prompt.label }}
          </button>
        </div>

        <div class="examples">
          <h3>예시 질문</h3>
          <button
            v-for="question in exampleQuestions"
            :key="question"
            type="button"
            @click="send(question)"
          >
            “{{ question }}”
          </button>
        </div>
      </section>

      <template v-for="item in chatStore.messages" :key="item.id">
        <div class="message-row" :class="`is-${item.role}`">
          <span v-if="item.role === 'assistant'" class="bot-avatar"><Bot :size="17" /></span>
          <div class="bubble">
            <p>{{ item.content }}</p>
            <em v-if="providerNotice(item)" class="provider-notice">{{ providerNotice(item) }}</em>
            <small>{{ new Date(item.created_at).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }) }}</small>
          </div>
        </div>

        <article v-if="item.recommended_course" class="chat-course">
          <div class="chat-course__image">
            <img :src="getCourseImageForCourse(item.recommended_course)" :alt="item.recommended_course.name" />
            <span><Sparkles :size="13" /> AI 추천 코스</span>
          </div>
          <div class="chat-course__body">
            <h2>{{ item.recommended_course.name }}</h2>
            <p>
              {{ item.recommended_course.distance_km }}km ·
              약 {{ item.recommended_course.estimated_minutes }}분 ·
              {{ item.recommended_course.difficulty_label }}
            </p>
            <div class="features">
              <span>난이도 <strong>{{ item.recommended_course.difficulty_label }}</strong></span>
              <span>지형 <strong>{{ item.recommended_course.course_type_label }}</strong></span>
              <span>혼잡도 <strong>{{ item.recommended_course.crowd_level }}</strong></span>
            </div>
            <div v-if="item.metadata.reasons?.length" class="reason-box">
              <strong>왜 추천했나요?</strong>
              <ul>
                <li v-for="reason in item.metadata.reasons" :key="reason">{{ reason }}</li>
              </ul>
            </div>
            <RouterLink :to="`/courses/${item.recommended_course.slug}`">
              코스 상세 페이지 보기 <ChevronRight :size="17" />
            </RouterLink>
          </div>
        </article>
      </template>

      <div v-if="chatStore.isSending" class="typing">
        <span><Bot :size="17" /></span><i></i><i></i><i></i>
      </div>
      <p v-if="chatStore.errorMessage" class="chat-error">{{ chatStore.errorMessage }}</p>
    </section>

    <form class="chat-input" @submit.prevent="send()">
      <input
        v-model="message"
        maxlength="500"
        placeholder="메시지를 입력하세요..."
        aria-label="챗봇 메시지"
        @input="handleInput"
        @focus="inputFocused = true"
        @blur="inputFocused = false"
      />
      <button type="submit" :disabled="!message.trim() || chatStore.isSending" aria-label="메시지 전송">
        <Send :size="20" />
      </button>
    </form>
    <AppBottomNav />
  </main>
</template>

<style scoped>
.chat-page {
  display: grid;
  height: 100vh;
  min-height: 640px;
  grid-template-rows: auto minmax(0, 1fr) auto auto;
  padding-bottom: 0;
  background: #f5f8fc;
}

.chat-header {
  display: grid;
  grid-template-columns: 1fr 1fr;
  padding: 18px 18px 0;
  background: #fff;
  border-bottom: 1px solid #dbe4f0;
}

.chat-header a,
.chat-header span {
  display: grid;
  min-height: 48px;
  place-items: center;
  color: #687285;
  font-size: 15px;
  font-weight: 800;
}

.chat-header span {
  color: #0b6cff;
  border-bottom: 2px solid #0b6cff;
}

.conversation {
  overflow-y: auto;
  padding: 18px 16px 18px;
  scroll-behavior: smooth;
}

.bot-intro {
  display: grid;
  grid-template-columns: 42px 1fr;
  gap: 10px;
}

.bot-intro > span,
.bot-avatar,
.typing > span {
  display: grid;
  place-items: center;
  color: #0b6cff;
  background: #eaf3ff;
  border-radius: 50%;
}

.bot-intro > span {
  width: 42px;
  height: 42px;
}

.bot-intro strong {
  color: #0f172a;
  font-size: 15px;
}

.bot-intro p {
  margin: 9px 0 8px;
  color: #334155;
  font-size: 12px;
  line-height: 1.55;
}

.bot-intro small {
  display: flex;
  align-items: flex-start;
  gap: 5px;
  max-width: 100%;
  padding: 8px 9px;
  color: #0b6cff;
  background: #f0f6ff;
  border-radius: 10px;
  font-size: 10px;
  line-height: 1.5;
}

.starter-panel {
  margin-top: 30px;
}

.starter-panel h2 {
  margin: 0 0 14px;
  color: #111827;
  font-size: 18px;
}

.quick-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.quick-grid button {
  display: flex;
  min-height: 58px;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px;
  color: #1f2937;
  background: #fff;
  border: 1px solid #dbe4f0;
  border-radius: 13px;
  font-size: 13px;
  font-weight: 800;
}

.quick-grid span {
  font-size: 18px;
}

.examples {
  margin-top: 28px;
  padding: 16px 14px;
  background: #fff;
  border: 1px solid #dbe4f0;
  border-radius: 14px;
}

.examples h3 {
  margin: 0 0 9px;
  color: #111827;
  font-size: 13px;
}

.examples button {
  display: block;
  width: max-content;
  max-width: 100%;
  margin-top: 8px;
  padding: 7px 10px;
  color: #586376;
  background: #f8fafc;
  border: 1px solid #edf2f7;
  border-radius: 9px;
  font-size: 11px;
  text-align: left;
}

.message-row {
  display: flex;
  align-items: flex-end;
  gap: 7px;
  margin-top: 12px;
}

.message-row.is-user {
  justify-content: flex-end;
}

.bot-avatar {
  width: 28px;
  height: 28px;
  flex: 0 0 auto;
}

.bubble {
  max-width: 80%;
  padding: 9px 11px 7px;
  color: #182235;
  background: #fff;
  border: 1px solid #d8e2ee;
  border-radius: 12px 12px 12px 4px;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
}

.is-user .bubble {
  color: #fff;
  background: #075ee8;
  border-color: #075ee8;
  border-radius: 12px 12px 4px 12px;
  box-shadow: 0 6px 16px rgba(11, 108, 255, 0.16);
}

.bubble p {
  margin: 0;
  font-size: 12px;
  font-weight: 650;
  line-height: 1.55;
  white-space: pre-wrap;
}

.provider-notice {
  display: block;
  margin-top: 6px;
  color: #64748b;
  font-size: 9px;
  font-style: normal;
  font-weight: 700;
  line-height: 1.35;
}

.bubble small {
  display: block;
  margin-top: 3px;
  color: #94a3b8;
  font-size: 8px;
  text-align: right;
}

.is-user .bubble small {
  color: rgba(255, 255, 255, 0.72);
}

.chat-course {
  width: min(76%, 276px);
  margin: 8px 0 0 35px;
  overflow: hidden;
  background: #fff;
  border: 1px solid #d8e2ee;
  border-radius: 12px;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.07);
}

.chat-course__image {
  position: relative;
  aspect-ratio: 16 / 5.6;
}

.chat-course__image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.chat-course__image span {
  position: absolute;
  top: 8px;
  left: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 7px;
  color: #fff;
  background: #0b6cff;
  border-radius: 999px;
  font-size: 8px;
  font-weight: 900;
}

.chat-course__body {
  padding: 10px;
}

.chat-course h2 {
  margin: 0;
  color: #0f172a;
  font-size: 14px;
  line-height: 1.3;
}

.chat-course__body > p {
  margin: 4px 0 0;
  color: #64748b;
  font-size: 10px;
  font-weight: 700;
}

.features {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  margin-top: 8px;
  padding: 7px 0;
  background: #f8fbff;
  border-radius: 9px;
}

.features span {
  display: grid;
  gap: 3px;
  color: #7b8493;
  font-size: 8px;
  text-align: center;
}

.features span + span {
  border-left: 1px solid #dbe4f0;
}

.features strong {
  color: #0f172a;
  font-size: 9px;
}

.reason-box {
  margin-top: 9px;
  padding: 8px;
  max-height: 78px;
  overflow-y: auto;
  color: #1e4f94;
  background: #f0f6ff;
  border-radius: 9px;
  scrollbar-width: none;
}

.reason-box::-webkit-scrollbar {
  display: none;
}

.reason-box strong {
  font-size: 10px;
}

.reason-box ul {
  display: grid;
  gap: 3px;
  margin: 5px 0 0;
  padding: 0;
  list-style: none;
}

.reason-box li {
  font-size: 9px;
  line-height: 1.4;
}

.reason-box li::before {
  content: '✓ ';
  color: #18a35b;
  font-weight: 900;
}

.chat-course a {
  display: flex;
  min-height: 34px;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-top: 8px;
  color: #fff;
  font-size: 11px;
  font-weight: 900;
  background: #075ee8;
  border-radius: 9px;
}

.typing {
  display: flex;
  width: max-content;
  align-items: center;
  gap: 4px;
  margin-top: 16px;
  padding: 7px 10px 7px 7px;
  background: #fff;
  border: 1px solid #dbe4f0;
  border-radius: 18px;
}

.typing > span {
  width: 25px;
  height: 25px;
}

.typing i {
  width: 5px;
  height: 5px;
  background: #8390a4;
  border-radius: 50%;
  animation: pulse 1s infinite alternate;
}

.typing i:nth-child(3) {
  animation-delay: .2s;
}

.typing i:nth-child(4) {
  animation-delay: .4s;
}

.chat-error {
  color: #d73c55;
  font-size: 11px;
  text-align: center;
}

.chat-input {
  display: grid;
  grid-template-columns: 1fr 46px;
  gap: 8px;
  padding: 10px 16px;
  background: #fff;
  border-top: 1px solid #e8eef7;
}

.chat-input input {
  min-width: 0;
  min-height: 46px;
  padding: 0 14px;
  color: #0f172a;
  border: 1px solid #dbe4f0;
  border-radius: 14px;
  outline: 0;
  font-size: 13px;
  font-weight: 650;
}

.chat-input input:focus {
  border-color: #0b6cff;
}

.chat-input button {
  display: grid;
  width: 46px;
  height: 46px;
  place-items: center;
  color: #fff;
  background: #075ee8;
  border-radius: 50%;
}

.chat-input button:disabled {
  background: #b4c0d0;
}

@keyframes pulse {
  to {
    opacity: .3;
    transform: translateY(-2px);
  }
}

@media (min-width: 768px) {
  .chat-page {
    height: min(900px, calc(100vh - 32px));
  }
}
</style>
