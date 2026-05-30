<template>
  <div class="max-w-4xl mx-auto px-6 py-10 animate-fade-in">
    <!-- Encabezado -->
    <div class="mb-8">
      <h1 class="font-display text-3xl text-surface-text dark:text-surface-textDark mb-1">
        Materiales del Curso
      </h1>

      <p class="text-surface-muted dark:text-surface-mutedDark text-sm">
        Sube PDFs, documentos Word o presentaciones PowerPoint para el sistema RAG.
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Panel de subida -->
      <div class="card p-6">
        <h2 class="font-medium text-surface-text dark:text-surface-textDark mb-4 flex items-center gap-2">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="2"
            stroke="currentColor"
            class="w-4 h-4 text-accent-orange"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M12 16V4m0 0l-4 4m4-4l4 4M4 16v3a1 1 0 001 1h14a1 1 0 001-1v-3"
            />
          </svg>

          Subir Material
        </h2>

        <!-- Zona drag & drop -->
        <div
          class="border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer mb-4"
          :class="dragOver
            ? 'border-brand-500 bg-brand-300/10 dark:border-brand-300 dark:bg-brand-500/10'
            : 'border-surface-border hover:border-brand-500 dark:border-surface-borderDark dark:hover:border-brand-300/60'"
          @dragover.prevent="dragOver = true"
          @dragleave="dragOver = false"
          @drop.prevent="onDrop"
          @click="fileRef?.click()"
        >
          <input
            ref="fileRef"
            type="file"
            accept=".pdf,.docx,.pptx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.presentationml.presentation"
            class="hidden"
            @change="onFile"
          />

          <div class="text-4xl mb-2">📎</div>

          <p class="text-surface-text dark:text-surface-textDark font-medium">
            Arrastra un archivo aquí
          </p>

          <p class="text-surface-muted dark:text-surface-mutedDark text-sm mt-1">
            o haz clic para seleccionar
          </p>

          <div class="flex justify-center gap-2 mt-3">
            <span class="badge text-xs bg-accent-orange/10 text-accent-orange border border-accent-orange/30">
              PDF
            </span>

            <span class="badge text-xs bg-accent-orange/10 text-accent-orange border border-accent-orange/30">
              DOCX
            </span>

            <span class="badge text-xs bg-accent-orange/10 text-accent-orange border border-accent-orange/30">
              PPTX
            </span>
          </div>
        </div>

        <!-- Preview del archivo seleccionado -->
        <div
          v-if="selectedFile"
          class="flex items-center gap-3 p-3 bg-surface-tag dark:bg-surface-tagDark rounded-xl border border-surface-border dark:border-surface-borderDark mb-4"
        >
          <span class="text-2xl">{{ fileIcon(selectedFile.name) }}</span>

          <div class="flex-1 min-w-0">
            <p class="text-sm text-surface-text dark:text-surface-textDark truncate">
              {{ selectedFile.name }}
            </p>

            <p class="text-xs text-surface-muted dark:text-surface-mutedDark">
              {{ (selectedFile.size / 1024 / 1024).toFixed(2) }} MB
              · {{ fileExtLabel(selectedFile.name) }}
            </p>
          </div>

          <button
            @click.stop="selectedFile = null"
            class="text-surface-muted hover:text-red-500 dark:text-surface-mutedDark dark:hover:text-red-400 p-1 transition-colors"
          >
            ✕
          </button>
        </div>

        <!-- Botón subir -->
        <button
          @click="uploadFile"
          :disabled="!selectedFile || uploading"
          class="btn-primary w-full justify-center"
        >
          <span v-if="uploading" class="spinner w-4 h-4"></span>

          <svg
            v-else
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="2"
            stroke="currentColor"
            class="w-4 h-4"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M21 21l-4.35-4.35M10.5 18a7.5 7.5 0 1 1 0-15 7.5 7.5 0 0 1 0 15z"
            />
          </svg>

          {{ uploading ? 'Indexando...' : 'Indexar Material' }}
        </button>

        <!-- Barra de progreso al indexar -->
        <div v-if="uploading" class="mt-3">
          <div class="w-full h-1.5 bg-surface-border dark:bg-surface-borderDark rounded-full overflow-hidden">
            <div class="h-full bg-brand-500 dark:bg-brand-400 rounded-full animate-pulse w-2/3"></div>
          </div>

          <p class="text-xs text-surface-muted dark:text-surface-mutedDark mt-1 text-center">
            Procesando y generando embeddings…
          </p>
        </div>

        <!-- Resultado exitoso -->
        <div
          v-if="uploadResult"
          class="mt-4 p-4 rounded-xl border border-green-500/20 bg-green-500/5 text-sm animate-slide-up"
        >
          <p class="text-green-600 dark:text-green-400 font-medium">
            ✅ Material indexado correctamente
          </p>

          <p class="text-surface-muted dark:text-surface-mutedDark mt-1">
            {{ uploadResult.paginas }}
            {{ uploadResult.formato === '.pptx' ? 'diapositivas' : 'páginas' }}
            · {{ uploadResult.chunks }} fragmentos RAG
          </p>
        </div>

        <!-- Error -->
        <div
          v-if="uploadError"
          class="mt-4 p-4 rounded-xl border border-red-500/20 bg-red-500/5 text-sm"
        >
          <p class="text-red-500 dark:text-red-400">
            ❌ {{ uploadError }}
          </p>
        </div>
      </div>

      <!-- Info panel -->
      <div class="space-y-4">
        <!-- Cómo funciona -->
        <div class="card p-5">
          <h3 class="font-medium text-surface-text dark:text-surface-textDark mb-3 text-sm flex items-center gap-2">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="2"
              stroke="currentColor"
              class="w-4 h-4 text-accent-pink"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M9.75 3a3 3 0 00-3 3v.75A3.75 3.75 0 003 10.5c0 1.2.57 2.27 1.45 2.96A3.75 3.75 0 007.5 19.5h.75M14.25 3a3 3 0 013 3v.75A3.75 3.75 0 0121 10.5c0 1.2-.57 2.27-1.45 2.96A3.75 3.75 0 0116.5 19.5h-.75M12 4.5v15"
              />
            </svg>

            Cómo funciona el RAG
          </h3>

          <ol class="space-y-2.5 text-xs text-surface-muted dark:text-surface-mutedDark">
            <li class="flex gap-2">
              <span class="text-brand-700 dark:text-brand-300 font-bold shrink-0">1.</span>
              El archivo se divide en fragmentos de ~500 caracteres con overlap
            </li>

            <li class="flex gap-2">
              <span class="text-brand-700 dark:text-brand-300 font-bold shrink-0">2.</span>
              Cada fragmento se convierte en un vector de embeddings (Google GenAI)
            </li>

            <li class="flex gap-2">
              <span class="text-brand-700 dark:text-brand-300 font-bold shrink-0">3.</span>
              Los vectores se almacenan en SQLite asociados a este curso
            </li>

            <li class="flex gap-2">
              <span class="text-brand-700 dark:text-brand-300 font-bold shrink-0">4.</span>
              Al calificar, los 5 fragmentos más relevantes se entregan a los agentes
            </li>
          </ol>
        </div>

        <!-- Estadísticas del curso -->
        <div class="card p-5">
          <div class="flex items-center gap-2 mb-3">
            <div
              class="w-8 h-8 rounded-lg bg-brand-100 dark:bg-brand-500/10 border border-brand-200 dark:border-brand-400/20 flex items-center justify-center"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke-width="2"
                stroke="currentColor"
                class="w-4 h-4 text-brand-700 dark:text-brand-300"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M4.26 10.147L12 14.147l7.74-4.000m-7.74 4.000v5.333c0 .355.244.667.667.667h.666c.423 0 .667-.312.667-.667v-5.333M12 2.667l-9.333 4.666 9.333 4.667 9.333-4.667-9.333-4.666z"
                />
              </svg>
            </div>

            <h3 class="font-medium text-surface-text dark:text-surface-textDark text-sm">
              Este curso
            </h3>
          </div>

          <div class="grid grid-cols-3 gap-3 text-center">
            <div class="p-2 bg-surface-tag dark:bg-surface-tagDark rounded-lg border border-surface-border/60 dark:border-surface-borderDark">
              <p class="text-xl font-mono text-brand-700 dark:text-brand-300 font-bold">
                {{ materials.length }}
              </p>

              <p class="text-xs text-surface-muted dark:text-surface-mutedDark mt-0.5">
                Archivos
              </p>
            </div>

            <div class="p-2 bg-surface-tag dark:bg-surface-tagDark rounded-lg border border-surface-border/60 dark:border-surface-borderDark">
              <p class="text-xl font-mono text-brand-700 dark:text-brand-300 font-bold">
                {{ totalChunks }}
              </p>

              <p class="text-xs text-surface-muted dark:text-surface-mutedDark mt-0.5">
                Fragmentos
              </p>
            </div>

            <div class="p-2 bg-surface-tag dark:bg-surface-tagDark rounded-lg border border-surface-border/60 dark:border-surface-borderDark">
              <p class="text-xl font-mono text-brand-700 dark:text-brand-300 font-bold">
                {{ indexedCount }}
              </p>

              <p class="text-xs text-surface-muted dark:text-surface-mutedDark mt-0.5">
                Indexados
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tabla de materiales -->
    <div class="mt-8">
      <h2 class="font-medium text-surface-text dark:text-surface-textDark mb-4 flex items-center gap-2">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="2"
          stroke="currentColor"
          class="w-4 h-4 text-accent-blue"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M4 5.5A2.5 2.5 0 016.5 3H20v16H6.5A2.5 2.5 0 004 21.5v-16zM4 5.5A2.5 2.5 0 006.5 8H20"
          />
        </svg>

        Materiales Indexados

        <button
          @click="loadMaterials"
          class="ml-auto text-xs text-surface-muted hover:text-surface-text dark:text-surface-mutedDark dark:hover:text-surface-textDark transition-colors"
        >
          ↺ Actualizar
        </button>
      </h2>

      <!-- Loading -->
      <div v-if="loadingMats" class="flex justify-center py-10">
        <div class="spinner w-7 h-7"></div>
      </div>

      <!-- Vacío -->
      <div v-else-if="!materials.length" class="card p-10 text-center">
        <p class="text-3xl mb-2">📭</p>

        <p class="text-surface-text dark:text-surface-textDark font-medium">
          No hay materiales indexados en este curso
        </p>

        <p class="text-surface-muted dark:text-surface-mutedDark text-sm mt-1">
          Sube un PDF, DOCX o PPTX para habilitar el contexto RAG.
        </p>
      </div>

      <!-- Tabla -->
      <div v-else class="card overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-sm min-w-[600px]">
            <thead>
              <tr
                class="border-b border-surface-border dark:border-surface-borderDark text-left text-xs text-surface-muted dark:text-surface-mutedDark uppercase tracking-wide bg-surface-cardSoft dark:bg-surface-cardDark"
              >
                <th class="px-5 py-3">Archivo</th>
                <th class="px-5 py-3 text-center">Páginas</th>
                <th class="px-5 py-3 text-center">Fragmentos</th>
                <th class="px-5 py-3 text-center">Estado</th>
                <th class="px-5 py-3">Indexado</th>
                <th class="px-5 py-3 text-right">Acciones</th>
              </tr>
            </thead>

            <tbody class="divide-y divide-surface-border dark:divide-surface-borderDark">
              <tr
                v-for="m in materials"
                :key="m.id"
                class="hover:bg-surface-tableHover dark:hover:bg-white/[0.03] transition-colors"
              >
                <!-- Nombre + icono de formato -->
                <td class="px-5 py-3 text-surface-text dark:text-surface-textDark">
                  <div class="flex items-center gap-2 min-w-0">
                    <span class="text-lg shrink-0">
                      {{ fileIcon(m.nombre) }}
                    </span>

                    <span class="truncate max-w-[180px]" :title="m.nombre">
                      {{ m.nombre }}
                    </span>

                    <span class="badge badge-muted text-xs shrink-0 hidden sm:inline">
                      {{ m.formato?.replace('.', '').toUpperCase() }}
                    </span>
                  </div>
                </td>

                <!-- Páginas -->
                <td class="px-5 py-3 font-mono text-surface-muted dark:text-surface-mutedDark text-center">
                  {{ m.paginas || '–' }}
                </td>

                <!-- Fragmentos -->
                <td class="px-5 py-3 font-mono text-surface-muted dark:text-surface-mutedDark text-center">
                  {{ m.chunks || '–' }}
                </td>

                <!-- Estado -->
                <td class="px-5 py-3 text-center">
                  <span :class="badgeClass(m.estado)">
                    {{ estadoLabel(m.estado) }}
                  </span>
                </td>

                <!-- Fecha -->
                <td class="px-5 py-3 text-surface-muted dark:text-surface-mutedDark text-xs whitespace-nowrap">
                  {{ formatDate(m.created_at) }}
                </td>

                <!-- Acciones -->
                <td class="px-5 py-3 text-right">
                  <button
                    @click="confirmDelete(m)"
                    :disabled="deletingId === m.id"
                    class="text-surface-muted hover:text-red-500 dark:text-surface-mutedDark dark:hover:text-red-400 transition-colors text-xs px-2 py-1 rounded hover:bg-red-500/10 disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Eliminar material"
                  >
                    <span
                      v-if="deletingId === m.id"
                      class="spinner w-3 h-3 inline-block"
                    ></span>

                    <svg
                      v-else
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke-width="2"
                      stroke="currentColor"
                      class="w-4 h-4 text-red-500 dark:text-red-400"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6M10 11v6M14 11v6"
                      />
                    </svg>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Modal confirmación eliminación -->
    <Teleport to="body">
      <div
        v-if="deleteTarget"
        class="fixed inset-0 bg-black/40 dark:bg-black/60 flex items-center justify-center z-50 p-4"
        @click.self="deleteTarget = null"
      >
        <div class="card p-6 max-w-sm w-full animate-slide-up">
          <h3 class="font-medium text-surface-text dark:text-surface-textDark mb-2">
            ¿Eliminar material?
          </h3>

          <p class="text-surface-muted dark:text-surface-mutedDark text-sm mb-1">
            Se eliminará
            <span class="text-surface-text dark:text-white font-medium">
              {{ deleteTarget.nombre }}
            </span>
          </p>

          <p class="text-surface-muted dark:text-surface-mutedDark text-xs mb-5">
            Se borrarán todos sus fragmentos del índice RAG. Esta acción no se puede deshacer.
          </p>

          <div class="flex gap-3">
            <button
              @click="deleteTarget = null"
              class="btn-secondary flex-1 justify-center"
            >
              Cancelar
            </button>

            <button
              @click="deleteMaterial"
              class="flex-1 justify-center inline-flex items-center gap-2 rounded-lg px-5 py-2 font-mono font-medium transition-all duration-200 bg-red-500/10 text-red-600 border border-red-500/30 hover:bg-red-500/15 dark:text-red-400 dark:hover:text-red-300"
            >
              Eliminar
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { uploadMaterial, listMaterials, deleteMaterial as apiDeleteMaterial } from '@/composables/useApi'
import { useCursoStore } from '@/stores/cursoStore'

