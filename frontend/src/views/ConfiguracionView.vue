<template>
  <div class="perfil-page">
    <!-- Header -->
    <div class="perfil-header">
      <button @click="$router.back()" class="perfil-back-btn">
        <svg
          class="w-4 h-4"
          viewBox="0 0 20 20"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path stroke-linecap="round" d="M12 5l-5 5 5 5" />
        </svg>
        Volver
      </button>

      <h1 class="perfil-title">Mi perfil</h1>

      <div class="w-16"></div>
    </div>

    <!-- Loading skeleton -->
    <div v-if="pageLoading" class="max-w-2xl mx-auto px-4 mt-6 space-y-4">
      <div v-for="n in 3" :key="n" class="perfil-skeleton-card"></div>
    </div>

    <div v-else class="max-w-2xl mx-auto px-4 pb-16 space-y-5 mt-6">
      <!-- Avatar + nombre -->
      <div class="perfil-card perfil-hero">
        <div class="flex items-center gap-5">
          <div class="perfil-avatar-ring">
            <div class="perfil-avatar-inner">
              {{ avatarLetters }}
            </div>
          </div>

          <div class="flex-1 min-w-0">
            <h2 class="text-surface-text dark:text-surface-textDark font-bold text-xl truncate">
              {{ docente.nombre || 'Docente' }}
            </h2>

            <p class="text-surface-muted dark:text-surface-mutedDark text-sm truncate">
              {{ docente.email }}
            </p>

            <div class="flex items-center gap-2 mt-2 flex-wrap">
              <span class="perfil-badge-active">
                <span class="perfil-pulse-dot"></span>
                Cuenta activa
              </span>

              <span v-if="docente.institucion" class="perfil-badge-inst">
                {{ docente.institucion }}
              </span>
            </div>
          </div>

          <div class="perfil-nivel-ring">
            <svg viewBox="0 0 44 44" class="w-11 h-11">
              <circle
                cx="22"
                cy="22"
                r="18"
                fill="none"
                class="perfil-ring-bg"
                stroke-width="3"
              />

              <circle
                cx="22"
                cy="22"
                r="18"
                fill="none"
                class="perfil-ring-progress"
                stroke-width="3"
                stroke-dasharray="113.1"
                :stroke-dashoffset="113.1 - (113.1 * docente.nivel_exigencia / 10)"
                stroke-linecap="round"
                transform="rotate(-90 22 22)"
              />
            </svg>

            <div class="perfil-nivel-label">
              <span class="text-brand-700 dark:text-brand-300 text-xs font-bold">
                {{ docente.nivel_exigencia }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="perfil-tabs-bar">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          class="perfil-tab-btn"
          :class="{ 'perfil-tab-active': activeTab === tab.id }"
        >
          <component
            :is="'svg'"
            class="w-4 h-4"
            viewBox="0 0 20 20"
            fill="none"
            stroke="currentColor"
            stroke-width="1.5"
            v-html="tab.icon"
          />
          {{ tab.label }}
        </button>
      </div>

      <!-- TAB: Información personal -->
      <Transition name="tab-fade" mode="out-in">
        <div v-if="activeTab === 'info'" key="info" class="perfil-card p-6 space-y-5">
          <div class="perfil-section-header">
            <svg
              class="w-4 h-4 text-brand-700 dark:text-brand-300"
              viewBox="0 0 20 20"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
            >
              <circle cx="10" cy="7" r="3" />
              <path stroke-linecap="round" d="M3 18c0-3.3 3.1-6 7-6s7 2.7 7 6" />
            </svg>

            <span>Información personal</span>
          </div>

          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div class="space-y-1">
              <label class="perfil-field-label">Nombre completo</label>

              <input
                v-model="infoForm.nombre"
                type="text"
                class="input w-full"
                placeholder="Tu nombre completo"
                :class="{ 'perfil-input-error': infoErrors.nombre }"
              />

              <p v-if="infoErrors.nombre" class="perfil-field-error">
                {{ infoErrors.nombre }}
              </p>
            </div>

            <div class="space-y-1">
              <label class="perfil-field-label">Institución educativa</label>

              <input
                v-model="infoForm.institucion"
                type="text"
                class="input w-full"
                placeholder="Tu universidad o colegio"
              />
            </div>
          </div>

          <div class="space-y-1">
            <label class="perfil-field-label">Correo electrónico</label>

            <div class="relative">
              <svg
                class="perfil-input-icon"
                viewBox="0 0 20 20"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <path
                  stroke-linecap="round"
                  d="M2.5 6.5l7.5 5 7.5-5M3 5h14a.5.5 0 01.5.5v9a.5.5 0 01-.5.5H3a.5.5 0 01-.5-.5v-9A.5.5 0 013 5z"
                />
              </svg>

              <input
                v-model="infoForm.email"
                type="email"
                class="input w-full pl-9"
                placeholder="docente@universidad.edu"
                :class="{ 'perfil-input-error': infoErrors.email }"
              />
            </div>

            <p v-if="infoErrors.email" class="perfil-field-error">
              {{ infoErrors.email }}
            </p>

            <p class="text-xs text-surface-muted dark:text-surface-mutedDark mt-1">
              Al cambiar el correo deberás iniciar sesión nuevamente
            </p>
          </div>

          <div class="space-y-2">
            <label class="perfil-field-label">
              Nivel de exigencia predeterminado

              <span class="perfil-nivel-badge">
                {{ infoForm.nivel_exigencia }}/10
              </span>
            </label>

            <div class="flex items-center gap-4">
              <span class="text-xs text-surface-muted dark:text-surface-mutedDark">
                Flexible
              </span>

              <input
                v-model.number="infoForm.nivel_exigencia"
                type="range"
                min="1"
                max="10"
                class="flex-1 perfil-range"
              />

              <span class="text-xs text-surface-muted dark:text-surface-mutedDark">
                Estricto
              </span>
            </div>

            <div class="perfil-nivel-desc">
              <svg
                class="w-3.5 h-3.5 text-brand-700 dark:text-brand-300 shrink-0"
                viewBox="0 0 14 14"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <circle cx="7" cy="7" r="6" />
                <path stroke-linecap="round" d="M7 6.5v3.5M7 4.5v.5" />
              </svg>

              <span class="text-xs text-surface-muted dark:text-surface-mutedDark">
                {{ nivelDesc(infoForm.nivel_exigencia) }}
              </span>
            </div>
          </div>

          <Transition name="error-slide">
            <div
              v-if="infoSuccess"
              class="perfil-success-box flex items-center gap-2.5 p-3.5 rounded-xl"
            >
              <svg
                class="w-4 h-4 text-green-600 dark:text-green-400 shrink-0"
                viewBox="0 0 16 16"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path stroke-linecap="round" d="M2 8l5 5 7-7" />
              </svg>

              <span class="text-sm text-green-600 dark:text-green-400">
                Perfil actualizado correctamente
              </span>
            </div>
          </Transition>

          <Transition name="error-slide">
            <div
              v-if="infoError"
              class="perfil-error-box flex items-start gap-2.5 p-3.5 rounded-xl"
            >
              <svg
                class="w-4 h-4 mt-0.5 shrink-0 text-red-500 dark:text-red-400"
                viewBox="0 0 16 16"
                fill="currentColor"
              >
                <path d="M8 0a8 8 0 100 16A8 8 0 008 0zm0 12a1 1 0 110-2 1 1 0 010 2zm1-4H7V4h2v4z" />
              </svg>

              <span class="text-sm text-red-500 dark:text-red-400">
                {{ infoError }}
              </span>
            </div>
          </Transition>

          <div class="flex justify-end">
            <button
              @click="saveInfo"
              :disabled="savingInfo"
              class="perfil-btn-primary-sm"
            >
              <span v-if="savingInfo" class="perfil-spinner-sm"></span>

              <svg
                v-else
                class="w-4 h-4"
                viewBox="0 0 20 20"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path stroke-linecap="round" d="M5 10l4 4 7-7" />
              </svg>

              {{ savingInfo ? 'Guardando...' : 'Guardar cambios' }}
            </button>
          </div>
        </div>
      </Transition>

      <!-- TAB: Seguridad / Contraseña -->
      <Transition name="tab-fade" mode="out-in">
        <div v-if="activeTab === 'seguridad'" key="seg" class="perfil-card p-6 space-y-5">
          <div class="perfil-section-header">
            <svg
              class="w-4 h-4 text-brand-700 dark:text-brand-300"
              viewBox="0 0 20 20"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
            >
              <rect x="4" y="8.5" width="12" height="8" rx="1.5" />
              <path stroke-linecap="round" d="M7 8.5V6a3 3 0 016 0v2.5" />
            </svg>

            <span>Cambiar contraseña</span>
          </div>

          <div class="space-y-1">
            <label class="perfil-field-label">Contraseña actual</label>

            <div class="relative">
              <svg
                class="perfil-input-icon"
                viewBox="0 0 20 20"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <rect x="4" y="8.5" width="12" height="8" rx="1.5" />
                <path stroke-linecap="round" d="M7 8.5V6a3 3 0 016 0v2.5" />
              </svg>

              <input
                v-model="pwdForm.actual"
                :type="showPwd.actual ? 'text' : 'password'"
                class="input w-full pl-9 pr-9"
                placeholder="Tu contraseña actual"
                :class="{ 'perfil-input-error': pwdErrors.actual }"
              />

              <button
                type="button"
                class="perfil-eye-btn"
                @click="showPwd.actual = !showPwd.actual"
              >
                <svg
                  viewBox="0 0 20 20"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.5"
                  class="w-4 h-4"
                >
                  <path
                    v-if="!showPwd.actual"
                    stroke-linecap="round"
                    d="M2 10s3-5 8-5 8 5 8 5-3 5-8 5-8-5-8-5z"
                  />

                  <circle v-if="!showPwd.actual" cx="10" cy="10" r="2" />

                  <path
                    v-if="showPwd.actual"
                    stroke-linecap="round"
                    d="M3 3l14 14M8.5 8.6A2 2 0 0011.4 11.5M6.3 6.4C4.5 7.4 3 10 3 10s3 5 7 5c1.4 0 2.7-.5 3.7-1.3M10 5c4 0 7 5 7 5s-.7 1.3-2 2.6"
                  />
                </svg>
              </button>
            </div>

            <p v-if="pwdErrors.actual" class="perfil-field-error">
              {{ pwdErrors.actual }}
            </p>
          </div>

          <div class="perfil-divider-thin"></div>

          <div class="space-y-1">
            <label class="perfil-field-label">Nueva contraseña</label>

            <div class="relative">
              <svg
                class="perfil-input-icon"
                viewBox="0 0 20 20"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <path stroke-linecap="round" d="M10 3v14m-7-7h14" />
              </svg>

              <input
                v-model="pwdForm.nueva"
                :type="showPwd.nueva ? 'text' : 'password'"
                class="input w-full pl-9 pr-9"
                placeholder="Mínimo 8 caracteres"
                :class="{ 'perfil-input-error': pwdErrors.nueva }"
              />

              <button
                type="button"
                class="perfil-eye-btn"
                @click="showPwd.nueva = !showPwd.nueva"
              >
                <svg
                  viewBox="0 0 20 20"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.5"
                  class="w-4 h-4"
                >
                  <path
                    v-if="!showPwd.nueva"
                    stroke-linecap="round"
                    d="M2 10s3-5 8-5 8 5 8 5-3 5-8 5-8-5-8-5z"
                  />

                  <circle v-if="!showPwd.nueva" cx="10" cy="10" r="2" />

                  <path
                    v-if="showPwd.nueva"
                    stroke-linecap="round"
                    d="M3 3l14 14M8.5 8.6A2 2 0 0011.4 11.5M6.3 6.4C4.5 7.4 3 10 3 10s3 5 7 5c1.4 0 2.7-.5 3.7-1.3M10 5c4 0 7 5 7 5s-.7 1.3-2 2.6"
                  />
                </svg>
              </button>
            </div>

            <div class="perfil-strength-bar mt-2">
              <div
                v-for="n in 4"
                :key="n"
                class="perfil-strength-seg"
                :class="strengthClass(n)"
              ></div>
            </div>

            <p v-if="pwdErrors.nueva" class="perfil-field-error">
              {{ pwdErrors.nueva }}
            </p>
          </div>

          <div class="space-y-1">
            <label class="perfil-field-label">Confirmar nueva contraseña</label>

            <div class="relative">
              <svg
                class="perfil-input-icon"
                viewBox="0 0 20 20"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <path stroke-linecap="round" d="M5 10l4 4 7-7" />
              </svg>

              <input
                v-model="pwdForm.confirmar"
                :type="showPwd.confirmar ? 'text' : 'password'"
                class="input w-full pl-9 pr-9"
                placeholder="Repite la nueva contraseña"
                :class="{ 'perfil-input-error': pwdErrors.confirmar }"
              />

              <button
                type="button"
                class="perfil-eye-btn"
                @click="showPwd.confirmar = !showPwd.confirmar"
              >
                <svg
                  viewBox="0 0 20 20"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.5"
                  class="w-4 h-4"
                >
                  <path
                    v-if="!showPwd.confirmar"
                    stroke-linecap="round"
                    d="M2 10s3-5 8-5 8 5 8 5-3 5-8 5-8-5-8-5z"
                  />

                  <circle v-if="!showPwd.confirmar" cx="10" cy="10" r="2" />

                  <path
                    v-if="showPwd.confirmar"
                    stroke-linecap="round"
                    d="M3 3l14 14M8.5 8.6A2 2 0 0011.4 11.5M6.3 6.4C4.5 7.4 3 10 3 10s3 5 7 5c1.4 0 2.7-.5 3.7-1.3M10 5c4 0 7 5 7 5s-.7 1.3-2 2.6"
                  />
                </svg>
              </button>
            </div>

            <p v-if="pwdErrors.confirmar" class="perfil-field-error">
              {{ pwdErrors.confirmar }}
            </p>
          </div>

          <Transition name="error-slide">
            <div
              v-if="pwdSuccess"
              class="perfil-success-box flex items-center gap-2.5 p-3.5 rounded-xl"
            >
              <svg
                class="w-4 h-4 text-green-600 dark:text-green-400 shrink-0"
                viewBox="0 0 16 16"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path stroke-linecap="round" d="M2 8l5 5 7-7" />
              </svg>

              <span class="text-sm text-green-600 dark:text-green-400">
                Contraseña actualizada correctamente
              </span>
            </div>
          </Transition>

          <Transition name="error-slide">
            <div
              v-if="pwdError"
              class="perfil-error-box flex items-start gap-2.5 p-3.5 rounded-xl"
            >
              <svg
                class="w-4 h-4 mt-0.5 shrink-0 text-red-500 dark:text-red-400"
                viewBox="0 0 16 16"
                fill="currentColor"
              >
                <path d="M8 0a8 8 0 100 16A8 8 0 008 0zm0 12a1 1 0 110-2 1 1 0 010 2zm1-4H7V4h2v4z" />
              </svg>

              <span class="text-sm text-red-500 dark:text-red-400">
                {{ pwdError }}
              </span>
            </div>
          </Transition>

          <div class="flex justify-end">
            <button
              @click="changePassword"
              :disabled="savingPwd"
              class="perfil-btn-primary-sm"
            >
              <span v-if="savingPwd" class="perfil-spinner-sm"></span>

              <svg
                v-else
                class="w-4 h-4"
                viewBox="0 0 20 20"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <rect x="4" y="8.5" width="12" height="8" rx="1.5" />
                <path stroke-linecap="round" d="M7 8.5V6a3 3 0 016 0v2.5" />
              </svg>

              {{ savingPwd ? 'Actualizando...' : 'Cambiar contraseña' }}
            </button>
          </div>
        </div>
      </Transition>

      <!-- TAB: Sesión / Peligro -->
      <Transition name="tab-fade" mode="out-in">
        <div v-if="activeTab === 'sesion'" key="ses" class="space-y-4">
          <div class="perfil-card p-6">
            <div class="perfil-section-header mb-5">
              <svg
                class="w-4 h-4 text-brand-700 dark:text-brand-300"
                viewBox="0 0 20 20"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <path stroke-linecap="round" d="M3 10h14M7 5l-4 5 4 5" />
              </svg>

              <span>Sesión activa</span>
            </div>

            <div class="perfil-session-info mb-5">
              <div class="perfil-session-row">
                <span class="text-surface-muted dark:text-surface-mutedDark text-sm">Usuario</span>
                <span class="text-surface-text dark:text-surface-textDark text-sm text-right">{{ docente.email }}</span>
              </div>

              <div class="perfil-session-row">
                <span class="text-surface-muted dark:text-surface-mutedDark text-sm">Cuenta desde</span>
                <span class="text-surface-text dark:text-surface-textDark text-sm text-right">{{ formattedDate }}</span>
              </div>

              <div class="perfil-session-row">
                <span class="text-surface-muted dark:text-surface-mutedDark text-sm">Exámenes calificados</span>
                <span class="text-surface-text dark:text-surface-textDark text-sm text-right">{{ docente.total_examenes || '—' }}</span>
              </div>
            </div>

            <button @click="logout" class="perfil-btn-logout w-full">
              <svg
                class="w-4 h-4"
                viewBox="0 0 20 20"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <path stroke-linecap="round" d="M13 10H3m4-4l-4 4 4 4M10 3h5a1 1 0 011 1v12a1 1 0 01-1 1h-5" />
              </svg>

              Cerrar sesión
            </button>
          </div>

          <div class="perfil-danger-card p-6">
            <div class="perfil-section-header mb-4">
              <svg
                class="w-4 h-4 text-red-500 dark:text-red-400"
                viewBox="0 0 20 20"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <path stroke-linecap="round" d="M10 4v7M10 14v.5" />
                <path stroke-linecap="round" d="M3 17L10 3l7 14H3z" />
              </svg>

              <span class="text-red-500 dark:text-red-400">Zona peligrosa</span>
            </div>

            <p class="text-surface-muted dark:text-surface-mutedDark text-sm mb-5">
              Eliminar tu cuenta es irreversible. Se eliminarán todos tus cursos,
              exámenes y calificaciones permanentemente.
            </p>

            <button
              @click="confirmDelete = !confirmDelete"
              class="perfil-btn-danger-outline"
            >
              <svg
                class="w-4 h-4"
                viewBox="0 0 20 20"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <path stroke-linecap="round" d="M6 4V3a1 1 0 011-1h6a1 1 0 011 1v1M4 4h12l-1 14H5L4 4zM8 8v6M12 8v6" />
              </svg>

              Eliminar mi cuenta
            </button>

            <Transition name="error-slide">
              <div
                v-if="confirmDelete"
                class="mt-4 p-4 rounded-xl border border-red-500/20 bg-red-500/5 space-y-3"
              >
                <p class="text-red-500 dark:text-red-400 text-sm font-medium">
                  ¿Confirmas que deseas eliminar tu cuenta?
                </p>

                <p class="text-surface-muted dark:text-surface-mutedDark text-xs">
                  Escribe tu correo para confirmar:
                  <strong class="text-surface-text dark:text-surface-textDark">
                    {{ docente.email }}
                  </strong>
                </p>

                <input
                  v-model="deleteConfirmEmail"
                  type="email"
                  class="input w-full"
                  placeholder="Tu correo"
                />

                <div class="flex gap-2">
                  <button
                    @click="confirmDelete = false"
                    class="perfil-btn-cancel-sm flex-1"
                  >
                    Cancelar
                  </button>

                  <button
                    @click="deleteAccount"
                    :disabled="deleteConfirmEmail !== docente.email || deletingAccount"
                    class="perfil-btn-danger-sm flex-1"
                  >
                    <span v-if="deletingAccount" class="perfil-spinner-sm"></span>
                    <span v-else>Eliminar definitivamente</span>
                  </button>
                </div>
              </div>
            </Transition>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  getPerfilDocente,
  updatePerfil,
  cambiarPassword,
  eliminarCuenta,
} from '@/composables/useApi'

