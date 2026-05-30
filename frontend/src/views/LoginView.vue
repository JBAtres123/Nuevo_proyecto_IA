<template>
  <div class="min-h-screen flex items-center justify-center px-4 py-10 animate-fade-in">
    <div class="w-full max-w-sm">

      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center gap-3 mb-4">
          <div
            class="
              w-14 h-14
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

          <span class="font-display text-3xl font-bold text-surface-text dark:text-surface-textDark">
            DeepGrader <span class="text-brand-700 dark:text-brand-300">AI</span>
          </span>
        </div>

        <p class="text-surface-muted dark:text-surface-mutedDark text-sm">
          Acceso docente
        </p>
      </div>

      <!-- Card -->
      <div class="card p-8 space-y-5">

        <!-- Correo -->
        <div>
          <label class="text-xs text-surface-muted dark:text-surface-mutedDark mb-1.5 block">
            Correo electrónico
          </label>

          <div class="relative">
            <svg
              class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-surface-muted dark:text-surface-mutedDark"
              viewBox="0 0 20 20"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M2.5 6.5l7.5 5 7.5-5"
              />
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M3 5h14a.5.5 0 01.5.5v9a.5.5 0 01-.5.5H3a.5.5 0 01-.5-.5v-9A.5.5 0 013 5z"
              />
            </svg>

            <input
              v-model="form.email"
              type="email"
              class="input w-full pl-10"
              placeholder="docente@universidad.edu"
              @keyup.enter="login"
            />
          </div>

          <p
            v-if="fieldErrors.email"
            class="text-xs text-red-500 dark:text-red-400 mt-1.5 flex items-center gap-1"
          >
            <svg
              class="w-3 h-3"
              viewBox="0 0 12 12"
              fill="currentColor"
            >
              <circle cx="6" cy="6" r="6" />
            </svg>

            {{ fieldErrors.email }}
          </p>
        </div>

        <!-- Contraseña -->
        <div>
          <label class="text-xs text-surface-muted dark:text-surface-mutedDark mb-1.5 block">
            Contraseña
          </label>

          <div class="relative">
            <svg
              class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-surface-muted dark:text-surface-mutedDark"
              viewBox="0 0 20 20"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
            >
              <rect
                x="4"
                y="8.5"
                width="12"
                height="8"
                rx="1.5"
              />
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M7 8.5V6a3 3 0 016 0v2.5"
              />
            </svg>

            <input
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              class="input w-full pl-10 pr-10"
              placeholder="••••••••"
              @keyup.enter="login"
            />

            <button
              type="button"
              class="
                absolute right-3 top-1/2 -translate-y-1/2
                text-surface-muted dark:text-surface-mutedDark
                hover:text-brand-700 dark:hover:text-brand-300
                transition-colors duration-150
              "
              @click="showPassword = !showPassword"
              :aria-label="showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'"
            >
              <svg
                v-if="!showPassword"
                class="w-4 h-4"
                viewBox="0 0 20 20"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M2 10s3-5 8-5 8 5 8 5-3 5-8 5-8-5-8-5z"
                />
                <circle cx="10" cy="10" r="2" />
              </svg>

              <svg
                v-else
                class="w-4 h-4"
                viewBox="0 0 20 20"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M3 3l14 14"
                />
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M8.5 8.6A2 2 0 0011.4 11.5"
                />
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M6.3 6.4C4.5 7.4 3 10 3 10s3 5 7 5c1.4 0 2.7-.5 3.7-1.3"
                />
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M10 5c4 0 7 5 7 5s-.7 1.3-2 2.6"
                />
              </svg>
            </button>
          </div>

          <p
            v-if="fieldErrors.password"
            class="text-xs text-red-500 dark:text-red-400 mt-1.5 flex items-center gap-1"
          >
            <svg
              class="w-3 h-3"
              viewBox="0 0 12 12"
              fill="currentColor"
            >
              <circle cx="6" cy="6" r="6" />
            </svg>

            {{ fieldErrors.password }}
          </p>
        </div>

        <!-- Error global -->
        <Transition name="error-slide">
          <div
            v-if="error"
            class="
              p-3 rounded-xl
              border border-red-500/20
              bg-red-500/5
              text-sm text-red-500 dark:text-red-400
              flex items-start gap-2
            "
          >
            <svg
              class="w-4 h-4 mt-0.5 shrink-0 text-red-500 dark:text-red-400"
              viewBox="0 0 16 16"
              fill="currentColor"
            >
              <path
                d="M8 0a8 8 0 100 16A8 8 0 008 0zm0 12a1 1 0 110-2 1 1 0 010 2zm1-4H7V4h2v4z"
              />
            </svg>

            <span>{{ error }}</span>
          </div>
        </Transition>

        <!-- Botón ingresar -->
        <button
          @click="login"
          :disabled="loading"
          class="btn-primary w-full justify-center text-sm py-2.5"
        >
          <span v-if="loading" class="spinner w-4 h-4"></span>

          <svg
            v-else
            class="w-4 h-4"
            viewBox="0 0 20 20"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M3 10h14"
            />
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M12 5l5 5-5 5"
            />
          </svg>

          {{ loading ? 'Verificando...' : 'Ingresar' }}
        </button>

        <!-- Crear cuenta -->
        <button
          type="button"
          @click="router.push({ name: 'registro' })"
          class="
            w-full flex items-center justify-center gap-2
            text-sm py-2.5 rounded-lg
            border border-surface-border dark:border-surface-borderDark
            bg-surface-tag dark:bg-surface-tagDark
            text-surface-muted dark:text-surface-mutedDark
            hover:text-brand-700 dark:hover:text-brand-300
            hover:border-brand-500/40 dark:hover:border-brand-300/40
            hover:bg-brand-300/10
            transition-all duration-150
          "
        >
          <svg
            class="w-4 h-4"
            viewBox="0 0 20 20"
            fill="none"
            stroke="currentColor"
            stroke-width="1.5"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M10 3v14"
            />
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M3 10h14"
            />
          </svg>

          Crear una cuenta
        </button>
      </div>

      <p class="text-center text-xs text-surface-muted dark:text-surface-mutedDark mt-6">
        Sistema Inteligente de Calificación · DeepGrader AI
      </p>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { loginDocente } from '@/composables/useApi'