// ── Props / Route ──────────────────────────────────────────
const cursoStore = useCursoStore()
const cursoId = computed(() => cursoStore.cursoId)

// ── Estado ─────────────────────────────────────────────────
const fileRef = ref(null)
const dragOver = ref(false)
const selectedFile = ref(null)
const uploading = ref(false)
const uploadResult = ref(null)
const uploadError = ref('')
const materials = ref([])
const loadingMats = ref(true)
const deletingId = ref(null)
const deleteTarget = ref(null)

// ── Computed ───────────────────────────────────────────────
const totalChunks = computed(() => materials.value.reduce((s, m) => s + (m.chunks || 0), 0))
const indexedCount = computed(() => materials.value.filter((m) => m.estado === 'indexado').length)

// ── Helpers de formato ─────────────────────────────────────
const ICONS = {
  pdf: '📄',
  docx: '📝',
  doc: '📝',
  pptx: '📊',
  ppt: '📊',
}

function fileExt(name = '') {
  return (name.split('.').pop() || '').toLowerCase()
}

function fileIcon(name = '') {
  return ICONS[fileExt(name)] || '📎'
}

function fileExtLabel(name = '') {
  return fileExt(name).toUpperCase()
}

function badgeClass(estado) {
  const map = {
    indexado: 'badge badge-success',
    pendiente: 'badge badge-muted',
    procesando: 'badge badge-info',
    error: 'badge badge-danger',
  }

  return map[estado] ?? 'badge badge-muted'
}

