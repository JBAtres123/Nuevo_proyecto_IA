
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useCursoStore = defineStore('curso', () => {
  const cursoId    = ref(null)
  const cursoNombre = ref('')
  const cursoDesc  = ref('')

  function setCurso(curso) {
    cursoId.value     = curso.id
    cursoNombre.value = curso.nombre
    cursoDesc.value   = curso.descripcion || ''
    localStorage.setItem('cursoActivo', JSON.stringify({
      id: curso.id,
      nombre: curso.nombre,
      descripcion: curso.descripcion || ''
    }))
  }

  function clearCurso() {
    cursoId.value     = null
    cursoNombre.value = ''
    cursoDesc.value   = ''
    localStorage.removeItem('cursoActivo')
  }

  function restoreFromStorage() {
    const raw = localStorage.getItem('cursoActivo')
    if (raw) {
      try { setCurso(JSON.parse(raw)) } catch { clearCurso() }
    }
  }

  return { cursoId, cursoNombre, cursoDesc, setCurso, clearCurso, restoreFromStorage }
})