<script setup>
import { onMounted } from 'vue'

import { useAuthStore } from './stores/auth'
import { useSettingsStore } from './stores/settings'
import { useThemeStore } from './stores/theme'

const authStore = useAuthStore()
const settingsStore = useSettingsStore()
const themeStore = useThemeStore()

themeStore.initialize()

onMounted(async () => {
  await authStore.restoreSession()
  if (authStore.isAuthenticated) {
    settingsStore.loadSettings().catch(() => {})
  }
})
</script>

<template>
  <RouterView />
</template>
