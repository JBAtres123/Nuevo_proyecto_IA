<template>
  <div class="max-w-7xl mx-auto px-4 xl:px-6 py-4 animate-fade-in h-[calc(100vh-72px)] overflow-hidden text-surface-text dark:text-surface-textDark">
    <!-- Header -->
    <div class="mb-4 flex items-center justify-between gap-4">
      <div>
        <h1 class="font-display text-3xl text-surface-text dark:text-white mb-1">
          Calificar Exámenes
        </h1>
        <p class="text-surface-muted dark:text-surface-mutedDark text-xs">
          Sube imágenes o PDFs — califica uno o varios exámenes a la vez.
        </p>
      </div>

      <div class="hidden lg:flex items-center gap-2 text-xs text-surface-muted dark:text-surface-mutedDark">
        <span class="badge badge-info">{{ form.punteoMaximo }} pts</span>
        <span class="badge badge-muted">{{ form.cantidadSeries }} serie(s)</span>
      </div>
    </div>

    <!-- ── PASO 1: Subida de archivos ── -->
    <div
      v-if="paso === 1"
      class="grid grid-cols-1 xl:grid-cols-12 gap-4 h-[calc(100%-58px)] overflow-hidden"
    >
      <!-- LEFT: Archivos + Config -->
      <div class="xl:col-span-8 space-y-4 overflow-y-auto pr-1 custom-scroll">
        <!-- Drop zone -->
        <div class="card p-4">
          <h2 class="font-semibold text-surface-text dark:text-surface-textDark mb-3 flex items-center gap-2">
            <SvgIcon
              name="paperclip"
              class="w-4 h-4 text-brand-700 dark:text-brand-300"
            />

            Archivos del Examen

            <span class="ml-auto text-xs text-surface-muted dark:text-surface-mutedDark">
              {{ archivos.length }} archivo(s)
            </span>
          </h2>

          <div
            class="border-2 border-dashed rounded-xl p-4 text-center transition-colors duration-200 cursor-pointer"
            :class="dragOver
              ? 'border-brand-400 bg-brand-500/10'
              : 'border-surface-border dark:border-surface-borderDark hover:border-brand-300/50'"
            @dragover.prevent="dragOver = true"
            @dragleave="dragOver = false"
            @drop.prevent="onDrop"
            @click="fileInputRef?.click()"
          >
            <input
              ref="fileInputRef"
              type="file"
              multiple
              accept=".jpg,.jpeg,.png,.webp,.pdf"
              class="hidden"
              @change="onFileInput"
            />

            <div v-if="!archivos.length" class="space-y-1">
              <SvgIcon name="folder" class="w-8 h-8 mx-auto text-surface-muted dark:text-surface-mutedDark" />
              <p class="text-surface-text dark:text-surface-textDark font-medium text-sm">
                Arrastra archivos aquí
              </p>
              <p class="text-surface-muted dark:text-surface-mutedDark text-xs">
                JPG · PNG · WEBP · PDF
              </p>
              <p class="text-surface-muted/80 dark:text-surface-mutedDark/80 text-xs">
                Puedes subir frente y dorso, múltiples exámenes o PDFs completos.
              </p>
            </div>

            <!-- Preview de archivos -->
            <div v-else class="grid grid-cols-3 sm:grid-cols-5 lg:grid-cols-6 gap-2">
              <div
                v-for="(archivo, i) in archivos"
                :key="i"
                class="relative group"
              >
                <!-- Preview imagen -->
                <img
                  v-if="archivo.tipo === 'imagen'"
                  :src="archivo.preview"
                  class="w-full h-16 object-cover rounded-lg border border-surface-border"
                />

                <!-- Icono PDF -->
                <div
                  v-else
                  class="w-full h-16 rounded-lg border border-surface-border dark:border-surface-borderDark bg-surface-tag dark:bg-surface-tagDark flex flex-col items-center justify-center gap-1"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke-width="1.5"
                    stroke="currentColor"
                    class="w-6 h-6 text-red-400"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5
                         A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25
                         m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25
                         c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504
                         1.125-1.125V11.25a9 9 0 0 0-9-9Z"
                    />
                  </svg>

                  <span class="text-[10px] text-surface-muted dark:text-surface-mutedDark truncate w-full text-center px-1">
                    {{ archivo.nombre }}
                  </span>
                </div>

                <!-- Overlay con nro y botón quitar -->
                <div
                  class="absolute inset-0 bg-black/60 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2"
                >
                  <span class="text-white text-xs font-medium">
                    {{ i + 1 }}
                  </span>

                  <button
                    @click.stop="quitarArchivo(i)"
                    class="text-red-400 hover:text-red-300 text-xs border border-red-400/30 rounded px-1.5 py-0.5"
                  >
                    <SvgIcon name="x" class="w-3 h-3" />
                  </button>
                </div>
              </div>

              <!-- Botón agregar más -->
              <div
                class="h-16 border-2 border-dashed border-surface-border dark:border-surface-borderDark rounded-lg flex items-center justify-center text-surface-muted dark:text-surface-mutedDark hover:border-brand-500 hover:text-brand-400 transition-colors cursor-pointer"
                @click.stop="fileInputRef?.click()"
              >
                <span class="text-2xl">+</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Configuración del lote -->
        <div class="card p-4 space-y-4">
          <h2 class="font-semibold text-surface-text dark:text-surface-textDark flex items-center gap-2">
            <SvgIcon
              name="settings"
              class="w-4 h-4 text-brand-700 dark:text-brand-300"
            />

            Configuración del Examen
          </h2>

          <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <!-- Número de exámenes en el lote -->
            <div>
              <label class="text-xs text-surface-muted dark:text-surface-mutedDark mb-1.5 block">
                ¿Cuántos exámenes hay en los archivos?
              </label>

              <div class="flex items-center gap-3">
                <button
                  @click="form.examenesEnLote = Math.max(1, form.examenesEnLote - 1)"
                  class="w-8 h-8 rounded-lg border border-surface-border dark:border-surface-borderDark text-surface-muted dark:text-surface-mutedDark hover:text-surface-text dark:hover:text-white hover:border-brand-300/50 flex items-center justify-center transition-colors"
                >
                  −
                </button>

                <span class="font-mono text-lg text-surface-text dark:text-white w-8 text-center">
                  {{ form.examenesEnLote }}
                </span>

                <button
                  @click="form.examenesEnLote = Math.min(50, form.examenesEnLote + 1)"
                  class="w-8 h-8 rounded-lg border border-surface-border dark:border-surface-borderDark text-surface-muted dark:text-surface-mutedDark hover:text-surface-text dark:hover:text-white hover:border-brand-300/50 flex items-center justify-center transition-colors"
                >
                  +
                </button>
              </div>

              <p class="text-xs text-surface-muted dark:text-surface-mutedDark mt-1">
                {{ archivos.length }} archivo(s) →
                ~{{ Math.ceil(archivos.length / Math.max(form.examenesEnLote, 1)) }}
                página(s) por examen
              </p>
            </div>

            <!-- Punteo máximo -->
            <div>
              <label class="text-xs text-surface-muted dark:text-surface-mutedDark mb-1.5 block">
                Punteo máximo del examen
              </label>

              <div class="flex flex-wrap gap-1.5">
                <button
                v-for="pts in [10, 15, 20, 25, 30, 50, 100]"
                :key="pts"
                @click="form.punteoMaximo = pts"
                class="
                  h-8 min-w-[44px]
                  px-3
                  rounded-lg
                  text-xs
                  font-mono
                  font-bold
                  border
                  transition-all
                  duration-150
                "
                :class="form.punteoMaximo === pts
                  ? 'bg-brand-600 border-brand-600 text-white shadow-lg scale-105 dark:bg-brand-300 dark:border-brand-300 dark:text-surface-dark'
                  : 'bg-brand-100/70 border-brand-100 text-surface-text hover:bg-brand-200 hover:border-brand-300 dark:bg-surface-tagDark dark:border-surface-borderDark dark:text-surface-mutedDark dark:hover:text-brand-300 dark:hover:border-brand-300/40'"
              >
                {{ pts }}
              </button>
              </div>

              <input
                v-model.number="form.punteoMaximo"
                type="number"
                min="1"
                max="1000"
                class="input mt-2 w-full text-sm"
                placeholder="O escribe un valor personalizado"
              />
            </div>
          </div>

          <!-- Nombres de estudiantes -->
          <div>
            <label class="text-xs text-surface-muted dark:text-surface-mutedDark mb-1.5 flex items-center gap-2">
              Nombres de estudiantes
              <span class="text-surface-muted/80 dark:text-surface-mutedDark/80">(opcional — separados por coma)</span>
            </label>

            <textarea
              v-model="form.nombresEstudiantes"
              rows="1"
              class="input w-full text-sm resize-none"
              :placeholder="form.examenesEnLote === 1
                ? 'Ej: María García (o déjalo vacío para auto-detección)'
                : 'Ej: María García, Carlos López, Ana Pérez...'"
            />

            <p class="text-xs text-surface-muted/80 dark:text-surface-mutedDark/80 mt-1">
              Si no los pones, el ICR los detectará automáticamente del examen.
            </p>
          </div>
        </div>

        <!-- Distribución dinámica por series -->
        <div class="card p-4 space-y-4">
          <!-- Header compacto -->
          <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
            <div>
              <h2 class="font-semibold text-surface-text dark:text-surface-textDark flex items-center gap-2">
                <SvgIcon
                  name="puzzle"
                  class="w-4 h-4 text-brand-700 dark:text-brand-300"
                />

                Distribución por series
              </h2>

              <p class="text-xs text-surface-muted dark:text-surface-mutedDark mt-0.5">
                Define cuántas series tendrá el examen y cuánto vale cada una.
              </p>
            </div>

            <div class="flex items-center gap-3">
              <!-- Cantidad de series -->
              <div class="flex items-center gap-3">
                <button
                  type="button"
                  @click="disminuirSeries"
                  class="w-8 h-8 rounded-lg border border-surface-border dark:border-surface-borderDark text-surface-muted dark:text-surface-mutedDark hover:text-surface-text dark:hover:text-white hover:border-brand-300/50 flex items-center justify-center transition-colors"
                  >
                  −
                </button>

                <span class="font-mono text-lg text-surface-text dark:text-white w-8 text-center">
                  {{ form.cantidadSeries }}
                </span>

                <button
                  type="button"
                  @click="aumentarSeries"
                  class="w-8 h-8 rounded-lg border border-surface-border dark:border-surface-borderDark text-surface-muted dark:text-surface-mutedDark hover:text-surface-text dark:hover:text-white hover:border-brand-300/50 flex items-center justify-center transition-colors"
                  >
                  +
                </button>
              </div>

              <!-- Total -->
              <div
                class="h-8 px-3 rounded-lg border flex items-center gap-2 text-xs font-mono font-bold"
                :class="seriesValidas
                  ? 'border-emerald-500/40 bg-emerald-50 text-emerald-700 dark:border-green-500/30 dark:bg-green-500/10 dark:text-green-300'
                  : 'border-red-500/40 bg-red-50 text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-300'"
              >
                <span>{{ totalSeries }} / {{ form.punteoMaximo }} pts</span>
                <SvgIcon
                  :name="seriesValidas ? 'check' : 'alert'"
                  class="w-4 h-4"
                />
              </div>
            </div>
          </div>

          <!-- Lista de series -->
