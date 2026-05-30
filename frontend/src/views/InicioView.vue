<template>
  <div class="w-full px-4 py-6 animate-fade-in space-y-5">

    <!-- ── Encabezado / Bienvenida ── -->
    <section
      class="card p-6 shadow-card bg-gradient-to-br
             from-surface-card to-surface-tag
             dark:from-surface-cardDark dark:to-surface-tagDark
             border border-surface-border dark:border-surface-borderDark"
    >
      <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-5">
        <div class="flex items-center gap-5">

          <!-- Avatar -->
          <div class="w-20 h-20 rounded-full border border-brand-300/40 bg-brand-300/10 flex items-center justify-center shadow-neon">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-10 h-10 text-brand-300">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 7.5a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0zM4.5 20.25a7.5 7.5 0 0 1 15 0" />
            </svg>
          </div>

          <div>
            <h1 class="font-display text-3xl text-surface-text dark:text-white mb-1">
              Bienvenido, {{ docenteNombre }}
            </h1>

            <!-- Selector de curso activo -->
<div class="flex items-center gap-2 mt-1 flex-wrap">
  <p class="text-sm text-surface-muted dark:text-surface-mutedDark">
    Curso activo:
  </p>

  <div ref="cursoMenuRef" class="relative">
    <button
      @click.stop="toggleCursoMenu"
      class="
        h-9 min-w-[170px] px-3
        flex items-center justify-between gap-3
        rounded-lg
        border border-surface-border dark:border-surface-borderDark
        bg-surface-card dark:bg-surface-cardDark
        text-brand-600 dark:text-brand-300
        hover:border-brand-300/40
        transition-all duration-200
      "
    >
      <span class="text-sm font-semibold truncate">
        {{ cursoActivoNombre }}
      </span>

      <span
        class="text-brand-300 text-xs transition-transform duration-200"
        :class="{ 'rotate-180': cursoMenuOpen }"
      >
        ▾
      </span>
    </button>

    <div
      v-if="cursoMenuOpen"
      @click.stop
      class="
        absolute left-0 mt-2 w-64
        bg-surface-card dark:bg-surface-cardDark
        border border-surface-border dark:border-surface-borderDark
        rounded-xl shadow-card
        overflow-hidden
        z-50
      "
    >
      <div class="px-4 py-3 border-b border-surface-border dark:border-surface-borderDark">
        <p class="text-xs text-surface-muted dark:text-surface-mutedDark">
          Seleccionar curso
        </p>
        <p class="text-sm font-medium text-surface-text dark:text-white truncate">
          {{ cursoActivoNombre }}
        </p>
      </div>

      <button
        @click.stop="seleccionarCurso(null)"
        class="
          w-full px-4 py-3 text-left text-sm
          text-surface-text dark:text-surface-textDark
          hover:bg-surface-tag dark:hover:bg-surface-tagDark
          transition-colors
          flex items-center gap-2
        "
        :class="{ '!text-brand-300 !bg-brand-300/10': !cursoActivoId }"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="2"
          stroke="currentColor"
          class="w-4 h-4 text-brand-300"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M4 6h16M4 12h16M4 18h16"
          />
        </svg>

        Todos los cursos
      </button>

      <button
        v-for="c in cursos"
        :key="c.id"
        @click.stop="seleccionarCurso(c)"
        class="
          w-full px-4 py-3 text-left text-sm
          text-surface-text dark:text-surface-textDark
          hover:bg-surface-tag dark:hover:bg-surface-tagDark
          transition-colors
          flex items-center gap-2
        "
        :class="{ '!text-brand-300 !bg-brand-300/10': cursoActivoId === c.id }"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="2"
          stroke="currentColor"
          class="w-4 h-4 text-brand-300"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M12 6.5c-1.8-1.2-3.8-1.8-6-1.8A2 2 0 0 0 4 6.7V19a1 1 0 0 0 1.2 1c2.4-.5 4.6 0 6.8 1.5m0-15c1.8-1.2 3.8-1.8 6-1.8a2 2 0 0 1 2 2V19a1 1 0 0 1-1.2 1c-2.4-.5-4.6 0-6.8 1.5m0-15v15"
          />
        </svg>

        <span class="truncate">
          {{ c.nombre }}
        </span>
      </button>
    </div>
  </div>

  <button
    @click="showCrearCurso = true"
    class="
      ml-1 text-xs
      text-surface-muted dark:text-surface-mutedDark
      hover:text-brand-300
      transition-colors
      flex items-center gap-1
    "
    title="Crear nuevo curso"
  >
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 20 20"
      fill="currentColor"
      class="w-3.5 h-3.5"
    >
      <path d="M10.75 4.75a.75.75 0 0 0-1.5 0v4.5h-4.5a.75.75 0 0 0 0 1.5h4.5v4.5a.75.75 0 0 0 1.5 0v-4.5h4.5a.75.75 0 0 0 0-1.5h-4.5v-4.5z" />
    </svg>

    Nuevo curso
  </button>
