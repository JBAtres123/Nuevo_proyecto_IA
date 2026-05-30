// stores/appStore.js — DeepGrader AI
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getConfigExigencia, setConfigExigencia } from '@/composables/useApi'

export const useAppStore = defineStore('app', () => {
  const nivelExigencia = ref(5)
  const darkMode = ref(false)

  const nivelLabels = {
    1:  '😊 Modo Amigo',
    2:  '😊 Amigo',
    3:  '🙂 Comprensivo',
    4:  '⚖️ Balanceado-Suave',
    5:  '⚖️ Balanceado',
    6:  '⚖️ Balanceado-Estricto',
    7:  '🎯 Estricto',
    8:  '🎯 Muy Estricto',
    9:  '🔬 Riguroso',
    10: '🔬 Modo Experto',
  }

  const nivelDescripcion = computed(
    () => nivelLabels[nivelExigencia.value] ?? `Nivel ${nivelExigencia.value}`
  )

  // ── Tema ────────────────────────────────────────────────────
  function toggleTheme() {
    darkMode.value = !darkMode.value
    document.documentElement.classList.toggle('dark', darkMode.value)
    localStorage.setItem('theme', darkMode.value ? 'dark' : 'light')
  }

  function loadTheme() {
    const saved = localStorage.getItem('theme')
    darkMode.value = saved === 'dark'
    document.documentElement.classList.toggle('dark', darkMode.value)
  }

  // ── Nivel de exigencia ──────────────────────────────────────
  async function loadConfig() {
    try {
      const config = await getConfigExigencia()
      nivelExigencia.value = config.nivel
    } catch {
      // Mantener el valor por defecto si falla la petición
    }
  }

  async function updateNivel(nivel) {
    nivelExigencia.value = nivel
    try {
      await setConfigExigencia(nivel)
    } catch {
      // El valor local ya se actualizó; el backend puede reintentarse después
    }
  }

  return {
    nivelExigencia,
    nivelDescripcion,
    nivelLabels,
    darkMode,
    toggleTheme,
    loadTheme,
    loadConfig,
    updateNivel,
  }
})