const router = useRouter()

// Limpiar sesión residual al entrar al login
onMounted(() => {
  localStorage.removeItem('token')
  localStorage.removeItem('docente_id')
  localStorage.removeItem('docente_nombre')
})

const loading = ref(false)
const error = ref('')
const showPassword = ref(false)

const form = reactive({
  email: '',
  password: '',
})

const fieldErrors = reactive({
  email: '',
  password: '',
})

function limpiarErroresCampo() {
  fieldErrors.email = ''
  fieldErrors.password = ''
}

function limpiarErrorGlobal() {
  error.value = ''
}

function validate() {
  limpiarErroresCampo()

  let ok = true

  if (!form.email) {
    fieldErrors.email = 'El correo es obligatorio'
    ok = false
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    fieldErrors.email = 'Correo inválido'
    ok = false
  }

  if (!form.password) {
    fieldErrors.password = 'La contraseña es obligatoria'
    ok = false
  }

  return ok
}

async function login() {
  limpiarErrorGlobal()

  if (!validate()) return

  loading.value = true

  try {
    const data = await loginDocente({
      email: form.email,
      password: form.password,
    })

    localStorage.setItem('token', data.token)
    localStorage.setItem('docente_id', data.docente_id)
    localStorage.setItem('docente_nombre', data.nombre || 'Docente')

    router.push({ name: 'cursos' })
  } catch (e) {
    error.value = e?.message || 'Credenciales incorrectas'
  } finally {
    loading.value = false
  }
}
</script>