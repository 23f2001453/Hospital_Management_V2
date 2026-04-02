import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const token = ref(localStorage.getItem('auth_token') || null)

  const isLoggedIn = computed(() => !!token.value)
  const role = computed(() => user.value?.role || null)
  const isAdmin = computed(() => role.value === 'admin')
  const isDoctor = computed(() => role.value === 'doctor')
  const isPatient = computed(() => role.value === 'patient')

  async function login(email, password) {
    const data = await api.login(email, password)
    token.value = data.auth_token
    user.value = data.user
    localStorage.setItem('auth_token', data.auth_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    return data.user
  }

  async function logout() {
    try { await api.logout() } catch (_) {}
    token.value = null
    user.value = null
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user')
  }

  async function fetchMe() {
    if (!token.value) return
    try {
      const data = await api.me()
      user.value = data.user
      localStorage.setItem('user', JSON.stringify(data.user))
    } catch (_) {
      await logout()
    }
  }

  return { user, token, isLoggedIn, role, isAdmin, isDoctor, isPatient, login, logout, fetchMe }
})
