<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { api } from '../../api'

const auth = useAuthStore()
const upcoming = ref([])
const patients = ref([])
const loading = ref(true)
const error = ref('')
const updatingId = ref(null)

const TRANSITIONS = {
  Booked: ['Confirmed', 'Cancelled'],
  Confirmed: ['Treated', 'Cancelled'],
  Treated: ['Completed'],
  Completed: [],
  Cancelled: []
}

onMounted(async () => {
  try {
    const [apptData, patData] = await Promise.all([
      api.getDoctorAppointments('?from_date=' + new Date().toISOString().slice(0,10)),
      api.getDoctorPatients()
    ])
    upcoming.value = apptData.appointments.filter(a => !['Completed','Cancelled'].includes(a.status))
    patients.value = patData.patients
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
})

async function updateStatus(appt, newStatus) {
  updatingId.value = appt.id
  try {
    const data = await api.updateAppointmentStatus(appt.id, newStatus)
    appt.status = data.appointment.status
  } catch (e) { alert(e.message) }
  finally { updatingId.value = null }
}
</script>

<template>
  <div class="container">
    <h1 class="page-title">Doctor dashboard</h1>
    <p class="page-sub">Welcome, {{ auth.user?.username }} · Manage your appointments and patients</p>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">Active appointments</div>
        <div class="stat-value stat-accent">{{ upcoming.length }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Total patients</div>
        <div class="stat-value">{{ patients.length }}</div>
      </div>
    </div>

    <div class="quick-actions" style="margin-bottom:28px;display:flex;gap:12px">
      <RouterLink to="/doctor/availability" class="btn btn-primary">+ Add availability slot</RouterLink>
      <RouterLink to="/doctor/appointments" class="btn btn-secondary">All appointments</RouterLink>
      <RouterLink to="/doctor/patients" class="btn btn-secondary">My patients</RouterLink>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <div class="card">
      <div class="card-header"><h3 style="font-size:1rem">Upcoming appointments (next 7 days)</h3></div>
      <div v-if="loading" class="loading"><span class="spinner"></span></div>
      <div v-else-if="!upcoming.length" class="empty-state"><div class="icon">✅</div><p>No upcoming appointments</p></div>
      <div v-else>
        <table>
          <thead><tr><th>#</th><th>Date</th><th>Time</th><th>Patient</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody>
            <tr v-for="a in upcoming" :key="a.id">
              <td class="muted">#{{ a.id }}</td>
              <td>{{ a.date }}</td>
              <td>{{ a.time }}</td>
              <td>Patient #{{ a.patient?.id }}</td>
              <td><span :class="`badge badge-${a.status.toLowerCase()}`">{{ a.status }}</span></td>
              <td class="actions">
                <button
                  v-for="s in TRANSITIONS[a.status]" :key="s"
                  class="btn btn-sm"
                  :class="s === 'Cancelled' ? 'btn-danger' : 'btn-secondary'"
                  :disabled="updatingId === a.id"
                  @click="updateStatus(a, s)"
                >{{ s }}</button>
                <RouterLink
                  v-if="a.status === 'Treated'"
                  :to="`/doctor/treat/${a.id}`"
                  class="btn btn-sm btn-primary"
                >Add treatment</RouterLink>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.actions { display: flex; gap: 6px; flex-wrap: wrap; }
.muted { color: var(--muted); font-size:13px; }
</style>
