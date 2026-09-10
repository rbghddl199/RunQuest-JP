import axios from 'axios'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api'

const api = axios.create({
  baseURL: apiBaseUrl,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

function getStoredToken(name) {
  return localStorage.getItem(name) ?? sessionStorage.getItem(name)
}

function setStoredAccessToken(token) {
  const storage = localStorage.getItem('runquest_refresh_token')
    ? localStorage
    : sessionStorage
  storage.setItem('runquest_access_token', token)
}

api.interceptors.request.use((config) => {
  const accessToken = getStoredToken('runquest_access_token')
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

let refreshPromise = null

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const refreshToken = getStoredToken('runquest_refresh_token')
    const isRefreshRequest = originalRequest?.url?.includes('/auth/token/refresh/')

    if (
      error.response?.status !== 401
      || !refreshToken
      || originalRequest?._retry
      || isRefreshRequest
    ) {
      return Promise.reject(error)
    }

    originalRequest._retry = true
    refreshPromise ??= axios
      .post(`${apiBaseUrl}/auth/token/refresh/`, { refresh: refreshToken })
      .then(({ data }) => {
        setStoredAccessToken(data.access)
        if (data.refresh) {
          const storage = localStorage.getItem('runquest_refresh_token')
            ? localStorage
            : sessionStorage
          storage.setItem('runquest_refresh_token', data.refresh)
        }
        return data.access
      })
      .finally(() => {
        refreshPromise = null
      })

    const accessToken = await refreshPromise
    originalRequest.headers.Authorization = `Bearer ${accessToken}`
    return api(originalRequest)
  },
)

export default api
