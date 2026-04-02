<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api'

const users = ref([])
const loading = ref(true)
const error = ref('')
const success = ref('')
const roleFilter = ref('')
const page = ref(1)
const total = ref(0)
const PER_PAGE = 20

onMounted(() => load())

async function load() {
  loading.value = true
  const params = `?page=${page.value}&per_page=${PER_PAGE}${roleFilter.value ? '&role=' + roleFilter.value : ''}`
  try {
    const data = await api.getUsers(params)
    users.value = data.users
    total.value = data.total
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
}

async function toggleActive(user) {
  try {
    await api.updateUser(user.id, { active: !user.active })
    user.active = !user.active
    success.value = `User ${user.active ? 'activated' : 'deactivated'}.`
    setTimeout(() => success.value = '', 3000)
  } catch (e) { error.value = e.message }
}

async function deleteUser(userId) {
  if (!confirm('Permanently delete this user? This cannot be undone.')) return
  try {
    await api.deleteUser(userId)
    users.value = users.value.filter(u => u.id !== userId)
    success.value = 'User deleted.'
    total.value--
    setTimeout(() => success.value = '', 3000)
  } catch (e) { error.value = e.message }
}

function changeFilter(role) {
  roleFilter.value = role
  page.value = 1
  load()
}
</script>

<template>
  <div class="container">
    <div class="page-top">
      <div>
        <h1 class="page-title">User management</h1>
        <p class="page-sub">{{ total }} total users</p>
      </div>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>
    <div v-if="success" class="alert alert-success">{{ success }}</div>

    <div class="toolbar">
      <div class="filter-tabs">
        <button class="filter-tab" :class="{ active: roleFilter==='' }" @click="changeFilter('')">All</button>
        <button class="filter-tab" :class="{ active: roleFilter==='patient' }" @click="changeFilter('patient')">Patients</button>
        <button class="filter-tab" :class="{ active: roleFilter==='doctor' }" @click="changeFilter('doctor')">Doctors</button>
        <button class="filter-tab" :class="{ active: roleFilter==='admin' }" @click="changeFilter('admin')">Admins</button>
      </div>
    </div>

    <div class="card">
      <div v-if="loading" class="loading"><span class="spinner"></span></div>
      <div v-else-if="!users.length" class="empty-state"><div class="icon">👥</div><p>No users found</p></div>
      <div v-else>
        <table>
          <thead>
            <tr><th>#</th><th>Username</th><th>Email</th><th>Role</th><th>Status</th><th>Actions</th></tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td class="muted">{{ u.id }}</td>
              <td style="font-weight:500">{{ u.username }}</td>
              <td class="muted">{{ u.email }}</td>
              <td><span class="role-pill" :class="u.role">{{ u.role }}</span></td>
              <td>
                <button
                  class="badge status-btn"
                  :class="u.active ? 'badge-open' : 'badge-cancelled'"
                  @click="toggleActive(u)"
                >{{ u.active ? 'Active' : 'Inactive' }}</button>
              </td>
              <td class="actions">
                <RouterLink :to="`/admin/users/${u.id}/edit`" class="btn btn-sm btn-secondary">Edit</RouterLink>
                <button class="btn btn-sm btn-danger" @click="deleteUser(u.id)">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-top { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 8px; }
.toolbar { margin-bottom: 16px; }
.filter-tabs { display: flex; gap: 4px; flex-wrap: wrap; }
.filter-tab { padding: 6px 14px; border-radius: 7px; border: 1px solid var(--border); background: var(--white); font-size: 13px; font-weight: 500; cursor: pointer; color: var(--muted); transition: all .15s; }
.filter-tab.active,.filter-tab:hover { border-color: var(--teal); color: var(--teal); background: var(--teal-lt); }
.muted { color: var(--muted); font-size: 13px; }
.actions { display: flex; gap: 8px; }
.role-pill { display: inline-flex; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; text-transform: capitalize; }
.role-pill.admin   { background: var(--navy); color: #fff; }
.role-pill.doctor  { background: var(--teal-lt); color: var(--teal2); }
.role-pill.patient { background: var(--blue-lt); color: var(--blue); }
.status-btn { cursor: pointer; border: none; font-family: inherit; }
</style>
