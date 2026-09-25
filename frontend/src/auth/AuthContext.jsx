import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { api } from '../api/client.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    async function restoreSession() {
      const access = localStorage.getItem('attendance.access')
      if (!access) {
        setLoading(false)
        return
      }
      try {
        const { data } = await api.get('/auth/me/')
        if (active) setUser(data)
      } catch {
        localStorage.removeItem('attendance.access')
        localStorage.removeItem('attendance.refresh')
      } finally {
        if (active) setLoading(false)
      }
    }
    restoreSession()
    const clearSession = () => {
      localStorage.removeItem('attendance.access')
      localStorage.removeItem('attendance.refresh')
      setUser(null)
    }
    window.addEventListener('attendance:unauthorized', clearSession)
    return () => {
      active = false
      window.removeEventListener('attendance:unauthorized', clearSession)
    }
  }, [])

  async function login(username, password) {
    const { data } = await api.post('/auth/token/', { username, password })
    localStorage.setItem('attendance.access', data.access)
    localStorage.setItem('attendance.refresh', data.refresh)
    setUser(data.user)
    return data.user
  }

  async function logout() {
    const refresh = localStorage.getItem('attendance.refresh')
    try {
      if (refresh) await api.post('/auth/logout/', { refresh })
    } finally {
      localStorage.removeItem('attendance.access')
      localStorage.removeItem('attendance.refresh')
      setUser(null)
    }
  }

  const value = useMemo(() => ({ user, loading, login, logout }), [user, loading])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}
