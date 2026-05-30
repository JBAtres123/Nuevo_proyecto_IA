"""
DeepGrader AI — Capa de base de datos (MySQL via SQLAlchemy async)

Versión corregida para el flujo actual:
- Upload de exámenes y materiales.
- ICR normalizado.
- RAG por docente/curso.
- Consenso con 3 agentes.
- Reprocesamiento seguro.
"""

from __future__ import annotations

from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    DECIMAL,
    Enum,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    text,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship

from config import get_settings

settings = get_settings()

# ─────────────────────────────────────────────
# Engine / Session
# ─────────────────────────────────────────────

engine = create_async_engine(
    settings.db_url,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependencia de FastAPI para obtener una sesión async.

    Importante:
    - Los endpoints hacen commit explícito.
    - Si ocurre un error, se hace rollback.
    - No se hace commit automático al finalizar un GET.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


# ─────────────────────────────────────────────
# ORM Base
# ─────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ─────────────────────────────────────────────
# Modelos principales
# ─────────────────────────────────────────────

class Docente(Base):
    __tablename__ = "docentes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(200), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    institucion = Column(String(300), nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    nivel_exigencia = Column(SmallInteger, nullable=False, default=5)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    cursos = relationship(
        "Curso",
        back_populates="docente",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    examenes = relationship(
        "Examen",
        back_populates="docente",
        passive_deletes=True,
    )
    materiales = relationship(
        "MaterialCurso",
        back_populates="docente",
        passive_deletes=True,
    )


class Curso(Base):
    __tablename__ = "cursos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    docente_id = Column(
        Integer,
        ForeignKey("docentes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nombre = Column(String(300), nullable=False)
    descripcion = Column(Text, nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    docente = relationship("Docente", back_populates="cursos")
    examenes = relationship(
        "Examen",
        back_populates="curso",
        passive_deletes=True,
    )
    materiales = relationship(
        "MaterialCurso",
        back_populates="curso",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("idx_cursos_docente_activo", "docente_id", "activo"),
    )


class Estudiante(Base):
    __tablename__ = "estudiantes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(200), nullable=False)
    clave = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)

    # Corrección del documento de mejoras:
    # si el FK usa ON DELETE SET NULL, la columna debe aceptar NULL.
    docente_id = Column(
        Integer,
        ForeignKey("docentes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    docente = relationship("Docente")
    examenes = relationship(
        "Examen",
        back_populates="estudiante",
        passive_deletes=True,
    )


class MaterialCurso(Base):
    __tablename__ = "materiales_curso"

    id = Column(Integer, primary_key=True, autoincrement=True)
    docente_id = Column(
        Integer,
        ForeignKey("docentes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    curso_id = Column(
        Integer,
        ForeignKey("cursos.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    nombre_archivo = Column(String(300), nullable=False)
    ruta_almacenamiento = Column(String(500), nullable=False)
    paginas = Column(Integer, nullable=False, default=0)
    chunks_indexados = Column(Integer, nullable=False, default=0)
    estado = Column(
        Enum("pendiente", "indexado", "error", name="estado_material_enum"),
        nullable=False,
        default="pendiente",
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    docente = relationship("Docente", back_populates="materiales")
    curso = relationship("Curso", back_populates="materiales")

    __table_args__ = (
        Index("idx_materiales_docente_curso", "docente_id", "curso_id"),
        Index("idx_materiales_estado", "estado"),
    )


class Examen(Base):
    __tablename__ = "examenes"

    id = Column(Integer, primary_key=True, autoincrement=True)

    docente_id = Column(
        Integer,
        ForeignKey("docentes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    curso_id = Column(
        Integer,
        ForeignKey("cursos.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    estudiante_id = Column(
        Integer,
        ForeignKey("estudiantes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    nombre_estudiante = Column(String(200), nullable=True)
    serie = Column(String(100), nullable=True)

    # Lista de rutas de imágenes generadas/subidas.
    imagenes_rutas = Column(JSON, nullable=False, default=list)

    nivel_exigencia = Column(SmallInteger, nullable=False, default=5)

    estado = Column(
        Enum(
            "pendiente",
            "procesando",
            "completado",
            "error",
            name="estado_examen_enum",
        ),
        nullable=False,
        default="pendiente",
        index=True,
    )

    texto_extraido_icr = Column(Text, nullable=True)

    punteo_total = Column(DECIMAL(8, 2), nullable=True)
    punteo_maximo = Column(DECIMAL(8, 2), nullable=True)
    porcentaje = Column(DECIMAL(5, 2), nullable=True)

    # Ejemplo:
    # [{"nombre":"Serie I","valor":10}, {"nombre":"Serie II","valor":20}]
    distribucion_series = Column(JSON, nullable=True, default=list)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    docente = relationship("Docente", back_populates="examenes")
    curso = relationship("Curso", back_populates="examenes")
    estudiante = relationship("Estudiante", back_populates="examenes")

    preguntas = relationship(
        "PreguntaExtraida",
        back_populates="examen",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    logs = relationship(
        "LogConsenso",
        back_populates="examen",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    calificacion = relationship(
        "CalificacionFinal",
        back_populates="examen",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("idx_examenes_docente_estado", "docente_id", "estado"),
        Index("idx_examenes_docente_curso", "docente_id", "curso_id"),
        Index("idx_examenes_created_at", "created_at"),
    )


class PreguntaExtraida(Base):
    __tablename__ = "preguntas_extraidas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    examen_id = Column(
        Integer,
        ForeignKey("examenes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    numero_pregunta = Column(SmallInteger, nullable=False)
    serie_pregunta = Column(String(100), nullable=True)
    texto_pregunta = Column(Text, nullable=True)
    respuesta_estudiante = Column(Text, nullable=True)
    tiene_latex = Column(Boolean, nullable=False, default=False)
    punteo_maximo = Column(DECIMAL(8, 2), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    examen = relationship("Examen", back_populates="preguntas")

    __table_args__ = (
        Index("idx_preguntas_examen_numero", "examen_id", "numero_pregunta"),
    )


class CalificacionFinal(Base):
    __tablename__ = "calificaciones_finales"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Se mantiene UNIQUE porque debe existir una sola calificación final por examen.
    # El main.py corregido hace upsert manual: actualiza si ya existe.
    examen_id = Column(
        Integer,
        ForeignKey("examenes.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # No se incluye pregunta_id aquí.
    # Esta tabla representa la calificación final del examen completo.
    # El detalle por pregunta se guarda como JSON en justificacion_final.
    punteo_obtenido = Column(DECIMAL(8, 2), nullable=False, default=0)
    punteo_maximo = Column(DECIMAL(8, 2), nullable=False, default=0)

    # En el main.py corregido este campo se guarda con json.dumps(...),
    # no con str(list), para que el frontend pueda parsearlo.
    justificacion_final = Column(Text, nullable=True)

    conclusion_general = Column(Text, nullable=True)
    fortalezas = Column(JSON, nullable=True, default=list)
    debilidades = Column(JSON, nullable=True, default=list)
    sugerencias = Column(JSON, nullable=True, default=list)

    ruta_reporte_pdf = Column(String(500), nullable=True)
    ruta_reporte_word = Column(String(500), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    examen = relationship("Examen", back_populates="calificacion")


class LogConsenso(Base):
    __tablename__ = "logs_consenso"

    id = Column(Integer, primary_key=True, autoincrement=True)
    examen_id = Column(
        Integer,
        ForeignKey("examenes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agente = Column(
        Enum("calificador_a", "calificador_b", "juez", name="agente_consenso_enum"),
        nullable=False,
    )
    modelo_usado = Column(String(100), nullable=False)
    nivel_exigencia = Column(SmallInteger, nullable=True)
    prompt_enviado = Column(Text, nullable=True)
    respuesta_raw = Column(Text, nullable=True)
    respuesta_json = Column(JSON, nullable=True)
    tokens_usados = Column(Integer, nullable=True)
    latencia_ms = Column(Integer, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    examen = relationship("Examen", back_populates="logs")

    __table_args__ = (
        Index("idx_logs_examen_agente", "examen_id", "agente"),
    )


# ─────────────────────────────────────────────
# Migraciones ligeras para desarrollo
# ─────────────────────────────────────────────

async def _column_exists(conn, table_name: str, column_name: str) -> bool:
    """
    Verifica si una columna existe en la base de datos actual.
    Funciona principalmente para MySQL/MariaDB.
    Si falla, retorna True para no romper el arranque.
    """
    try:
        result = await conn.execute(
            text(
                """
                SELECT COUNT(*) AS total
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = :table_name
                  AND COLUMN_NAME = :column_name
                """
            ),
            {"table_name": table_name, "column_name": column_name},
        )
        row = result.mappings().first()
        return bool(row and row["total"] > 0)
    except Exception:
        return True


async def _ensure_column(conn, table_name: str, column_name: str, ddl: str) -> None:
    exists = await _column_exists(conn, table_name, column_name)
    if not exists:
        await conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {ddl}"))


async def _run_light_migrations(conn) -> None:
    """
    create_all() no altera tablas existentes. Estas migraciones ligeras ayudan
    cuando el proyecto ya tenía tablas creadas y se agregaron columnas después.

    Para producción formal, lo ideal es usar Alembic.
    """
    await _ensure_column(
        conn,
        "docentes",
        "nivel_exigencia",
        "nivel_exigencia SMALLINT NOT NULL DEFAULT 5",
    )

    await _ensure_column(
        conn,
        "examenes",
        "curso_id",
        "curso_id INT NULL",
    )

    await _ensure_column(
        conn,
        "examenes",
        "distribucion_series",
        "distribucion_series JSON NULL",
    )

    await _ensure_column(
        conn,
        "preguntas_extraidas",
        "punteo_maximo",
        "punteo_maximo DECIMAL(8,2) NULL",
    )

    await _ensure_column(
        conn,
        "preguntas_extraidas",
        "created_at",
        "created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
    )

    await _ensure_column(
        conn,
        "calificaciones_finales",
        "ruta_reporte_word",
        "ruta_reporte_word VARCHAR(500) NULL",
    )

    await _ensure_column(
        conn,
        "calificaciones_finales",
        "updated_at",
        "updated_at DATETIME NULL",
    )


async def create_tables() -> None:
    """
    Crea las tablas si no existen y aplica migraciones ligeras de desarrollo.

    Nota:
    - Base.metadata.create_all() NO modifica columnas existentes.
    - Para cambios grandes de producción, usa Alembic.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _run_light_migrations(conn)
