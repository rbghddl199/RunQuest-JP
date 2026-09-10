import { createRouter, createWebHistory } from 'vue-router'

import AttendanceView from '../views/AttendanceView.vue'
import BadgeCollectionView from '../views/BadgeCollectionView.vue'
import BadgeDetailView from '../views/BadgeDetailView.vue'
import ChatView from '../views/ChatView.vue'
import CommunityDetailView from '../views/CommunityDetailView.vue'
import CommunityView from '../views/CommunityView.vue'
import CommunityWriteView from '../views/CommunityWriteView.vue'
import CourseDetailView from '../views/CourseDetailView.vue'
import CourseBuilderView from '../views/CourseBuilderView.vue'
import CourseListView from '../views/CourseListView.vue'
import CustomCourseDetailView from '../views/CustomCourseDetailView.vue'
import FavoriteCoursesView from '../views/FavoriteCoursesView.vue'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import MyPageView from '../views/MyPageView.vue'
import MyCoursesView from '../views/MyCoursesView.vue'
import NotificationsView from '../views/NotificationsView.vue'
import RecommendationView from '../views/RecommendationView.vue'
import RunActiveView from '../views/RunActiveView.vue'
import RunCompletedView from '../views/RunCompletedView.vue'
import RunStartView from '../views/RunStartView.vue'
import RunningRecordsView from '../views/RunningRecordsView.vue'
import SavedPostsView from '../views/SavedPostsView.vue'
import SettingsView from '../views/SettingsView.vue'
import SignupView from '../views/SignupView.vue'
import SignupTermsConsentView from '../views/SignupTermsConsentView.vue'
import SignupTermsView from '../views/SignupTermsView.vue'
import { useAuthStore } from '../stores/auth'
import SplashView from '../views/SplashView.vue'
import SurveyResultView from '../views/SurveyResultView.vue'
import SurveyView from '../views/SurveyView.vue'
import SystemCheckView from '../views/SystemCheckView.vue'
import WelcomeView from '../views/WelcomeView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'splash',
      component: SplashView,
      alias: '/splash',
    },
    {
      path: '/welcome',
      name: 'welcome',
      component: WelcomeView,
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/signup',
      name: 'signup',
      component: SignupView,
    },
    {
      path: '/signup/terms',
      name: 'signup-terms',
      component: SignupTermsView,
    },
    {
      path: '/signup/terms-consent',
      name: 'signup-terms-consent',
      component: SignupTermsConsentView,
    },
    {
      path: '/survey',
      name: 'survey',
      component: SurveyView,
      meta: { requiresAuth: true },
    },
    {
      path: '/survey/result',
      name: 'survey-result',
      component: SurveyResultView,
      meta: { requiresAuth: true },
    },
    {
      path: '/home',
      name: 'home',
      component: HomeView,
      meta: { requiresAuth: true },
      props: {
        eyebrow: 'RUNQUEST',
        title: '메인 페이지',
        description: '설문을 완료한 사용자가 진입할 메인 화면입니다.',
      },
    },
    {
      path: '/courses',
      name: 'courses',
      component: CourseListView,
      meta: { requiresAuth: true },
    },
    {
      path: '/recommendations',
      name: 'recommendations',
      component: RecommendationView,
      meta: { requiresAuth: true },
    },
    {
      path: '/chat',
      name: 'chat',
      component: ChatView,
      meta: { requiresAuth: true },
      props: {
        eyebrow: 'AI CHAT',
        title: 'RunQuest AI 챗봇',
        description: '챗봇 구현 단계에서 대화형 코스 추천을 연결합니다.',
      },
    },
    {
      path: '/courses/:slug',
      name: 'course-detail',
      component: CourseDetailView,
      meta: { requiresAuth: true },
    },
    {
      path: '/run/start',
      name: 'run-start',
      component: RunStartView,
      meta: { requiresAuth: true },
    },
    {
      path: '/run/active',
      name: 'run-active',
      component: RunActiveView,
      meta: { requiresAuth: true },
    },
    {
      path: '/run/completed/:id',
      name: 'run-completed',
      component: RunCompletedView,
      meta: { requiresAuth: true },
    },
    {
      path: '/community',
      name: 'community',
      component: CommunityView,
      meta: { requiresAuth: true },
      props: {
        eyebrow: 'RUNQUEST',
        title: '커뮤니티',
        description: '커뮤니티 구현 단계에서 게시글과 댓글을 연결합니다.',
      },
    },
    {
      path: '/community/write',
      name: 'community-write',
      component: CommunityWriteView,
      meta: { requiresAuth: true },
    },
    {
      path: '/community/:id',
      name: 'community-detail',
      component: CommunityDetailView,
      meta: { requiresAuth: true },
    },
    {
      path: '/my',
      name: 'my-page',
      component: MyPageView,
      meta: { requiresAuth: true },
      props: {
        eyebrow: 'RUNQUEST',
        title: '마이페이지',
        description: '러닝 기록과 배지, 출석 정보를 표시할 화면입니다.',
      },
    },
    {
      path: '/my/records',
      name: 'my-records',
      component: RunningRecordsView,
      meta: { requiresAuth: true },
    },
    {
      path: '/my/courses',
      name: 'my-courses',
      component: MyCoursesView,
      meta: { requiresAuth: true },
    },
    {
      path: '/my/courses/new',
      name: 'my-course-new',
      component: CourseBuilderView,
      meta: { requiresAuth: true },
    },
    {
      path: '/my/courses/:id',
      name: 'my-course-detail',
      component: CustomCourseDetailView,
      meta: { requiresAuth: true },
    },
    {
      path: '/my/favorites',
      name: 'my-favorites',
      component: FavoriteCoursesView,
      meta: { requiresAuth: true },
    },
    {
      path: '/my/saved-posts',
      name: 'my-saved-posts',
      component: SavedPostsView,
      meta: { requiresAuth: true },
    },
    {
      path: '/my/attendance',
      name: 'my-attendance',
      component: AttendanceView,
      meta: { requiresAuth: true },
    },
    {
      path: '/my/badges',
      name: 'my-badges',
      component: BadgeCollectionView,
      meta: { requiresAuth: true },
    },
    {
      path: '/my/badges/:code',
      name: 'my-badge-detail',
      component: BadgeDetailView,
      meta: { requiresAuth: true },
    },
    {
      path: '/my/settings',
      name: 'my-settings',
      component: SettingsView,
      meta: { requiresAuth: true },
    },
    {
      path: '/notifications',
      name: 'notifications',
      component: NotificationsView,
      meta: { requiresAuth: true },
    },
    {
      path: '/dev/system',
      name: 'system-check',
      component: SystemCheckView,
    },
  ],
})

router.beforeEach(async (to) => {
  if (!to.meta.requiresAuth) return true

  const authStore = useAuthStore()
  await authStore.restoreSession()

  if (!authStore.isAuthenticated) {
    return {
      name: 'login',
      query: { redirect: to.fullPath },
    }
  }

  return true
})

export default router
