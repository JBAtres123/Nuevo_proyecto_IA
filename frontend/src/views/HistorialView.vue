<template>
  <div class="max-w-6xl mx-auto px-6 py-10 animate-fade-in">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
      <div>
        <h1 class="font-display text-3xl text-surface-text dark:text-surface-textDark mb-1">
          Historial de Calificaciones
        </h1>

        <p class="text-surface-muted dark:text-surface-mutedDark text-sm">
          Todos los exámenes procesados por el sistema.
        </p>
      </div>

      <RouterLink to="/calificar" class="btn-primary inline-flex items-center gap-2">
        <SvgIcon name="plus" class="w-4 h-4" />
        Nuevo Examen
      </RouterLink>
    </div>

    <!-- Filtros -->
    <div class="flex flex-wrap items-center gap-3 mb-6">
      <button
        v-for="f in filtros"
        :key="f.value ?? 'todos'"
        @click="cambiarFiltro(f.value)"
        class="px-4 py-1.5 rounded-full text-sm transition-all inline-flex items-center gap-2 border"
        :class="filtroActivo === f.value
          ? 'bg-brand-600 border-brand-600 text-white shadow-sm dark:bg-brand-300 dark:border-brand-300 dark:text-surface-dark'
          : 'bg-surface-card border-surface-border text-surface-muted hover:text-surface-text hover:border-brand-400 dark:bg-surface-cardDark dark:border-surface-borderDark dark:text-surface-mutedDark dark:hover:text-surface-textDark dark:hover:border-brand-300/60'"
      >
        <SvgIcon :name="f.icon" class="w-4 h-4" />
        {{ f.label }}
      </button>

      <div
        class="ml-auto text-sm text-surface-muted dark:text-surface-mutedDark flex items-center"
      >
        {{ items.length }} resultado{{ items.length !== 1 ? 's' : '' }}
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-20">
      <div class="spinner w-8 h-8"></div>
    </div>

    <!-- Empty -->
    <div v-else-if="!items.length" class="card p-12 text-center">
      <div
        class="w-14 h-14 mx-auto mb-4 rounded-2xl border border-surface-border bg-surface-tag text-surface-muted flex items-center justify-center dark:border-surface-borderDark dark:bg-surface-tagDark dark:text-surface-mutedDark"
      >
        <SvgIcon name="inbox" class="w-8 h-8" />
      </div>

      <p class="text-surface-text dark:text-surface-textDark font-medium">
        No hay exámenes calificados aún
      </p>

      <p class="text-surface-muted dark:text-surface-mutedDark text-sm mt-1 mb-5">
        Sube el primer examen para comenzar
      </p>

      <RouterLink to="/calificar" class="btn-primary inline-flex items-center gap-2">
        <SvgIcon name="plus" class="w-4 h-4" />
        Calificar primer examen
      </RouterLink>
    </div>

    <!-- Table -->
    <div v-else class="card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr
              class="border-b border-surface-border text-left text-xs text-surface-muted uppercase tracking-wide bg-surface-cardSoft dark:border-surface-borderDark dark:text-surface-mutedDark dark:bg-surface-cardDark"
            >
              <th class="px-5 py-3.5">#</th>
              <th class="px-5 py-3.5">Estudiante</th>
              <th class="px-5 py-3.5 hidden sm:table-cell">Serie</th>
              <th class="px-5 py-3.5 hidden md:table-cell">Exigencia</th>
              <th class="px-5 py-3.5">Punteo</th>
              <th class="px-5 py-3.5">Estado</th>
              <th class="px-5 py-3.5 hidden lg:table-cell">Fecha y hora</th>
              <th class="px-5 py-3.5 text-right">Acciones</th>
            </tr>
          </thead>

          <tbody class="divide-y divide-surface-border dark:divide-surface-borderDark">
            <tr
              v-for="item in items"
              :key="item.id"
              class="hover:bg-surface-tableHover dark:hover:bg-white/[0.03] transition-colors group"
            >
              <td class="px-5 py-3.5 font-mono text-surface-muted dark:text-surface-mutedDark text-xs">
                {{ item.id }}
              </td>

              <td class="px-5 py-3.5">
                <p class="text-surface-text dark:text-surface-textDark font-medium">
                  {{ item.nombre_estudiante || '—' }}
                </p>
              </td>

              <td
                class="px-5 py-3.5 hidden sm:table-cell text-surface-muted dark:text-surface-mutedDark"
              >
                {{ item.serie || '—' }}
              </td>

              <td class="px-5 py-3.5 hidden md:table-cell">
                <span class="badge badge-info font-mono">
                  {{ item.nivel_exigencia }}/10
                </span>
              </td>

              <td class="px-5 py-3.5">
                <div v-if="item.porcentaje !== null" class="flex items-center gap-2">
                  <div
                    class="w-16 h-1.5 bg-surface-tag dark:bg-surface-tagDark rounded-full overflow-hidden"
                  >
                    <div
                      class="h-full rounded-full"
                      :class="barColor(item.porcentaje)"
                      :style="`width:${Math.min(item.porcentaje, 100)}%`"
                    ></div>
                  </div>

                  <span
                    class="font-mono font-bold text-xs"
                    :class="punteoColor(item.porcentaje)"
                  >
                    {{ item.porcentaje?.toFixed(1) }}%
                  </span>
                </div>

                <span
                  v-else
                  class="text-surface-muted dark:text-surface-mutedDark"
                >
                  —
                </span>
              </td>

              <td class="px-5 py-3.5">
                <span :class="estadoBadge(item.estado)">
                  {{ item.estado }}
                </span>
              </td>

              <td
                class="px-5 py-3.5 hidden lg:table-cell text-surface-muted dark:text-surface-mutedDark text-xs"
              >
                {{ formatDate(item.created_at || item.fecha_creacion || item.updated_at) }}
              </td>

              <td class="px-5 py-3.5">
                <div class="flex items-center justify-end gap-2">
                  <RouterLink
                    :to="`/historial/${item.id}`"
                    class="w-8 h-8 rounded-lg border border-surface-border text-surface-muted hover:text-brand-700 hover:border-brand-500 hover:bg-brand-300/10 transition-colors flex items-center justify-center dark:border-surface-borderDark dark:text-surface-mutedDark dark:hover:text-brand-300 dark:hover:border-brand-300/50 dark:hover:bg-brand-300/10"
                    title="Ver detalle"
                  >
                    <SvgIcon name="eye" class="w-4 h-4" />
                  </RouterLink>

                  <button
                    type="button"
                    @click="eliminarExamen(item)"
                    :disabled="eliminandoId === item.id"
                    class="w-8 h-8 rounded-lg border border-red-500/30 text-red-500 hover:text-red-600 hover:border-red-500/60 hover:bg-red-500/10 transition-colors flex items-center justify-center disabled:opacity-40 disabled:cursor-not-allowed dark:text-red-400 dark:hover:text-red-300"
                    title="Eliminar registro"
                  >
                    <span v-if="eliminandoId === item.id" class="spinner w-4 h-4"></span>
                    <SvgIcon v-else name="trash" class="w-4 h-4" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div
        v-if="totalPages > 1"
        class="flex items-center justify-between px-5 py-4 border-t border-surface-border dark:border-surface-borderDark"
      >
        <button
          @click="prevPage"
          :disabled="page === 1"
          class="btn-ghost text-sm py-1.5 px-3 disabled:opacity-40 inline-flex items-center gap-2"
        >
          <SvgIcon name="arrow-left" class="w-4 h-4" />
          Anterior
        </button>

        <span class="text-xs text-surface-muted dark:text-surface-mutedDark">
          Página {{ page }} de {{ totalPages }}
        </span>

        <button
          @click="nextPage"
          :disabled="page >= totalPages"
          class="btn-ghost text-sm py-1.5 px-3 disabled:opacity-40 inline-flex items-center gap-2"
        >
          Siguiente
          <SvgIcon name="arrow-right" class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- Error global -->
    <div
      v-if="errorGlobal"
      class="mt-4 card p-4 border-red-500/30 bg-red-500/5 text-red-500 dark:text-red-400 text-sm flex items-center gap-2"
    >
      <SvgIcon name="x-circle" class="w-5 h-5 shrink-0" />
      {{ errorGlobal }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, defineComponent, h } from 'vue'
