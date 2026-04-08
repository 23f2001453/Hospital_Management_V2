<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { roleDashboard } from '../router'

const router = useRouter()
const auth = useAuthStore()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function login() {
  if (!email.value || !password.value) {
    error.value = 'Please enter both email and password.'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const user = await auth.login(email.value, password.value)
    router.push(roleDashboard(user.role))
  } catch (e) {
    error.value = e.message || 'Login failed. Check your credentials.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-left">
      <div class="brand-block">
        <div class="brand-icon">✚</div>
        <h1 class="brand-title">MediCore</h1>
        <p class="brand-tagline">Name: Hospital Management System V2</p>
      </div>
      <div class="feature-list">
        <div class="feature-item" v-for="f in features" :key="f.title">
          <span class="feature-icon">{{ f.icon }}</span>
          <div>
            <div class="feature-title">{{ f.title }}</div>
            <div class="feature-desc">{{ f.desc }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="login-right">
      <div class="login-card">
        <div class="login-head">
          <h2 class="login-title">Welcome back</h2>
          <p class="login-sub">Sign in to your account</p>
        </div>

        <div v-if="error" class="alert alert-error">{{ error }}</div>

        <form @submit.prevent="login" class="login-form">
          <div class="form-group">
            <label class="form-label">Email address</label>
            <input
              type="email" class="form-control"
              v-model="email" placeholder="you@example.com"
              autocomplete="email"
            />
          </div>
          <div class="form-group">
            <label class="form-label">Password</label>
            <input
              type="password" class="form-control"
              v-model="password" placeholder="••••••••"
              autocomplete="current-password"
            />
          </div>

          <button type="submit" class="btn btn-primary login-submit" :disabled="loading">
            <span v-if="loading" class="spinner"></span>
            <span>{{ loading ? 'Signing in…' : 'Sign in' }}</span>
          </button>
        </form>

        <p class="login-footer">
          Don't have an account?
          <RouterLink to="/register">Create one</RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      features: [
        { icon: '📅', title: 'Smart Scheduling', desc: 'Manage availability slots and appointments effortlessly' },
        { icon: '💊', title: 'Treatment Records', desc: 'Secure diagnosis and prescription management' },
        { icon: '👥', title: 'Multi-role Access', desc: 'Separate dashboards for patients, doctors, and admins' },
      ]
    }
  }
}
</script>

<style scoped>
.login-page {
  display: flex; min-height: 100vh; width: 100%;
}

.login-left {
  flex: 1; 
  background: var(--navy);
  padding: 60px 48px;
  display: flex; 
  flex-direction: column; 
  justify-content: center;
}

.brand-block { 
  margin-bottom: 56px; 
}

.brand-icon { 
  font-size: 2.5rem; 
  color: var(--teal); 
  margin-bottom: 16px; 
}

.brand-title { 
  font-family: 'Instrument Serif', serif; 
  font-size: 2.8rem; 
  color: #fff; 
  margin-bottom: 8px; 
}

.brand-tagline {
  color: #94a3b8; 
  font-size: 15px; 
}

.feature-list { 
  display: flex; 
  flex-direction: column; 
  gap: 28px; 
}

.feature-item { 
  display: flex; 
  gap: 16px; 
  align-items: flex-start;
}

.feature-icon { font-size: 1.5rem; flex-shrink: 0; }
.feature-title { color: #fff; font-weight: 500; margin-bottom: 3px; }
.feature-desc { color: #94a3b8; font-size: 13px; }

.login-right {
  width: 480px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  padding: 48px 40px;
  background: var(--bg);
}
.login-card { width: 100%; max-width: 380px; }
.login-head { margin-bottom: 28px; }
.login-title { font-size: 1.9rem; margin-bottom: 4px; }
.login-sub { color: var(--muted); font-size: 14px; }

.login-form { display: flex; flex-direction: column; gap: 0; }
.login-submit { width: 100%; justify-content: center; padding: 11px; margin-top: 8px; font-size: 15px; }

.login-footer { margin-top: 24px; text-align: center; font-size: 13px; color: var(--muted); }
.login-footer a { color: var(--teal); text-decoration: none; font-weight: 500; }
.login-footer a:hover { text-decoration: underline; }

@media (max-width: 768px) {
  .login-left { display: none; }
  .login-right { width: 100%; }
}
</style>
