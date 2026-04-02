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
  // Auth
  login: (email, password) =>
    request('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  register: (payload) =>
    request('/auth/register', { method: 'POST', body: JSON.stringify(payload) }),
  logout: () => request('/auth/logout', { method: 'POST' }),
  me: () => request('/auth/me'),
  updateProfile: (payload) =>
    request('/auth/profile', { method: 'PUT', body: JSON.stringify(payload) }),

  // Doctors
  getDoctors: (params = '') => request(`/doctors${params}`),
  getDoctorSlots: (doctorId, params = '') =>
    request(`/doctors/${doctorId}/availability${params}`),

  // Doctor availability management
  getMySlots: (params = '') => request(`/doctor/availability${params}`),
  createSlot: (payload) =>
    request('/doctor/availability', { method: 'POST', body: JSON.stringify(payload) }),
  updateSlot: (slotId, payload) =>
    request(`/doctor/availability/${slotId}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteSlot: (slotId) =>
    request(`/doctor/availability/${slotId}`, { method: 'DELETE' }),

  // Doctor appointments
  getDoctorAppointments: (params = '') => request(`/doctor/appointments${params}`),
  updateAppointmentStatus: (id, status) =>
    request(`/doctor/appointments/${id}/status`, { method: 'POST', body: JSON.stringify({ status }) }),
  getDoctorPatients: () => request('/doctor/patients'),

  // Treatment
  saveTreatment: (appointmentId, payload) =>
    request(`/doctor/appointments/${appointmentId}/treat`, { method: 'POST', body: JSON.stringify(payload) }),
  updateTreatment: (appointmentId, payload) =>
    request(`/doctor/appointments/${appointmentId}/treat`, { method: 'PUT', body: JSON.stringify(payload) }),
  getTreatment: (appointmentId) =>
    request(`/doctor/appointments/${appointmentId}/treat`),
  getPatientHistory: (patientId) =>
    request(`/doctor/patients/${patientId}/history`),

  // Patient
  bookSlot: (slotId) =>
    request(`/appointments/book/${slotId}`, { method: 'POST' }),
  getMyAppointments: (params = '') => request(`/appointments/my${params}`),
  cancelAppointment: (id) =>
    request(`/appointments/${id}/cancel`, { method: 'POST' }),
  getMyTreatment: (appointmentId) =>
    request(`/appointments/${appointmentId}/treatment`),

  // Admin
  getUsers: (params = '') => request(`/admin/users${params}`),
  getUser: (id) => request(`/admin/users/${id}`),
  updateUser: (id, payload) =>
    request(`/admin/users/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteUser: (id) =>
    request(`/admin/users/${id}`, { method: 'DELETE' }),
}