<div class="grid grid-cols-1 lg:grid-cols-2 gap-3 max-h-[240px] overflow-y-auto pr-1 custom-scroll">
  <div
     v-for="(serie, index) in form.series"
  :key="index"
  class="
    flex flex-col gap-3
  "
  >
    <!-- Encabezado -->
    <div class="flex items-center gap-2">
      <div
        class="
          w-8 h-8
          rounded-lg
          border border-emerald-500/50
          bg-emerald-100
          dark:border-brand-300/40
          dark:bg-brand-300/10
          flex items-center justify-center
          shrink-0
        "
      >
        <span class="font-mono text-xs font-bold text-emerald-700 dark:text-brand-300">
          {{ numeroRomano(index + 1) }}
        </span>
      </div>

      <div class="min-w-0">
        <p class="text-sm font-medium text-surface-text dark:text-surface-textDark truncate">
          Serie {{ numeroRomano(index + 1) }}
        </p>
      </div>
    </div>

    <!-- Campos -->
    <div class="grid grid-cols-1 sm:grid-cols-5 gap-3">
      <div class="sm:col-span-3">
        <label class="text-[11px] text-surface-muted dark:text-surface-mutedDark mb-1 block">
          Nombre de la serie
        </label>

        <input
          v-model="serie.nombre"
          type="text"
          class="input w-full text-sm"
          :placeholder="`Serie ${numeroRomano(index + 1)}`"
        />
      </div>

      <div class="sm:col-span-2">
        <label class="text-[11px] text-surface-muted dark:text-surface-mutedDark mb-1 block">
          Punteo
        </label>

        <div class="relative">
          <input
            v-model.number="serie.valor"
            type="number"
            min="0"
            step="0.5"
            class="input w-full text-sm pr-10"
            placeholder="5"
          />

          <span
            class="
              absolute right-3 top-1/2 -translate-y-1/2
              text-xs text-surface-muted dark:text-surface-mutedDark
              pointer-events-none
            "
          >
            pts
          </span>
        </div>
      </div>
    </div>
  </div>
