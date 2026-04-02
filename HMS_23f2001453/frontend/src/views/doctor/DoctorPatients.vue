<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api'

const patients = ref([])
const loading = ref(true)
const error = ref('')
const search = ref('')
const selectedPatient = ref(null)
const history = ref([])
const historyLoading = ref(false)

onMounted(async () => {
  try {
    const data = await api.getDoctorPatients()
    patients.value = data.patients
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
})

const filtered = () => search.value
  ? patients.value.filter(p =>
      p.username?.toLowerCase().includes(search.value.toLowerCase()) ||
      p.email?.toLowerCase().includes(search.value.toLowerCase())
    )
  : patients.value

async function viewHistory(patient) {
  selectedPatient.value = patient
  historyLoading.value = true
  history.value = []
  try {
    const data = await api.getPatientHistory(patient.patient_id)
    history.value = data.history
  } catch (e) { error.value = e.message }
  finally { historyLoading.value = false }
}
</script>

<template>
  <div class="container">
    <h1 class="page-title">My patients</h1>
    <p class="page-sub">All patients who have had appointments with you</p>

    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <div class="layout">
      <!-- Patient list -->
      <div class="patient-panel card">
        <div class="card-header" style="padding:12px 16px">
          <input class="form-control" v-model="search" placeholder="Search patients…" style="font-size:13px;padding:7px 10px" />
        </div>
        <div v-if="loading" class="loading"><span class="spinner"></span></div>
        <div v-else-if="!filtered().length" class="empty-state"><div class="icon">👥</div><p>No patients found</p></div>
        <div v-else class="patient-list">
          <div
            v-for="p in filtered()" :key="p.patient_id"
            class="patient-item"
            :class="{ active: selectedPatient?.patient_id === p.patient_id }"
            @click="viewHistory(p)"
          >
            <div class="p-avatar">{{ p.username?.[0]?.toUpperCase() }}</div>
            <div>
              <div class="p-name">{{ p.username }}</div>
              <div class="p-email">{{ p.email }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- History panel -->
      <div class="history-panel card">
        <div v-if="!selectedPatient" class="empty-state" style="padding:60px 24px">
          <div class="icon">👈</div>
          <p>Select a patient to view their history</p>
        </div>
        <template v-else>
          <div class="card-header">
            <div>
              <div style="font-weight:600">{{ selectedPatient.username }}</div>
              <div style="font-size:12px;color:var(--muted)">{{ selectedPatient.email }} · {{ selectedPatient.phone }}</div>
            </div>
            <div class="patient-meta">
              <span v-if="selectedPatient.age" class="badge badge-booked">Age {{ selectedPatient.age }}</span>
              <span v-if="selectedPatient.gender" class="badge" style="background:var(--bg);color:var(--slate)">{{ selectedPatient.gender }}</span>
            </div>
          </div>
          <div v-if="historyLoading" class="loading"><span class="spinner"></span></div>
          <div v-else-if="!history.length" class="empty-state"><div class="icon">📭</div><p>No appointment history</p></div>
          <div v-else>
            <table>
              <thead><tr><th>Date</th><th>Time</th><th>Status</th><th>Diagnosis</th></tr></thead>
              <tbody>
                <tr v-for="h in history" :key="h.appointment_id">
                  <td>{{ h.date }}</td>
                  <td>{{ h.time }}</td>
                  <td><span :class="`badge badge-${h.status.toLowerCase()}`">{{ h.status }}</span></td>
                  <td>
                    <span v-if="h.treatment">{{ h.treatment.diagnosis || '—' }}</span>
                    <span v-else class="muted">No treatment yet</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.layout { display: grid; grid-template-columns: 280px 1fr; gap: 20px; align-items: start; }
.patient-list { display: flex; flex-direction: column; gap: 2px; padding: 8px; max-height: 560px; overflow-y: auto; }
.patient-item { display: flex; gap: 12px; align-items: center; padding: 10px 12px; border-radius: 8px; cursor: pointer; transition: background .15s; }
.patient-item:hover { background: var(--bg); }
.patient-item.active { background: var(--teal-lt); }
.p-avatar { width: 36px; height: 36px; border-radius: 50%; background: var(--navy); color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 13px; flex-shrink: 0; }
.p-name { font-weight: 500; font-size: 14px; }
.p-email { font-size: 12px; color: var(--muted); }
.patient-meta { display: flex; gap: 6px; }
.muted { color: var(--muted); font-size: 13px; }
@media (max-width: 700px) { .layout { grid-template-columns: 1fr; } }
</style>
