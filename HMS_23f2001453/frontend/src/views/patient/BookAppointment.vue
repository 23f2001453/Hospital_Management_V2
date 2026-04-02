<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../../api'

const router = useRouter()
const doctors = ref([])
const slots = ref([])
const selectedDoctor = ref(null)
const loading = ref(false)
const slotsLoading = ref(false)
const error = ref('')
const success = ref('')

onMounted(async () => {
  loading.value = true
  try {
    const data = await api.getDoctors()
    doctors.value = data.doctors
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
})

async function selectDoctor(doc) {
  selectedDoctor.value = doc
  slots.value = []
  slotsLoading.value = true
  try {
    const data = await api.getDoctorSlots(doc.id)
    slots.value = data.slots
  } catch (e) { error.value = e.message }
  finally { slotsLoading.value = false }
}

async function book(slotId) {
  try {
    await api.bookSlot(slotId)
    success.value = 'Appointment booked successfully!'
    const s = slots.value.find(x => x.id === slotId)
    if (s) { s.booked_count++; s.remaining--; if (s.remaining <= 0) s.is_full = true }
    setTimeout(() => router.push('/patient/dashboard'), 1500)
  } catch (e) { error.value = e.message }
}
</script>

<template>
  <div class="container">
    <h1 class="page-title">Book an appointment</h1>
    <p class="page-sub">Choose a doctor and pick an available time slot</p>

    <div v-if="error" class="alert alert-error">{{ error }}</div>
    <div v-if="success" class="alert alert-success">{{ success }}</div>

    <div class="book-layout">
      <!-- Doctor list -->
      <div class="doctor-panel card">
        <div class="card-header"><h3 style="font-size:1rem">Select a doctor</h3></div>
        <div v-if="loading" class="loading"><span class="spinner"></span></div>
        <div v-else class="doctor-list">
          <div
            v-for="doc in doctors" :key="doc.id"
            class="doctor-item"
            :class="{ active: selectedDoctor?.id === doc.id }"
            @click="selectDoctor(doc)"
          >
            <div class="doc-avatar">{{ doc.username?.[0]?.toUpperCase() }}</div>
            <div>
              <div class="doc-name">{{ doc.username }}</div>
              <div class="doc-spec">{{ doc.specialization || 'General' }}</div>
              <div class="doc-dept" v-if="doc.department_name">{{ doc.department_name }}</div>
            </div>
          </div>
          <div v-if="!doctors.length" class="empty-state"><p>No doctors available</p></div>
        </div>
      </div>

      <!-- Slots -->
      <div class="slots-panel card">
        <div class="card-header">
          <h3 style="font-size:1rem">
            {{ selectedDoctor ? `Available slots — ${selectedDoctor.username}` : 'Select a doctor to see slots' }}
          </h3>
        </div>
        <div v-if="!selectedDoctor" class="empty-state">
          <div class="icon">👈</div>
          <p>Pick a doctor from the list</p>
        </div>
        <div v-else-if="slotsLoading" class="loading"><span class="spinner"></span> Loading slots…</div>
        <div v-else-if="!slots.length" class="empty-state">
          <div class="icon">📭</div>
          <p>No available slots for this doctor</p>
        </div>
        <div v-else class="slots-grid">
          <div
            v-for="slot in slots" :key="slot.id"
            class="slot-card"
            :class="{ full: slot.is_full }"
          >
            <div class="slot-date">{{ slot.date }}</div>
            <div class="slot-time">{{ slot.start_time }} – {{ slot.end_time }}</div>
            <div class="slot-cap">
              <span class="badge" :class="slot.is_full ? 'badge-cancelled' : 'badge-open'">
                {{ slot.is_full ? 'Full' : `${slot.remaining} left` }}
              </span>
            </div>
            <button
              class="btn btn-primary btn-sm slot-btn"
              :disabled="slot.is_full"
              @click="book(slot.id)"
            >{{ slot.is_full ? 'Full' : 'Book' }}</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.book-layout { display: grid; grid-template-columns: 300px 1fr; gap: 20px; align-items: start; }
.doctor-list { padding: 8px; display: flex; flex-direction: column; gap: 4px; max-height: 560px; overflow-y: auto; }
.doctor-item { display: flex; gap: 12px; align-items: center; padding: 12px; border-radius: 8px; cursor: pointer; transition: background .15s; }
.doctor-item:hover { background: var(--bg); }
.doctor-item.active { background: var(--teal-lt); }
.doc-avatar { width: 40px; height: 40px; border-radius: 50%; background: var(--teal); color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 600; flex-shrink: 0; }
.doc-name { font-weight: 500; font-size: 14px; }
.doc-spec { font-size: 12px; color: var(--teal2); font-weight: 500; }
.doc-dept { font-size: 12px; color: var(--muted); }

.slots-grid { padding: 16px; display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.slot-card { border: 1px solid var(--border); border-radius: 10px; padding: 16px; display: flex; flex-direction: column; gap: 8px; }
.slot-card.full { opacity: .6; }
.slot-date { font-size: 13px; color: var(--muted); }
.slot-time { font-weight: 600; font-size: 15px; color: var(--navy); }
.slot-btn { width: 100%; justify-content: center; }

@media (max-width: 700px) {
  .book-layout { grid-template-columns: 1fr; }
}
</style>