</div>
          <!-- Aviso compacto -->
          <div
            class="rounded-lg border px-3 py-2 text-xs font-medium flex items-center gap-2"
            :class="seriesValidas
              ? 'border-emerald-500/40 bg-emerald-50 text-emerald-700 dark:border-green-500/20 dark:bg-green-500/5 dark:text-green-300'
              : 'border-orange-500/40 bg-orange-50 text-orange-700 dark:border-orange-500/20 dark:bg-orange-500/5 dark:text-orange-300'"
          >
            <SvgIcon
              :name="seriesValidas ? 'checkCircle' : 'warning'"
              class="w-4 h-4 shrink-0"
            />

            <p class="truncate">
              <template v-if="seriesValidas">
                La distribución coincide con el punteo máximo.
              </template>

              <template v-else>
                La suma actual es {{ totalSeries }} pts. Debe sumar {{ form.punteoMaximo }} pts.
              </template>
            </p>
          </div>
        </div>

        <!-- Nivel de exigencia -->
        <div class="card p-4">
          <h2 class="font-medium text-surface-text dark:text-surface-textDark mb-3 flex items-center gap-2">
            <SvgIcon name="scale" class="w-4 h-4 text-surface-muted dark:text-surface-mutedDark" />
            Nivel de Exigencia

            <span class="ml-auto badge badge-info font-mono font-bold">
              {{ nivelLocal }}/10
            </span>
          </h2>

          <div class="slider-container mb-2">
            <input
              type="range"
              min="1"
              max="10"
              v-model.number="nivelLocal"
              class="w-full"
              :style="`--progress: ${(nivelLocal - 1) / 9 * 100}%`"
            />
          </div>

          <div class="flex justify-between text-[11px] text-surface-muted dark:text-surface-mutedDark mb-2 px-0.5">
            <span class="inline-flex items-center gap-1"><SvgIcon name="smile" class="w-3.5 h-3.5" /> Amigo</span>
            <span class="inline-flex items-center gap-1"><SvgIcon name="scale" class="w-3.5 h-3.5" /> Balanceado</span>
            <span class="inline-flex items-center gap-1"><SvgIcon name="microscope" class="w-3.5 h-3.5" /> Experto</span>
          </div>

          <div class="grid grid-cols-10 gap-1">
            <button
              v-for="n in 10"
              :key="n"
              @click="nivelLocal = n"
              class="h-7 rounded-lg text-xs font-mono font-bold transition-all duration-150"
              :class="n === nivelLocal
                ? 'text-white shadow-lg scale-110 ' + nivelBgClass(n)
                : 'bg-surface-tag dark:bg-surface-tagDark text-surface-muted dark:text-surface-mutedDark hover:bg-surface-border dark:hover:bg-surface-borderDark'"
            >
              {{ n }}
            </button>
          </div>

          <div class="mt-3 p-2.5 rounded-xl text-xs flex items-center gap-2" :class="nivelDescStyle">
            <SvgIcon :name="nivelDescIcon" class="w-4 h-4 shrink-0" />
            <span>{{ nivelDescText }}</span>
          </div>
        </div>
      </div>

      <!-- RIGHT: Resumen + Submit -->
      <div class="xl:col-span-4 space-y-4 overflow-y-auto pr-1 custom-scroll">
        <!-- Resumen -->
        <div class="card p-4">
          <h3 class="font-medium text-surface-text dark:text-surface-textDark mb-3">
            Resumen del lote
          </h3>

          <div class="space-y-2.5 text-sm">
            <div class="flex justify-between">
              <span class="text-surface-text dark:text-surface-textDark">Archivos</span>
              <span
                class="font-mono"
                :class="archivos.length ? 'text-green-600 dark:text-green-400' : 'text-surface-muted dark:text-surface-mutedDark'"
              >
                {{ archivos.length || '—' }}
              </span>
            </div>

            <div class="flex justify-between">
              <span class="text-surface-text dark:text-surface-textDark">Exámenes</span>
              <span class="font-mono text-brand-300">
                {{ form.examenesEnLote }}
              </span>
            </div>

            <div class="flex justify-between">
              <span class="text-surface-text dark:text-surface-textDark">Punteo máx.</span>
              <span class="font-mono text-surface-text dark:text-white">
                {{ form.punteoMaximo }} pts
              </span>
            </div>

            <div class="flex justify-between">
              <span class="text-surface-text dark:text-surface-textDark">Series</span>
              <span class="font-mono text-brand-300">
                {{ form.cantidadSeries }}
              </span>
            </div>

            <div class="flex justify-between">
              <span class="text-surface-text dark:text-surface-textDark">Exigencia</span>
              <span class="badge badge-info text-xs">
                {{ store.nivelLabels[nivelLocal] }}
              </span>
            </div>

            <div class="border-t border-surface-border pt-3 text-xs text-surface-text dark:text-surface-textDark space-y-1">
              <div class="flex justify-between">
                <span>Curso activo</span>
                <span class="text-brand-300 truncate ml-2 max-w-[140px]">
                  {{ cursoStore.cursoNombre || '—' }}
                </span>
              </div>

              <div class="flex justify-between">
                <span>Agentes IA</span>
                <span>3 (consenso)</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Agentes -->