</div>

            <p class="text-sm text-surface-muted dark:text-surface-mutedDark mt-2 max-w-2xl">
              Gestiona, califica y analiza el desempeño académico de tus estudiantes con DeepGrader AI.
            </p>
          </div>
        </div>

        <div class="flex flex-wrap gap-3">
          <RouterLink
            to="/calificar"
            class="bg-brand-300 text-surface-dark font-mono font-bold text-sm
                   px-5 py-3 rounded-lg hover:bg-brand-200 shadow-neon
                   transition-all duration-200 flex items-center gap-2"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 3.487a2.1 2.1 0 0 1 2.97 2.97L8.5 17.79 4 19l1.21-4.5L16.862 3.487z M13 6l5 5" />
            </svg>
            Calificar examen
          </RouterLink>
          <button
            @click="irAMateriales"
            class="border border-brand-300/50 text-brand-600 dark:text-brand-300
                  font-mono font-bold text-sm px-5 py-3 rounded-lg
                  hover:bg-brand-300/10 transition-all duration-200 flex items-center gap-2"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 16V4m0 0 4 4m-4-4-4 4M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3" />
            </svg>
            Subir materiales
          </button>
        </div>
      </div>
    </section>

    <!-- ── Modal: Crear curso ── -->
    <Teleport to="body">
      <div
        v-if="showCrearCurso"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
        @click.self="cerrarModalCurso"
      >
        <div class="card w-full max-w-md p-6 shadow-card border border-surface-border dark:border-surface-borderDark mx-4">
          <h3 class="font-display text-2xl text-surface-text dark:text-white mb-4">Nuevo curso</h3>
          <div class="space-y-3">
            <input
              v-model="nuevoCurso.nombre"
              type="text"
              placeholder="Nombre del curso *"
              @keyup.enter="handleCrearCurso"
              class="w-full px-4 py-2.5 rounded-lg border border-surface-border dark:border-surface-borderDark
                     bg-surface-tag dark:bg-surface-tagDark text-surface-text dark:text-white
                     text-sm outline-none focus:border-brand-300/60 transition-colors"
            />
            <textarea
              v-model="nuevoCurso.descripcion"
              placeholder="Descripción (opcional)"
              rows="3"
              class="w-full px-4 py-2.5 rounded-lg border border-surface-border dark:border-surface-borderDark
                     bg-surface-tag dark:bg-surface-tagDark text-surface-text dark:text-white
                     text-sm outline-none focus:border-brand-300/60 transition-colors resize-none"
            />
            <p v-if="errorCurso" class="text-xs text-accent-pink">{{ errorCurso }}</p>
          </div>
          <div class="flex gap-3 mt-5">
            <button
              @click="cerrarModalCurso"
              class="flex-1 py-2.5 rounded-lg border border-surface-border dark:border-surface-borderDark
                     text-surface-muted dark:text-surface-mutedDark text-sm
                     hover:bg-surface-tag dark:hover:bg-surface-tagDark transition-colors"
            >
              Cancelar
            </button>
            <button
              @click="handleCrearCurso"
              :disabled="creandoCurso"
              class="flex-1 py-2.5 rounded-lg bg-brand-300 text-surface-dark font-mono font-bold
                     text-sm hover:bg-brand-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ creandoCurso ? 'Creando...' : 'Crear curso' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ── KPI Skeletons ── -->
    <div v-if="loadingStats" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
      <div v-for="i in 5" :key="i" class="card p-5 shadow-card animate-pulse">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-xl bg-surface-tag dark:bg-surface-tagDark shrink-0"></div>
          <div class="flex-1 space-y-2">
            <div class="h-3 bg-surface-tag dark:bg-surface-tagDark rounded w-3/4"></div>
            <div class="h-7 bg-surface-tag dark:bg-surface-tagDark rounded w-1/2"></div>
            <div class="h-3 bg-surface-tag dark:bg-surface-tagDark rounded w-2/3"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── KPIs ── -->
    <section v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
      <div
        v-for="card in kpis"
        :key="card.label"
        class="card dashboard-card p-5 shadow-card cursor-default"
      >
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-xl border flex items-center justify-center shrink-0" :class="card.iconBox">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-6 h-6">
              <path stroke-linecap="round" stroke-linejoin="round" :d="card.icon" />
            </svg>
          </div>
          <div>
            <p class="text-xs text-surface-muted dark:text-surface-mutedDark mb-1">{{ card.label }}</p>
            <p class="font-display text-3xl leading-none text-surface-text dark:text-white">{{ card.value }}</p>
            <p class="text-xs text-surface-muted dark:text-surface-mutedDark mt-1">{{ card.detail }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ── Fila principal ── -->
    <section class="grid grid-cols-1 xl:grid-cols-2 gap-5">

      <!-- Actividad reciente -->
      <div class="card dashboard-soft-card p-5 shadow-card border border-accent-pink/30 hover:border-accent-pink/70">
        <div class="flex items-center justify-between mb-4">
          <h2 class="font-display text-xl text-surface-text dark:text-white">Actividad reciente</h2>
          <RouterLink
            to="/historial"
            class="text-xs border border-surface-border dark:border-surface-borderDark
                   px-3 py-1.5 rounded-lg text-surface-muted dark:text-surface-mutedDark
                   hover:text-brand-300 hover:border-brand-300/40 transition-colors"
          >
            Ver todo
          </RouterLink>
        </div>

        <!-- Skeleton -->
        <div v-if="loadingStats" class="space-y-2">
          <div v-for="i in 5" :key="i" class="h-12 bg-surface-tag dark:bg-surface-tagDark rounded-lg animate-pulse"></div>
        </div>

        <!-- Vacío -->
        <div v-else-if="actividad.length === 0"
             class="flex flex-col items-center justify-center py-10 text-surface-muted dark:text-surface-mutedDark gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-10 h-10 opacity-30">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
          </svg>
          <p class="text-sm">No hay exámenes registrados aún.</p>
        </div>

        <!-- Tabla con scroll -->
        <div
          v-else
          class="
            max-h-[320px]
            overflow-y-auto
            overflow-x-auto
            rounded-xl
            border border-surface-border dark:border-surface-borderDark
            custom-scroll
          "
        >
          <table class="w-full text-sm">
            <thead class="bg-surface-tag dark:bg-surface-tagDark">
              <tr class="text-xs text-surface-muted dark:text-surface-mutedDark">
                <th class="text-left px-4 py-3 font-medium">Estudiante</th>
                <th class="text-left px-4 py-3 font-medium hidden sm:table-cell">Fecha</th>
                <th class="text-left px-4 py-3 font-medium">Estado</th>
                <th class="text-left px-4 py-3 font-medium">Nota</th>
                <th class="text-center px-4 py-3 font-medium">Ver</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in actividad"
                :key="item.id"
                class="border-t border-surface-border dark:border-surface-borderDark
                       hover:bg-surface-tag/60 dark:hover:bg-surface-tagDark/60 transition-colors"
              >
                <td class="px-4 py-3">
                  <div class="flex items-center gap-2">
                    <div class="w-7 h-7 rounded-full bg-brand-300/15 text-brand-600 dark:text-brand-300 flex items-center justify-center text-xs font-bold shrink-0">
                      {{ (item.estudiante || '?').charAt(0).toUpperCase() }}
                    </div>
                    <span class="text-surface-text dark:text-surface-textDark truncate max-w-[120px]">
                      {{ item.estudiante || 'Sin nombre' }}
                    </span>
                  </div>
                </td>
                <td class="px-4 py-3 hidden sm:table-cell text-surface-muted dark:text-surface-mutedDark text-xs">
                  {{ item.fecha }}
                </td>
                <td class="px-4 py-3">
                  <span class="badge" :class="badgeClass(item.estado)">
                    {{ estadoLabel(item.estado) }}
                  </span>
                </td>
                <td class="px-4 py-3 font-mono text-surface-text dark:text-white">
                  {{ item.porcentaje != null ? item.porcentaje + '%' : '—' }}
                </td>
                <td class="px-4 py-3 text-center">
                  <button
                    type="button"
                    @click.stop="irAHistorial(item.id)"
                    class="w-8 h-8 rounded-lg border border-surface-border dark:border-surface-borderDark
                          text-surface-muted dark:text-surface-mutedDark
                          hover:text-brand-300 hover:border-brand-300/40 transition-colors
                          inline-flex items-center justify-center"
                    title="Ver detalle"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6z M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z" />
                    </svg>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Distribución de notas -->
      <div class="card dashboard-soft-card p-5 shadow-card border border-accent-green/30 hover:border-accent-green/70">
        <div class="flex items-center justify-between mb-4">
          <h2 class="font-display text-xl text-surface-text dark:text-white">Distribución de notas</h2>
          <span class="text-xs border border-surface-border dark:border-surface-borderDark px-3 py-1.5 rounded-lg text-surface-muted dark:text-surface-mutedDark">
            {{ cursoActivoId ? 'Curso activo' : 'Todos los cursos' }}
          </span>
        </div>

        <!-- Skeleton -->
        <div v-if="loadingStats" class="h-64 flex items-end gap-4 px-5 pb-8">
          <div v-for="(h, i) in ['30%','45%','60%','80%','65%','40%']" :key="i"
               class="flex-1 bg-surface-tag dark:bg-surface-tagDark rounded-t-lg animate-pulse"
               :style="{ height: h }"></div>
        </div>

        <!-- Sin datos -->
        <div v-else-if="totalCalificados === 0"
             class="h-64 flex flex-col items-center justify-center text-surface-muted dark:text-surface-mutedDark gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-10 h-10 opacity-30">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
          </svg>
          <p class="text-sm">No hay exámenes completados aún.</p>
        </div>

        <!-- Gráfico de barras -->
        <div
  v-else
  class="h-64 flex items-end gap-3 border-l border-b border-surface-border dark:border-surface-borderDark px-4 pt-4 pb-8 relative"
>
  <!-- Líneas guía -->
  <div
    v-for="top in ['8px','56px','104px']"
    :key="top"
    class="absolute inset-x-4 border-t border-dashed border-surface-border dark:border-surface-borderDark opacity-50"
    :style="{ top }"
  ></div>

  <div
    v-for="bar in distribucionConAltura"
    :key="bar.label"
    class="flex-1 h-full flex flex-col items-center justify-end gap-2 relative z-10 group"
  >
    <!-- Tooltip -->
    <div class="absolute bottom-full mb-2 hidden group-hover:flex flex-col items-center pointer-events-none">
      <div class="bg-surface-card dark:bg-surface-cardDark border border-brand-300/40 rounded-lg px-2.5 py-1 text-xs text-brand-300 font-mono whitespace-nowrap shadow-lg">
        {{ bar.count }} {{ bar.count === 1 ? 'examen' : 'exámenes' }}
      </div>
      <div class="w-1.5 h-1.5 bg-brand-300/40 rotate-45 -mt-0.5 border-r border-b border-brand-300/40"></div>
    </div>

    <!-- Número arriba de cada barra -->
    <span class="text-xs font-mono text-surface-text dark:text-white">
      {{ bar.count }}
    </span>

    <!-- Barra -->
    <div
      class="w-full max-w-[52px] min-h-[8px] rounded-t-lg bg-accent-pink shadow-[0_0_18px_rgba(240,96,144,0.45)] transition-all duration-700"
      :style="{ height: bar.height }"
    ></div>

    <!-- Rango -->
    <span class="text-[11px] text-surface-muted dark:text-surface-mutedDark font-mono leading-tight text-center">
      {{ bar.label }}
    </span>
  </div>
</div>

<div class="flex items-center justify-center gap-2 mt-3 text-xs text-surface-muted dark:text-surface-mutedDark">
  <span class="w-3 h-3 rounded-sm bg-brand-300 inline-block"></span>
  Estudiantes por rango de nota
</div>
</div>

</section>

<!-- ── Fila inferior ── -->
<section class="grid grid-cols-1 lg:grid-cols-3 gap-5">

  <!-- Rendimiento general -->
  <div class="card dashboard-soft-card p-5 shadow-card border border-accent-orange/30 hover:border-accent-orange/70">
    <div class="flex items-center justify-between mb-4">
      <h2 class="font-display text-xl text-surface-text dark:text-white">Rendimiento general</h2>
      <span class="text-xs text-surface-muted dark:text-surface-mutedDark">
        {{ cursoActivoId ? 'Curso activo' : 'Global' }}
      </span>
    </div>

    <div v-if="loadingStats" class="space-y-3">
      <div
        v-for="i in 5"
        :key="i"
        class="h-14 bg-surface-tag dark:bg-surface-tagDark rounded-xl animate-pulse"
      ></div>
    </div>

    <div v-else class="space-y-4">
      <div
        v-for="item in rendimiento"
        :key="item.label"
        class="flex items-center justify-between p-3 rounded-xl
               bg-surface-tag dark:bg-surface-tagDark
               border border-surface-border dark:border-surface-borderDark
               transition-all duration-300 hover:-translate-y-0.5
               hover:border-brand-300/40 hover:bg-brand-300/5"
      >
        <div class="flex items-center gap-3">
          <div
            class="w-9 h-9 rounded-lg flex items-center justify-center border"
            :class="item.box"
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
                :d="item.icon"
              />
            </svg>
          </div>
          <span class="text-sm text-surface-text dark:text-surface-textDark">
            {{ item.label }}
          </span>
        </div>

        <span class="font-display text-2xl" :class="item.color">
          {{ item.value }}
        </span>
      </div>
    </div>
  </div>
      <!-- Progreso de calificación -->
      <div class="card dashboard-soft-card p-5 shadow-card border border-accent-blue/30 hover:border-accent-blue/70">
        <div class="flex items-center justify-between mb-4">
          <h2 class="font-display text-xl text-surface-text dark:text-white">Progreso de calificación</h2>
          <span class="text-xs border border-surface-border dark:border-surface-borderDark px-3 py-1.5 rounded-lg text-surface-muted dark:text-surface-mutedDark">
            {{ cursoActivoId ? 'Curso activo' : 'Global' }}
          </span>
        </div>

        <!-- Skeleton anillo -->
        <div v-if="loadingStats" class="flex items-center justify-center py-3">
          <div class="w-40 h-40 rounded-full border-[12px] border-surface-tag dark:border-surface-tagDark animate-pulse"></div>
        </div>

        <div v-else class="flex items-center justify-center py-3">
          <div class="relative w-40 h-40">
            <svg class="w-full h-full rotate-[-90deg]" viewBox="0 0 120 120">
              <circle cx="60" cy="60" r="48" fill="none" stroke="currentColor" stroke-width="12" class="text-surface-tag dark:text-surface-tagDark" />
              <circle
                cx="60" cy="60" r="48" fill="none"
                stroke="#c8f060" stroke-width="12" stroke-linecap="round"
                stroke-dasharray="301"
                :stroke-dashoffset="301 - (301 * progreso.porcentaje) / 100"
                style="transition: stroke-dashoffset 1s ease"
              />
            </svg>
            <div class="absolute inset-0 flex flex-col items-center justify-center">
              <span class="font-display text-4xl text-brand-300">{{ progreso.porcentaje }}%</span>
              <span class="text-xs text-surface-muted dark:text-surface-mutedDark">procesado</span>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3 mt-3">
          <div
            v-for="item in progresoItems"
            :key="item.label"
            class="p-3 rounded-xl bg-surface-tag dark:bg-surface-tagDark border border-surface-border dark:border-surface-borderDark"
          >
            <p class="text-xs text-surface-muted dark:text-surface-mutedDark">{{ item.label }}</p>
            <p class="font-display text-2xl mt-1" :class="item.color">
              {{ loadingStats ? '—' : item.value }}
            </p>
          </div>
        </div>
      </div>

      <!-- Estado del sistema -->
      <div class="card dashboard-soft-card p-5 shadow-card border border-accent-pink/30 hover:border-accent-pink/70">
        <h2 class="font-display text-xl text-surface-text dark:text-white mb-4">Estado del sistema</h2>

        <div class="space-y-4">
          <div v-for="servicio in servicios" :key="servicio.nombre" class="flex items-center justify-between gap-4">
            <div class="flex items-center gap-3">
              <div class="w-9 h-9 rounded-lg border border-surface-border dark:border-surface-borderDark flex items-center justify-center text-surface-muted dark:text-surface-mutedDark">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4">
                  <path stroke-linecap="round" stroke-linejoin="round" :d="servicio.icon" />
                </svg>
              </div>
              <span class="text-sm text-surface-text dark:text-surface-textDark">{{ servicio.nombre }}</span>
            </div>
            <div class="flex items-center gap-2">
              <span
                class="w-2 h-2 rounded-full transition-colors"
                :class="healthResult === null
                  ? 'bg-surface-muted dark:bg-surface-mutedDark'
                  : healthResult.ok ? 'bg-brand-300 shadow-neon' : 'bg-accent-pink'"
              ></span>
              <span class="text-xs text-surface-muted dark:text-surface-mutedDark">
                {{ healthResult === null ? 'Sin verificar' : healthResult.ok ? 'Operativo' : 'Error' }}
              </span>
            </div>
          </div>
        </div>

        <!-- Botón verificar API -->
        <button
          @click="handleCheckHealth"
          :disabled="checkingHealth"
          class="mt-5 w-full border border-brand-300/50 text-brand-600 dark:text-brand-300
                 font-mono font-bold text-sm rounded-lg py-2.5 hover:bg-brand-300/10
                 transition-all duration-200 flex items-center justify-center gap-2
                 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"
               class="w-5 h-5" :class="{ 'animate-spin': checkingHealth }">
            <path stroke-linecap="round" stroke-linejoin="round"
                  d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
          </svg>
          {{ checkingHealth ? 'Verificando...' : 'Verificar API' }}
        </button>

        <!-- Resultado health -->
<div
  v-if="healthResult !== null"
  class="mt-4 p-3 rounded-lg text-sm border transition-all"
  :class="healthResult.ok
    ? 'bg-brand-300/10 border-brand-500/30 text-brand-700 dark:bg-brand-300/10 dark:border-brand-300/30 dark:text-brand-300'
    : 'bg-accent-pink/10 border-accent-pink/30 text-pink-700 dark:bg-accent-pink/10 dark:border-accent-pink/30 dark:text-accent-pink'"
>
  <template v-if="healthResult.ok">
    <span class="font-medium">
      ✓ API OK — v{{ healthResult.version }}
    </span>

    <span
      v-if="healthResult.model"
      class="opacity-80 text-xs block mt-0.5 text-brand-800 dark:text-brand-200"
    >
      Modelo: {{ healthResult.model }}
    </span>
  </template>

  <template v-else>
    <span class="font-medium">
      ✗ Error: {{ healthResult.error }}
    </span>
  </template>
</div>
        <!-- Nivel de exigencia actual -->
        <div class="mt-4 p-3 rounded-xl bg-surface-tag dark:bg-surface-tagDark border border-surface-border dark:border-surface-borderDark">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs text-surface-muted dark:text-surface-mutedDark">Nivel de exigencia</span>
            <span class="font-mono text-sm text-brand-300 font-bold">
              {{ loadingStats ? '—' : nivelExigencia + '/10' }}
            </span>
          </div>
          <div class="w-full h-2 bg-surface-border dark:bg-surface-borderDark rounded-full overflow-hidden">
            <div
              class="h-full bg-gradient-to-r from-brand-600 to-brand-300 rounded-full transition-all duration-700"
              :style="{ width: (nivelExigencia * 10) + '%' }"
            ></div>
          </div>
          <p class="text-xs text-surface-muted dark:text-surface-mutedDark mt-1.5 truncate">{{ nivelLabel }}</p>
        </div>
      </div>

    </section>

    <!-- ── Error global ── -->
    <div
      v-if="errorStats"
      class="p-4 rounded-xl bg-accent-pink/10 border border-accent-pink/30 text-accent-pink text-sm flex items-center gap-3"
    >
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5 shrink-0">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
      </svg>
      <span>{{ errorStats }}</span>
      <button @click="loadDashboard" class="ml-auto text-xs underline hover:no-underline whitespace-nowrap">
        Reintentar
      </button>
    </div>

  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useCursoStore } from '@/stores/cursoStore'

