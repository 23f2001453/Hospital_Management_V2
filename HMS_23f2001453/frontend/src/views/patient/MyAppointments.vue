<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api'

const appointments = ref([])
const loading = ref(true)
const error = ref('')
const filter = ref('')

onMounted(async () => {
  try {
    const data = await api.getMyAppointments()
    appointments.value = data.appointments
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
})

async function cancel(id) {
  if (!confirm('Cancel this appointment?')) return
  try {
    await api.cancelAppointment(id)
    const a = appointments.value.find(x => x.id === id)
    if (a) a.status = 'Cancelled'
  } catch (e) { alert(e.message) }
}

const filtered = () => filter.value
  ? appointments.value.filter(a => a.status === filter.value)
  : appointments.value
</script>

<template>
  <div class="container">
    <h1 class="page-title">My appointments</h1>
    <p class="page-sub">All your scheduled and past appointments</p>

    <div class="toolbar">
      <div class="filter-tabs">
        <button class="filter-tab" :class="{ active: filter === '' }" @click="filter = ''">All</button>
        <button class="filter-tab" :class="{ active: filter === 'Booked' }" @click="filter = 'Booked'">Booked</button>
        <button class="filter-tab" :class="{ active: filter === 'Confirmed' }" @click="filter = 'Confirmed'">Confirmed</button>
        <button class="filter-tab" :class="{ active: filter === 'Completed' }" @click="filter = 'Completed'">Completed</button>
        <button class="filter-tab" :class="{ active: filter === 'Cancelled' }" @click="filter = 'Cancelled'">Cancelled</button>
      </div>
      <RouterLink to="/patient/book" class="btn btn-primary btn-sm">+ Book new</RouterLink>
    </div>

    <div class="card">
      <div v-if="loading" class="loading"><span class="spinner"></span> Loading…</div>
      <div v-else-if="error" class="alert alert-error" style="margin:16px">{{ error }}</div>
      <div v-else-if="!filtered().length" class="empty-state">
        <div class="icon">📭</div><p>No appointments found</p>
      </div>
      <div v-else>
        <table>
          <thead>
            <tr><th>#</th><th>Date</th><th>Time</th><th>Doctor</th><th>Status</th><th>Actions</th></tr>
          </thead>
          <tbody>
            <tr v-for="a in filtered()" :key="a.id">
              <td class="id-col">#{{ a.id }}</td>
              <td>{{ a.date }}</td>
              <td>{{ a.time }}</td>
              <td>Dr. #{{ a.doctor?.id }}</td>
              <td><span :class="`badge badge-${a.status.toLowerCase()}`">{{ a.status }}</span></td>
              <td class="actions">
                <RouterLink v-if="a.status === 'Completed' && a.treatment" :to="`/patient/treatment/${a.id}`" class="btn btn-sm btn-secondary">View prescription</RouterLink>
                <button v-if="a.status === 'Booked'" class="btn btn-sm btn-danger" @click="cancel(a.id)">Cancel</button>
                <span v-if="a.status === 'Completed' && !a.treatment" class="no-rx">No Rx yet</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; gap: 16px; flex-wrap: wrap; }
.filter-tabs { display: flex; gap: 4px; flex-wrap: wrap; }
.filter-tab { padding: 6px 14px; border-radius: 7px; border: 1px solid var(--border); background: var(--white); font-size: 13px; font-weight: 500; cursor: pointer; color: var(--muted); transition: all .15s; }
.filter-tab.active, .filter-tab:hover { border-color: var(--teal); color: var(--teal); background: var(--teal-lt); }
.id-col { color: var(--muted); font-size: 13px; }
.actions { display: flex; gap: 8px; align-items: center; }
.no-rx { font-size: 12px; color: var(--muted); }
</style>
