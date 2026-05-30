// src/composables/useApi.js

import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120_000,
})

// Inyectar token en cada request automáticamente
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Manejo de errores global
api.interceptors.response.use(
  r => r,
  err => {
    const msg = err.response?.data?.detail || err.message || 'Error desconocido'
    // Si el backend devuelve 401, limpiar sesión
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('docente_id')
      localStorage.removeItem('cursoActivo')
      window.location.href = '/login'
    }
    return Promise.reject(new Error(msg))
  }
)

// Helper para obtener curso_id activo
function getCursoId() {
  const raw = localStorage.getItem('cursoActivo')
  if (!raw) return null
  try { return JSON.parse(raw).id } catch { return null }
}

// ── Auth ──────────────────────────────────────────────────────
// POST /auth/login → { token, docente_id, nombre }
export async function loginDocente({ email, password }) {
  const { data } = await api.post('/auth/login', { email, password })
  return data
}

// POST /auth/registro → { token, docente_id, nombre }
export async function registrarDocente(payload) {
  const { data } = await api.post('/auth/registro', payload)
  return data
}

export async function getPerfilDocente() {
  const { data } = await api.get('/perfil')
  return data
}

export async function updatePerfil(payload) {
  const { data } = await api.put('/perfil', payload)
  return data
}

export async function cambiarPassword(payload) {
  const { data } = await api.post('/perfil/password', payload)
  return data
}

export async function eliminarCuenta() {
  const { data } = await api.delete('/perfil')
  return data
}
// ── Cursos ────────────────────────────────────────────────────
// GET /cursos → { cursos: [...] }
export async function getCursos() {
  const { data } = await api.get('/cursos')
  return data
}

// POST /cursos → { curso: { id, nombre, descripcion } }
export async function crearCursoApi(payload) {
  const { data } = await api.post('/cursos', payload)
  return data
}

// ── Dashboard ─────────────────────────────────────────────────
export async function getDashboardStats(cursoId = null) {
  const params = {}

  if (cursoId) {
    params.curso_id = cursoId
  }

  const { data } = await api.get('/dashboard/stats', { params })
  return data
}

// ── Exámenes ──────────────────────────────────────────────────
export async function uploadExam(formData) {
  // Agregar curso_id al FormData antes de enviar
  const cursoId = getCursoId()
  if (cursoId) formData.append('curso_id', cursoId)
  const { data } = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function processExam(examenId) {
  const { data } = await api.post(`/process/${examenId}`)
  return data
}

export async function getHistory(page = 1, pageSize = 20, estado = null) {
  const cursoId = getCursoId()
  const params = { page, page_size: pageSize, curso_id: cursoId }
  if (estado) params.estado = estado
  const { data } = await api.get('/history', { params })
  return data
}

export async function getExamDetail(examenId) {
  const { data } = await api.get(`/history/${examenId}`)
  return data
}

// ── Configuración ─────────────────────────────────────────────
export async function getConfigExigencia() {
  const { data } = await api.get('/config-exigencia')
  return data
}

export async function setConfigExigencia(nivel) {
  const { data } = await api.post('/config-exigencia', { nivel })
  return data
}

// ── Materiales ────────────────────────────────────────────────
export async function uploadMaterial(cursoId, formData) {
  formData.append('curso_id', cursoId)
  const { data } = await api.post('/materials/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function listMaterials(cursoId) {
  const { data } = await api.get('/materials', { params: { curso_id: cursoId } })
  return data
}

export async function deleteMaterial(cursoId, materialId) {
  const { data } = await api.delete(`/materials/${materialId}`, {
    params: { curso_id: cursoId },
  })
  return data
}

// ── Descargas ─────────────────────────────────────────────────
function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

function filenameFromDisposition(disposition, fallback) {
  const match = disposition?.match(/filename="?([^"]+)"?/i)
  return match?.[1] || fallback
}

export async function downloadPDF(examenId) {
  const response = await api.get(`/download/pdf/${examenId}`, { responseType: 'blob' })
  const filename = filenameFromDisposition(
    response.headers['content-disposition'],
    `resultado_examen_${examenId}.pdf`,
  )
  downloadBlob(response.data, filename)
}

export async function downloadWord(examenId) {
  const response = await api.get(`/download/word/${examenId}`, { responseType: 'blob' })
  const filename = filenameFromDisposition(
    response.headers['content-disposition'],
    `resultado_examen_${examenId}.docx`,
  )
  downloadBlob(response.data, filename)
}

// ── Health ────────────────────────────────────────────────────
export async function checkHealth() {
  const { data } = await api.get('/health')
  return data
}
