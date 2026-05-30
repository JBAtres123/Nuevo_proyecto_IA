// router/index.js — DeepGrader AI
import { createRouter, createWebHistory } from 'vue-router'
import { useCursoStore } from '@/stores/cursoStore'

const routes = [
  // ── Públicas (solo accesibles SIN sesión) ─────────────────
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { guest: true }
  },
  {
    path: '/registro',
    name: 'registro',
    component: () => import('@/views/RegistroView.vue'),
    meta: { guest: true }
  },

  // ── Requiere auth, sin curso obligatorio ──────────────────
  {
    path: '/cursos',
    name: 'cursos',
    component: () => import('@/views/CursosView.vue'),
    meta: { requiresAuth: true }
  },

  // ── Requiere auth + curso activo ──────────────────────────
  {
    path: '/',
    name: 'inicio',
    component: () => import('@/views/InicioView.vue'),
    meta: { requiresAuth: true, requiresCurso: true }
  },
  {
    path: '/calificar',
    name: 'calificar',
    component: () => import('@/views/CalificacionesView.vue'),
    meta: { requiresAuth: true, requiresCurso: true }
  },
  {
    path: '/historial',
    name: 'historial',
    component: () => import('@/views/HistorialView.vue'),
    meta: { requiresAuth: true, requiresCurso: true }
  },
  {
    path: '/historial/:id',
    name: 'detalle-examen',
    component: () => import('@/views/DetalleExamenView.vue'),
    meta: { requiresAuth: true, requiresCurso: true }
  },
  {
    path: '/materiales',
    name: 'materiales',
    component: () => import('@/views/MaterialesView.vue'),
    meta: { requiresAuth: true, requiresCurso: true }
  },
  {
  path: '/configuracion',
  name: 'configuracion',
  component: () => import('@/views/ConfiguracionView.vue'),
  meta: { requiresAuth: true }
  },

  // ── Fallback ──────────────────────────────────────────────
  { path: '/:pathMatch(.*)*', redirect: '/login' }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 })
})

router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  const cursoStore = useCursoStore()

  // 1. Rutas guest: si ya hay sesión, redirigir al inicio
  if (to.meta.guest) {
    return token ? { name: 'inicio' } : true
  }

  // 2. Rutas protegidas: sin token → login
  if (to.meta.requiresAuth && !token) {
    return { name: 'login' }
  }

  // 3. Rutas que requieren curso activo: sin curso → selector
  if (to.meta.requiresCurso && !cursoStore.cursoId) {
    return { name: 'cursos' }
  }

  return true
})

export default router