<template>
  <div class="registro-auth-page min-h-screen flex items-center justify-center px-4 py-10 animate-fade-in">
    <div class="w-full max-w-md">

      <!-- Logo + volver -->
      <div class="flex items-center justify-between mb-8">
        <button
          type="button"
          @click="$router.push({ name: 'login' })"
          class="registro-back-btn"
        >
          <svg
            class="w-4 h-4"
            viewBox="0 0 20 20"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path stroke-linecap="round" d="M12 5l-5 5 5 5" />
          </svg>

          Volver al login
        </button>

        <div class="inline-flex items-center gap-2">
          <div
            class="
              w-10 h-10
              rounded-xl
              bg-brand-300
              border border-brand-400/70
              flex items-center justify-center
              overflow-hidden
              shadow-lg shadow-brand-300/30
            "
          >
            <img
              src="/logo.png"
              alt="Logo DeepGrader AI"
              class="w-full h-full object-cover"
            />
          </div>

          <span class="font-display text-lg font-bold text-surface-text dark:text-surface-textDark">
            DeepGrader <span class="text-brand-700 dark:text-brand-300">AI</span>
          </span>
        </div>
      </div>

      <!-- Card -->
      <div class="card registro-card p-8">
        <div class="mb-7">
          <h1 class="text-surface-text dark:text-surface-textDark text-2xl font-bold tracking-tight">
            Crear cuenta
          </h1>

          <p class="text-surface-muted dark:text-surface-mutedDark text-sm mt-1">
            Completa tus datos para comenzar a calificar con IA
          </p>
        </div>

        <!-- Pasos -->
        <div class="registro-progress-steps mb-8">
          <div
            v-for="(step, i) in steps"
            :key="i"
            class="registro-step-item"
          >
            <div
              class="registro-step-dot"
              :class="{
                'registro-step-done': currentStep > i,
                'registro-step-active': currentStep === i,
                'registro-step-pending': currentStep < i
              }"
            >
              <svg
                v-if="currentStep > i"
                class="w-3 h-3"
                viewBox="0 0 12 12"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path stroke-linecap="round" d="M2 6l3 3 5-5" />
              </svg>

              <span v-else class="text-xs font-bold">
                {{ i + 1 }}
              </span>
            </div>

            <span
              class="registro-step-label"
              :class="{
                'registro-step-label-active': currentStep >= i,
                'registro-step-label-pending': currentStep < i
              }"
            >
              {{ step }}
            </span>

            <div
              v-if="i < steps.length - 1"
              class="registro-step-line"
              :class="{ 'registro-step-line-done': currentStep > i }"
            ></div>
          </div>
        </div>

        <!-- PASO 0 -->
        <Transition name="slide-step" mode="out-in">
          <div
            v-if="currentStep === 0"
            key="step0"
            class="space-y-4"
          >
            <!-- Nombre -->
            <div class="space-y-1">
              <label class="registro-field-label">
                Nombre completo <span class="text-brand-700 dark:text-brand-300">*</span>
              </label>

              <div class="registro-input-wrapper">
                <svg
                  class="registro-input-icon"
                  viewBox="0 0 20 20"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.5"
                >
                  <circle cx="10" cy="7" r="3" />
                  <path
                    stroke-linecap="round"
                    d="M3 18c0-3.3 3.1-6 7-6s7 2.7 7 6"
                  />
                </svg>

                <input
                  v-model="form.nombre"
                  type="text"
                  class="input pl-9"
                  placeholder="Ej: María García López"
                  :class="{ 'registro-input-error': errors.nombre }"
                />
              </div>

              <p v-if="errors.nombre" class="registro-field-error">
                {{ errors.nombre }}
              </p>
            </div>

            <!-- Institución -->
            <div class="space-y-1">
              <label class="registro-field-label">
                Institución educativa
              </label>

              <div class="registro-input-wrapper">
                <svg
                  class="registro-input-icon"
                  viewBox="0 0 20 20"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.5"
                >
                  <path
                    stroke-linecap="round"
                    d="M10 3L2 8h2v8h4v-4h4v4h4V8h2L10 3z"
                  />
                </svg>

                <input
                  v-model="form.institucion"
                  type="text"
                  class="input pl-9"
                  placeholder="Ej: Universidad del Valle"
                />
              </div>
            </div>

            <!-- Correo -->
            <div class="space-y-1">
              <label class="registro-field-label">
                Correo electrónico <span class="text-brand-700 dark:text-brand-300">*</span>
              </label>

              <div class="registro-input-wrapper">
                <svg
                  class="registro-input-icon"
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
                  v-model="form.email"
                  type="email"
                  class="input pl-9"
                  placeholder="docente@universidad.edu"
                  :class="{ 'registro-input-error': errors.email }"
                />
              </div>

              <p v-if="errors.email" class="registro-field-error">
                {{ errors.email }}
              </p>
            </div>

            <!-- Nivel de exigencia -->
            <div class="space-y-1">
              <label class="registro-field-label">
                Nivel de exigencia por defecto

                <span class="registro-nivel-badge">
                  {{ form.nivel_exigencia }}/10
                </span>
              </label>

              <div class="flex items-center gap-4">
                <span class="text-xs text-surface-muted dark:text-surface-mutedDark">
                  Flexible
                </span>

                <input
                  v-model.number="form.nivel_exigencia"
                  type="range"
                  min="1"
                  max="10"
                  class="flex-1 registro-range"
                />

                <span class="text-xs text-surface-muted dark:text-surface-mutedDark">
                  Estricto
                </span>
              </div>

              <p class="text-xs text-surface-muted dark:text-surface-mutedDark mt-1">
                {{ nivelDescripcion }}
              </p>
            </div>
          </div>
        </Transition>

        <!-- PASO 1 -->
        <Transition name="slide-step" mode="out-in">
          <div
            v-if="currentStep === 1"
            key="step1"
            class="space-y-4"
          >
            <!-- Contraseña -->
            <div class="space-y-1">
              <label class="registro-field-label">
                Contraseña <span class="text-brand-700 dark:text-brand-300">*</span>
              </label>

              <div class="registro-input-wrapper">
                <svg
                  class="registro-input-icon"
                  viewBox="0 0 20 20"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.5"
                >
                  <rect x="4" y="8.5" width="12" height="8" rx="1.5" />
                  <path
                    stroke-linecap="round"
                    d="M7 8.5V6a3 3 0 016 0v2.5"
                  />
                </svg>

                <input
                  v-model="form.password"
                  :type="showPwd ? 'text' : 'password'"
                  class="input pl-9 pr-9"
                  placeholder="Mínimo 8 caracteres"
                  :class="{ 'registro-input-error': errors.password }"
                />

                <button
                  type="button"
                  class="registro-eye-btn"
                  @click="showPwd = !showPwd"
                >
                  <svg
                    viewBox="0 0 20 20"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.5"
                    class="w-4 h-4"
                  >
                    <path
                      v-if="!showPwd"
                      stroke-linecap="round"
                      d="M2 10s3-5 8-5 8 5 8 5-3 5-8 5-8-5-8-5z"
                    />
                    <circle
                      v-if="!showPwd"
                      cx="10"
                      cy="10"
                      r="2"
                    />
                    <path
                      v-if="showPwd"
                      stroke-linecap="round"
                      d="M3 3l14 14M8.5 8.6A2 2 0 0011.4 11.5M6.3 6.4C4.5 7.4 3 10 3 10s3 5 7 5c1.4 0 2.7-.5 3.7-1.3M10 5c4 0 7 5 7 5s-.7 1.3-2 2.6"
                    />
                  </svg>
                </button>
              </div>

              <div class="registro-strength-bar mt-2">
                <div
                  v-for="n in 4"
                  :key="n"
                  class="registro-strength-seg"
                  :class="strengthClass(n)"
                ></div>
              </div>

              <p class="text-xs mt-1" :class="strengthColor">
                {{ strengthLabel }}
              </p>

              <p v-if="errors.password" class="registro-field-error">
                {{ errors.password }}
              </p>
            </div>

            <!-- Confirmar contraseña -->
            <div class="space-y-1">
              <label class="registro-field-label">
                Confirmar contraseña <span class="text-brand-700 dark:text-brand-300">*</span>
              </label>

              <div class="registro-input-wrapper">
                <svg
                  class="registro-input-icon"
                  viewBox="0 0 20 20"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.5"
                >
                  <path stroke-linecap="round" d="M5 10l4 4 7-7" />
                </svg>

                <input
                  v-model="form.confirm"
                  :type="showConfirm ? 'text' : 'password'"
                  class="input pl-9 pr-9"
                  placeholder="Repite la contraseña"
                  :class="{ 'registro-input-error': errors.confirm }"
                />

                <button
                  type="button"
                  class="registro-eye-btn"
                  @click="showConfirm = !showConfirm"
                >
                  <svg
                    viewBox="0 0 20 20"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.5"
                    class="w-4 h-4"
                  >
                    <path
                      v-if="!showConfirm"
                      stroke-linecap="round"
                      d="M2 10s3-5 8-5 8 5 8 5-3 5-8 5-8-5-8-5z"
                    />
                    <circle
                      v-if="!showConfirm"
                      cx="10"
                      cy="10"
                      r="2"
                    />
                    <path
                      v-if="showConfirm"
                      stroke-linecap="round"
                      d="M3 3l14 14M8.5 8.6A2 2 0 0011.4 11.5M6.3 6.4C4.5 7.4 3 10 3 10s3 5 7 5c1.4 0 2.7-.5 3.7-1.3M10 5c4 0 7 5 7 5s-.7 1.3-2 2.6"
                    />
                  </svg>
                </button>
              </div>

              <p v-if="errors.confirm" class="registro-field-error">
                {{ errors.confirm }}
              </p>

              <div
                v-if="form.confirm && form.password === form.confirm"
                class="flex items-center gap-1.5 mt-1"
              >
                <svg
                  class="w-3.5 h-3.5 text-brand-700 dark:text-brand-300"
                  viewBox="0 0 14 14"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path stroke-linecap="round" d="M2 7l4 4 6-6" />
                </svg>

                <span class="text-xs text-brand-700 dark:text-brand-300">
                  Las contraseñas coinciden
                </span>
              </div>
            </div>
          </div>
        </Transition>

        <!-- PASO 2 -->
        <Transition name="slide-step" mode="out-in">
          <div
            v-if="currentStep === 2"
            key="step2"
          >
            <div class="registro-confirm-card mb-5">
              <div class="flex items-center gap-3 mb-4">
                <div class="registro-avatar-circle">
                  {{ form.nombre.charAt(0).toUpperCase() }}{{ form.nombre.split(' ')[1]?.charAt(0).toUpperCase() || '' }}
                </div>

                <div>
                  <p class="text-surface-text dark:text-surface-textDark font-semibold text-base">
                    {{ form.nombre }}
                  </p>

                  <p class="text-surface-muted dark:text-surface-mutedDark text-sm">
                    {{ form.email }}
                  </p>
                </div>
              </div>

              <div class="registro-confirm-rows">
                <div class="registro-confirm-row">
                  <span class="text-surface-muted dark:text-surface-mutedDark text-sm">
                    Institución
                  </span>

                  <span class="text-surface-text dark:text-surface-textDark text-sm text-right">
                    {{ form.institucion || 'No especificada' }}
                  </span>
                </div>

                <div class="registro-confirm-row">
                  <span class="text-surface-muted dark:text-surface-mutedDark text-sm">
                    Nivel de exigencia
                  </span>

                  <span class="text-surface-text dark:text-surface-textDark text-sm text-right">
                    {{ form.nivel_exigencia }}/10 — {{ nivelDescripcion }}
                  </span>
                </div>
              </div>
            </div>

            <div class="flex items-start gap-2.5 mb-4">
              <button
                type="button"
                @click="acceptTerms = !acceptTerms"
                class="registro-checkbox-btn mt-0.5"
                :class="{ checked: acceptTerms }"
              >
                <svg
                  v-if="acceptTerms"
                  class="w-3 h-3"
                  viewBox="0 0 12 12"
                  fill="none"
                  stroke="#161719"
                  stroke-width="2"
                >
                  <path stroke-linecap="round" d="M2 6l3 3 5-5" />
                </svg>
              </button>

              <label
                class="text-xs text-surface-muted dark:text-surface-mutedDark leading-relaxed cursor-pointer"
                @click="acceptTerms = !acceptTerms"
              >
                Acepto los
                <a href="#" class="text-brand-700 dark:text-brand-300 hover:underline">términos de uso</a>
                y la
                <a href="#" class="text-brand-700 dark:text-brand-300 hover:underline">política de privacidad</a>
                de DeepGrader AI. Los datos de exámenes se procesan de forma confidencial.
              </label>
            </div>

            <p v-if="errors.terms" class="registro-field-error mb-3">
              {{ errors.terms }}
            </p>
          </div>
        </Transition>

        <!-- Error global -->
        <Transition name="error-slide">
          <div
            v-if="globalError"
            class="registro-error-box flex items-start gap-2.5 p-3.5 rounded-xl mt-4"
          >
            <svg
              class="w-4 h-4 mt-0.5 shrink-0 text-red-500 dark:text-red-400"
              viewBox="0 0 16 16"
              fill="currentColor"
            >
              <path d="M8 0a8 8 0 100 16A8 8 0 008 0zm0 12a1 1 0 110-2 1 1 0 010 2zm1-4H7V4h2v4z" />
            </svg>

            <span class="text-sm text-red-500 dark:text-red-400">
              {{ globalError }}
            </span>
          </div>
        </Transition>

        <!-- Acciones -->
        <div class="flex gap-3 mt-7">
          <button
            v-if="currentStep > 0"
            type="button"
            @click="prevStep"
            class="registro-btn-back-step"
          >
            <svg
              class="w-4 h-4"
              viewBox="0 0 20 20"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path stroke-linecap="round" d="M12 5l-5 5 5 5" />
            </svg>

            Atrás
          </button>

          <button
            type="button"
            @click="nextOrSubmit"
            :disabled="loading"
            class="btn-primary flex-1"
          >
            <span
              v-if="loading"
              class="spinner w-4 h-4"
            ></span>

            <template v-else>
              <svg
                v-if="currentStep < 2"
                class="w-4 h-4"
                viewBox="0 0 20 20"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path stroke-linecap="round" d="M8 5l5 5-5 5" />
              </svg>

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
            </template>

            {{ loading ? 'Creando cuenta...' : currentStep < 2 ? 'Continuar' : 'Crear mi cuenta' }}
          </button>
        </div>
      </div>

      <p class="text-center text-xs text-surface-muted dark:text-surface-mutedDark mt-6">
        ¿Ya tienes cuenta?

        <button
          type="button"
          @click="$router.push({ name: 'login' })"
          class="text-surface-text hover:text-brand-700 dark:text-surface-textDark dark:hover:text-brand-300 transition-colors ml-1"
        >
          Iniciar sesión →
        </button>
      </p>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { registrarDocente } from '@/composables/useApi'

