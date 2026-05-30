<template>
  <div class="max-w-6xl mx-auto px-6 py-10 animate-fade-in">
    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-24 gap-3">
      <div class="spinner w-8 h-8"></div>
      <span class="text-surface-muted dark:text-surface-mutedDark">
        Cargando resultado...
      </span>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="card p-8 text-center border-red-500/20">
      <p class="text-red-500 dark:text-red-400">
        {{ error }}
      </p>

      <RouterLink to="/historial" class="btn-ghost mt-4 inline-flex">
        <SvgIcon name="arrow-left" class="w-4 h-4 inline-block mr-1 align-text-bottom" />
        Volver al historial
      </RouterLink>
    </div>

    <template v-else-if="detail">
      <!-- Header -->
      <div class="flex flex-wrap items-start justify-between gap-4 mb-8">
        <div>
          <RouterLink
            to="/historial"
            class="text-surface-muted hover:text-surface-text dark:text-surface-mutedDark dark:hover:text-surface-textDark text-sm flex items-center gap-1 mb-2 transition-colors"
          >
            <SvgIcon name="arrow-left" class="w-4 h-4" />
            Historial
          </RouterLink>

          <h1 class="font-display text-3xl text-surface-text dark:text-surface-textDark">
            {{ detail.examen.nombre_estudiante || 'Estudiante' }}
          </h1>

          <p class="text-surface-muted dark:text-surface-mutedDark text-sm mt-1">
            {{ detail.examen.serie || 'Sin serie' }} · Examen #{{ detail.examen.id }}
            · {{ formatDate(detail.examen.created_at) }}
          </p>
        </div>

        <div class="flex items-center gap-3">
          <div class="card px-5 py-3 text-center min-w-[110px]">
            <p class="text-3xl font-display" :class="punteoColor">
              {{ detail.examen.porcentaje?.toFixed(1) }}%
            </p>

            <p class="text-xs text-surface-muted dark:text-surface-mutedDark mt-0.5">
              {{ detail.examen.punteo_total }} / {{ detail.examen.punteo_maximo }} pts
            </p>
          </div>

          <div class="flex flex-col gap-2">
            <button @click="downloadPDF(detail.examen.id)" class="btn-ghost text-sm">
              <SvgIcon name="arrow-down-tray" class="w-4 h-4 inline-block mr-1 align-text-bottom" />
              PDF
            </button>

            <button @click="downloadWord(detail.examen.id)" class="btn-ghost text-sm">
              <SvgIcon name="arrow-down-tray" class="w-4 h-4 inline-block mr-1 align-text-bottom" />
              Word
            </button>
          </div>
        </div>
      </div>

      <!-- Status + nivel -->
      <div class="flex flex-wrap gap-2 mb-8">
        <span :class="estadoBadge(detail.examen.estado)">
          {{ detail.examen.estado }}
        </span>

        <span class="badge badge-info">
          Exigencia {{ detail.examen.nivel_exigencia }}/10
        </span>
      </div>

      <!-- Tabs -->
      <div
        class="flex gap-1 mb-6 border-b border-surface-border dark:border-surface-borderDark overflow-x-auto"
      >
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          class="px-5 py-2.5 text-sm font-medium border-b-2 transition-all -mb-px whitespace-nowrap"
          :class="activeTab === tab.id
            ? 'border-brand-600 text-brand-700 dark:border-brand-300 dark:text-brand-300'
            : 'border-transparent text-surface-muted hover:text-surface-text dark:text-surface-mutedDark dark:hover:text-surface-textDark'"
        >
          <SvgIcon :name="tab.icon" class="w-4 h-4 inline-block mr-1.5 align-text-bottom" />
          {{ tab.label }}
        </button>
      </div>

      <!-- Tab: Resultado Final -->
      <div v-show="activeTab === 'final'" class="space-y-5 animate-fade-in">
        <div class="card p-6">
          <h2 class="font-medium text-surface-text dark:text-surface-textDark mb-4 flex items-center gap-2">
            <SvgIcon name="scale" class="w-5 h-5 text-surface-text dark:text-surface-textDark" />
            Calificación Final (Agente Juez)
          </h2>

          <div v-if="seriesAgrupadas.length" class="space-y-5">
            <div
              v-for="serie in seriesAgrupadas"
              :key="serie.nombre"
              class="rounded-2xl border border-surface-border bg-surface-cardSoft dark:border-surface-borderDark dark:bg-surface-tagDark/40 overflow-hidden"
            >
              <!-- Encabezado de la serie -->
              <div
                class="px-5 py-4 flex items-center justify-between gap-4 border-b border-surface-border dark:border-surface-borderDark"
              >
                <div class="flex items-center gap-3">
                  <div
                    class="w-9 h-9 rounded-xl bg-brand-300/15 border border-brand-500/30 dark:border-brand-300/30 flex items-center justify-center"
                  >
                    <span class="text-brand-700 dark:text-brand-300 font-mono text-xs font-bold">
                      {{ serie.romano }}
                    </span>
                  </div>

                  <div>
                    <h3 class="text-surface-text dark:text-surface-textDark font-medium">
                      {{ serie.nombre }}
                    </h3>

                    <p class="text-xs text-surface-muted dark:text-surface-mutedDark">
                      {{ serie.items.length }} item(s) ·
                      {{ serie.punteoObtenido }} / {{ serie.punteoMaximo }} pts
                    </p>
                  </div>
                </div>

                <span
                  class="badge text-xs"
                  :class="serie.punteoObtenido >= serie.punteoMaximo * 0.6
                    ? 'badge-success'
                    : 'badge-danger'"
                >
                  {{ serie.punteoObtenido }} / {{ serie.punteoMaximo }} pts
                </span>
              </div>

              <!-- Items de la serie -->
              <div class="space-y-3 p-3">
                <div
                  v-for="(p, index) in serie.items"
                  :key="`${serie.nombre}-${p.numero}-${index}`"
                  class="px-5 py-4 flex items-start justify-between gap-4 rounded-xl border"
                  :class="p.es_correcta
                    ? 'bg-green-500/5 border-green-500/20'
                    : 'bg-red-500/5 border-red-500/20'"
                >
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 flex-wrap">
                      <span
                        class="w-6 h-6 rounded-lg flex items-center justify-center text-xs font-bold"
                        :class="p.es_correcta
                          ? 'bg-green-500/15 text-green-600 dark:text-green-300 border border-green-500/30'
                          : 'bg-red-500/15 text-red-600 dark:text-red-300 border border-red-500/30'"
                      >
                        <SvgIcon
                          v-if="p.es_correcta"
                          name="check"
                          class="w-3.5 h-3.5"
                        />

                        <SvgIcon
                          v-else
                          name="x-mark"
                          class="w-3.5 h-3.5"
                        />
                      </span>

                      <p class="text-sm font-medium text-surface-text dark:text-surface-textDark">
                        Item {{ index + 1 }}
                      </p>

                      <span
                        class="text-xs"
                        :class="p.es_correcta
                          ? 'text-green-600 dark:text-green-400'
                          : 'text-red-600 dark:text-red-400'"
                      >
                        {{ p.es_correcta ? 'Correcto' : 'Incorrecto' }}
                      </span>
                    </div>

                    <p
                      v-if="p.texto_pregunta"
                      class="text-xs text-surface-muted dark:text-surface-mutedDark mt-2 math-content"
                      v-html="renderizarLatexEnTexto(p.texto_pregunta)"
                    ></p>

                    <p
                      v-if="p.respuesta_estudiante"
                      class="text-xs text-surface-text dark:text-surface-textDark mt-2 font-mono math-content"
                    >
                      Respuesta:
                      <span v-html="renderizarLatexEnTexto(p.respuesta_estudiante)"></span>
                    </p>

                    <p
                      v-if="p.justificacion"
                      class="text-xs text-surface-text dark:text-surface-textDark mt-2 math-content opacity-90"
                      v-html="renderizarLatexEnTexto(p.justificacion)"
                    ></p>
                  </div>

                  <div class="text-right shrink-0">
                    <p
                      class="font-mono text-lg font-bold"
                      :class="p.es_correcta
                        ? 'text-green-600 dark:text-green-400'
                        : 'text-red-600 dark:text-red-400'"
                    >
                      {{ p.punteo_obtenido }}/{{ p.punteo_maximo }}
                    </p>

                    <p class="text-[11px] text-surface-muted dark:text-surface-mutedDark">
                      puntos
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div
            v-else
            class="p-4 rounded-xl border border-surface-border bg-surface-tag text-surface-muted dark:border-surface-borderDark dark:bg-surface-tagDark dark:text-surface-mutedDark text-sm"
          >
            No hay preguntas detectadas para mostrar por series.
          </div>

          <!-- Conclusión -->
          <div
            v-if="detail.calificacion_final?.conclusion"
            class="mt-5 p-4 bg-surface-tag dark:bg-surface-tagDark rounded-xl border border-surface-border dark:border-surface-borderDark"
          >
            <h3 class="text-sm font-medium text-surface-text dark:text-surface-textDark mb-2">
              <SvgIcon
                name="chat-bubble"
                class="w-4 h-4 inline-block mr-1.5 align-text-bottom text-surface-text dark:text-surface-textDark"
              />
              Conclusión General
            </h3>

            <p
              class="text-sm text-surface-text dark:text-surface-textDark math-content opacity-90"
              v-html="renderizarLatexEnTexto(detail.calificacion_final.conclusion)"
            ></p>
          </div>

          <!-- Fortalezas / Debilidades / Sugerencias -->
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-5">
            <div
              v-for="section in finalSections"
              :key="section.key"
              class="p-4 rounded-xl border"
              :class="section.style"
            >
              <h4 class="text-xs font-medium mb-2" :class="section.titleColor">
                <SvgIcon :name="section.icon" class="w-4 h-4 inline-block mr-1.5 align-text-bottom" />
                {{ section.title }}
              </h4>

              <ul class="space-y-1">
                <li
                  v-for="item in (detail.calificacion_final?.[section.key] || [])"
                  :key="item"
                  class="text-xs text-surface-text dark:text-surface-textDark math-content opacity-90"
                >
                  • <span v-html="renderizarLatexEnTexto(item)"></span>
                </li>

                <li
                  v-if="!(detail.calificacion_final?.[section.key]?.length)"
                  class="text-xs text-surface-muted dark:text-surface-mutedDark italic"
                >
                  Sin datos
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab: Comparación de Agentes -->
      <div v-show="activeTab === 'comparacion'" class="animate-fade-in">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <AgentCard
            v-for="agent in agentCards"
            :key="agent.key"
            :agent="agent"
            :data="detail.agentes?.[agent.key]"
          />
        </div>

        <!-- Discrepancias -->
        <div v-if="discrepancias?.length" class="mt-5 card p-5">
          <h3 class="font-medium text-surface-text dark:text-surface-textDark mb-4">
            <SvgIcon
              name="magnifying-glass"
              class="w-5 h-5 inline-block mr-1.5 align-text-bottom text-surface-text dark:text-surface-textDark"
            />
            Discrepancias Resueltas por el Juez
          </h3>

          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr
                  class="text-left text-surface-muted dark:text-surface-mutedDark text-xs border-b border-surface-border dark:border-surface-borderDark"
                >
                  <th class="pb-2">Pregunta</th>
                  <th class="pb-2">Calificador</th>
                  <th class="pb-2">Juez (Final)</th>
                  <th class="pb-2">Razón</th>
                </tr>
              </thead>

              <tbody class="divide-y divide-surface-border dark:divide-surface-borderDark">
                <tr
                  v-for="d in discrepancias"
                  :key="d.pregunta"
                  class="text-surface-text dark:text-surface-textDark"
                >
                  <td class="py-2 font-mono">
                    {{ d.pregunta }}
                  </td>

                  <td class="py-2 font-mono text-purple-600 dark:text-purple-300">
                    {{ d.punteo_b ?? d.punteo_a ?? '—' }}
                  </td>

                  <td class="py-2 font-mono text-amber-600 dark:text-amber-300 font-bold">
                    {{ d.punteo_final }}
                  </td>

                  <td
                    class="py-2 text-xs text-surface-muted dark:text-surface-mutedDark math-content"
                    v-html="renderizarLatexEnTexto(d.razon)"
                  ></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Tab: Texto ICR -->
      <div v-show="activeTab === 'icr'" class="animate-fade-in">
        <div class="card p-6">
          <h2 class="font-medium text-surface-text dark:text-surface-textDark mb-4">
            <SvgIcon
              name="document-text"
              class="w-5 h-5 inline-block mr-1.5 align-text-bottom text-surface-text dark:text-surface-textDark"
            />
            Texto Extraído por ICR
          </h2>

          <div
            class="
              text-xs
              text-surface-text
              dark:text-surface-textDark
              bg-surface-tag
              dark:bg-surface-tagDark
              rounded-xl
              p-4
              overflow-x-auto
              whitespace-pre-wrap
              border
              border-surface-border
              dark:border-surface-borderDark
              leading-relaxed
              icr-math-content
            "
            v-html="textoIcrRenderizado"
          ></div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, defineComponent, h } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import { getExamDetail, downloadPDF, downloadWord } from '@/composables/useApi'

