<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../../api'

const route = useRoute()
const router = useRouter()
const userId = Number(route.params.id)

const user = ref(null)
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const success = ref('')

const form = ref({
  age: '', gender: '', phone: '', address: '',
  active: true, password: '',
  specialization: '', experience_years: '',
  emergency_contact: ''
})

onMounted(async () => {
  try {
    const data = await api.getUser(userId)
    user.value = data.user
    form.value.age     = data.user.age     || ''
    form.value.gender  = data.user.gender  || ''
    form.value.phone   = data.user.phone   || ''
    form.value.address = data.user.address || ''
    form.value.active  = data.user.active
    if (data.user.doctor) {
      form.value.specialization   = data.user.doctor.specialization   || ''
      form.value.experience_years = data.user.doctor.experience_years || ''
    }
    if (data.user.patient) {
      form.value.emergency_contact = data.user.patient.emergency_contact || ''
    }
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
})

async function save() {
  saving.value = true
  error.value = ''
  try {
    const payload = { ...form.value }
    if (!payload.password) delete payload.password
    if (payload.age) payload.age = Number(payload.age)
    if (payload.experience_years) payload.experience_years = Number(payload.experience_years)
    await api.updateUser(userId, payload)
    success.value = 'User updated successfully!'
    setTimeout(() => router.push('/admin/users'), 1500)
  } catch (e) { error.value = e.message }
  finally { saving.value = false }
}
</script>

<template>
  <div class="container" style="max-width:640px">
    <button class="btn btn-secondary btn-sm" style="margin-bottom:20px" @click="router.back()">← Back</button>

    <div v-if="loading" class="loading"><span class="spinner"></span></div>
    <div v-else-if="user">
      <h1 class="page-title">Edit user</h1>
      <p class="page-sub">{{ user.username }} · {{ user.email }}</p>

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

            <!-- Doctor fields -->
            <template v-if="user.doctor">
              <div class="section-label">Doctor details</div>
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

            <!-- Patient fields -->
            <template v-if="user.patient">
              <div class="section-label">Patient details</div>
              <div class="form-group">
                <label class="form-label">Emergency contact</label>
                <input class="form-control" v-model="form.emergency_contact" />
              </div>
            </template>

            <div class="section-label">Account</div>
            <div class="form-group">
              <label class="form-label">New password (leave blank to keep current)</label>
              <input type="password" class="form-control" v-model="form.password" placeholder="••••••••" minlength="6" />
            </div>
            <div class="form-group active-toggle">
              <label class="form-label">Account status</label>
              <label class="toggle-label">
                <input type="checkbox" v-model="form.active" />
                <span class="toggle-track"></span>
                <span>{{ form.active ? 'Active' : 'Deactivated' }}</span>
              </label>
            </div>

            <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;padding:11px" :disabled="saving">
              <span v-if="saving" class="spinner"></span>
              {{ saving ? 'Saving…' : 'Save changes' }}
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.section-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); margin: 24px 0 12px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }
.active-toggle { display: flex; flex-direction: column; gap: 8px; }
.toggle-label { display: flex; align-items: center; gap: 10px; cursor: pointer; font-size: 14px; font-weight: 500; }
.toggle-label input { display: none; }
.toggle-track { width: 40px; height: 22px; border-radius: 999px; background: var(--border); position: relative; transition: background .2s; flex-shrink: 0; }
.toggle-label input:checked ~ .toggle-track { background: var(--teal); }
.toggle-track::after { content:''; position: absolute; top: 3px; left: 3px; width: 16px; height: 16px; border-radius: 50%; background: #fff; transition: transform .2s; }
.toggle-label input:checked ~ .toggle-track::after { transform: translateX(18px); }
</style>
