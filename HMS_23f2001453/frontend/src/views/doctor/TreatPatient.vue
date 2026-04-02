<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../../api'

const route = useRoute()
const router = useRouter()

const appointmentId = Number(route.params.id)
const existing = ref(null)
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const success = ref('')

const form = ref({ diagnosis: '', prescription: '', treatment_notes: '' })

onMounted(async () => {
  try {
    const data = await api.getTreatment(appointmentId)
    existing.value = data.treatment
    form.value.diagnosis      = data.treatment.diagnosis      || ''
    form.value.prescription   = data.treatment.prescription   || ''
    form.value.treatment_notes= data.treatment.treatment_notes|| ''
  } catch (_) {
    // 404 means no treatment yet — that's fine
  } finally {
    loading.value = false
  }
})

async function save() {
  if (!form.value.diagnosis.trim()) { error.value = 'Diagnosis is required.'; return }
  saving.value = true
  error.value = ''
  try {
    if (existing.value) {
      await api.updateTreatment(appointmentId, form.value)
      success.value = 'Treatment updated successfully!'
    } else {
      await api.saveTreatment(appointmentId, form.value)
      success.value = 'Treatment saved! Appointment marked as Completed.'
    }
    setTimeout(() => router.push('/doctor/appointments'), 1500)
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="container" style="max-width:640px">
    <button class="btn btn-secondary btn-sm" style="margin-bottom:20px" @click="router.back()">← Back</button>

    <h1 class="page-title">{{ existing ? 'Update treatment' : 'Add treatment' }}</h1>
    <p class="page-sub">Appointment #{{ appointmentId }}</p>

    <div v-if="loading" class="loading"><span class="spinner"></span></div>
    <div v-else class="card">
      <div class="card-body">
        <div v-if="error" class="alert alert-error">{{ error }}</div>
        <div v-if="success" class="alert alert-success">{{ success }}</div>

        <form @submit.prevent="save">
          <div class="form-group">
            <label class="form-label">Diagnosis *</label>
            <textarea class="form-control" v-model="form.diagnosis" rows="3" placeholder="Primary diagnosis…" required></textarea>
          </div>
          <div class="form-group">
            <label class="form-label">Prescription</label>
            <textarea class="form-control" v-model="form.prescription" rows="4" placeholder="Medications, dosage, instructions…"></textarea>
          </div>
          <div class="form-group">
            <label class="form-label">Doctor's notes</label>
            <textarea class="form-control" v-model="form.treatment_notes" rows="3" placeholder="Follow-up instructions, observations…"></textarea>
          </div>

          <div v-if="!existing" class="info-box">
            ℹ️ Saving this treatment will automatically mark the appointment as <strong>Completed</strong>.
          </div>

          <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;padding:11px" :disabled="saving">
            <span v-if="saving" class="spinner"></span>
            {{ saving ? 'Saving…' : existing ? 'Update treatment' : 'Save treatment' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.info-box {
  background: var(--blue-lt); color: #1e40af;
  border: 1px solid #bfdbfe; border-radius: 8px;
  padding: 12px 16px; font-size: 13px; margin-bottom: 16px;
}
textarea.form-control { resize: vertical; min-height: 80px; }
</style>