const route = useRoute()
const detail = ref(null)
const loading = ref(true)
const error = ref('')
const activeTab = ref('final')

const SVG_PATHS = {
  'arrow-left': [
    'M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18',
  ],
  'arrow-down-tray': [
    'M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5',
    'M7.5 10.5 12 15m0 0 4.5-4.5M12 15V3',
  ],
  scale: [
    'M12 3v18m7.5-14.25H4.5M6.75 6.75 3.75 12a3.75 3.75 0 0 0 6 0L6.75 6.75Zm10.5 0-3 5.25a3.75 3.75 0 0 0 6 0l-3-5.25Z',
  ],
  beaker: [
    'M9.75 3.104v5.714a2.25 2.25 0 0 1-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 0 1 4.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19 14.5m-4.75-11.396c.251.023.501.05.75.082M19 14.5l-3.221 5.635A2.25 2.25 0 0 1 13.824 21H10.176a2.25 2.25 0 0 1-1.955-1.865L5 14.5m14 0H5',
  ],
  'document-text': [
    'M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12h7.5m-7.5 3h4.5m-4.5-6h7.5m-7.5-9H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z',
  ],
  check: [
    'M4.5 12.75l6 6 9-13.5',
  ],
  'x-mark': [
    'M6 18 18 6M6 6l12 12',
  ],
  'chat-bubble': [
    'M8.625 12a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 0 1-2.555-.337A5.972 5.972 0 0 1 5.41 20.97a5.969 5.969 0 0 1-.474-.065 4.48 4.48 0 0 0 .978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25Z',
  ],
  'magnifying-glass': [
    'm21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z',
  ],
  'hand-thumb-up': [
    'M6.633 10.5c.806 0 1.533-.446 2.031-1.08a9.041 9.041 0 0 0 1.44-2.04c.318-.621.496-1.327.496-2.07A2.25 2.25 0 0 1 12.85 3a2.25 2.25 0 0 1 2.25 2.25c0 1.152-.26 2.243-.723 3.218-.266.558.107 1.232.725 1.232h3.126c1.026 0 1.945.694 2.054 1.715.224 2.103-.097 4.212-.886 6.105C18.76 19.06 17.228 20.25 15.568 20.25H9.681c-.688 0-1.329-.354-1.696-.937L6.633 10.5ZM3.75 10.5h2.883v9.75H3.75A1.5 1.5 0 0 1 2.25 18.75v-6.75a1.5 1.5 0 0 1 1.5-1.5Z',
  ],
  'exclamation-triangle': [
    'M12 9v3.75m0 3.75h.008v.008H12v-.008Zm-1.07-13.25c.478-.826 1.664-.826 2.142 0l8.058 13.93c.478.827-.119 1.861-1.071 1.861H3.943c-.952 0-1.55-1.034-1.071-1.861L10.93 3.25Z',
  ],
  'light-bulb': [
    'M12 18v-5.25m0 0a6 6 0 1 0-3.464-1.098c.28.19.464.507.464.848v.75m3-5.25v5.25m0 0h3m-6 0h6m-5.25 3h4.5m-4.5 3h4.5',
  ],
  'cpu-chip': [
    'M8.25 3v1.5M15.75 3v1.5M8.25 19.5V21M15.75 19.5V21M3 8.25h1.5M3 15.75h1.5M19.5 8.25H21M19.5 15.75H21M7.5 7.5h9v9h-9v-9ZM9 9h6v6H9V9Z',
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
      const paths = SVG_PATHS[props.name] || SVG_PATHS['document-text']

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


const tabs = [
  { id: 'final', label: 'Resultado Final', icon: 'scale' },
  { id: 'comparacion', label: 'Comparación Agentes', icon: 'beaker' },
  { id: 'icr', label: 'Texto ICR', icon: 'document-text' },
]

const agentCards = [
  { key: 'calificador_b', label: 'Calificador', color: 'purple', icon: 'cpu-chip', modelo: 'Pro' },
  { key: 'juez', label: 'Juez / Supervisor', color: 'amber', icon: 'scale', modelo: 'Flash' },
]

const finalSections = [
  {
    key: 'fortalezas',
    title: 'Fortalezas',
    icon: 'hand-thumb-up',
    style: 'border-green-500/20 bg-green-500/5',
    titleColor: 'text-green-600 dark:text-green-400',
  },
  {
    key: 'debilidades',
    title: 'Áreas de Mejora',
    icon: 'exclamation-triangle',
    style: 'border-red-500/20 bg-red-500/5',
    titleColor: 'text-red-600 dark:text-red-400',
  },
  {
    key: 'sugerencias',
    title: 'Sugerencias',
    icon: 'light-bulb',
    style: 'border-brand-500/20 bg-brand-500/5',
    titleColor: 'text-brand-700 dark:text-brand-300',
  },
]
const juezData = computed(() => detail.value?.agentes?.juez?.respuesta)

function normalizarSerie(nombre) {
  if (!nombre) return 'Sin serie'

  const limpio = String(nombre).trim()

  if (/^serie/i.test(limpio)) {
    return limpio
  }

  if (/^[IVXLCDM]+$/i.test(limpio)) {
    return `Serie ${limpio.toUpperCase()}`
  }

  if (/^\d+$/.test(limpio)) {
    return `Serie ${limpio}`
  }

  return limpio
}

function romanoDesdeSerie(nombre) {
  const texto = String(nombre || '').toUpperCase()

  const matchRomano = texto.match(/\b(I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|XIV|XV)\b/)
  if (matchRomano) return matchRomano[1]

  const matchNumero = texto.match(/\d+/)
  if (matchNumero) return matchNumero[0]

  return '—'
}

const seriesAgrupadas = computed(() => {
  const preguntas = juezData.value?.preguntas || []
  const grupos = {}

  preguntas.forEach((p) => {
    const nombreSerie = normalizarSerie(p.serie_seccion || p.serie || 'Sin serie')

    if (!grupos[nombreSerie]) {
      grupos[nombreSerie] = {
        nombre: nombreSerie,
        romano: romanoDesdeSerie(nombreSerie),
        items: [],
        punteoObtenido: 0,
        punteoMaximo: 0,
      }
    }

    grupos[nombreSerie].items.push(p)
  })

  return Object.values(grupos).map((serie) => {
    const itemsOrdenados = [...serie.items].sort((a, b) => {
      return Number(a.numero || 0) - Number(b.numero || 0)
    })

    const punteoObtenido = itemsOrdenados.reduce((total, p) => {
      return total + Number(p.punteo_obtenido || 0)
    }, 0)

    const punteoMaximo = itemsOrdenados.reduce((total, p) => {
      return total + Number(p.punteo_maximo || 0)
    }, 0)

    return {
      ...serie,
      items: itemsOrdenados,
      punteoObtenido: Number(punteoObtenido.toFixed(2)),
      punteoMaximo: Number(punteoMaximo.toFixed(2)),
    }
  })
})

const discrepancias = computed(() => juezData.value?.discrepancias_resueltas || [])

const punteoColor = computed(() => {
  const p = detail.value?.examen?.porcentaje

  if (!p && p !== 0) {
    return 'text-surface-muted dark:text-surface-mutedDark'
  }

  if (p >= 70) {
    return 'text-green-600 dark:text-green-400'
  }

  if (p >= 60) {
    return 'text-yellow-600 dark:text-yellow-400'
  }

  return 'text-red-600 dark:text-red-400'
})

const textoIcrRenderizado = computed(() => {
  return renderizarLatexEnTexto(detail.value?.examen?.texto_icr || 'No disponible')
})

function estadoBadge(estado) {
  const map = {
    completado: 'badge badge-success',
    procesando: 'badge badge-info',
    error: 'badge badge-danger',
    pendiente: 'badge badge-muted',
  }

  return map[estado] || 'badge badge-muted'
}

function formatDate(iso) {
  if (!iso) return ''

  return new Date(iso).toLocaleString('es-GT', {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

/* ============================================================
   UTILIDADES DE TEXTO SEGURO
============================================================ */

function escaparHtml(texto) {
  return String(texto || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function desescaparHtmlBasico(texto) {
  return String(texto || '')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
}

/* ============================================================
   NORMALIZACIÓN MATEMÁTICA
============================================================ */

function normalizarTextoMatematico(texto) {
  let t = String(texto || '').trim()

  t = t
    .replace(/×/g, '\\times ')
    .replace(/÷/g, '\\div ')
    .replace(/−/g, '-')
    .replace(/≤/g, '\\le ')
    .replace(/≥/g, '\\ge ')
    .replace(/π/g, '\\pi ')
    .replace(/√\s*\(([^)]+)\)/g, '\\sqrt{$1}')
    .replace(/√\s*([a-zA-Z0-9]+)/g, '\\sqrt{$1}')
    .replace(/\^([a-zA-Z0-9]+)/g, '^{$1}')

  // Fracciones con paréntesis: (x+1)/(x-2)
  t = t.replace(/\(([^()]+)\)\s*\/\s*\(([^()]+)\)/g, '\\frac{$1}{$2}')

  // Fracciones simples: 1/2, x/2, 2/x, a/b
  t = t.replace(/\b([a-zA-Z0-9]+)\s*\/\s*([a-zA-Z0-9]+)\b/g, '\\frac{$1}{$2}')

  return t
}

function renderizarFormula(formula, displayMode = false) {
  try {
    const formulaLimpia = desescaparHtmlBasico(formula)
    const formulaNormalizada = normalizarTextoMatematico(formulaLimpia)

    return katex.renderToString(formulaNormalizada, {
      throwOnError: false,
      displayMode,
      strict: false,
      trust: false,
    })
  } catch {
    return escaparHtml(formula)
  }
}

function esFechaOTextoNoMatematico(match, textoCompleto, index) {
  const antes = textoCompleto[index - 1] || ''
  const despues = textoCompleto[index + match.length] || ''

  // Evita convertir fechas como 28/05/2026
  if (/^\d{1,2}\/\d{1,2}$/.test(match) && despues === '/') {
    return true
  }

  // Evita convertir partes dentro de palabras
  if (/[a-zA-Z]/.test(antes) || /[a-zA-Z]/.test(despues)) {
    return true
  }

  return false
}

function renderizarMatematicaSinDelimitadores(textoSeguro) {
  let resultado = String(textoSeguro || '')

  // Primero fracciones con paréntesis: (x+1)/(x-2)
  resultado = resultado.replace(/\(([^()\n]{1,80})\)\s*\/\s*\(([^()\n]{1,80})\)/g, (match, numerador, denominador) => {
    return renderizarFormula(`\\frac{${desescaparHtmlBasico(numerador)}}{${desescaparHtmlBasico(denominador)}}`)
  })

  // Fracciones simples: 1/2, x/2, 2/x, a/b
  resultado = resultado.replace(/\b([a-zA-Z0-9]+)\s*\/\s*([a-zA-Z0-9]+)\b/g, (match, numerador, denominador, index, fullText) => {
    if (esFechaOTextoNoMatematico(match, fullText, index)) {
      return match
    }

    return renderizarFormula(`\\frac{${numerador}}{${denominador}}`)
  })

  // Raíces sin delimitadores: √x o √(x+1)
  resultado = resultado.replace(/√\s*\(([^)\n]{1,80})\)|√\s*([a-zA-Z0-9]+)/g, (match, raizParentesis, raizSimple) => {
    const contenido = raizParentesis || raizSimple
    return renderizarFormula(`\\sqrt{${desescaparHtmlBasico(contenido)}}`)
  })

  // Potencias simples: x^2, y^3
  resultado = resultado.replace(/\b([a-zA-Z0-9]+)\^([a-zA-Z0-9]+)\b/g, (match, base, exponente) => {
    return renderizarFormula(`${base}^{${exponente}}`)
  })

  return resultado
}

function renderizarLatexEnTexto(texto) {
  if (!texto) return 'No disponible'

  const original = String(texto)

  const formulas = []

  // Guardamos las fórmulas ya delimitadas para que no se mezclen con el HTML final
  let textoConPlaceholders = original.replace(/\$\$([\s\S]+?)\$\$|\$([^$\n]+)\$/g, (_, formulaBloque, formulaLinea) => {
    const formula = formulaBloque || formulaLinea
    const displayMode = Boolean(formulaBloque)
    const html = renderizarFormula(formula, displayMode)

    const placeholder = `@@FORMULA_KATEX_${formulas.length}@@`
    formulas.push(html)

    return placeholder
  })

  // Escapamos HTML del texto normal
  let seguro = escaparHtml(textoConPlaceholders)

  // Renderizamos fracciones, raíces y potencias que vienen sin $...$
  seguro = renderizarMatematicaSinDelimitadores(seguro)

  // Restauramos las fórmulas renderizadas
  formulas.forEach((html, index) => {
    seguro = seguro.replace(`@@FORMULA_KATEX_${index}@@`, html)
  })

  return seguro
}

/* ============================================================
   COMPONENTE AGENT CARD
============================================================ */

const AgentCard = defineComponent({
  name: 'AgentCard',

  props: {
    agent: {
      type: Object,
      required: true,
    },
    data: {
      type: Object,
      default: null,
    },
  },

  setup(props) {
    const colorMap = {
      blue: 'border-blue-500/30 bg-blue-500/5',
      purple: 'border-purple-500/30 bg-purple-500/5',
      amber: 'border-amber-500/30 bg-amber-500/5',
    }

    const textMap = {
      blue: 'text-blue-600 dark:text-blue-300',
      purple: 'text-purple-600 dark:text-purple-300',
      amber: 'text-amber-600 dark:text-amber-300',
    }

    return () => {
      const d = props.data
      const a = props.agent

      return h('div', { class: `card p-5 border ${colorMap[a.color]}` }, [
        h('div', { class: 'flex items-center gap-2 mb-4' }, [
          h(SvgIcon, {
            name: a.icon,
            class: `w-5 h-5 ${textMap[a.color]}`,
          }),

          h('div', {}, [
            h(
              'p',
              { class: `font-medium text-sm ${textMap[a.color]}` },
              a.label,
            ),

            h(
              'p',
              {
                class:
                  'text-xs text-surface-muted dark:text-surface-mutedDark',
              },
              d ? `Modelo: ${d.modelo || a.modelo}` : 'Sin datos',
            ),
          ]),
        ]),

        d
          ? [
              h('div', { class: 'space-y-2 text-xs' }, [
                h('div', { class: 'flex justify-between gap-3' }, [
                  h(
                    'span',
                    {
                      class:
                        'text-surface-muted dark:text-surface-mutedDark',
                    },
                    'Punteo Total',
                  ),

                  h(
                    'span',
                    {
                      class: `font-mono font-bold ${textMap[a.color]}`,
                    },
                    d.respuesta?.punteo_total ?? '—',
                  ),
                ]),

                h('div', { class: 'flex justify-between gap-3' }, [
                  h(
                    'span',
                    {
                      class:
                        'text-surface-muted dark:text-surface-mutedDark',
                    },
                    'Tokens',
                  ),

                  h(
                    'span',
                    {
                      class:
                        'font-mono text-surface-text dark:text-surface-textDark',
                    },
                    d.tokens ?? '—',
                  ),
                ]),

                h('div', { class: 'flex justify-between gap-3' }, [
                  h(
                    'span',
                    {
                      class:
                        'text-surface-muted dark:text-surface-mutedDark',
                    },
                    'Latencia',
                  ),

                  h(
                    'span',
                    {
                      class:
                        'font-mono text-surface-text dark:text-surface-textDark',
                    },
                    d.latencia_ms ? `${d.latencia_ms}ms` : '—',
                  ),
                ]),
              ]),

              d.error
                ? h(
                    'p',
                    {
                      class:
                        'text-xs text-red-500 dark:text-red-400 mt-3 p-2 bg-red-500/10 rounded',
                    },
                    [
                      h(SvgIcon, {
                        name: 'exclamation-triangle',
                        class:
                          'w-4 h-4 inline-block mr-1 align-text-bottom',
                      }),
                      h('span', {}, d.error),
                    ],
                  )
                : null,

              d.respuesta?.conclusion
                ? h('p', {
                    class:
                      'text-xs text-surface-muted dark:text-surface-mutedDark mt-3 line-clamp-3 italic math-content',
                    innerHTML: `"${renderizarLatexEnTexto(d.respuesta.conclusion)}"`,
                  })
                : null,
            ]
          : h(
              'p',
              {
                class:
                  'text-surface-muted dark:text-surface-mutedDark text-sm italic',
              },
              'Sin datos de este agente',
            ),
      ])
    }
  },
})

/* ============================================================
   CARGA DEL DETALLE
============================================================ */

onMounted(async () => {
  try {
    loading.value = true
    error.value = ''
    detail.value = await getExamDetail(route.params.id)
  } catch (e) {
    error.value = e?.message || 'No se pudo cargar el resultado del examen.'
  } finally {
    loading.value = false
  }
})
</script>