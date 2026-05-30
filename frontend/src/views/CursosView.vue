<!-- src/views/CursosView.vue -->

<template>
  <div class="max-w-4xl mx-auto px-6 py-12 animate-fade-in">

    <!-- Header -->
    <div class="mb-10 text-center">
      <h1 class="font-display text-4xl text-surface-text dark:text-surface-textDark mb-2">
        Mis Cursos
      </h1>

      <p class="text-surface-muted dark:text-surface-mutedDark text-sm">
        Selecciona un curso para trabajar o crea uno nuevo.
      </p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-20">
      <div class="spinner w-8 h-8"></div>
    </div>

    <!-- Sin cursos -->
<div v-else-if="!cursos.length" class="card p-12 text-center">
  <div
    class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-surface-tag dark:bg-surface-tagDark border border-surface-border dark:border-surface-borderDark flex items-center justify-center"
  >
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 20 20"
      class="w-8 h-8 text-surface-text dark:text-surface-textDark"
      fill="currentColor"
    >
      <!-- Libro izquierdo -->
      <path d="M3 5.5a1 1 0 0 1 1-1h4.5a1.5 1.5 0 0 1 1.5 1.5v8.75a.75.75 0 0 1-.75.75H4a1 1 0 0 1-1-1V5.5z" />
      <path d="M8 6v9" stroke="white" stroke-width="0.75" />
      
      <!-- Líneas de texto libro izquierdo -->
      <line x1="4.5" y1="9" x2="6.5" y2="9" stroke="white" stroke-width="0.5" stroke-linecap="round"/>
      <line x1="4.5" y1="10.5" x2="6.5" y2="10.5" stroke="white" stroke-width="0.5" stroke-linecap="round"/>
      <line x1="4.5" y1="12" x2="5.5" y2="12" stroke="white" stroke-width="0.5" stroke-linecap="round"/>
      
      <!-- Libro derecho -->
      <path d="M8.5 5.5a1 1 0 0 1 1-1H14a1.5 1.5 0 0 1 1.5 1.5v8.75a.75.75 0 0 1-.75.75H10a.75.75 0 0 1-.75-.75V5.5z" />
      <path d="M14 6v9" stroke="white" stroke-width="0.75" />
      
      <!-- Líneas de texto libro derecho -->
      <line x1="11" y1="9" x2="13" y2="9" stroke="white" stroke-width="0.5" stroke-linecap="round"/>
      <line x1="11" y1="10.5" x2="13" y2="10.5" stroke="white" stroke-width="0.5" stroke-linecap="round"/>
      <line x1="11" y1="12" x2="12" y2="12" stroke="white" stroke-width="0.5" stroke-linecap="round"/>
    </svg>
  </div>

  <p class="text-surface-text dark:text-surface-textDark font-medium mb-1">
    No tienes cursos aún
  </p>

  <p class="text-surface-muted dark:text-surface-mutedDark text-sm mb-6">
    Crea tu primer curso para empezar a calificar exámenes.
  </p>

  <button @click="mostrarForm = true" class="btn-primary inline-flex">
    + Crear primer curso
  </button>
