-- ============================================================
-- DeepGrader AI — Esquema MySQL corregido
-- Sistema Inteligente Multimodal para Calificación de Exámenes
-- ============================================================

DROP DATABASE IF EXISTS deepgrader_db;

CREATE DATABASE deepgrader_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE deepgrader_db;

-- ============================================================
-- TABLA: docentes
-- ============================================================
CREATE TABLE docentes (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(200) NOT NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    institucion     VARCHAR(300),
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    nivel_exigencia TINYINT UNSIGNED NOT NULL DEFAULT 5,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT chk_docentes_nivel_exigencia
    CHECK (nivel_exigencia BETWEEN 1 AND 10)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- TABLA: cursos
-- Cada docente puede tener varios cursos
-- ============================================================
CREATE TABLE cursos (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    docente_id  INT UNSIGNED NOT NULL,
    nombre      VARCHAR(300) NOT NULL,
    descripcion TEXT,
    activo      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_cursos_docente (docente_id),

    CONSTRAINT fk_cursos_docentes
    FOREIGN KEY (docente_id)
    REFERENCES docentes(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- TABLA: estudiantes
-- ============================================================
CREATE TABLE estudiantes (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    docente_id  INT UNSIGNED NOT NULL,
    curso_id    INT UNSIGNED,
    nombre      VARCHAR(200) NOT NULL,
    clave       VARCHAR(100),
    email       VARCHAR(255),
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_estudiantes_docente (docente_id),
    INDEX idx_estudiantes_curso (curso_id),

    CONSTRAINT fk_estudiantes_docentes
    FOREIGN KEY (docente_id)
    REFERENCES docentes(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

    CONSTRAINT fk_estudiantes_cursos
    FOREIGN KEY (curso_id)
    REFERENCES cursos(id)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- TABLA: materiales_curso
-- Archivos PDF subidos por el docente para RAG
-- ============================================================
CREATE TABLE materiales_curso (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    docente_id          INT UNSIGNED NOT NULL,
    curso_id            INT UNSIGNED NOT NULL,
    nombre_archivo      VARCHAR(300) NOT NULL,
    ruta_almacenamiento VARCHAR(500) NOT NULL,
    paginas             INT UNSIGNED DEFAULT 0,
    chunks_indexados    INT UNSIGNED DEFAULT 0,
    estado              ENUM('pendiente','indexado','error') DEFAULT 'pendiente',
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_materiales_docente (docente_id),
    INDEX idx_materiales_curso (curso_id),
    INDEX idx_materiales_estado (estado),

    CONSTRAINT fk_materiales_docentes
    FOREIGN KEY (docente_id)
    REFERENCES docentes(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

    CONSTRAINT fk_materiales_cursos
    FOREIGN KEY (curso_id)
    REFERENCES cursos(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- TABLA: examenes
-- Metadata de cada examen cargado
-- ============================================================
CREATE TABLE examenes (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    docente_id          INT UNSIGNED NOT NULL,
    curso_id            INT UNSIGNED NOT NULL,
    estudiante_id       INT UNSIGNED,
    nombre_estudiante   VARCHAR(200),
    serie               VARCHAR(100),
    imagenes_rutas      JSON NOT NULL,
    nivel_exigencia     TINYINT UNSIGNED NOT NULL DEFAULT 5,
    estado              ENUM('pendiente','procesando','completado','error') DEFAULT 'pendiente',
    texto_extraido_icr  LONGTEXT,
    punteo_total        DECIMAL(6,2),
    punteo_maximo       DECIMAL(6,2),
    porcentaje          DECIMAL(5,2),
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_examenes_docente (docente_id),
    INDEX idx_examenes_curso (curso_id),
    INDEX idx_examenes_estudiante (estudiante_id),
    INDEX idx_examenes_estado (estado),
    INDEX idx_examenes_created_at (created_at),

    CONSTRAINT fk_examenes_docentes
    FOREIGN KEY (docente_id)
    REFERENCES docentes(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

    CONSTRAINT fk_examenes_cursos
    FOREIGN KEY (curso_id)
    REFERENCES cursos(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

    CONSTRAINT fk_examenes_estudiantes
    FOREIGN KEY (estudiante_id)
    REFERENCES estudiantes(id)
    ON DELETE SET NULL
    ON UPDATE CASCADE,

    CONSTRAINT chk_examenes_nivel_exigencia
    CHECK (nivel_exigencia BETWEEN 1 AND 10),

    CONSTRAINT chk_examenes_porcentaje
    CHECK (porcentaje IS NULL OR porcentaje BETWEEN 0 AND 100)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- TABLA: preguntas_extraidas
-- Cada pregunta/respuesta detectada en el examen
-- ============================================================
CREATE TABLE preguntas_extraidas (
    id                   INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    examen_id            INT UNSIGNED NOT NULL,
    numero_pregunta      SMALLINT UNSIGNED NOT NULL,
    serie_pregunta       VARCHAR(50),
    texto_pregunta       TEXT,
    respuesta_estudiante TEXT,
    tiene_latex          BOOLEAN DEFAULT FALSE,
    punteo_maximo        DECIMAL(5,2),
    created_at           DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_preguntas_examen (examen_id),

    CONSTRAINT fk_preguntas_examenes
    FOREIGN KEY (examen_id)
    REFERENCES examenes(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- TABLA: calificaciones_finales
-- Resultado consolidado del sistema de consenso
-- ============================================================
CREATE TABLE calificaciones_finales (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    examen_id           INT UNSIGNED NOT NULL UNIQUE,
    pregunta_id         INT UNSIGNED,
    punteo_obtenido     DECIMAL(5,2) NOT NULL DEFAULT 0,
    punteo_maximo       DECIMAL(5,2) NOT NULL DEFAULT 0,
    es_correcta         BOOLEAN DEFAULT FALSE,
    justificacion_final TEXT,
    conclusion_general  TEXT,
    fortalezas          JSON,
    debilidades         JSON,
    sugerencias         JSON,
    ruta_reporte_pdf    VARCHAR(500),
    ruta_reporte_word   VARCHAR(500),
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_calificaciones_pregunta (pregunta_id),

    CONSTRAINT fk_calificaciones_examenes
    FOREIGN KEY (examen_id)
    REFERENCES examenes(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

    CONSTRAINT fk_calificaciones_preguntas
    FOREIGN KEY (pregunta_id)
    REFERENCES preguntas_extraidas(id)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- TABLA: logs_consenso
-- Auditoría completa de lo que dijo cada agente
-- ============================================================
CREATE TABLE logs_consenso (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    examen_id       INT UNSIGNED NOT NULL,
    agente          ENUM('calificador_a','calificador_b','juez') NOT NULL,
    modelo_usado    VARCHAR(100) NOT NULL,
    nivel_exigencia TINYINT UNSIGNED,
    prompt_enviado  LONGTEXT,
    respuesta_raw   LONGTEXT,
    respuesta_json  JSON,
    tokens_usados   INT UNSIGNED,
    latencia_ms     INT UNSIGNED,
    error           TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_logs_examen (examen_id),
    INDEX idx_logs_agente (agente),

    CONSTRAINT fk_logs_examenes
    FOREIGN KEY (examen_id)
    REFERENCES examenes(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

    CONSTRAINT chk_logs_nivel_exigencia
    CHECK (nivel_exigencia IS NULL OR nivel_exigencia BETWEEN 1 AND 10)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- VISTA: v_cursos_resumen
-- Resumen para dashboard o pantalla de cursos
-- ============================================================
CREATE OR REPLACE VIEW v_cursos_resumen AS
SELECT
    c.id,
    c.docente_id,
    c.nombre,
    c.descripcion,
    c.activo,
    COUNT(DISTINCT e.id) AS total_examenes,
    COUNT(DISTINCT CASE WHEN e.estado = 'pendiente' THEN e.id END) AS examenes_pendientes,
    COUNT(DISTINCT CASE WHEN e.estado = 'procesando' THEN e.id END) AS examenes_procesando,
    COUNT(DISTINCT CASE WHEN e.estado = 'completado' THEN e.id END) AS examenes_completados,
    COUNT(DISTINCT CASE WHEN e.estado = 'error' THEN e.id END) AS examenes_error,
    COUNT(DISTINCT m.id) AS total_materiales,
    COUNT(DISTINCT CASE WHEN m.estado = 'indexado' THEN m.id END) AS materiales_indexados,
    COALESCE(ROUND(AVG(CASE WHEN e.estado = 'completado' THEN e.porcentaje END), 1), 0) AS promedio_porcentaje,
    c.created_at,
    c.updated_at
FROM cursos c
LEFT JOIN examenes e
    ON e.curso_id = c.id
LEFT JOIN materiales_curso m
    ON m.curso_id = c.id
GROUP BY
    c.id,
    c.docente_id,
    c.nombre,
    c.descripcion,
    c.activo,
    c.created_at,
    c.updated_at;


-- ============================================================
-- CONSULTAS DE VERIFICACIÓN
-- ============================================================

SHOW TABLES;

SELECT
    TABLE_NAME,
    COLUMN_NAME,
    CONSTRAINT_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'deepgrader_db'
  AND REFERENCED_TABLE_NAME IS NOT NULL
ORDER BY TABLE_NAME, COLUMN_NAME;