// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login',    name: 'Login',    component: () => import('../views/LoginView.vue'),    meta: { guest: true } },
  { path: '/register', name: 'Register', component: () => import('../views/RegisterView.vue'), meta: { guest: true } },

  // ── Patient ────────────────────────────────────────────────────────────
  { path: '/patient/dashboard',     name: 'PatientDashboard',  component: () => import('../views/patient/PatientDashboard.vue'),  meta: { role: 'patient' } },
  { path: '/patient/book',          name: 'BookAppointment',   component: () => import('../views/patient/BookAppointment.vue'),   meta: { role: 'patient' } },
  { path: '/patient/appointments',  name: 'MyAppointments',    component: () => import('../views/patient/MyAppointments.vue'),    meta: { role: 'patient' } },
  { path: '/patient/treatment/:id', name: 'ViewTreatment',     component: () => import('../views/patient/ViewTreatment.vue'),     meta: { role: 'patient' } },

  // ── Doctor ────────────────────────────────────────────────────────────
  { path: '/doctor/dashboard',    name: 'DoctorDashboard',    component: () => import('../views/doctor/DoctorDashboard.vue'),   meta: { role: 'doctor' } },
  { path: '/doctor/appointments', name: 'DoctorAppointments', component: () => import('../views/doctor/DoctorAppointments.vue'),meta: { role: 'doctor' } },
  { path: '/doctor/availability', name: 'DoctorAvailability', component: () => import('../views/doctor/DoctorAvailability.vue'),meta: { role: 'doctor' } },
  { path: '/doctor/patients',     name: 'DoctorPatients',     component: () => import('../views/doctor/DoctorPatients.vue'),    meta: { role: 'doctor' } },
  { path: '/doctor/treat/:id',    name: 'TreatPatient',       component: () => import('../views/doctor/TreatPatient.vue'),      meta: { role: 'doctor' } },

  // ── Admin ─────────────────────────────────────────────────────────────
  { path: '/admin/dashboard',          name: 'AdminDashboard',      component: () => import('../views/admin/AdminDashboard.vue'),      meta: { role: 'admin' } },
  { path: '/admin/users',              name: 'AdminUsers',          component: () => import('../views/admin/AdminUsers.vue'),          meta: { role: 'admin' } },
  { path: '/admin/users/:id/edit',     name: 'AdminEditUser',       component: () => import('../views/admin/AdminEditUser.vue'),       meta: { role: 'admin' } },
  { path: '/admin/appointments',       name: 'AdminAppointments',   component: () => import('../views/admin/AdminAppointments.vue'),   meta: { role: 'admin' } },
  { path: '/admin/search',             name: 'AdminSearch',         component: () => import('../views/admin/AdminSearch.vue'),         meta: { role: 'admin' } },

  // ── Shared ────────────────────────────────────────────────────────────
  { path: '/profile', name: 'Profile', component: () => import('../views/ProfileView.vue'), meta: { auth: true } },

  { path: '/:pathMatch(.*)*', redirect: '/login' },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.guest && auth.isLoggedIn)              return roleDashboard(auth.role)
  if ((to.meta.auth || to.meta.role) && !auth.isLoggedIn) return { name: 'Login' }
  if (to.meta.role && auth.role !== to.meta.role)    return roleDashboard(auth.role)
})

export function roleDashboard(role) {
  if (role === 'admin')   return { name: 'AdminDashboard' }
  if (role === 'doctor')  return { name: 'DoctorDashboard' }
  if (role === 'patient') return { name: 'PatientDashboard' }
  return { name: 'Login' }
}

export default router
