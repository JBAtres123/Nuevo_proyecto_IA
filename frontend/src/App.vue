<template>
  <div
    class="
      min-h-screen flex flex-col
      bg-surface
      text-surface-text
      dark:bg-surface-dark
      dark:text-surface-textDark
      transition-colors duration-300
    "
  >
    <!-- Navigation -->
    <nav
      v-if="!ocultarLayout"
      class="
        border-b
        border-surface-border
        dark:border-surface-borderDark
        bg-surface-card/95
        dark:bg-surface-cardDark/95
        backdrop-blur-md
        sticky top-0 z-50
        transition-colors duration-300
      "
    >
      <div class="w-full px-6 lg:px-10 py-2.5 flex items-center gap-4">

        <!-- Logo -->
        <RouterLink to="/" class="flex items-center gap-5 shrink-0 group">
          <div
            class="
              w-12 h-12
              rounded-xl
              bg-brand-300
              border-0
              flex items-center justify-center
              overflow-hidden
              shadow-lg shadow-brand-300/30
            "
          >
            <img
              src="/logo.png"
              alt="Logo DeepGrader AI"
              class="w-full h-full object-cover object-center"
            />
          </div>

          <span
            class="
              font-display text-2xl leading-6 font-bold tracking-tight
              text-surface-text dark:text-surface-textDark
              whitespace-nowrap
            "
          >
            DeepGrader
            <span class="text-brand-700 dark:text-brand-300">AI</span>
          </span>
        </RouterLink>

        <!-- Links principales -->
        <div
          v-if="cursoStore.cursoId"
          class="hidden lg:flex items-center gap-1 ml-auto justify-end min-w-0"
        >
          <RouterLink
            v-for="link in navLinks"
            :key="link.to"
            :to="link.to"
            class="
              px-3 py-2 rounded-lg text-[11px] font-mono uppercase tracking-wide
              text-surface-muted dark:text-surface-mutedDark
              hover:text-surface-text dark:hover:text-surface-textDark
              hover:bg-surface-tag dark:hover:bg-surface-tagDark
              transition-all duration-150
              flex items-center gap-2
              whitespace-nowrap
            "
            active-class="!text-brand-700 dark:!text-brand-300 !bg-brand-300/15"
          >
            <svg
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
                :d="link.icon"
              />
            </svg>

            {{ link.label }}
          </RouterLink>
        </div>

        <!-- Panel derecho -->
        <div class="flex items-center gap-2 shrink-0">

          <!-- Curso activo -->
          <div
            v-if="cursoStore.cursoId"
            class="
              hidden md:flex items-center gap-2
              bg-surface-tag dark:bg-surface-tagDark
              border border-brand-500/30 dark:border-brand-300/25
              rounded-lg px-3 py-2 text-xs
              max-w-[170px]
              transition-colors duration-300
            "
            title="Curso activo"
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
                d="M12 6.5c-1.8-1.2-3.8-1.8-6-1.8A2 2 0 0 0 4 6.7V19a1 1 0 0 0 1.2 1c2.4-.5 4.6 0 6.8 1.5m0-15c1.8-1.2 3.8-1.8 6-1.8a2 2 0 0 1 2 2V19a1 1 0 0 1-1.2 1c-2.4-.5-4.6 0-6.8 1.5m0-15v15"
              />
            </svg>

            <span class="text-surface-text dark:text-surface-textDark truncate font-medium">
              {{ cursoStore.cursoNombre }}
            </span>
          </div>

          <!-- Exigencia -->
          <div
            class="
              hidden xl:flex items-center gap-2
              bg-surface-tag dark:bg-surface-tagDark
              border border-surface-border dark:border-surface-borderDark
              rounded-lg px-3 py-2 text-xs
              transition-colors duration-300
            "
          >
            <span class="text-brand-700 dark:text-brand-300">
              Exigencia
            </span>

            <span class="font-mono font-bold text-brand-700 dark:text-brand-300">
              {{ store.nivelExigencia }}/10
            </span>
          </div>

          <!-- Botón tema -->
          <button
            @click="store.toggleTheme()"
            class="
              w-10 h-10
              flex items-center justify-center
              rounded-lg
              border border-surface-border dark:border-surface-borderDark
              bg-surface-tag dark:bg-surface-tagDark
              text-surface-text dark:text-surface-textDark
              hover:text-brand-700 dark:hover:text-brand-300
              hover:border-brand-500/40 dark:hover:border-brand-300/40
              transition-all duration-200
            "
            title="Cambiar tema"
          >
            <svg
              v-if="store.darkMode"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="2"
              stroke="currentColor"
              class="w-5 h-5"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M12 3v2m0 14v2m9-9h-2M5 12H3m15.364 6.364-1.414-1.414M7.05 7.05 5.636 5.636m12.728 0-1.414 1.414M7.05 16.95l-1.414 1.414M12 8a4 4 0 100 8 4 4 0 000-8z"
              />
            </svg>

            <svg
              v-else
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="2"
              stroke="currentColor"
              class="w-5 h-5"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M21 12.79A9 9 0 1111.21 3c0 .28.02.56.05.83A7 7 0 0021 12.79z"
              />
            </svg>
          </button>

          <!-- Usuario / submenu -->
          <div ref="userMenuRef" class="relative">
            <button
              @click.stop="toggleUserMenu"
              class="
                h-10
                px-3
                flex items-center gap-2
                rounded-lg
                border border-surface-border dark:border-surface-borderDark
                bg-surface-tag dark:bg-surface-tagDark
                text-surface-text dark:text-surface-textDark
                hover:border-brand-500/40 dark:hover:border-brand-300/40
                transition-all duration-200
              "
            >
              <div
                class="
                  w-6 h-6 rounded-full
                  bg-brand-300 text-surface-dark
                  flex items-center justify-center
                  font-bold text-xs
                "
              >
                {{ docenteNombre.charAt(0).toUpperCase() }}
              </div>

              <span class="hidden xl:inline text-xs font-medium max-w-[110px] truncate">
                {{ docenteNombre }}
              </span>

              <span class="text-surface-muted dark:text-surface-mutedDark text-xs">
                ▾
              </span>
            </button>

            <div
              v-if="userMenuOpen"
              class="
                absolute right-0 mt-2 w-56
                bg-surface-card dark:bg-surface-cardDark
                border border-surface-border dark:border-surface-borderDark
                rounded-xl shadow-card
                overflow-hidden
                z-50
                transition-colors duration-300
              "
            >
              <div class="px-4 py-3 border-b border-surface-border dark:border-surface-borderDark">
                <p class="text-xs text-surface-muted dark:text-surface-mutedDark">
                  Sesión activa
                </p>

                <p class="text-sm font-medium text-surface-text dark:text-surface-textDark truncate">
                  {{ docenteNombre }}
                </p>
              </div>

              <RouterLink
                to="/configuracion"
                @click="userMenuOpen = false"
                class="
                  w-full px-4 py-3 text-left text-sm
                  text-surface-text dark:text-surface-textDark
                  hover:bg-surface-tag dark:hover:bg-surface-tagDark
                  transition-colors
                  flex items-center gap-2
                "
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
                    d="M15.75 7.5a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0zM4.5 20.25a7.5 7.5 0 0 1 10.2-6.98M16.86 17.49l3.18-3.18a1.5 1.5 0 0 1 2.12 2.12l-3.18 3.18-3.6.9.9-3.6z"
                  />
                </svg>

                Editar Perfil
              </RouterLink>

              <button
                v-if="cursoStore.cursoId"
                @click="cambiarCurso"
                class="
                  w-full px-4 py-3 text-left text-sm
                  text-surface-text dark:text-surface-textDark
                  hover:bg-surface-tag dark:hover:bg-surface-tagDark
                  transition-colors
                  flex items-center gap-2
                "
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
                    d="M12 6.5c-1.8-1.2-3.8-1.8-6-1.8A2 2 0 0 0 4 6.7V19a1 1 0 0 0 1.2 1c2.4-.5 4.6 0 6.8 1.5m0-15c1.8-1.2 3.8-1.8 6-1.8a2 2 0 0 1 2 2V19a1 1 0 0 1-1.2 1c-2.4-.5-4.6 0-6.8 1.5m0-15v15"
                  />
                </svg>

                Cambiar curso
              </button>

              <button
                @click="logout"
                class="
                  w-full px-4 py-3 text-left text-sm
                  text-red-500 dark:text-red-400
                  hover:bg-red-500/10
                  transition-colors
                "
              >
                Cerrar sesión
              </button>
            </div>
          </div>
        </div>
      </div>
    </nav>

    <!-- Page -->
    <main class="flex-1">
      <RouterView v-slot="{ Component }">
        <Transition name="page" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
    </main>

    <!-- Footer -->
    <footer
      v-if="!ocultarLayout"
      class="
        border-t
        border-surface-border
        dark:border-surface-borderDark
        py-4
        text-center
        text-xs
        text-surface-muted
        dark:text-surface-mutedDark
        transition-colors duration-300
      "
    >
      DeepGrader AI — Sistema Inteligente para Calificación de Exámenes
    </footer>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import { RouterLink, RouterView, useRouter, useRoute } from 'vue-router'