// ── useApi: importar exactamente las funciones que ya existen ─────────────────
import {
  getCursos,
  crearCursoApi,
  checkHealth,
  getDashboardStats,
} from '@/composables/useApi'

const router = useRouter()

// ── Store ─────────────────────────────────────────────────────────────────────
const cursoStore = useCursoStore()

// ── Estado reactivo ───────────────────────────────────────────────────────────
const loadingStats   = ref(true)
const errorStats     = ref(null)
const checkingHealth = ref(false)
const healthResult   = ref(null)
const showCrearCurso = ref(false)
const creandoCurso   = ref(false)
const errorCurso     = ref('')

const cursos        = ref([])
const statsData     = ref(null)
const nuevoCurso    = ref({ nombre: '', descripcion: '' })

// Inicializar cursoActivoId desde el store (que ya restaura de localStorage)
const cursoActivoId = ref(cursoStore.cursoId || null)

const cursoMenuOpen = ref(false)
const cursoMenuRef = ref(null)

// ── Computed ──────────────────────────────────────────────────────────────────

const cursoActivoNombre = computed(() => {
  if (!cursoActivoId.value) return 'Todos los cursos'

  const curso = cursos.value.find(c => c.id === cursoActivoId.value)
  return curso?.nombre || cursoStore.cursoNombre || 'Curso activo'
})