<div class="card p-4 space-y-3">
  <h3 class="font-semibold text-surface-text dark:text-surface-textDark text-sm">
    Flujo de Agentes
  </h3>

  <div
    v-for="agent in agentFlow"
    :key="agent.id"
    class="flex items-start gap-3"
  >
    <div
      class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
      :class="agent.color"
    >
      <SvgIcon
        v-if="agent.icon"
        :name="agent.icon"
        class="w-4 h-4"
      />

      <span v-else>{{ agent.id }}</span>
    </div>

    <div>
      <p class="text-xs font-semibold text-surface-text dark:text-surface-textDark">
        {{ agent.name }}
      </p>

      <p class="text-xs text-surface-text/80 dark:text-surface-mutedDark">
        {{ agent.desc }}
      </p>
    </div>
  </div>
</div>
        <!-- Botón calificar -->
        <button
          @click="iniciarCalificacion"
          :disabled="!archivos.length || cargando || !seriesValidas"
          class="btn-primary w-full justify-center py-3 text-base"
        >
          <span v-if="cargando" class="spinner w-5 h-5"></span>
          <SvgIcon v-else name="rocket" class="w-5 h-5" />

          {{ cargando ? 'Preparando...' : `Calificar ${form.examenesEnLote > 1 ? form.examenesEnLote + ' exámenes' : 'examen'}` }}
        </button>

        <div
          v-if="errorGlobal"
          class="card p-4 border-red-500/30 bg-red-500/5"
        >
          <p class="text-red-400 text-sm">
            <SvgIcon name="xCircle" class="w-4 h-4 inline-block mr-1 align-[-2px]" />
            {{ errorGlobal }}
          </p>
        </div>
      </div>
    </div>

    <!-- ── PASO 2: Progreso de calificación ── -->
    <div v-if="paso === 2" class="space-y-4 h-[calc(100%-58px)] overflow-y-auto custom-scroll pr-1">
      <!-- Header de progreso -->
      <div class="card p-5">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="font-medium text-surface-text dark:text-surface-textDark text-lg">
              Calificando {{ examenesLote.length }}
              {{ examenesLote.length === 1 ? 'examen' : 'exámenes' }}
            </h2>

            <p class="text-surface-muted dark:text-surface-mutedDark text-sm mt-0.5">
              Curso: {{ cursoStore.cursoNombre }} · {{ form.punteoMaximo }} pts · Nivel {{ nivelLocal }}/10
            </p>
          </div>

          <div class="text-right">
            <p class="font-mono text-2xl text-brand-300 font-bold">
              {{ completados }}/{{ examenesLote.length }}
            </p>
            <p class="text-xs text-surface-muted dark:text-surface-mutedDark">
              completados
            </p>
          </div>
        </div>

        <!-- Barra general -->
        <div class="w-full h-2 bg-surface-border rounded-full overflow-hidden">
          <div
            class="h-full bg-gradient-to-r from-brand-600 to-brand-300 rounded-full transition-all duration-500"
            :style="{ width: porcentajeGeneral + '%' }"
          ></div>
        </div>

        <div class="flex justify-between text-xs text-surface-muted dark:text-surface-mutedDark mt-1">
          <span>{{ porcentajeGeneral }}% completado</span>
          <span v-if="hayErrores" class="text-red-400">
            {{ errores }} con error
          </span>
        </div>
      </div>

      <!-- Lista de exámenes con estado individual -->
      <div class="space-y-3">
        <div
          v-for="examen in examenesLote"
          :key="examen.id"
          class="card p-4 transition-all duration-300"
          :class="{
            'border-green-500/30 bg-green-500/5': examen.estado === 'completado',
            'border-red-500/30 bg-red-500/5': examen.estado === 'error',
            'border-brand-300/30': examen.estado === 'procesando',
          }"
        >
          <div class="flex items-center gap-4">
            <!-- Indicador de estado -->
            <div class="shrink-0">
              <!-- Completado -->
              <div
                v-if="examen.estado === 'completado'"
                class="w-10 h-10 rounded-full bg-green-500/20 border border-green-500/40 flex items-center justify-center"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke-width="2.5"
                  stroke="currentColor"
                  class="w-5 h-5 text-green-400"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M4.5 12.75l6 6 9-13.5"
                  />
                </svg>
              </div>

              <!-- Error -->
              <div
                v-else-if="examen.estado === 'error'"
                class="w-10 h-10 rounded-full bg-red-500/20 border border-red-500/40 flex items-center justify-center"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke-width="2"
                  stroke="currentColor"
                  class="w-5 h-5 text-red-400"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </div>

              <!-- Procesando -->
              <div
                v-else-if="examen.estado === 'procesando'"
                class="w-10 h-10 rounded-full bg-brand-300/10 border border-brand-300/30 flex items-center justify-center"
              >
                <span class="spinner w-5 h-5 text-brand-300"></span>
              </div>

              <!-- Pendiente -->
              <div
                v-else
                class="w-10 h-10 rounded-full bg-surface-tag dark:bg-surface-tagDark border border-surface-border dark:border-surface-borderDark flex items-center justify-center"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke-width="1.5"
                  stroke="currentColor"
                  class="w-5 h-5 text-surface-muted dark:text-surface-mutedDark"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M12 6v6l4 2m6-2a10 10 0 1 1-20 0 10 10 0 0 1 20 0Z"
                  />
                </svg>
              </div>
            </div>

            <!-- Info del examen -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <p class="font-medium text-surface-text dark:text-surface-textDark text-sm">
                  {{ examen.nombre_estudiante || `Examen #${examen.id}` }}
                </p>

                <span
                  class="badge text-xs"
                  :class="{
                    'badge-success': examen.estado === 'completado',
                    'badge-danger':  examen.estado === 'error',
                    'badge-info':    examen.estado === 'procesando',
                    'badge-muted':   examen.estado === 'pendiente',
                  }"
                >
                  {{ estadoLabel(examen.estado) }}
                </span>
              </div>

              <p class="text-xs text-surface-muted dark:text-surface-mutedDark mt-0.5">
                {{ examen.imagenes }} página(s) · {{ form.punteoMaximo }} pts máx.
              </p>
            </div>

            <!-- Nota si está completado -->
            <div
              v-if="examen.estado === 'completado'"
              class="text-right shrink-0"
            >
              <p
                class="font-mono text-xl font-bold"
                :class="colorNota(examen.porcentaje)"
              >
                {{ examen.punteo_total?.toFixed(1) }}
              </p>

              <p class="text-xs text-surface-muted dark:text-surface-mutedDark">
                {{ examen.porcentaje?.toFixed(1) }}%
              </p>
            </div>

            <!-- Ver resultado -->
            <RouterLink
              v-if="examen.estado === 'completado'"
              :to="`/historial/${examen.id}`"
              class="shrink-0 w-8 h-8 rounded-lg border border-surface-border dark:border-surface-borderDark text-surface-muted dark:text-surface-mutedDark hover:text-brand-300 hover:border-brand-300/40 transition-colors flex items-center justify-center"
              title="Ver detalle"
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
                  d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6z
                     M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"
                />
              </svg>
            </RouterLink>
          </div>
        </div>
      </div>

      <!-- Botones finales -->
      <div class="flex gap-3 flex-wrap">
        <button
          v-if="todoTerminado"
          @click="reiniciar"
          class="btn-primary flex items-center gap-2"
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
              d="M12 4v1m0 14v1m8-8h-1M5 12H4m13.66-5.66-.71.71
                 M7.05 16.95l-.71.71M18.36 18.36l-.71-.71M7.05 7.05l-.71-.71"
            />
          </svg>

          Calificar más exámenes
        </button>

        <RouterLink
          v-if="todoTerminado"
          to="/historial"
          class="btn-secondary flex items-center gap-2"
        >
          Ver historial completo →
        </RouterLink>

        <div
          v-if="!todoTerminado"
          class="text-sm text-surface-muted dark:text-surface-mutedDark flex items-center gap-2"
        >
          <span class="spinner w-4 h-4"></span>
          Procesando... no cierres esta página
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted, h } from 'vue'
import { RouterLink } from 'vue-router'
import { useAppStore } from '@/stores/appStore'
import { useCursoStore } from '@/stores/cursoStore'
import { uploadExam, processExam } from '@/composables/useApi'
import axios from 'axios'

