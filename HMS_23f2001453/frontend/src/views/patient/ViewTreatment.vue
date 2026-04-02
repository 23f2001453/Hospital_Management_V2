<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../../api'

const route = useRoute()
const router = useRouter()
const treatment = ref(null)
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const data = await api.getMyTreatment(route.params.id)
    treatment.value = data.treatment
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
})
</script>

<template>
  <div class="container" style="max-width:640px">
    <button class="btn btn-secondary btn-sm" style="margin-bottom:20px" @click="router.back()">← Back</button>

    <div v-if="loading" class="loading"><span class="spinner"></span></div>
    <div v-else-if="error" class="alert alert-error">{{ error }}</div>
    <div v-else-if="treatment">
      <h1 class="page-title">Treatment record</h1>
      <p class="page-sub">Appointment #{{ treatment.appointment_id }} · {{ treatment.appointment_date }} at {{ treatment.appointment_time }}</p>

      <div class="card">
        <div class="rx-section">
          <div class="rx-label">Diagnosis</div>
          <div class="rx-value">{{ treatment.diagnosis || '—' }}</div>
        </div>
        <div class="rx-section">
          <div class="rx-label">Prescription</div>
          <div class="rx-value">{{ treatment.prescription || '—' }}</div>
        </div>
        <div class="rx-section" style="border-bottom:none">
          <div class="rx-label">Doctor's notes</div>
          <div class="rx-value">{{ treatment.treatment_notes || '—' }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.rx-section { padding: 20px 24px; border-bottom: 1px solid var(--border); }
.rx-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .07em; color: var(--muted); margin-bottom: 8px; }
.rx-value { font-size: 15px; color: var(--navy); line-height: 1.6; white-space: pre-wrap; }
</style>
