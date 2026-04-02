<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { api } from '../api'

const auth = useAuthStore()
const saving = ref(false)
const error = ref('')
const success = ref('')

const form = ref({
  age:      auth.user?.age      || '',
  gender:   auth.user?.gender   || '',
  phone:    auth.user?.phone    || '',
  address:  auth.user?.address  || '',
  password: '',
  confirm_password: '',
  emergency_contact: auth.user?.patient?.emergency_contact || '',
  specialization:    auth.user?.doctor?.specialization     || '',
  experience_years:  auth.user?.doctor?.experience_years   || '',
})

async function save() {
  if (form.value.password && form.value.password !== form.value.confirm_password) {
    error.value = 'Passwords do not match.'
    return
  }
  saving.value = true
  error.value = ''
  try {
    const payload = { ...form.value }
    if (!payload.password) { delete payload.password; delete payload.confirm_password }
    if (payload.age) payload.age = Number(payload.age)
    if (payload.experience_years) payload.experience_years = Number(payload.experience_years)
    await api.updateProfile(payload)
    await auth.fetchMe()
    success.value = 'Profile updated!'
    form.value.password = ''
    form.value.confirm_password = ''
    setTimeout(() => success.value = '', 3000)
  } catch (e) { error.value = e.message }
  finally { saving.value = false }
}
</script>

<template>
  <div class="container" style="max-width:600px">
    <h1 class="page-title">My profile</h1>
    <p class="page-sub">{{ auth.user?.email }}</p>

    <div class="user-hero card">
      <div class="hero-avatar">{{ auth.user?.username?.[0]?.toUpperCase() }}</div>
      <div>
        <div class="hero-name">{{ auth.user?.username }}</div>
        <div class="hero-role">
          <span class="role-badge" :class="auth.role">{{ auth.role }}</span>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-body">
        <div v-if="error" class="alert alert-error">{{ error }}</div>
        <div v-if="success" class="alert alert-success">{{ success }}</div>

        <form @submit.prevent="save">
          <div class="section-label">Personal details</div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Age</label>
              <input type="number" class="form-control" v-model="form.age" min="1" max="120" />
            </div>
            <div class="form-group">
              <label class="form-label">Gender</label>
              <select class="form-control" v-model="form.gender">
                <option value="">Select</option>
                <option>Male</option><option>Female</option><option>Other</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Phone</label>
            <input class="form-control" v-model="form.phone" />
          </div>
          <div class="form-group">
            <label class="form-label">Address</label>
            <input class="form-control" v-model="form.address" />
          </div>

          <template v-if="auth.isPatient">
            <div class="section-label">Emergency contact</div>
            <div class="form-group">
              <label class="form-label">Emergency contact number</label>
              <input class="form-control" v-model="form.emergency_contact" />
            </div>
          </template>

          <template v-if="auth.isDoctor">
            <div class="section-label">Professional details</div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">Specialization</label>
                <input class="form-control" v-model="form.specialization" />
              </div>
              <div class="form-group">
                <label class="form-label">Experience (years)</label>
                <input type="number" class="form-control" v-model="form.experience_years" min="0" />
              </div>
            </div>
          </template>

          <div class="section-label">Change password</div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">New password</label>
              <input type="password" class="form-control" v-model="form.password" placeholder="Leave blank to keep current" minlength="6" />
            </div>
            <div class="form-group">
              <label class="form-label">Confirm password</label>
              <input type="password" class="form-control" v-model="form.confirm_password" placeholder="••••••••" />
            </div>
          </div>

          <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;padding:11px" :disabled="saving">
            <span v-if="saving" class="spinner"></span>
            {{ saving ? 'Saving…' : 'Save changes' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.user-hero { display: flex; align-items: center; gap: 20px; padding: 20px 24px; margin-bottom: 20px; }
.hero-avatar { width: 60px; height: 60px; border-radius: 50%; background: var(--teal); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: 600; flex-shrink: 0; }
.hero-name { font-size: 1.2rem; font-weight: 600; margin-bottom: 6px; }
.section-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); margin: 24px 0 12px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }
.role-badge { display: inline-flex; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; text-transform: capitalize; }
.role-badge.admin   { background: var(--navy); color: #fff; }
.role-badge.doctor  { background: var(--teal-lt); color: var(--teal2); }
.role-badge.patient { background: var(--blue-lt); color: var(--blue); }
</style>