</div>

    

    <!-- Grid de cursos -->
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
      <button
        v-for="curso in cursos"
        :key="curso.id"
        @click="seleccionar(curso)"
        class="card p-6 text-left hover:border-brand-500/50 hover:bg-brand-300/10 dark:hover:bg-brand-500/5 transition-all group cursor-pointer"
      >
        <div class="flex items-start justify-between mb-3">
          <div
            class="w-10 h-10 rounded-xl flex items-center justify-center text-lg font-bold shadow-sm"
            :style="`background: ${colorCurso(curso.id)}22; color: ${colorCurso(curso.id)}`"
          >
            {{ curso.nombre.charAt(0).toUpperCase() }}
          </div>

          <span class="text-xs text-surface-muted dark:text-surface-mutedDark font-mono">
            ID {{ curso.id }}
          </span>
        </div>

        <p
          class="font-medium text-surface-text dark:text-surface-textDark group-hover:text-brand-700 dark:group-hover:text-brand-300 transition-colors mb-1"
        >
          {{ curso.nombre }}
        </p>

        <p
          v-if="curso.descripcion"
          class="text-xs text-surface-muted dark:text-surface-mutedDark line-clamp-2"
        >
          {{ curso.descripcion }}
        </p>

        <div class="mt-4 flex items-center justify-between">
          <span class="text-xs text-surface-muted dark:text-surface-mutedDark">
            {{ curso.total_examenes ?? 0 }} exámenes
          </span>

          <span
            class="text-brand-700 dark:text-brand-300 text-xs opacity-0 group-hover:opacity-100 transition-opacity"
          >
            Seleccionar →
          </span>
        </div>
      </button>

      <!-- Tarjeta "nuevo curso" -->
      <button
        @click="mostrarForm = true"
        class="card p-6 text-center hover:border-brand-500/50 hover:bg-brand-300/10 dark:hover:bg-brand-500/5 transition-all border-dashed cursor-pointer flex flex-col items-center justify-center gap-2 min-h-[140px]"
      >
        <div
          class="w-10 h-10 rounded-xl bg-surface-tag dark:bg-surface-tagDark border border-surface-border dark:border-surface-borderDark flex items-center justify-center text-2xl text-surface-muted dark:text-surface-mutedDark"
        >
          +
        </div>

        <p
          class="text-sm text-surface-muted dark:text-surface-mutedDark hover:text-surface-text dark:hover:text-surface-textDark transition-colors"
        >
          Nuevo curso
        </p>
      </button>
    </div>

    <!-- Modal crear curso -->
    <div
      v-if="mostrarForm"
      class="min-h-[300px] bg-surface-cardSoft/80 dark:bg-black/50 border border-surface-border dark:border-surface-borderDark rounded-2xl flex items-center justify-center p-6"
    >
      <div class="card p-8 w-full max-w-md">
        <h2 class="font-display text-xl text-surface-text dark:text-surface-textDark mb-6">
          Crear nuevo curso
        </h2>

        <div class="space-y-4">
          <div>
            <label
              class="text-xs text-surface-muted dark:text-surface-mutedDark mb-1.5 block"
            >
              Nombre del curso *
            </label>

            <input
              v-model="nuevoCurso.nombre"
              class="input w-full"
              placeholder="Ej: Cálculo I — Sección A"
              @keyup.enter="crearCurso"
            />
          </div>

          <div>
            <label
              class="text-xs text-surface-muted dark:text-surface-mutedDark mb-1.5 block"
            >
              Descripción (opcional)
            </label>

            <textarea
              v-model="nuevoCurso.descripcion"
              class="input w-full resize-none"
              rows="3"
              placeholder="Ej: Primer semestre 2025, Facultad de Ingeniería"
            ></textarea>
          </div>
        </div>

        <div
          v-if="formError"
          class="mt-4 p-3 rounded-xl border border-red-500/20 bg-red-500/5 text-sm text-red-500 dark:text-red-400"
        >
          {{ formError }}
        </div>

        <div class="flex flex-col sm:flex-row gap-3 mt-6">
          <button
            @click="mostrarForm = false; formError = ''"
            class="btn-ghost flex-1 justify-center"
          >
            Cancelar
          </button>

          <button
            @click="crearCurso"
            :disabled="creando"
            class="btn-primary flex-1 justify-center"
          >
            <span v-if="creando" class="spinner w-4 h-4"></span>
            <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 20 20"
        fill="currentColor"
        class="w-3.5 h-3.5"
      >
        <!-- Libro izquierdo -->
        <path d="M3 5.5a1 1 0 0 1 1-1h4.5a1.5 1.5 0 0 1 1.5 1.5v8.75a.75.75 0 0 1-.75.75H4a1 1 0 0 1-1-1V5.5z" />
        <path d="M8 6v9" stroke="white" stroke-width="0.75" />
        
        <!-- Líneas de texto libro izquierdo -->
        <line x1="4.5" y1="9" x2="6.5" y2="9" stroke="white" stroke-width="0.5" stroke-linecap="round"/>
        <line x1="4.5" y1="10.5" x2="6.5" y2="10.5" stroke="white" stroke-width="0.5" stroke-linecap="round"/>
        <line x1="4.5" y1="12" x2="5.5" y2="12" stroke="white" stroke-width="0.5" stroke-linecap="round"/>
        
        <!-- Libro derecho -->
        <path d="M8.5 5.5a1 1 0 0 1 1-1H14a1.5 1.5 0 0 1 1.5 1.5v8.75a.75.75 0 0 1-.75.75H10a.75.75 0 0 1-.75-.75V5.5z" />
        <path d="M14 6v9" stroke="white" stroke-width="0.75" />
        
        <!-- Líneas de texto libro derecho -->
        <line x1="11" y1="9" x2="13" y2="9" stroke="white" stroke-width="0.5" stroke-linecap="round"/>
        <line x1="11" y1="10.5" x2="13" y2="10.5" stroke="white" stroke-width="0.5" stroke-linecap="round"/>
        <line x1="11" y1="12" x2="12" y2="12" stroke="white" stroke-width="0.5" stroke-linecap="round"/>
      </svg>
            {{ creando ? 'Creando...' : 'Crear curso' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Cerrar sesión -->
    <div class="text-center mt-8">
      <button
        @click="logout"
        class="text-xs text-surface-muted hover:text-surface-text dark:text-surface-mutedDark dark:hover:text-surface-textDark transition-colors"
      >
        Cerrar sesión
      </button>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCursoStore } from '@/stores/cursoStore'
import { getCursos, crearCursoApi } from '@/composables/useApi'

const router = useRouter()
const cursoStore = useCursoStore()

const cursos = ref([])
const loading = ref(true)
const mostrarForm = ref(false)
const creando = ref(false)
const formError = ref('')

const nuevoCurso = ref({
  nombre: '',
  descripcion: '',
})

const COLORES = [
  '#a3e635',
  '#60a5fa',
  '#a78bfa',
  '#fb923c',
  '#34d399',
  '#f472b6',
  '#facc15',
]

function colorCurso(id) {
  return COLORES[id % COLORES.length]
}

async function cargarCursos() {
  loading.value = true

  try {
    const data = await getCursos()
    cursos.value = data.cursos || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function seleccionar(curso) {
  cursoStore.setCurso(curso)
  router.push({ name: 'inicio' })
}

async function crearCurso() {
  formError.value = ''

  if (!nuevoCurso.value.nombre.trim()) {
    formError.value = 'El nombre del curso es obligatorio'
    return
  }

  creando.value = true

  try {
    const data = await crearCursoApi(nuevoCurso.value)

    cursos.value.push(data.curso)
    mostrarForm.value = false

    nuevoCurso.value = {
      nombre: '',
      descripcion: '',
    }

    seleccionar(data.curso)
  } catch (e) {
    formError.value = e.message || 'Error al crear el curso'
  } finally {
    creando.value = false
  }
}

function logout() {
  cursoStore.clearCurso()

  localStorage.removeItem('token')
  localStorage.removeItem('docente_id')

  router.push({ name: 'login' })
}

onMounted(cargarCursos)
</script>