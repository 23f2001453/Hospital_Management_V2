<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api'

const stats   = ref({ total: 0, doctors: 0, patients: 0, admins: 0, appointments: 0, completed: 0 })
const recentUsers  = ref([])
const recentAppts  = ref([])
const loading      = ref(true)
const error        = ref('')

onMounted(async () => {
  try {
    const [all, docs, pats, appts, completedAppts] = await Promise.all([
      api.getUsers(),
      api.getUsers('?role=doctor'),
      api.getUsers('?role=patient'),
      api.adminGetAppointments('?per_page=5'),
      api.adminGetAppointments('?status=Completed&per_page=5'),
    ])
    stats.value.total    = all.total
    stats.value.doctors  = docs.total
    stats.value.patients = pats.total
    stats.value.admins   = all.total - docs.total - pats.total
    stats.value.appointments = appts.total
    stats.value.completed    = completedAppts.total
    recentUsers.value  = all.users.slice(0, 6)
    recentAppts.value  = appts.appointments
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
})
</script>

<template>
  <div class="container">
    <h1 class="page-title">Admin dashboard</h1>
    <p class="page-sub">Full system overview</p>

    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <!-- Stats -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">Total users</div>
        <div class="stat-value stat-accent">{{ stats.total }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Doctors</div>
        <div class="stat-value">{{ stats.doctors }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Patients</div>
        <div class="stat-value">{{ stats.patients }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Total appointments</div>
        <div class="stat-value">{{ stats.appointments }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Completed</div>
        <div class="stat-value">{{ stats.completed }}</div>
      </div>
    </div>

    <!-- Quick actions -->
    <div class="quick-row">
      <RouterLink to="/admin/users"        class="btn btn-primary">Manage users</RouterLink>
      <RouterLink to="/admin/appointments" class="btn btn-secondary">All appointments</RouterLink>
      <RouterLink to="/admin/search"       class="btn btn-secondary">🔍 Search</RouterLink>
    </div>

    <div class="dash-grid">
      <!-- Recent appointments -->
      <div class="card">
        <div class="card-header">
          <h3 style="font-size:1rem">Recent appointments</h3>
          <RouterLink to="/admin/appointments" class="btn btn-sm btn-secondary">View all</RouterLink>
        </div>
        <div v-if="loading" class="loading"><span class="spinner"></span></div>
        <div v-else-if="!recentAppts.length" class="empty-state"><div class="icon">📭</div><p>No appointments</p></div>
        <div v-else>
          <table>
            <thead><tr><th>#</th><th>Date</th><th>Patient</th><th>Doctor</th><th>Status</th><th>Treatment</th></tr></thead>
            <tbody>
              <tr v-for="a in recentAppts" :key="a.id">
                <td class="muted">{{ a.id }}</td>
                <td>{{ a.date }}</td>
                <td>{{ a.patient?.username || '—' }}</td>
                <td>{{ a.doctor?.username || '—' }}</td>
                <td><span :class="`badge badge-${a.status.toLowerCase()}`">{{ a.status }}</span></td>
                <td>
                  <RouterLink v-if="a.treatment" :to="`/admin/appointments?highlight=${a.id}`" class="btn btn-sm btn-secondary">View Rx</RouterLink>
                  <span v-else class="muted">—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Recent users -->
      <div class="card">
        <div class="card-header">
          <h3 style="font-size:1rem">Recent users</h3>
          <RouterLink to="/admin/users" class="btn btn-sm btn-secondary">View all</RouterLink>
        </div>
        <div v-if="loading" class="loading"><span class="spinner"></span></div>
        <div v-else>
          <table>
            <thead><tr><th>Username</th><th>Role</th><th>Status</th><th></th></tr></thead>
            <tbody>
              <tr v-for="u in recentUsers" :key="u.id">
                <td style="font-weight:500">{{ u.username }}</td>
                <td><span class="role-pill" :class="u.role">{{ u.role }}</span></td>
                <td><span class="badge" :class="u.active ? 'badge-open' : 'badge-cancelled'">{{ u.active ? 'Active' : 'Blacklisted' }}</span></td>
                <td><RouterLink :to="`/admin/users/${u.id}/edit`" class="btn btn-sm btn-secondary">Edit</RouterLink></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.quick-row { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 28px; }
.dash-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.muted { color: var(--muted); font-size: 13px; }
.role-pill { display: inline-flex; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; text-transform: capitalize; }
.role-pill.admin   { background: var(--navy); color: #fff; }
.role-pill.doctor  { background: var(--teal-lt); color: var(--teal2); }
.role-pill.patient { background: var(--blue-lt); color: var(--blue); }
@media (max-width: 900px) { .dash-grid { grid-template-columns: 1fr; } }
</style>
