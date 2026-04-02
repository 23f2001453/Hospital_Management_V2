<script setup>
import { computed } from 'vue'
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()
const router = useRouter()

async function logout() {
  await auth.logout()
  router.push('/login')
}

const navLinks = computed(() => {
  if (!auth.isLoggedIn) return []
  if (auth.isAdmin) return [
    { to: '/admin/dashboard', label: 'Dashboard' },
    { to: '/admin/users',     label: 'Users' },
  ]
  if (auth.isDoctor) return [
    { to: '/doctor/dashboard',    label: 'Dashboard' },
    { to: '/doctor/appointments', label: 'Appointments' },
    { to: '/doctor/availability', label: 'Availability' },
    { to: '/doctor/patients',     label: 'My Patients' },
  ]
  if (auth.isPatient) return [
    { to: '/patient/dashboard',    label: 'Dashboard' },
    { to: '/patient/book',         label: 'Book' },
    { to: '/patient/appointments', label: 'My Appointments' },
  ]
  return []
})
</script>

<template>
  <div class="app-shell">
    <nav class="topnav" v-if="auth.isLoggedIn">
      <div class="nav-inner">
        <RouterLink class="brand" to="/">
          <span class="brand-cross">✚</span>
          <span class="brand-name">MediCore</span>
        </RouterLink>

        <div class="nav-links">
          <RouterLink
            v-for="link in navLinks"
            :key="link.to"
            :to="link.to"
            class="nav-link"
          >{{ link.label }}</RouterLink>
        </div>

        <div class="nav-right">
          <RouterLink to="/profile" class="user-chip">
            <span class="user-avatar">{{ auth.user?.username?.[0]?.toUpperCase() }}</span>
            <span class="user-name">{{ auth.user?.username }}</span>
            <span class="role-badge" :class="auth.role">{{ auth.role }}</span>
          </RouterLink>
          <button class="logout-btn" @click="logout">Sign out</button>
        </div>
      </div>
    </nav>

    <main class="page-content" :class="{ 'no-nav': !auth.isLoggedIn }">
      <RouterView />
    </main>
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Instrument+Serif:ital@0;1&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --navy:    #0f172a;
  --navy2:   #1e293b;
  --slate:   #334155;
  --muted:   #64748b;
  --border:  #e2e8f0;
  --bg:      #f8fafc;
  --white:   #ffffff;
  --teal:    #0d9488;
  --teal2:   #0f766e;
  --teal-lt: #ccfbf1;
  --red:     #ef4444;
  --red-lt:  #fee2e2;
  --amber:   #f59e0b;
  --amber-lt:#fef3c7;
  --green:   #22c55e;
  --green-lt:#dcfce7;
  --blue:    #3b82f6;
  --blue-lt: #dbeafe;
  --radius:  10px;
  --shadow:  0 1px 3px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.06);
  --shadow-md: 0 4px 16px rgba(0,0,0,.1);
}

body {
  font-family: 'DM Sans', sans-serif;
  background: var(--bg);
  color: var(--navy);
  font-size: 15px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}

h1,h2,h3 { font-family: 'Instrument Serif', serif; font-weight: 400; letter-spacing: -.02em; }

.app-shell { min-height: 100vh; display: flex; flex-direction: column; }

/* ── Navbar ── */
.topnav {
  position: sticky; top: 0; z-index: 100;
  background: var(--white);
  border-bottom: 1px solid var(--border);
  box-shadow: var(--shadow);
}
.nav-inner {
  max-width: 1280px; margin: 0 auto;
  padding: 0 24px;
  height: 60px;
  display: flex; align-items: center; gap: 32px;
}
.brand {
  display: flex; align-items: center; gap: 8px;
  text-decoration: none; color: var(--navy); font-weight: 600; font-size: 17px;
  flex-shrink: 0;
}
.brand-cross { color: var(--teal); font-size: 20px; }
.nav-links { display: flex; gap: 4px; flex: 1; }
.nav-link {
  padding: 6px 14px; border-radius: 7px;
  text-decoration: none; color: var(--muted); font-size: 14px; font-weight: 500;
  transition: color .15s, background .15s;
}
.nav-link:hover         { color: var(--navy); background: var(--bg); }
.nav-link.router-link-active { color: var(--teal); background: var(--teal-lt); }

.nav-right { display: flex; align-items: center; gap: 12px; margin-left: auto; }