function estadoLabel(estado) {
  const map = {
    indexado: '✓ Indexado',
    pendiente: '⏳ Pendiente',
    procesando: '⚙️ Procesando',
    error: '✗ Error',
  }

  return map[estado] ?? estado
}

function formatDate(iso) {
  if (!iso) return '–'

  return new Date(iso).toLocaleString('es-GT', {
    dateStyle: 'short',
    timeStyle: 'short',
  })
}

// ── Subida de archivo ──────────────────────────────────────
const ALLOWED_EXTS = ['pdf', 'docx', 'pptx']

function validateFile(file) {
  if (!file) return 'No se seleccionó ningún archivo.'

  const ext = fileExt(file.name)

  if (!ALLOWED_EXTS.includes(ext)) {
    return `Formato no soportado: .${ext}. Solo se aceptan PDF, DOCX y PPTX.`
  }

  if (file.size > 50 * 1024 * 1024) {
    return 'El archivo supera el límite de 50 MB.'
  }

  return null
}

function onDrop(e) {
  dragOver.value = false

  const file = e.dataTransfer.files[0]
  const err = validateFile(file)

  if (err) {
    uploadError.value = err
    return
  }

  uploadError.value = ''
  selectedFile.value = file
}

function onFile(e) {
  const file = e.target.files[0] || null
  const err = validateFile(file)

  if (err) {
    uploadError.value = err
    selectedFile.value = null
    return
  }

  uploadError.value = ''
  selectedFile.value = file
}

