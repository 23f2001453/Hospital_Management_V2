<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { api } from '../../api'

const auth         = useAuthStore()
const appointments = ref([])
const loading      = ref(true)
const error        = ref('')
const stats        = ref({ booked: 0, completed: 0, cancelled: 0 })

// Export state
const exporting    = ref(false)
const exportTaskId = ref(null)
const exportStatus = ref('')   // '', 'pending', 'success', 'error'
const exportMsg    = ref('')
let pollTimer      = null

onMounted(async () => {
  try {
    const data = await api.getMyAppointments()
    appointments.value  = data.appointments
    stats.value.booked    = data.appointments.filter(a => ['Booked','Confirmed'].includes(a.status)).length
    stats.value.completed = data.appointments.filter(a => a.status === 'Completed').length
    stats.value.cancelled = data.appointments.filter(a => a.status === 'Cancelled').length
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})

// ── Export CSV ────────────────────────────────────────────────────────────
async function triggerExport() {
  exporting.value   = true
  exportStatus.value = 'pending'
  exportMsg.value   = 'Queuing your export…'
  try {
    const data = await api.triggerExport()
    exportTaskId.value = data.task_id
    exportMsg.value    = 'Export queued! We\'ll email you when it\'s ready.'
    startPolling(data.task_id)
  } catch (e) {
    exportStatus.value = 'error'
    exportMsg.value    = e.message
    exporting.value    = false
  }
}

function startPolling(taskId) {
  pollTimer = setInterval(async () => {
    try {
      const data = await api.getJobStatus(taskId)
      if (data.status === 'SUCCESS') {
        clearInterval(pollTimer)
        exportStatus.value = 'success'
        exportMsg.value    = `Done! Check your email (${auth.user?.email}) for the CSV attachment.`
        exporting.value    = false
      } else if (data.status === 'FAILURE') {
        clearInterval(pollTimer)
        exportStatus.value = 'error'
        exportMsg.value    = 'Export failed. Please try again.'
        exporting.value    = false
      }
    } catch (_) {}
  }, 3000)   // poll every 3 seconds
}

// ── Cancel appointment ────────────────────────────────────────────────────
async function cancel(id) {
  if (!confirm('Cancel this appointment?')) return
  try {
    await api.cancelAppointment(id)
    const a = appointments.value.find(x => x.id === id)
    if (a) { a.status = 'Cancelled'; stats.value.booked--; stats.value.cancelled++ }
  } catch (e) { alert(e.message) }
}
</script>

<template>
  <div class="container">
    <h1 class="page-title">Good day, {{ auth.user?.username }} 👋</h1>
    <p class="page-sub">Here's your health overview</p>

    <!-- Stats -->
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

    <!-- Quick actions -->
    <div class="quick-actions">
      <RouterLink to="/patient/book"         class="btn btn-primary">📅 Book appointment</RouterLink>
      <RouterLink to="/patient/appointments" class="btn btn-secondary">View all appointments</RouterLink>
    </div>

    <!-- Export CSV panel -->
    <div class="export-card card">
      <div class="export-left">
        <div class="export-title">Treatment history export</div>
        <div class="export-desc">Download all your appointment records, diagnoses, and prescriptions as a CSV file. The file will be emailed to {{ auth.user?.email }}.</div>
        <div
          v-if="exportMsg"
          class="export-msg"
          :class="{
            'export-pending': exportStatus === 'pending',
            'export-success': exportStatus === 'success',
            'export-error':   exportStatus === 'error',
          }"
        >{{ exportMsg }}</div>
      </div>
      <button
        class="btn btn-secondary export-btn"
        :disabled="exporting"
        @click="triggerExport"
      >
        <span v-if="exporting" class="spinner"></span>
        <span>{{ exporting ? 'Processing…' : '⬇ Export CSV' }}</span>
      </button>
    </div>

    <!-- Recent appointments -->
    <div class="card" style="margin-top:8px">
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
          <thead>
            <tr><th>Date</th><th>Time</th><th>Doctor</th><th>Status</th><th>Actions</th></tr>
          </thead>
          <tbody>
            <tr v-for="a in appointments.slice(0, 5)" :key="a.id">
              <td>{{ a.date }}</td>
              <td>{{ a.time }}</td>
              <td>Dr. #{{ a.doctor?.id }}</td>
              <td><span :class="`badge badge-${a.status.toLowerCase()}`">{{ a.status }}</span></td>
              <td class="actions">
                <RouterLink
                  v-if="a.status === 'Completed' && a.treatment"
                  :to="`/patient/treatment/${a.id}`"
                  class="btn btn-sm btn-secondary"
                >View Rx</RouterLink>
                <button
                  v-if="a.status === 'Booked'"
                  class="btn btn-sm btn-danger"
                  @click="cancel(a.id)"
                >Cancel</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.quick-actions { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px; }
.table-wrap    { overflow-x: auto; }
.actions       { display: flex; gap: 8px; }

.export-card {
  display: flex; align-items: center; gap: 24px;
  padding: 20px 24px; margin-bottom: 20px;
  border-left: 3px solid var(--teal);
}
.export-left  { flex: 1; }
.export-title { font-weight: 600; font-size: 15px; margin-bottom: 4px; }
.export-desc  { font-size: 13px; color: var(--muted); line-height: 1.5; }
.export-msg   { margin-top: 8px; font-size: 13px; padding: 6px 10px; border-radius: 6px; }
.export-pending { background: var(--amber-lt); color: #92400e; }
.export-success { background: var(--green-lt); color: #15803d; }
.export-error   { background: var(--red-lt);   color: var(--red); }
.export-btn   { flex-shrink: 0; white-space: nowrap; }
</style>
