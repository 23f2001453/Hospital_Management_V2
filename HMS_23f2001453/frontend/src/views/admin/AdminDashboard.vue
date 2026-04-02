<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api'

const stats = ref({ total: 0, doctors: 0, patients: 0, admins: 0 })
const recentUsers = ref([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const [all, docs, pats] = await Promise.all([
      api.getUsers(),
      api.getUsers('?role=doctor'),
      api.getUsers('?role=patient'),
    ])
    stats.value.total   = all.total
    stats.value.doctors = docs.total
    stats.value.patients= pats.total
    stats.value.admins  = all.total - docs.total - pats.total
    recentUsers.value   = all.users.slice(0, 8)
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
})
</script>

<template>
  <div class="container">
    <h1 class="page-title">Admin dashboard</h1>
    <p class="page-sub">System overview and user management</p>

    <div v-if="error" class="alert alert-error">{{ error }}</div>

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
        <div class="stat-label">Admins</div>
        <div class="stat-value">{{ stats.admins }}</div>
      </div>
    </div>

    <div class="admin-actions" style="display:flex;gap:12px;margin-bottom:28px">
      <RouterLink to="/admin/users" class="btn btn-primary">Manage users</RouterLink>
    </div>

    <div class="card">
      <div class="card-header"><h3 style="font-size:1rem">Recent users</h3></div>
      <div v-if="loading" class="loading"><span class="spinner"></span></div>
      <div v-else>
        <table>
          <thead><tr><th>#</th><th>Username</th><th>Email</th><th>Role</th><th>Status</th><th></th></tr></thead>
          <tbody>
            <tr v-for="u in recentUsers" :key="u.id">
              <td class="muted">{{ u.id }}</td>
              <td style="font-weight:500">{{ u.username }}</td>
              <td class="muted">{{ u.email }}</td>
              <td><span class="role-badge" :class="u.role">{{ u.role }}</span></td>
              <td><span class="badge" :class="u.active ? 'badge-open' : 'badge-cancelled'">{{ u.active ? 'Active' : 'Inactive' }}</span></td>
              <td><RouterLink :to="`/admin/users/${u.id}/edit`" class="btn btn-sm btn-secondary">Edit</RouterLink></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.muted { color: var(--muted); font-size: 13px; }
.role-badge { display: inline-flex; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; text-transform: capitalize; }
.role-badge.admin   { background: var(--navy); color: #fff; }
.role-badge.doctor  { background: var(--teal-lt); color: var(--teal2); }
.role-badge.patient { background: var(--blue-lt); color: var(--blue); }
</style>
