import { defineStore } from 'pinia'

const STORAGE_KEY = 'runquest_theme'
const THEME_VALUES = ['system', 'light', 'dark']

function readStoredTheme() {
  const stored = localStorage.getItem(STORAGE_KEY)
  return THEME_VALUES.includes(stored) ? stored : 'system'
}

function resolveTheme(preference) {
  if (preference !== 'system') return preference
  return window.matchMedia('(prefers-color-scheme: dark)').matches
    ? 'dark'
    : 'light'
}

export const useThemeStore = defineStore('theme', {
  state: () => ({
    preference: readStoredTheme(),
    resolvedTheme: 'light',
    mediaQuery: null,
  }),
  actions: {
    applyTheme() {
      this.resolvedTheme = resolveTheme(this.preference)
      document.documentElement.dataset.theme = this.resolvedTheme
      document.documentElement.style.colorScheme = this.resolvedTheme
    },
    setTheme(preference) {
      if (!THEME_VALUES.includes(preference)) return
      this.preference = preference
      localStorage.setItem(STORAGE_KEY, preference)
      this.applyTheme()
    },
    initialize() {
      this.applyTheme()
      if (this.mediaQuery) return

      this.mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      this.mediaQuery.addEventListener('change', () => {
        if (this.preference === 'system') this.applyTheme()
      })
    },
  },
})