const router = useRouter()

const loading = ref(false)
const globalError = ref('')
const currentStep = ref(0)
const showPwd = ref(false)
const showConfirm = ref(false)
const acceptTerms = ref(false)

const steps = ['Datos personales', 'Contraseña', 'Confirmar']

const form = reactive({
  nombre: '',
  email: '',
  institucion: '',
  nivel_exigencia: 5,
  password: '',
  confirm: '',
})

const errors = reactive({
  nombre: '',
  email: '',
  password: '',
  confirm: '',
  terms: '',
})

const nivelDescripcion = computed(() => {
  const n = form.nivel_exigencia

  if (n <= 2) return 'Muy flexible, acepta respuestas aproximadas'
  if (n <= 4) return 'Flexible, tolera pequeños errores'
  if (n <= 6) return 'Estándar, equilibrado y justo'
  if (n <= 8) return 'Exigente, requiere precisión'

  return 'Muy estricto, solo respuestas exactas'
})

const passwordStrength = computed(() => {
  const p = form.password

  if (!p) return 0

  let s = 0

  if (p.length >= 8) s++
  if (/[A-Z]/.test(p)) s++
  if (/[0-9]/.test(p)) s++
  if (/[^A-Za-z0-9]/.test(p)) s++

  return s
})

const strengthLabel = computed(() => {
  const labels = ['', 'Débil', 'Regular', 'Buena', 'Fuerte']
  return labels[passwordStrength.value] || ''
})

