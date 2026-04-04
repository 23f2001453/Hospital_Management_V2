<script setup>
import { ref, watch } from 'vue'
import { api } from '../../api'

const query      = ref('')
const typeFilter = ref('')
const results    = ref({ users: [], departments: [] })
const total      = ref(0)
const loading    = ref(false)
const error      = ref('')
const searched   = ref(false)

let debounceTimer = null

watch(query, (val) => {
  clearTimeout(debounceTimer)
  if (val.trim().length < 2) { results.value = { users: [], departments: [] }; searched.value = false; return }
  debounceTimer = setTimeout(search, 400)
})

watch(typeFilter, () => {
  if (query.value.trim().length >= 2) search()
})

async function search() {
  if (query.value.trim().length < 2) return
  loading.value = true
  error.value   = ''
  try {
    const data = await api.adminSearch(query.value, typeFilter.value)
    results.value = data.results
    total.value   = data.total
    searched.value = true
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
}

async function blacklist(user) {
  if (!confirm(`Blacklist ${user.username}? They will not be able to log in.`)) return
  try {
    await api.blacklist(user.id)
    user.active = false
  } catch (e) { error.value = e.message }
}

async function unblacklist(user) {
  try {
    await api.unblacklist(user.id)
    user.active = true
  } catch (e) { error.value = e.message }
}
</script>

<template>
  <div class="container">
    <h1 class="page-title">Search</h1>
    <p class="page-sub">Search users by name, email, phone, or specialization — or search departments</p>

    <div class="search-bar card">
      <div class="search-row">
        <div class="search-input-wrap">
          <span class="search-icon">🔍</span>
          <input
            class="search-input"
            v-model="query"
            placeholder="Search by name, email, phone, specialization…"
            autofocus
          />
          <span v-if="loading" class="spinner" style="width:16px;height:16px"></span>
        </div>
        <div class="type-tabs">
          <button class="type-tab" :class="{ active: typeFilter==='' }"           @click="typeFilter=''">All</button>
          <button class="type-tab" :class="{ active: typeFilter==='doctor' }"     @click="typeFilter='doctor'">Doctors</button>
          <button class="type-tab" :class="{ active: typeFilter==='patient' }"    @click="typeFilter='patient'">Patients</button>
          <button class="type-tab" :class="{ active: typeFilter==='admin' }"      @click="typeFilter='admin'">Admins</button>
          <button class="type-tab" :class="{ active: typeFilter==='department' }" @click="typeFilter='department'">Departments</button>
        </div>
      </div>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <div v-if="!searched && !loading" class="empty-state" style="padding:60px 0">
      <div class="icon">🔎</div>
      <p>Type at least 2 characters to search</p>
    </div>

    <template v-if="searched">
      <div class="result-count">{{ total }} result{{ total !== 1 ? 's' : '' }} for "{{ query }}"</div>

      <!-- Users -->
      <div v-if="results.users.length" class="card result-section">
        <div class="card-header"><h3 style="font-size:1rem">Users ({{ results.users.length }})</h3></div>
        <table>
          <thead><tr><th>#</th><th>Username</th><th>Email</th><th>Role</th><th>Detail</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody>
            <tr v-for="u in results.users" :key="u.id">
              <td class="muted">{{ u.id }}</td>
              <td style="font-weight:500">{{ u.username }}</td>
              <td class="muted">{{ u.email }}</td>
              <td><span class="role-pill" :class="u.role">{{ u.role }}</span></td>
              <td class="muted">
                <span v-if="u.doctor">{{ u.doctor.specialization || 'Doctor' }}</span>
                <span v-else-if="u.patient">Patient</span>
                <span v-else>Admin</span>
              </td>
              <td>
                <span class="badge" :class="u.active ? 'badge-open' : 'badge-cancelled'">
                  {{ u.active ? 'Active' : 'Blacklisted' }}
                </span>
              </td>
              <td class="actions">
                <RouterLink :to="`/admin/users/${u.id}/edit`" class="btn btn-sm btn-secondary">Edit</RouterLink>
                <button v-if="u.active && u.role !== 'admin'" class="btn btn-sm btn-danger" @click="blacklist(u)">Blacklist</button>
                <button v-if="!u.active" class="btn btn-sm btn-secondary" @click="unblacklist(u)">Restore</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Departments -->
      <div v-if="results.departments.length" class="card result-section">
        <div class="card-header"><h3 style="font-size:1rem">Departments ({{ results.departments.length }})</h3></div>
        <table>
          <thead><tr><th>Name</th><th>Description</th><th>Doctors</th></tr></thead>
          <tbody>
            <tr v-for="d in results.departments" :key="d.id">
              <td style="font-weight:500">{{ d.name }}</td>
              <td class="muted">{{ d.description || '—' }}</td>
              <td><span class="badge badge-booked">{{ d.doctor_count }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="total === 0" class="empty-state">
        <div class="icon">📭</div>
        <p>No results found for "{{ query }}"</p>
      </div>
    </template>
  </div>
</template>

<style scoped>
.search-bar { padding: 16px 20px; margin-bottom: 20px; }
.search-row { display: flex; flex-direction: column; gap: 12px; }
.search-input-wrap { display: flex; align-items: center; gap: 10px; border: 1px solid var(--border); border-radius: 10px; padding: 8px 14px; transition: border-color .15s; }
.search-input-wrap:focus-within { border-color: var(--teal); box-shadow: 0 0 0 3px rgba(13,148,136,.1); }
.search-icon { font-size: 16px; flex-shrink: 0; }
.search-input { flex: 1; border: none; outline: none; font-size: 15px; font-family: inherit; background: transparent; color: var(--navy); }
.type-tabs { display: flex; gap: 4px; flex-wrap: wrap; }
.type-tab { padding: 5px 14px; border-radius: 7px; border: 1px solid var(--border); background: var(--white); font-size: 13px; font-weight: 500; cursor: pointer; color: var(--muted); transition: all .15s; }
.type-tab.active,.type-tab:hover { border-color: var(--teal); color: var(--teal); background: var(--teal-lt); }
.result-count { font-size: 13px; color: var(--muted); margin-bottom: 14px; }
.result-section { margin-bottom: 20px; }
.actions { display: flex; gap: 8px; }
.muted { color: var(--muted); font-size: 13px; }
.role-pill { display: inline-flex; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; text-transform: capitalize; }
.role-pill.admin   { background: var(--navy); color: #fff; }
.role-pill.doctor  { background: var(--teal-lt); color: var(--teal2); }
.role-pill.patient { background: var(--blue-lt); color: var(--blue); }
</style>