const router = useRouter()

const pageLoading = ref(true)
const activeTab = ref('info')

const docente = reactive({
  nombre: '',
  email: '',
  institucion: '',
  nivel_exigencia: 5,
  activo: true,
  created_at: null,
  total_examenes: 0,
})

const tabs = [
  {
    id: 'info',
    label: 'Información',
    icon: '<circle cx="10" cy="7" r="3"/><path stroke-linecap="round" d="M3 18c0-3.3 3.1-6 7-6s7 2.7 7 6"/>',
  },
  {
    id: 'seguridad',
    label: 'Contraseña',
    icon: '<rect x="4" y="8.5" width="12" height="8" rx="1.5"/><path stroke-linecap="round" d="M7 8.5V6a3 3 0 016 0v2.5"/>',
  },
  {
    id: 'sesion',
    label: 'Sesión',
    icon: '<path stroke-linecap="round" d="M3 10h14M7 5l-4 5 4 5"/>',
  },
]

// Info form
const infoForm = reactive({
  nombre: '',
  email: '',
  institucion: '',
  nivel_exigencia: 5,
})

const infoErrors = reactive({
  nombre: '',
  email: '',
})

const infoError = ref('')
const infoSuccess = ref(false)
const savingInfo = ref(false)

// Password form
const pwdForm = reactive({
  actual: '',
  nueva: '',
  confirmar: '',
})

