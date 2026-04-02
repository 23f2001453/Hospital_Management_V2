<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { api } from '../../api'

const router = useRouter()
const auth = useAuthStore()
const appointments = ref([])
const loading = ref(true)
const error = ref('')

const stats = ref({ booked: 0, completed: 0, cancelled: 0 })

onMounted(async () => {
  try {
    const data = await api.getMyAppointments()
    appointments.value = data.appointments
    stats.value.booked    = data.appointments.filter(a => ['Booked','Confirmed'].includes(a.status)).length
    stats.value.completed = data.appointments.filter(a => a.status === 'Completed').length
    stats.value.cancelled = data.appointments.filter(a => a.status === 'Cancelled').length
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})

async function cancel(id) {
  if (!confirm('Cancel this appointment?')) return
  try {
    await api.cancelAppointment(id)
    const a = appointments.value.find(x => x.id === id)
    if (a) { a.status = 'Cancelled'; stats.value.booked--; stats.value.cancelled++ }
  } catch (e) { alert(e.message) }
}

function statusClass(s) {
  return `badge badge-${s.toLowerCase()}`
}
</script>

<template>
  <div class="container">
    <h1 class="page-title">Good day, {{ auth.user?.username }} 👋</h1>
    <p class="page-sub">Here's your health overview</p>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">Upcoming</div>
        <div class="stat-value stat-accent">{{ stats.booked }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Completed</div>
        <div class="stat-value">{{ stats.completed }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Cancelled</div>
        <div class="stat-value">{{ stats.cancelled }}</div>
      </div>
    </div>

    <div class="quick-actions">
      <RouterLink to="/patient/book" class="btn btn-primary">📅 Book appointment</RouterLink>
      <RouterLink to="/patient/appointments" class="btn btn-secondary">View all appointments</RouterLink>
    </div>

    <div class="card" style="margin-top:28px">
      <div class="card-header">
        <h3 style="font-size:1.1rem">Recent appointments</h3>
      </div>
      <div v-if="loading" class="loading"><span class="spinner"></span> Loading…</div>
      <div v-else-if="error" class="alert alert-error" style="margin:16px">{{ error }}</div>
      <div v-else-if="!appointments.length" class="empty-state">
        <div class="icon">📭</div>
        <p>No appointments yet. <RouterLink to="/patient/book">Book one now</RouterLink></p>
      </div>
      <div v-else class="table-wrap">
        <table>
          <thead><tr><th>Date</th><th>Time</th><th>Doctor</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody>
            <tr v-for="a in appointments.slice(0,5)" :key="a.id">
              <td>{{ a.date }}</td>
              <td>{{ a.time }}</td>
              <td>Dr. #{{ a.doctor?.id }}</td>
              <td><span :class="statusClass(a.status)">{{ a.status }}</span></td>
              <td class="actions">
                <RouterLink v-if="a.status === 'Completed' && a.treatment" :to="`/patient/treatment/${a.id}`" class="btn btn-sm btn-secondary">View Rx</RouterLink>
                <button v-if="a.status === 'Booked'" class="btn btn-sm btn-danger" @click="cancel(a.id)">Cancel</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.quick-actions { display: flex; gap: 12px; flex-wrap: wrap; }
.table-wrap { overflow-x: auto; }
.actions { display: flex; gap: 8px; }
</style>