const docenteNombre = computed(() =>
  localStorage.getItem('docente_nombre') || 'Docente'
)

const nivelExigencia = computed(() => statsData.value?.kpis?.nivel_exigencia ?? 5)

const NIVEL_LABELS = {
  1: 'Muy indulgente',     2: 'Amigo — Indulgente',
  3: 'Comprensivo',        4: 'Balanceado-Suave',
  5: 'Balanceado',         6: 'Balanceado-Estricto',
  7: 'Estricto',           8: 'Muy Estricto',
  9: 'Riguroso',           10: 'Máxima exigencia',
}
const nivelLabel = computed(() =>
  NIVEL_LABELS[nivelExigencia.value] || `Nivel ${nivelExigencia.value}`
)

const kpis = computed(() => {
  const k = statsData.value?.kpis || {}
  return [
    {
      label: 'Exámenes totales',
      value: k.total_examenes ?? '—',
      detail: 'Todos los tiempos',
      iconBox: 'border-brand-300/30 bg-brand-300/10 text-brand-300',
      icon: 'M7 3h7l5 5v13H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z M14 3v5h5 M9 13h6 M9 17h4',
    },
    {
      label: 'Pendientes',
      value: k.pendientes ?? '—',
      detail: 'Por calificar',
      iconBox: 'border-accent-orange/30 bg-accent-orange/10 text-accent-orange',
      icon: 'M12 6v6l4 2 M21 12a9 9 0 1 1-18 0a9 9 0 0 1 18 0z',
    },
    {
      label: 'Promedio del curso',
      value: k.promedio != null ? k.promedio + '%' : '—',
      detail: 'Exámenes completados',
      iconBox: 'border-accent-blue/30 bg-accent-blue/10 text-accent-blue',
      icon: 'M4 17l5-5 4 4 7-9 M4 21h16',
    },
    {
      label: 'Materiales indexados',
      value: k.materiales_indexados ?? '—',
      detail: 'Documentos RAG',
      iconBox: 'border-brand-300/30 bg-brand-300/10 text-brand-300',
      icon: 'M3 7a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z',
    },
    {
      label: 'Exigencia global',
      value: k.nivel_exigencia != null ? `${k.nivel_exigencia}/10` : '—',
      detail: nivelLabel.value,
      iconBox: 'border-accent-pink/30 bg-accent-pink/10 text-accent-pink',
      icon: 'M12 16v-4l3-3 M12 4a8 8 0 0 0-8 8c0 2.21.9 4.21 2.34 5.66A2 2 0 0 0 7.76 18h8.48a2 2 0 0 0 1.42-.34A8 8 0 0 0 20 12a8 8 0 0 0-8-8z M4.93 6.93l2.12 2.12 M19.07 6.93l-2.12 2.12 M12 4v3',
    },
  ]
})

