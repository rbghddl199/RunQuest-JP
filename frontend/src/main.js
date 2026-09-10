import { createApp } from 'vue'
import { createPinia } from 'pinia'

import './style.css'
import App from './App.vue'
import router from './router'
import { preloadKakaoMap } from './services/kakaoMap'

const shouldUseLocalhost = import.meta.env.DEV && window.location.hostname === '127.0.0.1'

if (shouldUseLocalhost) {
  const nextUrl = new URL(window.location.href)
  nextUrl.hostname = 'localhost'
  window.location.replace(nextUrl.toString())
} else {
  const app = createApp(App)

  app.use(createPinia())
  app.use(router)
  app.mount('#app')

  preloadKakaoMap()
}
