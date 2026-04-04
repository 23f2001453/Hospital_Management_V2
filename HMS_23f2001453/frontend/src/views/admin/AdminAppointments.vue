<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api'

const appointments = ref([])
const total        = ref(0)
const loading      = ref(true)
const error        = ref('')

const filters = ref({ status: '', doctor_id: '', patient_id: '', from_date: '', to_date: '' })
const page    = ref(1)
const PER_PAGE = 20

const selectedTreatment = ref(null)
const treatmentLoading  = ref(false)

onMounted(load)

async function load() {
  loading.value = true
  error.value   = ''
  const p = new URLSearchParams()
  p.set('page', page.value)
  p.set('per_page', PER_PAGE)
  if (filters.value.status)    p.set('status',     filters.value.status)
  if (filters.value.doctor_id) p.set('doctor_id',  filters.value.doctor_id)
  if (filters.value.patient_id)p.set('patient_id', filters.value.patient_id)
  if (filters.value.from_date) p.set('from_date',  filters.value.from_date)
  if (filters.value.to_date)   p.set('to_date',    filters.value.to_date)

  try {
    const data = await api.adminGetAppointments('?' + p.toString())
    appointments.value = data.appointments
    total.value        = data.total
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
}

function applyFilters() { page.value = 1; load() }
function resetFilters()  { filters.value = { status:'', doctor_id:'', patient_id:'', from_date:'', to_date:'' }; applyFilters() }

async function viewTreatment(appt) {
  if (!appt.treatment) return
  treatmentLoading.value = true
  selectedTreatment.value = null
  try {
    const data = await api.adminGetTreatmentDetail(appt.id)
    selectedTreatment.value = { appt: data.appointment, treatment: data.treatment }
  } catch (e) { error.value = e.message }
  finally { treatmentLoading.value = false }
}

const totalPages = () => Math.ceil(total.value / PER_PAGE)
</script>

<template>
  <div class="container">
    <h1 class="page-title">All appointments</h1>
    <p class="page-sub">System-wide appointment and treatment records</p>

    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <!-- Filters -->
    <div class="card filter-card">
      <div class="filter-row">
        <div class="form-group" style="margin-bottom:0">
          <label class="form-label">Status</label>
          <select class="form-control" v-model="filters.status">
            <option value="">All statuses</option>
            <option v-for="s in ['Booked','Confirmed','Treated','Completed','Cancelled']" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
        <div class="form-group" style="margin-bottom:0">
          <label class="form-label">Doctor ID</label>
          <input class="form-control" v-model="filters.doctor_id" placeholder="e.g. 2" type="number" />
        </div>
        <div class="form-group" style="margin-bottom:0">
          <label class="form-label">Patient ID</label>
          <input class="form-control" v-model="filters.patient_id" placeholder="e.g. 3" type="number" />
        </div>
        <div class="form-group" style="margin-bottom:0">
          <label class="form-label">From date</label>
          <input type="date" class="form-control" v-model="filters.from_date" />
        </div>
        <div class="form-group" style="margin-bottom:0">
          <label class="form-label">To date</label>
          <input type="date" class="form-control" v-model="filters.to_date" />
        </div>
        <div class="filter-btns">
          <button class="btn btn-primary" @click="applyFilters">Apply</button>
          <button class="btn btn-secondary" @click="resetFilters">Reset</button>
        </div>
      </div>
    </div>

    <!-- Main layout: table + treatment panel -->
    <div class="appt-layout" :class="{ 'panel-open': selectedTreatment }">
      <div class="card">
        <div class="card-header">
          <span style="font-size:14px;color:var(--muted)">{{ total }} appointments found</span>
        </div>
        <div v-if="loading" class="loading"><span class="spinner"></span></div>
        <div v-else-if="!appointments.length" class="empty-state">
          <div class="icon">📭</div><p>No appointments match your filters</p>
        </div>
        <div v-else>
          <div style="overflow-x:auto">
            <table>
              <thead>
                <tr><th>#</th><th>Date</th><th>Time</th><th>Patient</th><th>Doctor</th><th>Status</th><th>Treatment</th></tr>
              </thead>
              <tbody>
                <tr v-for="a in appointments" :key="a.id">
                  <td class="muted">{{ a.id }}</td>
                  <td>{{ a.date }}</td>
                  <td>{{ a.time }}</td>
                  <td>
                    <div style="font-weight:500">{{ a.patient?.username || '—' }}</div>
                    <div class="muted">{{ a.patient?.email }}</div>
                  </td>
                  <td>
                    <div style="font-weight:500">{{ a.doctor?.username || '—' }}</div>
                    <div class="muted">{{ a.doctor?.specialization }}</div>
                  </td>
                  <td><span :class="`badge badge-${a.status.toLowerCase()}`">{{ a.status }}</span></td>
                  <td>
                    <button
                      v-if="a.treatment"
                      class="btn btn-sm btn-secondary"
                      @click="viewTreatment(a)"
                    >View Rx</button>
                    <span v-else class="muted">No Rx</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Pagination -->
          <div class="pagination" v-if="totalPages() > 1">
            <button class="btn btn-sm btn-secondary" :disabled="page===1" @click="page--;load()">← Prev</button>
            <span class="page-info">Page {{ page }} of {{ totalPages() }}</span>
            <button class="btn btn-sm btn-secondary" :disabled="page>=totalPages()" @click="page++;load()">Next →</button>
          </div>
        </div>
      </div>

      <!-- Treatment detail panel -->
      <div class="treatment-panel card" v-if="selectedTreatment || treatmentLoading">
        <div class="card-header">
          <h3 style="font-size:1rem">Treatment record</h3>
          <button class="btn btn-sm btn-secondary" @click="selectedTreatment=null">✕ Close</button>
        </div>
        <div v-if="treatmentLoading" class="loading"><span class="spinner"></span></div>
        <div v-else-if="selectedTreatment" class="card-body">
          <div class="rx-meta">
            <div>Appointment <strong>#{{ selectedTreatment.appt.id }}</strong></div>
            <div class="muted">{{ selectedTreatment.appt.date }} · {{ selectedTreatment.appt.time }}</div>
            <div class="muted">Patient: {{ selectedTreatment.appt.patient?.username }}</div>
            <div class="muted">Doctor: {{ selectedTreatment.appt.doctor?.username }}</div>
          </div>
          <div class="rx-divider"></div>
          <div class="rx-field">
            <div class="rx-label">Diagnosis</div>
            <div class="rx-value">{{ selectedTreatment.treatment?.diagnosis || '—' }}</div>
          </div>
          <div class="rx-field">
            <div class="rx-label">Prescription</div>
            <div class="rx-value">{{ selectedTreatment.treatment?.prescription || '—' }}</div>
          </div>
          <div class="rx-field">
            <div class="rx-label">Doctor's notes</div>
            <div class="rx-value">{{ selectedTreatment.treatment?.treatment_notes || '—' }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.filter-card { padding: 16px 20px; margin-bottom: 20px; }
.filter-row { display: flex; gap: 12px; flex-wrap: wrap; align-items: flex-end; }
.filter-row .form-group { flex: 1; min-width: 140px; }
.filter-btns { display: flex; gap: 8px; align-items: flex-end; flex-shrink: 0; }
.appt-layout { display: grid; grid-template-columns: 1fr; gap: 20px; }
.appt-layout.panel-open { grid-template-columns: 1fr 340px; }
.pagination { display: flex; align-items: center; gap: 12px; padding: 14px 16px; border-top: 1px solid var(--border); }
.page-info { font-size: 13px; color: var(--muted); }
.muted { color: var(--muted); font-size: 13px; }
.rx-meta { font-size: 13px; line-height: 1.8; margin-bottom: 12px; }
.rx-divider { border-top: 1px solid var(--border); margin-bottom: 14px; }
.rx-field { margin-bottom: 14px; }
.rx-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); margin-bottom: 4px; }
.rx-value { font-size: 14px; color: var(--navy); line-height: 1.6; white-space: pre-wrap; }
@media (max-width: 900px) { .appt-layout.panel-open { grid-template-columns: 1fr; } }
</style>