import { RouterLink } from 'vue-router'
import axios from 'axios'
import { getHistory } from '@/composables/useApi'

const SVG_PATHS = {
  plus: [
    'M12 4.5v15m7.5-7.5h-15',
  ],
  inbox: [
    'M2.25 13.5h3.86a2.25 2.25 0 0 1 2.012 1.244l.256.512a2.25 2.25 0 0 0 2.013 1.244h3.218a2.25 2.25 0 0 0 2.013-1.244l.256-.512A2.25 2.25 0 0 1 17.89 13.5h3.86',
    'M2.25 13.5 4.35 5.738A2.25 2.25 0 0 1 6.52 4.125h10.96a2.25 2.25 0 0 1 2.17 1.613l2.1 7.762v3.375A2.625 2.625 0 0 1 19.125 19.5H4.875A2.625 2.625 0 0 1 2.25 16.875V13.5Z',
  ],
  check: [
    'M4.5 12.75l6 6 9-13.5',
  ],
  clock: [
    'M12 6v6l4 2m6-2a10 10 0 1 1-20 0 10 10 0 0 1 20 0Z',
  ],
  'x-circle': [
    'M9.75 9.75 14.25 14.25M14.25 9.75 9.75 14.25',
    'M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z',
  ],
  eye: [
    'M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z',
    'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z',
  ],
  trash: [
    'M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673A2.25 2.25 0 0 1 15.916 21.75H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0',
  ],
  'arrow-left': [
    'M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18',
  ],
  'arrow-right': [
    'M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3',
  ],
  list: [
    'M8.25 6.75h12M8.25 12h12M8.25 17.25h12',
    'M3.75 6.75h.007v.008H3.75V6.75Zm0 5.25h.007v.008H3.75V12Zm0 5.25h.007v.008H3.75v-.008Z',
  ],
}