const strengthColor = computed(() => {
  const colors = [
    '',
    'text-red-500 dark:text-red-400',
    'text-yellow-600 dark:text-yellow-400',
    'text-brand-700 dark:text-brand-300',
    'text-brand-700 dark:text-brand-300',
  ]

  return colors[passwordStrength.value] || 'text-surface-muted dark:text-surface-mutedDark'
})

function strengthClass(n) {
  const s = passwordStrength.value

  if (s === 0) return 'registro-seg-empty'

  const colors = [
    '',
    'registro-seg-weak',
    'registro-seg-fair',
    'registro-seg-good',
    'registro-seg-strong',
  ]

  return n <= s ? colors[s] : 'registro-seg-empty'
}

function clearErrors() {
  Object.keys(errors).forEach((key) => {
    errors[key] = ''
  })

  globalError.value = ''
}

function validateStep0() {
  clearErrors()

  let ok = true

  if (!form.nombre.trim()) {
    errors.nombre = 'El nombre es obligatorio'
    ok = false
  }

  if (!form.email) {
    errors.email = 'El correo es obligatorio'
    ok = false
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    errors.email = 'Formato de correo inválido'
    ok = false
  }

  return ok
}

function validateStep1() {
  clearErrors()

  let ok = true

  if (!form.password) {
    errors.password = 'La contraseña es obligatoria'
    ok = false
  } else if (form.password.length < 8) {
    errors.password = 'Mínimo 8 caracteres'
    ok = false
  }

  if (!form.confirm) {
    errors.confirm = 'Confirma tu contraseña'
    ok = false
  } else if (form.password !== form.confirm) {
    errors.confirm = 'Las contraseñas no coinciden'
    ok = false
  }

  return ok
}

function validateStep2() {
  clearErrors()

  if (!acceptTerms.value) {
    errors.terms = 'Debes aceptar los términos para continuar'
    return false
  }

  return true
}

function prevStep() {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

async function nextOrSubmit() {
  if (currentStep.value === 0 && !validateStep0()) return
  if (currentStep.value === 1 && !validateStep1()) return

  if (currentStep.value < 2) {
    currentStep.value++
    return
  }

  if (!validateStep2()) return

  loading.value = true
  globalError.value = ''

  try {
    const data = await registrarDocente({
      nombre: form.nombre.trim(),
      email: form.email,
      password: form.password,
      institucion: form.institucion.trim() || null,
      nivel_exigencia: form.nivel_exigencia,
    })

    localStorage.setItem('token', data.token)
    localStorage.setItem('docente_id', data.docente_id)
    localStorage.setItem('docente_nombre', data.nombre || form.nombre)

    router.push({ name: 'cursos' })
  } catch (e) {
    globalError.value = e.message || 'Error al crear la cuenta. Intenta de nuevo.'
    currentStep.value = 0
  } finally {
    loading.value = false
  }
}
</script>