.user-chip {
  display: flex; align-items: center; gap: 8px;
  padding: 4px 10px 4px 4px;
  border: 1px solid var(--border); border-radius: 999px;
  text-decoration: none; color: var(--navy);
  transition: border-color .15s;
}
.user-chip:hover { border-color: var(--teal); }
.user-avatar {
  width: 28px; height: 28px; border-radius: 50%;
  background: var(--teal); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 600;
}
.user-name { font-size: 13px; font-weight: 500; }
.role-badge {
  font-size: 11px; font-weight: 600; padding: 2px 7px; border-radius: 999px;
  text-transform: uppercase; letter-spacing: .04em;
}
.role-badge.admin   { background: var(--navy); color: #fff; }
.role-badge.doctor  { background: var(--teal-lt); color: var(--teal2); }
.role-badge.patient { background: var(--blue-lt); color: var(--blue); }

.logout-btn {
  padding: 6px 16px; border-radius: 7px;
  border: 1px solid var(--border);
  background: var(--white); color: var(--muted);
  font-size: 13px; font-weight: 500; cursor: pointer;
  transition: all .15s;
}
.logout-btn:hover { border-color: var(--red); color: var(--red); background: var(--red-lt); }

/* ── Page ── */
.page-content { flex: 1; }
.page-content.no-nav { display: flex; align-items: center; justify-content: center; min-height: 100vh; }

/* ── Shared utilities ── */
.container { max-width: 1280px; margin: 0 auto; padding: 32px 24px; }
.card { background: var(--white); border: 1px solid var(--border); border-radius: var(--radius); box-shadow: var(--shadow); }
.card-body { padding: 24px; }
.card-header { padding: 18px 24px; border-bottom: 1px solid var(--border); display: flex; align-items: center; justify-content: space-between; }

.btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 18px; border-radius: 8px;
  font-size: 14px; font-weight: 500; cursor: pointer;
  border: 1px solid transparent; text-decoration: none;
  transition: all .15s;
}
.btn-primary { background: var(--teal); color: #fff; }
.btn-primary:hover { background: var(--teal2); }
.btn-secondary { background: var(--white); color: var(--navy); border-color: var(--border); }
.btn-secondary:hover { border-color: var(--teal); color: var(--teal); }
.btn-danger { background: var(--red-lt); color: var(--red); border-color: #fecaca; }
.btn-danger:hover { background: var(--red); color: #fff; }
.btn-sm { padding: 5px 12px; font-size: 13px; }

.form-group { margin-bottom: 18px; }
.form-label { display: block; font-size: 13px; font-weight: 500; color: var(--slate); margin-bottom: 6px; }
.form-control {
  width: 100%; padding: 9px 13px;
  border: 1px solid var(--border); border-radius: 8px;
  font-size: 14px; font-family: inherit; color: var(--navy);
  background: var(--white); outline: none;
  transition: border-color .15s, box-shadow .15s;
}
.form-control:focus { border-color: var(--teal); box-shadow: 0 0 0 3px rgba(13,148,136,.1); }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.form-row-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }

.badge {
  display: inline-flex; align-items: center;
  padding: 3px 10px; border-radius: 999px;
  font-size: 12px; font-weight: 600;
}
.badge-booked    { background: var(--blue-lt);   color: var(--blue); }
.badge-confirmed { background: var(--amber-lt);  color: #92400e; }
.badge-treated   { background: #ede9fe;           color: #5b21b6; }
.badge-completed { background: var(--green-lt);  color: #15803d; }
.badge-cancelled { background: var(--red-lt);    color: var(--red); }
.badge-open      { background: var(--green-lt);  color: #15803d; }
.badge-blocked   { background: var(--red-lt);    color: var(--red); }

.page-title { font-size: 2rem; color: var(--navy); margin-bottom: 4px; }
.page-sub   { color: var(--muted); font-size: 14px; margin-bottom: 28px; }

.alert { padding: 12px 16px; border-radius: 8px; font-size: 14px; margin-bottom: 16px; }
.alert-error   { background: var(--red-lt);   color: #991b1b; border: 1px solid #fecaca; }
.alert-success { background: var(--green-lt); color: #15803d; border: 1px solid #bbf7d0; }

.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 28px; }
.stat-card { background: var(--white); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px 24px; box-shadow: var(--shadow); }
.stat-label { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); margin-bottom: 8px; }
.stat-value { font-family: 'Instrument Serif', serif; font-size: 2.4rem; color: var(--navy); line-height: 1; }
.stat-accent { color: var(--teal); }

table { width: 100%; border-collapse: collapse; font-size: 14px; }
th { text-align: left; padding: 10px 16px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); border-bottom: 1px solid var(--border); }
td { padding: 13px 16px; border-bottom: 1px solid var(--border); color: var(--navy); vertical-align: middle; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: var(--bg); }

.empty-state { text-align: center; padding: 48px 24px; color: var(--muted); }
.empty-state .icon { font-size: 2.5rem; margin-bottom: 12px; opacity: .5; }
.empty-state p { font-size: 15px; }

.spinner { display: inline-block; width: 20px; height: 20px; border: 2px solid var(--border); border-top-color: var(--teal); border-radius: 50%; animation: spin .7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.loading { display: flex; align-items: center; justify-content: center; padding: 48px; gap: 12px; color: var(--muted); }
</style>