const actividad = computed(() => statsData.value?.actividad_reciente || [])

const totalCalificados = computed(() => {
  const dist = statsData.value?.distribucion || []
  return dist.reduce((s, b) => s + Number(b.count || 0), 0)
})

const distribucionConAltura = computed(() => {
  const dist = statsData.value?.distribucion || []
  const maxCount = Math.max(...dist.map(b => Number(b.count || 0)), 1)

  return dist.map(b => {
    const count = Number(b.count || 0)

    return {
      ...b,
      count,
      height: count > 0 ? `${Math.max((count / maxCount) * 85, 8)}%` : '8%',
    }
  })
})

const rendimiento = computed(() => {
  const k = statsData.value?.kpis || {}
  return [
    {
      label: 'Promedio',
      value: k.promedio != null ? k.promedio + '%' : '—',
      color: 'text-accent-blue',
      box: 'border-accent-blue/30 bg-accent-blue/10 text-accent-blue',
      icon: 'M4 17l5-5 4 4 7-9 M4 21h16',
    },
    {
      label: 'Nota más alta',
      value: k.nota_maxima != null ? k.nota_maxima + '%' : '—',
      color: 'text-brand-300',
      box: 'border-brand-300/30 bg-brand-300/10 text-brand-300',
      icon: 'M12 19V5m0 0-5 5m5-5 5 5',
    },
    {
      label: 'Nota más baja',
      value: k.nota_minima != null ? k.nota_minima + '%' : '—',
      color: 'text-accent-pink',
      box: 'border-accent-pink/30 bg-accent-pink/10 text-accent-pink',
      icon: 'M12 5v14m0 0-5-5m5 5 5-5',
    },
    {
      label: 'Aprobados',
      value: k.aprobados ?? '—',
      color: 'text-brand-300',
      box: 'border-brand-300/30 bg-brand-300/10 text-brand-300',
      icon: 'M5 13l4 4L19 7',
    },
    {
      label: 'Reprobados',
      value: k.reprobados ?? '—',
      color: 'text-accent-orange',
      box: 'border-accent-orange/30 bg-accent-orange/10 text-accent-orange',
      icon: 'M6 18L18 6M6 6l12 12',
    },
  ]
})

