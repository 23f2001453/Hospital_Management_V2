<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'

const router = useRouter()

const role = ref('patient')
const loading = ref(false)
const error = ref('')
const success = ref('')

const form = ref({
  username: '', email: '', password: '', confirm_password: '',
  first_name: '', last_name: '', age: '', gender: '', phone: '', address: '',
  emergency_contact: '',
  specialization: '', experience_years: '', availability: ''
})

async function register() {
  error.value = ''
  if (form.value.password !== form.value.confirm_password) {
    error.value = 'Passwords do not match.'
    return
  }
  loading.value = true
  try {
    const payload = { ...form.value, role: role.value, age: Number(form.value.age) }
    if (role.value === 'patient') {
      delete payload.specialization; delete payload.experience_years; delete payload.availability
    } else {
      delete payload.emergency_contact
      payload.experience_years = Number(payload.experience_years)
    }
    await api.register(payload)
    success.value = 'Account created! Redirecting to login…'
    setTimeout(() => router.push('/login'), 1500)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="reg-page">
    <div class="reg-card card">
      <div class="card-header">
        <div>
          <h1 class="page-title" style="margin-bottom:0;font-size:1.7rem">Create account</h1>
          <p class="page-sub" style="margin-bottom:0">Join MediCore</p>
        </div>
        <RouterLink to="/login" class="btn btn-secondary btn-sm">Sign in instead</RouterLink>
      </div>

      <div class="card-body">
        <div v-if="error" class="alert alert-error">{{ error }}</div>
        <div v-if="success" class="alert alert-success">{{ success }}</div>

        <div class="form-group">
          <label class="form-label">I am a</label>
          <div class="role-toggle">
            <button type="button" class="role-opt" :class="{ active: role === 'patient' }" @click="role = 'patient'">🧑‍⚕️ Patient</button>
            <button type="button" class="role-opt" :class="{ active: role === 'doctor' }" @click="role = 'doctor'">👨‍⚕️ Doctor</button>
          </div>
        </div>

        <form @submit.prevent="register">
          <div class="section-label">Account details</div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Username *</label>
              <input class="form-control" v-model="form.username" required />
            </div>
            <div class="form-group">
              <label class="form-label">Email *</label>
              <input type="email" class="form-control" v-model="form.email" required />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Password *</label>
              <input type="password" class="form-control" v-model="form.password" required minlength="6" />
            </div>
            <div class="form-group">
              <label class="form-label">Confirm password *</label>
              <input type="password" class="form-control" v-model="form.confirm_password" required />
            </div>
          </div>

          <div class="section-label">Personal details</div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">First name *</label>
              <input class="form-control" v-model="form.first_name" required />
            </div>
            <div class="form-group">
              <label class="form-label">Last name *</label>
              <input class="form-control" v-model="form.last_name" required />
            </div>
          </div>
          <div class="form-row-3">
            <div class="form-group">
              <label class="form-label">Age *</label>
              <input type="number" class="form-control" v-model="form.age" min="1" max="120" required />
            </div>
            <div class="form-group">
              <label class="form-label">Gender *</label>
              <select class="form-control" v-model="form.gender" required>
                <option value="">Select</option>
                <option>Male</option><option>Female</option><option>Other</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Phone *</label>
              <input class="form-control" v-model="form.phone" required />
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Address *</label>
            <input class="form-control" v-model="form.address" required />
          </div>

          <!-- Patient-only -->
          <template v-if="role === 'patient'">
            <div class="section-label">Emergency contact</div>
            <div class="form-group">
              <label class="form-label">Emergency contact number</label>
              <input class="form-control" v-model="form.emergency_contact" placeholder="Phone number" />
            </div>
          </template>

          <!-- Doctor-only -->
          <template v-if="role === 'doctor'">
            <div class="section-label">Professional details</div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">Specialization *</label>
                <input class="form-control" v-model="form.specialization" required />
              </div>
              <div class="form-group">
                <label class="form-label">Years of experience *</label>
                <input type="number" class="form-control" v-model="form.experience_years" min="0" required />
              </div>
            </div>
          </template>

          <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;padding:11px;font-size:15px;margin-top:8px" :disabled="loading">
            <span v-if="loading" class="spinner"></span>
            {{ loading ? 'Creating account…' : 'Create account' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.reg-page { min-height: 100vh; padding: 40px 24px; display: flex; align-items: flex-start; justify-content: center; background: var(--bg); }
.reg-card { width: 100%; max-width: 680px; }
.section-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); margin: 24px 0 12px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }
.role-toggle { display: flex; gap: 8px; }
.role-opt { flex: 1; padding: 10px; border: 2px solid var(--border); border-radius: 8px; background: var(--white); font-size: 14px; font-weight: 500; cursor: pointer; transition: all .15s; }
.role-opt.active { border-color: var(--teal); background: var(--teal-lt); color: var(--teal2); }
</style>
