<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api'

const appointments = ref([])
const loading = ref(true)
const error = ref('')
const filter = ref('')
const updatingId = ref(null)

const TRANSITIONS = {
  Booked: ['Confirmed', 'Cancelled'],
  Confirmed: ['Treated', 'Cancelled'],
  Treated: ['Completed'],
  Completed: [], Cancelled: []
}

onMounted(load)

async function load() {
  loading.value = true
  try {
    const data = await api.getDoctorAppointments()
    appointments.value = data.appointments
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
}

async function updateStatus(appt, newStatus) {
  updatingId.value = appt.id
  try {
    const data = await api.updateAppointmentStatus(appt.id, newStatus)
    appt.status = data.appointment.status
  } catch (e) { alert(e.message) }
  finally { updatingId.value = null }
}

const filtered = () => filter.value
  ? appointments.value.filter(a => a.status === filter.value)
  : appointments.value
</script>

<template>
  <div class="container">
    <h1 class="page-title">Appointments</h1>
    <p class="page-sub">All appointments assigned to you</p>

    <div class="toolbar">
      <div class="filter-tabs">
        <button class="filter-tab" :class="{ active: filter==='' }" @click="filter=''">All</button>
        <button v-for="s in ['Booked','Confirmed','Treated','Completed','Cancelled']" :key="s"
          class="filter-tab" :class="{ active: filter===s }" @click="filter=s">{{ s }}</button>
      </div>
    </div>

    <div class="card">
      <div v-if="loading" class="loading"><span class="spinner"></span></div>
      <div v-else-if="error" class="alert alert-error" style="margin:16px">{{ error }}</div>
      <div v-else-if="!filtered().length" class="empty-state"><div class="icon">📭</div><p>No appointments</p></div>
      <div v-else>
        <table>
          <thead><tr><th>#</th><th>Date</th><th>Time</th><th>Patient</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody>
            <tr v-for="a in filtered()" :key="a.id">
              <td class="muted">#{{ a.id }}</td>
              <td>{{ a.date }}</td>
              <td>{{ a.time }}</td>
              <td>Patient #{{ a.patient?.id }}</td>
              <td><span :class="`badge badge-${a.status.toLowerCase()}`">{{ a.status }}</span></td>
              <td class="actions">
                <button
                  v-for="s in TRANSITIONS[a.status]" :key="s"
                  class="btn btn-sm" :class="s==='Cancelled'?'btn-danger':'btn-secondary'"
                  :disabled="updatingId===a.id"
                  @click="updateStatus(a,s)"
                >{{ s }}</button>
                <RouterLink v-if="a.status==='Treated'" :to="`/doctor/treat/${a.id}`" class="btn btn-sm btn-primary">Add treatment</RouterLink>
                <RouterLink v-if="a.status==='Completed' && a.treatment" :to="`/doctor/treat/${a.id}`" class="btn btn-sm btn-secondary">View Rx</RouterLink>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.toolbar { margin-bottom: 16px; }
.filter-tabs { display: flex; gap: 4px; flex-wrap: wrap; }
.filter-tab { padding: 6px 14px; border-radius: 7px; border: 1px solid var(--border); background: var(--white); font-size: 13px; font-weight: 500; cursor: pointer; color: var(--muted); transition: all .15s; }
.filter-tab.active,.filter-tab:hover { border-color: var(--teal); color: var(--teal); background: var(--teal-lt); }
.actions { display: flex; gap: 6px; flex-wrap: wrap; }
.muted { color: var(--muted); font-size:13px; }
</style>