import { useAppStore } from '@/stores/appStore'
import { useCursoStore } from '@/stores/cursoStore'

const store = useAppStore()
const cursoStore = useCursoStore()
const router = useRouter()
const route = useRoute()

const ocultarLayout = computed(() => {
  return ['login', 'registro', 'cursos'].includes(route.name)
})

const userMenuOpen = ref(false)
const userMenuRef = ref(null)

const docenteNombre = computed(() => {
  return localStorage.getItem('docente_nombre') || 'Docente'
})

function toggleUserMenu() {
  userMenuOpen.value = !userMenuOpen.value
}

function cerrarMenuSiClickAfuera(event) {
  if (
    userMenuOpen.value &&
    userMenuRef.value &&
    !userMenuRef.value.contains(event.target)
  ) {
    userMenuOpen.value = false
  }
}


function logout() {
  userMenuOpen.value = false

  cursoStore.clearCurso()

  localStorage.removeItem('token')
  localStorage.removeItem('docente_id')
  localStorage.removeItem('docente_nombre')
  localStorage.removeItem('cursoActivo')

  router.push({ name: 'login' })
}

function cambiarCurso() {
  userMenuOpen.value = false
  router.push({ name: 'cursos' })
}

const navLinks = [
  {
    to: '/',
    label: 'Inicio',
    icon: 'M3 10.5 12 3l9 7.5V21a1 1 0 0 1-1 1h-5v-6H8v6H4a1 1 0 0 1-1-1V10.5z',
  },
  {
    to: '/historial',
    label: 'Historial',
    icon: 'M12 8v5l3 3 M21 12a9 9 0 1 1-18 0a9 9 0 0 1 18 0z',
  },
]

onMounted(() => {
  store.loadConfig()
  document.addEventListener('click', cerrarMenuSiClickAfuera)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', cerrarMenuSiClickAfuera)
})
</script>

<style scoped>
.page-enter-active,
.page-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>