const iconPaths = {
  paperclip: {
    viewBox: '0 0 24 24',
    strokeWidth: 1.8,
    paths: ['M16.5 6.75 8.1 15.15a3 3 0 1 0 4.24 4.24l8.13-8.13a5 5 0 0 0-7.07-7.07L5.1 12.49a7 7 0 0 0 9.9 9.9l7.43-7.43'],
  },
  folder: {
    viewBox: '0 0 24 24',
    strokeWidth: 1.6,
    paths: ['M3.75 6.75A2.25 2.25 0 0 1 6 4.5h4.1c.6 0 1.17.24 1.59.66l1.15 1.09H18A2.25 2.25 0 0 1 20.25 8.5v8.75A2.25 2.25 0 0 1 18 19.5H6a2.25 2.25 0 0 1-2.25-2.25V6.75Z'],
  },
  settings: {
    viewBox: '0 0 24 24',
    strokeWidth: 1.7,
    paths: ['M10.3 4.4c.44-1.8 2.96-1.8 3.4 0 .28 1.14 1.57 1.68 2.58 1.07 1.6-.96 3.38.82 2.42 2.42-.61 1.01-.07 2.3 1.07 2.58 1.8.44 1.8 2.96 0 3.4-1.14.28-1.68 1.57-1.07 2.58.96 1.6-.82 3.38-2.42 2.42-1.01-.61-2.3-.07-2.58 1.07-.44 1.8-2.96 1.8-3.4 0-.28-1.14-1.57-1.68-2.58-1.07-1.6.96-3.38-.82-2.42-2.42.61-1.01.07-2.3-1.07-2.58-1.8-.44-1.8-2.96 0-3.4 1.14-.28 1.68-1.57 1.07-2.58-.96-1.6.82-3.38 2.42-2.42 1.01.61 2.3.07 2.58-1.07Z', 'M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z'],
  },
  puzzle: {
    viewBox: '0 0 24 24',
    strokeWidth: 1.7,
    paths: ['M8.25 4.5h3a2.25 2.25 0 0 1 2.25 2.25v.25a1.75 1.75 0 1 0 3.5 0v-.25h.25A2.25 2.25 0 0 1 19.5 9v3.25h-.25a1.75 1.75 0 1 0 0 3.5h.25V18A2.25 2.25 0 0 1 17.25 20.25H14v-.25a1.75 1.75 0 1 0-3.5 0v.25H6.75A2.25 2.25 0 0 1 4.5 18v-3.25h.25a1.75 1.75 0 1 0 0-3.5H4.5V6.75A2.25 2.25 0 0 1 6.75 4.5h1.5Z'],
  },
  check: {
    viewBox: '0 0 24 24',
    strokeWidth: 2.4,
    paths: ['M4.5 12.75l6 6 9-13.5'],
  },
  alert: {
    viewBox: '0 0 24 24',
    strokeWidth: 2.2,
    paths: ['M12 7.5v6', 'M12 17.25h.01'],
  },
  checkCircle: {
    viewBox: '0 0 24 24',
    strokeWidth: 1.8,
    paths: ['M9 12.75 11.25 15 15.75 9.75', 'M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z'],
  },
  warning: {
    viewBox: '0 0 24 24',
    strokeWidth: 1.8,
    paths: ['M12 9v4', 'M12 17h.01', 'M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z'],
  },
  scale: {
    viewBox: '0 0 24 24',
    strokeWidth: 1.7,
    paths: ['M12 3v18', 'M5 6h14', 'M6 6l-3 6h6L6 6Z', 'M18 6l-3 6h6l-3-6Z', 'M8 21h8'],
  },
  smile: {
    viewBox: '0 0 24 24',
    strokeWidth: 1.8,
    paths: ['M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z', 'M9 10h.01', 'M15 10h.01', 'M8.5 14.5c1.8 2 5.2 2 7 0'],
  },
  microscope: {
    viewBox: '0 0 24 24',
    strokeWidth: 1.7,
    paths: ['M9.5 3.75h4.25v3H9.5v-3Z', 'M10.5 6.75 8 13a3.75 3.75 0 0 0 7.5 0l-2.5-6.25', 'M12 16.75V20', 'M6 20h12', 'M15.5 11.5h2.25A2.25 2.25 0 0 1 20 13.75V20'],
  },
  rocket: {
    viewBox: '0 0 24 24',
    strokeWidth: 1.7,
    paths: ['M14.5 4.5c2.2-.9 4.1-.95 5-.75.2.9.15 2.8-.75 5-1.1 2.7-3.4 5.6-7.25 8.25L7 12.5c2.65-3.85 5.3-6.9 7.5-8Z', 'M9 15l-2 2H4.5v-2.5l2-2', 'M12 18l-2 2v1.5h2.5l2-2', 'M15.5 8.5h.01'],
  },
  x: {
    viewBox: '0 0 24 24',
    strokeWidth: 2,
    paths: ['M6 18L18 6M6 6l12 12'],
  },
  xCircle: {
    viewBox: '0 0 24 24',
    strokeWidth: 1.8,
    paths: ['M15 9l-6 6', 'M9 9l6 6', 'M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z'],
  },
  target: {
    viewBox: '0 0 24 24',
    strokeWidth: 1.7,
    paths: ['M12 21a9 9 0 1 1 9-9', 'M12 17a5 5 0 1 1 5-5', 'M12 13a1 1 0 1 1 1-1', 'M19 5v4h-4', 'M19 5l-7 7'],
  },
}