const progreso = computed(() => statsData.value?.progreso || { porcentaje: 0 })

const progresoItems = computed(() => {
  const p = statsData.value?.progreso || {}
  return [
    { label: 'Completados', value: p.completados ?? '—', color: 'text-brand-300' },
    { label: 'Pendientes',  value: p.pendientes  ?? '—', color: 'text-accent-orange' },
    { label: 'Procesando',  value: p.procesando  ?? '—', color: 'text-accent-blue' },
    { label: 'Con error',   value: p.con_error   ?? '—', color: 'text-accent-pink' },
  ]
})

const servicios = [
  { nombre: 'Servicio de IA',           icon: 'M12 6V3m0 18v-3M6 12H3m18 0h-3M7.05 7.05 4.93 4.93m14.14 14.14-2.12-2.12M7.05 16.95l-2.12 2.12M19.07 4.93l-2.12 2.12' },
  { nombre: 'Indexación de materiales', icon: 'M4 5a2 2 0 0 1 2-2h7l5 5v11a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5z M13 3v5h5 M8 13h8 M8 17h5' },
  { nombre: 'Base de datos',            icon: 'M4 6c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3z M4 6v6c0 1.7 3.6 3 8 3s8-1.3 8-3V6 M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6' },
  { nombre: 'Almacenamiento',           icon: 'M3 7a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z' },
]

