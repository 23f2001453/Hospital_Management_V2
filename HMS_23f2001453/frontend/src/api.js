// src/api.js
const BASE = 'http://127.0.0.1:5000/api'

function getToken() {
  return localStorage.getItem('auth_token')
}

async function request(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  const token = getToken()
  if (token) headers['Authentication-Token'] = token

  const res = await fetch(`${BASE}${path}`, { ...options, headers })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || data.message || 'Request failed')
  return data
}

export const api = {
  // ── Auth ──────────────────────────────────────────────────────────────
  login:         (email, password) => request('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  register:      (payload)         => request('/auth/register', { method: 'POST', body: JSON.stringify(payload) }),
  logout:        ()                => request('/auth/logout', { method: 'POST' }),
  me:            ()                => request('/auth/me'),
  updateProfile: (payload)         => request('/auth/profile', { method: 'PUT', body: JSON.stringify(payload) }),

  // ── Doctors ───────────────────────────────────────────────────────────
  getDoctors:    (params = '') => request(`/doctors${params}`),
  getDoctorSlots:(doctorId, params = '') => request(`/doctors/${doctorId}/availability${params}`),

  // ── Doctor availability ────────────────────────────────────────────────
  getMySlots:  (params = '') => request(`/doctor/availability${params}`),
  createSlot:  (payload)     => request('/doctor/availability', { method: 'POST', body: JSON.stringify(payload) }),
  updateSlot:  (id, payload) => request(`/doctor/availability/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteSlot:  (id)          => request(`/doctor/availability/${id}`, { method: 'DELETE' }),

  // ── Doctor appointments ───────────────────────────────────────────────
  getDoctorAppointments:    (params = '') => request(`/doctor/appointments${params}`),
  updateAppointmentStatus:  (id, status) => request(`/doctor/appointments/${id}/status`, { method: 'POST', body: JSON.stringify({ status }) }),
  getDoctorPatients:        ()           => request('/doctor/patients'),

  // ── Treatment ─────────────────────────────────────────────────────────
  saveTreatment:    (apptId, payload) => request(`/doctor/appointments/${apptId}/treat`, { method: 'POST', body: JSON.stringify(payload) }),
  updateTreatment:  (apptId, payload) => request(`/doctor/appointments/${apptId}/treat`, { method: 'PUT', body: JSON.stringify(payload) }),
  getTreatment:     (apptId)          => request(`/doctor/appointments/${apptId}/treat`),
  getPatientHistory:(patientId)       => request(`/doctor/patients/${patientId}/history`),

  // ── Patient ───────────────────────────────────────────────────────────
  bookSlot:          (slotId)  => request(`/appointments/book/${slotId}`, { method: 'POST' }),
  getMyAppointments: (params = '') => request(`/appointments/my${params}`),
  cancelAppointment: (id)      => request(`/appointments/${id}/cancel`, { method: 'POST' }),
  getMyTreatment:    (apptId)  => request(`/appointments/${apptId}/treatment`),

  // ── Patient async export ──────────────────────────────────────────────
  triggerExport:     ()        => request('/patient/export-csv', { method: 'POST' }),
  getJobStatus:      (taskId)  => request(`/jobs/${taskId}`),

  // ── Admin — users ─────────────────────────────────────────────────────
  getUsers:    (params = '') => request(`/admin/users${params}`),
  getUser:     (id)          => request(`/admin/users/${id}`),
  updateUser:  (id, payload) => request(`/admin/users/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteUser:  (id)          => request(`/admin/users/${id}`, { method: 'DELETE' }),
  blacklist:   (id)          => request(`/admin/users/${id}/blacklist`, { method: 'POST' }),
  unblacklist: (id)          => request(`/admin/users/${id}/blacklist`, { method: 'DELETE' }),

  // ── Admin — search ────────────────────────────────────────────────────
  adminSearch: (q, type = '') => request(`/admin/search?q=${encodeURIComponent(q)}${type ? '&type=' + type : ''}`),

  // ── Admin — appointments & treatments ────────────────────────────────
  adminGetAppointments:     (params = '') => request(`/admin/appointments${params}`),
  adminGetTreatmentDetail:  (apptId)      => request(`/admin/appointments/${apptId}/treatment`),
}