const SvgIcon = {
  name: 'SvgIcon',
  props: {
    name: {
      type: String,
      required: true,
    },
  },
  setup(props, { attrs }) {
    return () => {
      const icon = iconPaths[props.name] || iconPaths.alert

      return h(
        'svg',
        {
          ...attrs,
          xmlns: 'http://www.w3.org/2000/svg',
          fill: 'none',
          viewBox: icon.viewBox,
          stroke: 'currentColor',
          'stroke-width': icon.strokeWidth,
          'aria-hidden': 'true',
        },
        icon.paths.map(path => h('path', {
          'stroke-linecap': 'round',
          'stroke-linejoin': 'round',
          d: path,
        }))
      )
    }
  },
}

const store = useAppStore()
const cursoStore = useCursoStore()

// ── Estado general ────────────────────────────────────────────────────────────
const paso         = ref(1)   // 1 = subida, 2 = progreso
const fileInputRef = ref(null)
const dragOver     = ref(false)
const archivos     = ref([])   // { file, preview, nombre, tipo }
const cargando     = ref(false)
const errorGlobal  = ref('')
const nivelLocal   = ref(store.nivelExigencia)

const form = ref({
  examenesEnLote: 1,
  punteoMaximo: 20,
  nombresEstudiantes: '',
  cantidadSeries: 1,
  series: [
    { nombre: 'Serie I', valor: 20 },
  ],
})

