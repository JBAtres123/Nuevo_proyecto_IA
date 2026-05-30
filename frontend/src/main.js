import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'
import { useAppStore } from '@/stores/appStore'
import { useCursoStore } from '@/stores/cursoStore'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// Inicializar stores una sola vez antes de montar la app.
// Tema: evita el parpadeo de modo claro/oscuro al cargar.
// Curso: restaura el curso activo para que el guard del router
//        ya lo tenga disponible en la primera navegación.
const appStore = useAppStore()
appStore.loadTheme()

const cursoStore = useCursoStore()
cursoStore.restoreFromStorage()

app.mount('#app')