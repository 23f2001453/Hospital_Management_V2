<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api'

const slots = ref([])
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const success = ref('')
const showForm = ref(false)
const editingSlot = ref(null)

const form = ref({ date: '', start_time: '', end_time: '', slot_capacity: 1 })
const editForm = ref({ date: '', start_time: '', end_time: '', slot_capacity: 1, status: 'open' })

onMounted(load)

async function load() {
  loading.value = true
  try {
    const data = await api.getMySlots()
    slots.value = data.slots
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
}

async function createSlot() {
  saving.value = true
  error.value = ''
  try {
    const data = await api.createSlot({ ...form.value, slot_capacity: Number(form.value.slot_capacity) })
    slots.value.unshift(data.slot)
    success.value = 'Slot created successfully!'
    showForm.value = false
    form.value = { date: '', start_time: '', end_time: '', slot_capacity: 1 }
    setTimeout(() => success.value = '', 3000)
  } catch (e) { error.value = e.message }
  finally { saving.value = false }
}

function startEdit(slot) {
  editingSlot.value = slot.id
  editForm.value = {
    date: slot.date,
    start_time: slot.start_time,
    end_time: slot.end_time,
    slot_capacity: slot.slot_capacity,
    status: slot.status
  }
}

async function saveEdit(slotId) {
  saving.value = true
  error.value = ''
  try {
    const data = await api.updateSlot(slotId, { ...editForm.value, slot_capacity: Number(editForm.value.slot_capacity) })
    const idx = slots.value.findIndex(s => s.id === slotId)
    if (idx !== -1) slots.value[idx] = data.slot
    editingSlot.value = null
    success.value = 'Slot updated!'
    setTimeout(() => success.value = '', 3000)
  } catch (e) { error.value = e.message }
  finally { saving.value = false }
}

async function deleteSlot(slotId) {
  if (!confirm('Delete this slot? This cannot be undone.')) return
  try {
    await api.deleteSlot(slotId)
    slots.value = slots.value.filter(s => s.id !== slotId)
    success.value = 'Slot deleted.'
    setTimeout(() => success.value = '', 3000)
  } catch (e) { error.value = e.message }
}
</script>

<template>
  <div class="container">
    <div class="page-top">
      <div>
        <h1 class="page-title">Availability slots</h1>
        <p class="page-sub">Manage when you're available for appointments</p>
      </div>
      <button class="btn btn-primary" @click="showForm = !showForm">
        {{ showForm ? '✕ Cancel' : '+ New slot' }}
      </button>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>
    <div v-if="success" class="alert alert-success">{{ success }}</div>

    <!-- Create form -->
    <div v-if="showForm" class="card new-slot-card">
      <div class="card-header"><h3 style="font-size:1rem">New availability slot</h3></div>
      <div class="card-body">
        <form @submit.prevent="createSlot">
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Date *</label>
              <input type="date" class="form-control" v-model="form.date" required />
            </div>
            <div class="form-group">
              <label class="form-label">Max patients *</label>
              <input type="number" class="form-control" v-model="form.slot_capacity" min="1" required />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Start time *</label>
              <input type="time" class="form-control" v-model="form.start_time" required />
            </div>
            <div class="form-group">
              <label class="form-label">End time *</label>
              <input type="time" class="form-control" v-model="form.end_time" required />
            </div>
          </div>
          <button type="submit" class="btn btn-primary" :disabled="saving">
            <span v-if="saving" class="spinner"></span>
            {{ saving ? 'Creating…' : 'Create slot' }}
          </button>
        </form>
      </div>
    </div>

    <!-- Slots list -->
    <div v-if="loading" class="loading"><span class="spinner"></span> Loading slots…</div>
    <div v-else-if="!slots.length" class="empty-state card" style="padding:48px">
      <div class="icon">📅</div>
      <p>No availability slots yet. Create your first one above.</p>
    </div>
    <div v-else class="slots-list">
      <div v-for="slot in slots" :key="slot.id" class="slot-row card">
        <!-- View mode -->
        <template v-if="editingSlot !== slot.id">
          <div class="slot-info">
            <div class="slot-date">{{ slot.date }}</div>
            <div class="slot-time">{{ slot.start_time }} – {{ slot.end_time }}</div>
          </div>
          <div class="slot-caps">
            <div class="cap-item">
              <span class="cap-label">Capacity</span>
              <span class="cap-val">{{ slot.slot_capacity }}</span>
            </div>
            <div class="cap-item">
              <span class="cap-label">Booked</span>
              <span class="cap-val">{{ slot.booked_count }}</span>
            </div>
            <div class="cap-item">
              <span class="cap-label">Remaining</span>
              <span class="cap-val" :style="slot.remaining === 0 ? 'color:var(--red)' : 'color:var(--teal)'">{{ slot.remaining }}</span>
            </div>
          </div>
          <span :class="`badge badge-${slot.status}`">{{ slot.status }}</span>
          <div class="slot-actions">
            <button class="btn btn-sm btn-secondary" @click="startEdit(slot)">Edit</button>
            <button class="btn btn-sm btn-danger" @click="deleteSlot(slot.id)">Delete</button>
          </div>
        </template>

        <!-- Edit mode -->
        <template v-else>
          <form class="edit-form" @submit.prevent="saveEdit(slot.id)">
            <div class="form-row" style="gap:12px">
              <div class="form-group" style="margin-bottom:0">
                <label class="form-label">Date</label>
                <input type="date" class="form-control" v-model="editForm.date" required />
              </div>
              <div class="form-group" style="margin-bottom:0">
                <label class="form-label">Start</label>
                <input type="time" class="form-control" v-model="editForm.start_time" required />
              </div>
              <div class="form-group" style="margin-bottom:0">
                <label class="form-label">End</label>
                <input type="time" class="form-control" v-model="editForm.end_time" required />
              </div>
              <div class="form-group" style="margin-bottom:0">
                <label class="form-label">Capacity</label>
                <input type="number" class="form-control" v-model="editForm.slot_capacity" min="1" required />
              </div>
              <div class="form-group" style="margin-bottom:0">
                <label class="form-label">Status</label>
                <select class="form-control" v-model="editForm.status">
                  <option value="open">Open</option>
                  <option value="blocked">Blocked</option>
                </select>
              </div>
            </div>
            <div class="edit-btns">
              <button type="submit" class="btn btn-sm btn-primary" :disabled="saving">Save</button>
              <button type="button" class="btn btn-sm btn-secondary" @click="editingSlot = null">Cancel</button>
            </div>
          </form>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-top { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 8px; }
.new-slot-card { margin-bottom: 24px; border-color: var(--teal); }
.slots-list { display: flex; flex-direction: column; gap: 12px; }
.slot-row { display: flex; align-items: center; gap: 24px; padding: 16px 20px; }
.slot-info { flex: 1; }
.slot-date { font-size: 13px; color: var(--muted); }
.slot-time { font-weight: 600; font-size: 15px; }
.slot-caps { display: flex; gap: 20px; }
.cap-item { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.cap-label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; }
.cap-val { font-weight: 600; font-size: 15px; }
.slot-actions { display: flex; gap: 8px; }
.edit-form { width: 100%; display: flex; flex-direction: column; gap: 12px; }
.edit-btns { display: flex; gap: 8px; }

@media (max-width: 700px) {
  .slot-row { flex-direction: column; align-items: flex-start; }
}
</style>
