import { useCallback, useEffect, useMemo, useState } from 'react'
import AuthContext from './authContextValue'
import api from '../services/api'

function readUser() {
  try {
    return JSON.parse(window.localStorage.getItem('furninest-user') || 'null')
  } catch {
    return null
  }
}

function saveSession(data) {
  window.localStorage.setItem('furninest-access', data.access)
  window.localStorage.setItem('furninest-refresh', data.refresh)
  window.localStorage.setItem('furninest-user', JSON.stringify(data.user))
  return data.user
}

function clearSession() {
  window.localStorage.removeItem('furninest-access')
  window.localStorage.removeItem('furninest-refresh')
  window.localStorage.removeItem('furninest-user')
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(readUser)

  const expireSession = useCallback(() => {
    clearSession()
    setUser(null)
  }, [])

  useEffect(() => {
    window.addEventListener('furninest:session-expired', expireSession)
    return () => window.removeEventListener('furninest:session-expired', expireSession)
  }, [expireSession])

  const login = useCallback(async (email, password) => {
    const { data } = await api.post('/auth/login/', { email, password })
    const authenticatedUser = saveSession(data)
    setUser(authenticatedUser)
    return authenticatedUser
  }, [])

  const register = useCallback(async (values) => {
    const { data } = await api.post('/auth/register/', values)
    return data
  }, [])

  const logout = useCallback(async () => {
    const refresh = window.localStorage.getItem('furninest-refresh')
    try {
      if (refresh) await api.post('/auth/logout/', { refresh })
    } finally {
      clearSession()
      setUser(null)
    }
  }, [])

  const refreshProfile = useCallback(async () => {
    const { data } = await api.get('/profile/')
    setUser((current) => {
      const updated = { ...current, ...data }
      window.localStorage.setItem('furninest-user', JSON.stringify(updated))
      return updated
    })
    return data
  }, [])

  const value = useMemo(
    () => ({ user, isAuthenticated: Boolean(user), login, register, logout, refreshProfile }),
    [user, login, register, logout, refreshProfile],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