// ── Helpers ───────────────────────────────────────────────────────────────────
function irAMateriales() {
  if (!cursoStore.cursoId && cursoActivoId.value) {
    const curso = cursos.value.find(c => c.id === cursoActivoId.value)
    if (curso) cursoStore.setCurso(curso)
  }
  router.push('/materiales')
}

function cerrarCursoMenuSiClickAfuera(event) {
  if (
    cursoMenuOpen.value &&
    cursoMenuRef.value &&
    !cursoMenuRef.value.contains(event.target)
  ) {
    cursoMenuOpen.value = false
  }
}

function toggleCursoMenu() {
  cursoMenuOpen.value = !cursoMenuOpen.value
}

async function seleccionarCurso(curso) {
  if (curso) {
    cursoActivoId.value = curso.id
    cursoStore.setCurso({
      id: curso.id,
      nombre: curso.nombre,
      descripcion: curso.descripcion || ''
    })
  } else {
    cursoActivoId.value = null
    cursoStore.clearCurso()
  }

  cursoMenuOpen.value = false
  await loadDashboard()
}

function estadoLabel(estado) {
  return { completado: 'Calificado', pendiente: 'Pendiente', procesando: 'Procesando', error: 'Error' }[estado] || estado
}

function badgeClass(estado) {
  return {
    completado: 'badge-success',
    pendiente:  'badge-warning',
    procesando: 'badge-info',
    error:      'badge-error',
  }[estado] || ''
}