const SvgIcon = defineComponent({
  name: 'SvgIcon',
  inheritAttrs: false,

  props: {
    name: {
      type: String,
      required: true,
    },
  },

  setup(props, { attrs }) {
    return () => {
      const paths = SVG_PATHS[props.name] || SVG_PATHS.list

      return h(
        'svg',
        {
          xmlns: 'http://www.w3.org/2000/svg',
          fill: 'none',
          viewBox: '0 0 24 24',
          strokeWidth: '1.5',
          stroke: 'currentColor',
          ...attrs,
        },
        paths.map((d) =>
          h('path', {
            'stroke-linecap': 'round',
            'stroke-linejoin': 'round',
            d,
          }),
        ),
      )
    }
  },
})

const items = ref([])
const loading = ref(true)
const page = ref(1)
const pageSize = 20
const totalItems = ref(0)
const filtroActivo = ref(null)
const eliminandoId = ref(null)
const errorGlobal = ref('')

const filtros = [
  { label: 'Todos', value: null, icon: 'list' },
  { label: 'Completados', value: 'completado', icon: 'check' },
  { label: 'Procesando', value: 'procesando', icon: 'clock' },
  { label: 'Con Error', value: 'error', icon: 'x-circle' },
]

const totalPages = computed(() => Math.max(1, Math.ceil(totalItems.value / pageSize)))

async function loadHistory() {
  loading.value = true
  errorGlobal.value = ''

  try {
    const data = await getHistory(page.value, pageSize, filtroActivo.value)

    items.value = data.items || []
    totalItems.value = data.total ?? data.totalItems ?? data.count ?? items.value.length
  } catch (e) {
    console.error(e)
    errorGlobal.value =
      e?.response?.data?.detail ||
      e?.message ||
      'No se pudo cargar el historial.'
  } finally {
    loading.value = false
  }
}

function cambiarFiltro(value) {
  filtroActivo.value = value
  page.value = 1
  loadHistory()
}

function prevPage() {
  if (page.value > 1) {
    page.value--
    loadHistory()
  }
}

function nextPage() {
  if (page.value < totalPages.value) {
    page.value++
    loadHistory()
  }
}

async function eliminarExamen(item) {
  const confirmar = window.confirm(
    `¿Deseas eliminar el examen #${item.id}? Esta acción no se puede deshacer.`,
  )

  if (!confirmar) return

  eliminandoId.value = item.id
  errorGlobal.value = ''

  try {
    const token = localStorage.getItem('token')

    await axios.delete(`/api/exams/${item.id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })

    items.value = items.value.filter((examen) => examen.id !== item.id)
    totalItems.value = Math.max(0, totalItems.value - 1)

    if (!items.value.length && page.value > 1) {
      page.value--
      await loadHistory()
    }
  } catch (e) {
    console.error(e)

    errorGlobal.value =
      e?.response?.data?.detail ||
      e?.message ||
      'No se pudo eliminar el examen. Verifica que exista el endpoint DELETE /api/exams/{id} en el backend.'
  } finally {
    eliminandoId.value = null
  }
}

function estadoBadge(estado) {
  const map = {
    completado: 'badge badge-success',
    procesando: 'badge badge-info',
    error: 'badge badge-danger',
    pendiente: 'badge badge-muted',
  }

  return map[estado] || 'badge badge-muted'
}

function punteoColor(p) {
  if (p >= 70) return 'text-green-600 dark:text-green-400'
  if (p >= 60) return 'text-yellow-600 dark:text-yellow-400'
  return 'text-red-600 dark:text-red-400'
}

function barColor(p) {
  if (p >= 70) return 'bg-green-500'
  if (p >= 60) return 'bg-yellow-500'
  return 'bg-red-500'
}

function normalizarFechaBackend(iso) {
  if (!iso) return null

  let valor = String(iso).trim()
  valor = valor.replace(' ', 'T')

  const tieneZonaHoraria = /([zZ]|[+-]\d{2}:?\d{2})$/.test(valor)

  if (!tieneZonaHoraria) {
    valor = `${valor}Z`
  }

  const fecha = new Date(valor)

  if (Number.isNaN(fecha.getTime())) return null

  return fecha
}

function formatDate(iso) {
  const fecha = normalizarFechaBackend(iso)
  if (!fecha) return '—'

  return fecha.toLocaleString('es-GT', {
    timeZone: 'America/Guatemala',
    dateStyle: 'short',
    timeStyle: 'short',
    hour12: true,
  })
}

onMounted(loadHistory)
</script>