// ── Exámenes en proceso ───────────────────────────────────────────────────────
const examenesLote = ref([])   // lista de exámenes con su estado
let pollingTimer   = null

// ── Computed ──────────────────────────────────────────────────────────────────
const completados       = computed(() => examenesLote.value.filter(e => e.estado === 'completado').length)
const errores           = computed(() => examenesLote.value.filter(e => e.estado === 'error').length)
const hayErrores        = computed(() => errores.value > 0)
const todoTerminado     = computed(() =>
  examenesLote.value.length > 0 &&
  examenesLote.value.every(e => ['completado', 'error'].includes(e.estado))
)
const porcentajeGeneral = computed(() => {
  if (!examenesLote.value.length) return 0
  return Math.round((completados.value + errores.value) / examenesLote.value.length * 100)
})

function numeroRomano(num) {
  const romanos = [
    'I', 'II', 'III', 'IV', 'V',
    'VI', 'VII', 'VIII', 'IX', 'X',
    'XI', 'XII', 'XIII', 'XIV', 'XV',
  ]

  return romanos[num - 1] || num
}

function generarSeries(cantidad) {
  const nuevasSeries = []

  for (let i = 1; i <= cantidad; i++) {
    nuevasSeries.push({
      nombre: `Serie ${numeroRomano(i)}`,
      valor: form.value.series[i - 1]?.valor || 0,
    })
  }

  form.value.series = nuevasSeries
}

function aumentarSeries() {
  if (form.value.cantidadSeries >= 15) return

  form.value.cantidadSeries++

  form.value.series.push({
    nombre: `Serie ${numeroRomano(form.value.cantidadSeries)}`,
    valor: 0,
  })
}

function disminuirSeries() {
  if (form.value.cantidadSeries <= 1) return

  form.value.cantidadSeries--
  form.value.series.pop()
}

const totalSeries = computed(() => {
  return (form.value.series || []).reduce((total, serie) => {
    return total + Number(serie.valor || 0)
  }, 0)
})

const seriesValidas = computed(() => {
  return Number(totalSeries.value) === Number(form.value.punteoMaximo)
})

watch(() => store.nivelExigencia, v => { nivelLocal.value = v })
watch(nivelLocal, v => store.updateNivel(v))
watch(todoTerminado, (val) => { if (val) detenerPolling() })

// ── Manejo de archivos ────────────────────────────────────────────────────────
const TIPOS_IMAGEN = ['image/jpeg', 'image/png', 'image/webp', 'image/bmp']