async function uploadFile() {
  if (!selectedFile.value) return

  uploading.value = true
  uploadResult.value = null
  uploadError.value = ''

  try {
    const fd = new FormData()
    fd.append('archivo', selectedFile.value, selectedFile.value.name)

    uploadResult.value = await uploadMaterial(cursoId.value, fd)
    selectedFile.value = null

    if (fileRef.value) {
      fileRef.value.value = ''
    }

    await loadMaterials()
  } catch (e) {
    uploadError.value = e?.detail ?? e?.message ?? 'Error al indexar el material.'
  } finally {
    uploading.value = false
  }
}

// ── Carga de materiales ────────────────────────────────────
async function loadMaterials() {
  loadingMats.value = true

  try {
    const data = await listMaterials(cursoId.value)
    materials.value = data.materiales ?? []
  } catch {
    materials.value = []
  } finally {
    loadingMats.value = false
  }
}

// ── Eliminación ────────────────────────────────────────────
function confirmDelete(material) {
  deleteTarget.value = material
}

async function deleteMaterial() {
  if (!deleteTarget.value) return

  const id = deleteTarget.value.id

  deletingId.value = id
  deleteTarget.value = null

  try {
    await apiDeleteMaterial(cursoId.value, id)
    await loadMaterials()
  } catch (e) {
    uploadError.value = e?.detail ?? 'No se pudo eliminar el material.'
  } finally {
    deletingId.value = null
  }
}

// ── Lifecycle ──────────────────────────────────────────────
onMounted(loadMaterials)
</script>