const pwdErrors = reactive({
  actual: '',
  nueva: '',
  confirmar: '',
})

const pwdError = ref('')
const pwdSuccess = ref(false)
const savingPwd = ref(false)

const showPwd = reactive({
  actual: false,
  nueva: false,
  confirmar: false,
})

// Delete
const confirmDelete = ref(false)
const deleteConfirmEmail = ref('')
const deletingAccount = ref(false)

const avatarLetters = computed(() => {
  const parts = docente.nombre.trim().split(' ')
  const a = parts[0]?.charAt(0) || ''
  const b = parts[1]?.charAt(0) || ''

  return (a + b).toUpperCase()
})

const formattedDate = computed(() => {
  if (!docente.created_at) return '—'

  return new Date(docente.created_at).toLocaleDateString('es-GT', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
})

function nivelDesc(n) {
  if (n <= 2) return 'Muy flexible — acepta respuestas aproximadas'
  if (n <= 4) return 'Flexible — tolera pequeños errores'
  if (n <= 6) return 'Estándar — equilibrado y justo'
  if (n <= 8) return 'Exigente — requiere precisión'

  return 'Muy estricto — solo respuestas exactas'
}

const passwordStrength = computed(() => {
  const p = pwdForm.nueva

  if (!p) return 0

  let s = 0

  if (p.length >= 8) s++
  if (/[A-Z]/.test(p)) s++
  if (/[0-9]/.test(p)) s++
  if (/[^A-Za-z0-9]/.test(p)) s++

  return s
})

function strengthClass(n) {
  const s = passwordStrength.value

  if (s === 0) return 'perfil-seg-empty'

  const c = [
    '',
    'perfil-seg-weak',
    'perfil-seg-fair',
    'perfil-seg-good',
    'perfil-seg-strong',
  ]

  return n <= s ? c[s] : 'perfil-seg-empty'
}

onMounted(async () => {
  try {
    const data = await getPerfilDocente()

    Object.assign(docente, data)

    Object.assign(infoForm, {
      nombre: data.nombre,
      email: data.email,
      institucion: data.institucion || '',
      nivel_exigencia: data.nivel_exigencia,
    })
  } catch (e) {
    const nombre = localStorage.getItem('docente_nombre') || ''

    docente.nombre = nombre
    infoForm.nombre = nombre
  } finally {
    pageLoading.value = false
  }
})

async function saveInfo() {
  infoErrors.nombre = ''
  infoErrors.email = ''
  infoError.value = ''
  infoSuccess.value = false

  if (!infoForm.nombre.trim()) {
    infoErrors.nombre = 'El nombre es obligatorio'
    return
  }

  if (!infoForm.email) {
    infoErrors.email = 'El correo es obligatorio'
    return
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(infoForm.email)) {
    infoErrors.email = 'Correo inválido'
    return
  }

  savingInfo.value = true

  try {
    await updatePerfil({
      nombre: infoForm.nombre.trim(),
      email: infoForm.email,
      institucion: infoForm.institucion.trim() || null,
      nivel_exigencia: infoForm.nivel_exigencia,
    })

    Object.assign(docente, infoForm)
    localStorage.setItem('docente_nombre', infoForm.nombre.trim())

    infoSuccess.value = true

    setTimeout(() => {
      infoSuccess.value = false
    }, 4000)
  } catch (e) {
    infoError.value = e.message || 'Error al guardar los cambios'
  } finally {
    savingInfo.value = false
  }
}

async function changePassword() {
  pwdErrors.actual = ''
  pwdErrors.nueva = ''
  pwdErrors.confirmar = ''
  pwdError.value = ''
  pwdSuccess.value = false

  if (!pwdForm.actual) {
    pwdErrors.actual = 'Ingresa tu contraseña actual'
    return
  }

  if (!pwdForm.nueva) {
    pwdErrors.nueva = 'Ingresa la nueva contraseña'
    return
  }

  if (pwdForm.nueva.length < 8) {
    pwdErrors.nueva = 'Mínimo 8 caracteres'
    return
  }

  if (pwdForm.nueva === pwdForm.actual) {
    pwdErrors.nueva = 'La nueva contraseña debe ser diferente'
    return
  }

  if (!pwdForm.confirmar) {
    pwdErrors.confirmar = 'Confirma la nueva contraseña'
    return
  }

  if (pwdForm.nueva !== pwdForm.confirmar) {
    pwdErrors.confirmar = 'Las contraseñas no coinciden'
    return
  }

  savingPwd.value = true

  try {
    await cambiarPassword({
      actual: pwdForm.actual,
      nueva: pwdForm.nueva,
    })

    pwdSuccess.value = true

    pwdForm.actual = ''
    pwdForm.nueva = ''
    pwdForm.confirmar = ''

    setTimeout(() => {
      pwdSuccess.value = false
    }, 4000)
  } catch (e) {
    pwdError.value = e.message || 'Error al cambiar la contraseña'
  } finally {
    savingPwd.value = false
  }
}

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('docente_id')
  localStorage.removeItem('docente_nombre')

  router.push({ name: 'login' })
}

async function deleteAccount() {
  if (deleteConfirmEmail.value !== docente.email) return

  deletingAccount.value = true

  try {
    await eliminarCuenta()
    logout()
  } catch (e) {
    deletingAccount.value = false
  }
}
</script>