function cerrarModalCurso() {
  showCrearCurso.value = false
  errorCurso.value = ''
  nuevoCurso.value = { nombre: '', descripcion: '' }
}

function irAHistorial(id) {
  cursoMenuOpen.value = false
  router.push(`/historial/${id}`)
}

// ── Métodos ───────────────────────────────────────────────────────────────────

async function loadDashboard() {
  loadingStats.value = true
  errorStats.value = null

  try {
    statsData.value = await getDashboardStats(cursoActivoId.value)
  } catch (e) {
    errorStats.value = e.message || 'No se pudieron cargar las estadísticas del dashboard'
  } finally {
    loadingStats.value = false
  }
}

async function loadCursos() {
  try {
    const data = await getCursos()          // getCursos() de useApi.js existente
    cursos.value = data.cursos || []
  } catch {
    // silencioso: el selector quedará vacío, no es crítico
  }
}

async function onCursoChange() {
  const curso = cursos.value.find(c => c.id === cursoActivoId.value) || null
  // setCurso espera un objeto { id, nombre, descripcion }  según tu cursoStore
  if (curso) {
    cursoStore.setCurso({ id: curso.id, nombre: curso.nombre, descripcion: curso.descripcion || '' })
  } else {
    cursoStore.clearCurso()
  }
  await loadDashboard()
}

async function handleCrearCurso() {
  errorCurso.value = ''
  if (!nuevoCurso.value.nombre.trim()) {
    errorCurso.value = 'El nombre es obligatorio.'
    return
  }
  creandoCurso.value = true
  try {
    // crearCursoApi(payload) de useApi.js existente
    const data = await crearCursoApi({
      nombre:      nuevoCurso.value.nombre.trim(),
      descripcion: nuevoCurso.value.descripcion.trim() || null,
    })
    const cursoNuevo = data.curso
    cursos.value.push(cursoNuevo)
    cursoActivoId.value = cursoNuevo.id
    cursoStore.setCurso({ id: cursoNuevo.id, nombre: cursoNuevo.nombre, descripcion: cursoNuevo.descripcion || '' })
    cerrarModalCurso()
    await loadDashboard()
  } catch (e) {
    errorCurso.value = e.message
  } finally {
    creandoCurso.value = false
  }
}

async function handleCheckHealth() {
  checkingHealth.value = true
  try {
    const data = await checkHealth()        // checkHealth() de useApi.js existente
    healthResult.value = { ok: true, version: data.version, model: data.model || null }
  } catch (e) {
    healthResult.value = { ok: false, error: e.message }
  } finally {
    checkingHealth.value = false
  }
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────
onMounted(async () => {
  cursoStore.restoreFromStorage()
  cursoActivoId.value = cursoStore.cursoId || null

  document.addEventListener('click', cerrarCursoMenuSiClickAfuera)

  await Promise.all([loadCursos(), loadDashboard()])
})
onBeforeUnmount(() => {
  document.removeEventListener('click', cerrarCursoMenuSiClickAfuera)
})
</script>