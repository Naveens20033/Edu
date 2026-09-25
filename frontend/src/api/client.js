import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const access = localStorage.getItem('attendance.access')
  if (access) config.headers.Authorization = `Bearer ${access}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    const refresh = localStorage.getItem('attendance.refresh')
    const isAuthEndpoint = /\/auth\/(token\/refresh|token|logout)\//.test(original?.url || '')
    if (error.response?.status === 401 && refresh && !original?._retried && !isAuthEndpoint) {
      original._retried = true
      try {
        const { data } = await axios.post(`${api.defaults.baseURL}/auth/token/refresh/`, { refresh })
        localStorage.setItem('attendance.access', data.access)
        if (data.refresh) localStorage.setItem('attendance.refresh', data.refresh)
        original.headers.Authorization = `Bearer ${data.access}`
        return api(original)
      } catch {
        localStorage.removeItem('attendance.access')
        localStorage.removeItem('attendance.refresh')
        window.dispatchEvent(new Event('attendance:unauthorized'))
      }
    }
    return Promise.reject(error)
  },
)

export function getApiError(error, fallback = 'Something went wrong. Please try again.') {
  const data = error?.response?.data
  if (typeof data?.detail === 'string') return data.detail
  if (data && typeof data === 'object') {
    const first = Object.values(data).flat(Infinity).find((value) => typeof value === 'string')
    if (first) return first
  }
  return fallback
}