function esImagen(file) { return TIPOS_IMAGEN.includes(file.type) }
function esPDF(file)    { return file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf') }

function onDrop(e) {
  dragOver.value = false
  agregarArchivos([...e.dataTransfer.files])
}
function onFileInput(e) {
  agregarArchivos([...e.target.files])
  e.target.value = ''
}

function agregarArchivos(files) {
  for (const file of files) {
    if (!esImagen(file) && !esPDF(file)) continue
    archivos.value.push({
      file,
      nombre: file.name,
      tipo:   esImagen(file) ? 'imagen' : 'pdf',
      preview: esImagen(file) ? URL.createObjectURL(file) : null,
    })
  }
}

function quitarArchivo(i) {
  const a = archivos.value[i]
  if (a.preview) URL.revokeObjectURL(a.preview)
  archivos.value.splice(i, 1)
}

// ── Iniciar calificación ──────────────────────────────────────────────────────
async function iniciarCalificacion() {
  if (!archivos.value.length) return
  cargando.value  = true
  errorGlobal.value = ''

  try {
    const fd = new FormData()

    // Archivos
    archivos.value.forEach(a => fd.append('archivos', a.file, a.nombre))

    // Parámetros
    fd.append('nivel_exigencia',      nivelLocal.value)
    fd.append('punteo_maximo',        form.value.punteoMaximo)
    fd.append('examenes_en_lote',     form.value.examenesEnLote)
    fd.append('curso_id',             cursoStore.cursoId)
    fd.append('distribucion_series', JSON.stringify(form.value.series || []))
    if (form.value.nombresEstudiantes.trim()) {
      fd.append('nombres_estudiantes', form.value.nombresEstudiantes.trim())
    }

    // Upload
    const token = localStorage.getItem('token')
    const { data: uploadData } = await axios.post('/api/upload', fd, {
      headers: { Authorization: `Bearer ${token}` },
    })

    // Inicializar lista de exámenes para el paso 2
    examenesLote.value = uploadData.examenes.map(e => ({
      id:               e.examen_id,
      nombre_estudiante: e.nombre_estudiante,
      imagenes:          e.imagenes,
      estado:           'pendiente',
      porcentaje:       null,
      punteo_total:     null,
    }))

    // Iniciar procesamiento de todos
    const ids = uploadData.examenes.map(e => e.examen_id)
    await axios.post('/api/process/lote', ids, {
      headers: {
        Authorization:  `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    })

    // Cambiar al paso 2 y empezar polling
    paso.value = 2
    iniciarPolling(ids)

  } catch (err) {
    errorGlobal.value = err.response?.data?.detail ?? err.message ?? 'Error al subir archivos.'
  } finally {
    cargando.value = false
  }
}

// ── Polling de estado ─────────────────────────────────────────────────────────
function iniciarPolling(ids) {
  detenerPolling()
  pollingTimer = setInterval(() => actualizarEstados(ids), 3000)
}

function detenerPolling() {
  if (pollingTimer) { clearInterval(pollingTimer); pollingTimer = null }
}

async function actualizarEstados(ids) {
  try {
    const token = localStorage.getItem('token')
    const { data } = await axios.get('/api/process/estado', {
      params:  { ids: ids.join(',') },
      headers: { Authorization: `Bearer ${token}` },
    })
    for (const actualizado of data.examenes) {
      const local = examenesLote.value.find(e => e.id === actualizado.id)
      if (local) Object.assign(local, actualizado)
    }
  } catch { /* silencioso */ }
}

// ── Reiniciar ─────────────────────────────────────────────────────────────────
function reiniciar() {
  archivos.value.forEach(a => { if (a.preview) URL.revokeObjectURL(a.preview) })
  archivos.value   = []
  examenesLote.value = []
  errorGlobal.value  = ''
  form.value = {
    examenesEnLote: 1,
    punteoMaximo: 20,
    nombresEstudiantes: '',
    cantidadSeries: 1,
    series: [
      { nombre: 'Serie I', valor: 20 },
    ],
  }
  paso.value = 1
}

// ── Helpers de UI ─────────────────────────────────────────────────────────────

function estadoLabel(estado) {
  return {
    completado: 'Calificado',
    pendiente:  'Pendiente',
    procesando: 'Calificando...',
    error:      'Error',
  }[estado] || estado
}

function colorNota(pct) {
  if (pct == null) return 'text-surface-muted dark:text-surface-mutedDark'
  if (pct >= 75)   return 'text-green-400'
  if (pct >= 60)   return 'text-brand-300'
  if (pct >= 40)   return 'text-orange-400'
  return 'text-red-400'
}

function nivelBgClass(n) {
  if (n <= 3) return 'bg-green-600'
  if (n <= 6) return 'bg-brand-600'
  if (n <= 8) return 'bg-orange-600'
  return 'bg-red-600'
}

const nivelDescText = computed(() => {
  const n = nivelLocal.value
  if (n <= 2) return 'Muy indulgente — valora el esfuerzo aunque haya errores.'
  if (n <= 4) return 'Comprensivo — da crédito por procedimientos parcialmente correctos.'
  if (n <= 6) return 'Balanceado — evalúa resultado y proceso objetivamente.'
  if (n <= 8) return 'Estricto — penaliza errores de signos y procedimientos incompletos.'
  return 'Experto — evaluación académica máxima. Solo puntaje completo si todo es correcto.'
})

const nivelDescIcon = computed(() => {
  const n = nivelLocal.value
  if (n <= 4) return 'smile'
  if (n <= 6) return 'scale'
  if (n <= 8) return 'target'
  return 'microscope'
})

const nivelDescStyle = computed(() => {
  const n = nivelLocal.value

  if (n <= 2) {
    return `
      bg-green-50 text-green-700 border border-green-500/40
      dark:bg-green-500/10 dark:text-green-300 dark:border-green-500/20
    `
  }

  if (n <= 4) {
    return `
      bg-teal-50 text-teal-700 border border-teal-500/40
      dark:bg-teal-500/10 dark:text-teal-300 dark:border-teal-500/20
    `
  }

  if (n <= 6) {
    return `
      bg-brand-50 text-brand-700 border border-brand-500/40
      dark:bg-brand-500/10 dark:text-brand-300 dark:border-brand-500/20
    `
  }

  if (n <= 8) {
    return `
      bg-orange-50 text-orange-700 border border-orange-500/40
      dark:bg-orange-500/10 dark:text-orange-300 dark:border-orange-500/20
    `
  }

  return `
    bg-red-50 text-red-700 border border-red-500/40
    dark:bg-red-500/10 dark:text-red-300 dark:border-red-500/20
  `
})

const agentFlow = [
  { id: 'A', name: 'Calificador A', desc: 'Evaluación independiente (Flash)',   color: 'bg-blue-500/20 text-blue-300 border border-blue-500/30' },
  { id: 'B', name: 'Calificador B', desc: 'Evaluación independiente (Pro)',     color: 'bg-purple-500/20 text-purple-300 border border-purple-500/30' },
  { id: 'J', icon: 'scale', name: 'Juez/Supervisor', desc: 'Consenso y justificación final', color: 'bg-amber-500/20 text-amber-300 border border-amber-500/30' },
]

// ── Cleanup ───────────────────────────────────────────────────────────────────
onUnmounted(() => {
  detenerPolling()
  archivos.value.forEach(a => { if (a.preview) URL.revokeObjectURL(a.preview) })
})
</script>