"""
DeepGrader AI — FastAPI Backend
"""
from __future__ import annotations

import asyncio
import logging
import os
import shutil
import uuid
import jwt
import json
import traceback
import fitz  # pymupdf
from passlib.context import CryptContext
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

# ── Logging persistente ──────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),                          # consola
        logging.FileHandler("backend.log", encoding="utf-8"),  # archivo
    ],
)
logger = logging.getLogger("deepgrader")

from fastapi import (
    BackgroundTasks, Depends, FastAPI, File, Form,
    Header, HTTPException, Query, UploadFile, status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from db.database import (
    CalificacionFinal, Examen, LogConsenso, MaterialCurso,
    PreguntaExtraida, Docente, Curso, create_tables, get_db,
)
from agents.consensus import run_consensus_grading
from services.icr_service import extract_text_from_images
from services.rag_service import rag_service
from services.report_service import generate_pdf_report, generate_word_report

# ─────────────────────────────────────────────
# Configuración
# ─────────────────────────────────────────────

settings = get_settings()
settings.ensure_dirs()

SECRET_KEY = os.getenv("SECRET_KEY", "clave_temporal_deepgrader_ai")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─────────────────────────────────────────────
# Utilidades
# ─────────────────────────────────────────────

def _pdf_to_images(pdf_path: str, output_dir: Path) -> list[str]:
    """Convierte un PDF a imágenes JPG usando PyMuPDF, sin Poppler."""
    paths: list[str] = []
    doc = fitz.open(pdf_path)
    try:
        for i, page in enumerate(doc):
            mat = fitz.Matrix(200 / 72, 200 / 72)  # 200 DPI
            pix = page.get_pixmap(matrix=mat)
            img_path = output_dir / f"page_{i + 1:02d}.jpg"
            pix.save(str(img_path))
            paths.append(str(img_path))
    finally:
        doc.close()
    return paths

# ─────────────────────────────────────────────
# App
# ─────────────────────────────────────────────

app = FastAPI(
    title="DeepGrader AI API",
    description="Sistema Inteligente para Calificación Autónoma de Exámenes",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Limita cuántos exámenes se califican al mismo tiempo.
# Esto evita saturar Groq/ICR/MySQL cuando se procesan lotes grandes.
_lote_semaphore = asyncio.Semaphore(2)

# ─────────────────────────────────────────────
# Startup
# ─────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    await create_tables()

# ─────────────────────────────────────────────
# Schemas Pydantic
# ─────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str

class RegistroDocenteRequest(BaseModel):
    nombre: str
    email: str
    password: str
    institucion: Optional[str] = None
    nivel_exigencia: int = Field(default=5, ge=1, le=10)

class PerfilUpdateRequest(BaseModel):
    nombre: str
    email: str
    institucion: Optional[str] = None
    nivel_exigencia: int = Field(default=5, ge=1, le=10)

class CambiarPasswordRequest(BaseModel):
    actual: str
    nueva: str

class CursoCreateRequest(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class ConfigExigenciaRequest(BaseModel):
    nivel: int = Field(..., ge=1, le=10)
    descripcion: Optional[str] = None

class ConfigExigenciaResponse(BaseModel):
    nivel: int
    descripcion: str
    mensaje: str

# ─────────────────────────────────────────────
# Auth helpers
# ─────────────────────────────────────────────

def crear_token(docente_id: int, email: str) -> str:
    payload = {
        "docente_id": docente_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verificar_password(password_plano: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(password_plano, password_hash)
    except Exception:
        return False


def obtener_docente_id_desde_token(authorization: Optional[str]) -> int:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token no enviado")
    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Formato de token inválido")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload["docente_id"])
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

# ─────────────────────────────────────────────
# Health
# ─────────────────────────────────────────────

@app.get("/api/health", tags=["Sistema"])
async def health():
    return {"status": "ok", "version": "1.0.0", "model": settings.model_calificador_a}

# ─────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────

@app.post("/api/auth/login", tags=["Auth"])
async def login_docente(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Docente).where(Docente.email == body.email))
    docente = result.scalar_one_or_none()

    if not docente:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if hasattr(docente, "activo") and not docente.activo:
        raise HTTPException(status_code=403, detail="Usuario inactivo")
    if not verificar_password(body.password, docente.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    token = crear_token(docente.id, docente.email)
    return {"token": token, "docente_id": docente.id, "nombre": docente.nombre}

@app.post("/api/auth/registro", tags=["Auth"], status_code=status.HTTP_201_CREATED)
async def registrar_docente(
    body: RegistroDocenteRequest,
    db: AsyncSession = Depends(get_db),
):
    nombre = body.nombre.strip()
    email = body.email.strip().lower()
    password = body.password

    if not nombre:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    if not email:
        raise HTTPException(status_code=400, detail="El correo es obligatorio")

    if len(password) < 8:
        raise HTTPException(status_code=400, detail="La contraseña debe tener mínimo 8 caracteres")

    result = await db.execute(
        select(Docente).where(Docente.email == email)
    )
    existente = result.scalar_one_or_none()

    if existente:
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con este correo")

    docente = Docente(
        nombre=nombre,
        email=email,
        password_hash=pwd_context.hash(password),
        institucion=body.institucion.strip() if body.institucion else None,
        nivel_exigencia=body.nivel_exigencia,
        activo=True,
    )

    db.add(docente)
    await db.flush()
    await db.commit()
    await db.refresh(docente)

    token = crear_token(docente.id, docente.email)

    return {
        "token": token,
        "docente_id": docente.id,
        "nombre": docente.nombre,
        "email": docente.email,
        "nivel_exigencia": docente.nivel_exigencia,
    }

@app.get("/api/perfil", tags=["Perfil"])
async def obtener_perfil(
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    docente_id = obtener_docente_id_desde_token(authorization)
    docente = await db.get(Docente, docente_id)

    if not docente or not docente.activo:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {
        "id": docente.id,
        "nombre": docente.nombre,
        "email": docente.email,
        "institucion": docente.institucion,
        "nivel_exigencia": docente.nivel_exigencia,
        "created_at": docente.created_at.isoformat() if docente.created_at else None,
    }

@app.put("/api/perfil", tags=["Perfil"])
async def actualizar_perfil(
    body: PerfilUpdateRequest,
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    docente_id = obtener_docente_id_desde_token(authorization)
    docente = await db.get(Docente, docente_id)

    if not docente or not docente.activo:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    nombre = body.nombre.strip()
    email = body.email.strip().lower()

    if not nombre:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")
    if not email:
        raise HTTPException(status_code=400, detail="El correo es obligatorio")

    result = await db.execute(
        select(Docente).where(Docente.email == email, Docente.id != docente_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con este correo")

    docente.nombre = nombre
    docente.email = email
    docente.institucion = body.institucion.strip() if body.institucion else None
    docente.nivel_exigencia = body.nivel_exigencia
    docente.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(docente)

    return {
        "id": docente.id,
        "nombre": docente.nombre,
        "email": docente.email,
        "institucion": docente.institucion,
        "nivel_exigencia": docente.nivel_exigencia,
        "created_at": docente.created_at.isoformat() if docente.created_at else None,
    }

@app.post("/api/perfil/password", tags=["Perfil"])
async def cambiar_password(
    body: CambiarPasswordRequest,
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    docente_id = obtener_docente_id_desde_token(authorization)
    docente = await db.get(Docente, docente_id)

    if not docente or not docente.activo:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not verificar_password(body.actual, docente.password_hash):
        raise HTTPException(status_code=401, detail="Contraseña actual incorrecta")
    if len(body.nueva) < 8:
        raise HTTPException(status_code=400, detail="La nueva contraseña debe tener mínimo 8 caracteres")

    docente.password_hash = pwd_context.hash(body.nueva)
    docente.updated_at = datetime.utcnow()

    await db.commit()
    return {"mensaje": "Contraseña actualizada correctamente"}

@app.delete("/api/perfil", tags=["Perfil"])
async def eliminar_cuenta(
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    docente_id = obtener_docente_id_desde_token(authorization)
    docente = await db.get(Docente, docente_id)

    if not docente:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    docente.activo = False
    docente.updated_at = datetime.utcnow()

    await db.commit()
    return {"mensaje": "Cuenta desactivada correctamente"}

# ─────────────────────────────────────────────
# Cursos
# ─────────────────────────────────────────────

@app.get("/api/cursos", tags=["Cursos"])
async def listar_cursos(
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    docente_id = obtener_docente_id_desde_token(authorization)

    result = await db.execute(
        select(
            Curso.id,
            Curso.nombre,
            Curso.descripcion,
            func.count(Examen.id).label("total_examenes"),
        )
        .outerjoin(Examen, Examen.curso_id == Curso.id)
        .where(Curso.docente_id == docente_id)
        .where(Curso.activo == True)
        .group_by(Curso.id, Curso.nombre, Curso.descripcion)
        .order_by(Curso.created_at.desc())
    )
    cursos = result.all()

    return {
        "cursos": [
            {
                "id": c.id,
                "nombre": c.nombre,
                "descripcion": c.descripcion,
                "total_examenes": c.total_examenes,
            }
            for c in cursos
        ]
    }


@app.post("/api/cursos", tags=["Cursos"], status_code=status.HTTP_201_CREATED)
async def crear_curso(
    body: CursoCreateRequest,
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    docente_id = obtener_docente_id_desde_token(authorization)
    nombre = body.nombre.strip()
    if not nombre:
        raise HTTPException(status_code=400, detail="El nombre del curso es obligatorio")

    curso = Curso(
        docente_id=docente_id,
        nombre=nombre,
        descripcion=body.descripcion,
        activo=True,
    )
    db.add(curso)
    await db.flush()
    await db.commit()
    await db.refresh(curso)

    return {
        "curso": {
            "id": curso.id,
            "nombre": curso.nombre,
            "descripcion": curso.descripcion,
        }
    }

# ─────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────

_nivel_global: int = 5

NIVEL_LABELS = {
    1: "😊 Modo Amigo — Muy indulgente",
    2: "😊 Amigo — Indulgente",
    3: "🙂 Comprensivo",
    4: "⚖️ Balanceado-Suave",
    5: "⚖️ Balanceado",
    6: "⚖️ Balanceado-Estricto",
    7: "🎯 Estricto",
    8: "🎯 Muy Estricto",
    9: "🔬 Riguroso",
    10: "🔬 Modo Experto — Máxima exigencia",
}


@app.get("/api/dashboard/stats", tags=["Dashboard"])
async def get_dashboard_stats(
    authorization: Optional[str] = Header(default=None),
    curso_id: Optional[int] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    docente_id = obtener_docente_id_desde_token(authorization)

    if curso_id:
        filtro_examenes   = and_(Examen.docente_id == docente_id, Examen.curso_id == curso_id)
        filtro_materiales = and_(MaterialCurso.docente_id == docente_id, MaterialCurso.curso_id == curso_id)
    else:
        filtro_examenes   = Examen.docente_id == docente_id
        filtro_materiales = MaterialCurso.docente_id == docente_id

    def q_count(extra=None):
        cond = and_(filtro_examenes, extra) if extra is not None else filtro_examenes
        return select(func.count(Examen.id)).where(cond)

    total_examenes = (await db.execute(q_count())).scalar() or 0
    pendientes     = (await db.execute(q_count(Examen.estado == "pendiente"))).scalar() or 0
    procesando     = (await db.execute(q_count(Examen.estado == "procesando"))).scalar() or 0
    completados    = (await db.execute(q_count(Examen.estado == "completado"))).scalar() or 0
    con_error      = (await db.execute(q_count(Examen.estado == "error"))).scalar() or 0

    stats_row = (await db.execute(
        select(
            func.avg(Examen.porcentaje).label("promedio"),
            func.max(Examen.porcentaje).label("maximo"),
            func.min(Examen.porcentaje).label("minimo"),
        ).where(and_(filtro_examenes, Examen.estado == "completado"))
    )).one()

    promedio    = round(float(stats_row.promedio), 1) if stats_row.promedio else 0.0
    nota_maxima = round(float(stats_row.maximo),   1) if stats_row.maximo   else 0.0
    nota_minima = round(float(stats_row.minimo),   1) if stats_row.minimo   else 0.0

    aprobados  = (await db.execute(q_count(and_(Examen.estado == "completado", Examen.porcentaje >= 60)))).scalar() or 0
    reprobados = completados - aprobados

    mat_cond = and_(filtro_materiales, MaterialCurso.estado == "indexado")
    materiales_indexados = (await db.execute(select(func.count(MaterialCurso.id)).where(mat_cond))).scalar() or 0

    rangos = [
        ("0-49",    0,  49),
        ("50-59",  50,  59),
        ("60-69",  60,  69),
        ("70-79",  70,  79),
        ("80-89",  80,  89),
        ("90-100", 90, 100),
    ]
    distribucion = []
    for label, low, high in rangos:
        cnt = (await db.execute(
            q_count(and_(Examen.estado == "completado", Examen.porcentaje >= low, Examen.porcentaje <= high))
        )).scalar() or 0
        distribucion.append({"label": label, "count": cnt})

    recientes = (await db.execute(
        select(Examen).where(filtro_examenes).order_by(Examen.created_at.desc()).limit(10)
    )).scalars().all()

    actividad = [
        {
            "id": e.id,
            "estudiante": e.nombre_estudiante or "Sin nombre",
            "serie": e.serie,
            "fecha": e.created_at.strftime("%d/%m/%Y, %H:%M") if e.created_at else "",
            "estado": e.estado,
            "porcentaje": round(float(e.porcentaje), 1) if e.porcentaje else None,
        }
        for e in recientes
    ]

    procesados   = completados + con_error
    pct_progreso = round((procesados / total_examenes) * 100) if total_examenes > 0 else 0

    return {
        "kpis": {
            "total_examenes":       total_examenes,
            "pendientes":           pendientes,
            "procesando":           procesando,
            "completados":          completados,
            "con_error":            con_error,
            "promedio":             promedio,
            "nota_maxima":          nota_maxima,
            "nota_minima":          nota_minima,
            "aprobados":            aprobados,
            "reprobados":           reprobados,
            "materiales_indexados": materiales_indexados,
            "nivel_exigencia":      _nivel_global,
        },
        "progreso": {
            "porcentaje":  pct_progreso,
            "completados": completados,
            "pendientes":  pendientes,
            "procesando":  procesando,
            "con_error":   con_error,
        },
        "distribucion":       distribucion,
        "actividad_reciente": actividad,
    }

# ─────────────────────────────────────────────
# Exámenes — Upload
# ─────────────────────────────────────────────

@app.post("/api/upload", tags=["Exámenes"], status_code=status.HTTP_201_CREATED)
async def upload_exam(
    archivos: list[UploadFile] = File(..., description="Imágenes (JPG/PNG/WEBP) o PDFs"),
    nivel_exigencia: int = Form(default=5, ge=1, le=10),
    punteo_maximo: float = Form(default=100.0, ge=1.0),
    nombres_estudiantes: Optional[str] = Form(default=None),
    serie: Optional[str] = Form(default=None),
    distribucion_series: Optional[str] = Form(default=None),
    curso_id: int = Form(...),
    examenes_en_lote: int = Form(default=1, ge=1, le=50),
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    
    
    docente_id = obtener_docente_id_desde_token(authorization)

    result = await db.execute(
        select(Curso).where(
            Curso.id == curso_id,
            Curso.docente_id == docente_id,
            Curso.activo == True,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    if not archivos:
        raise HTTPException(status_code=400, detail="Se requiere al menos un archivo.")
    
    distribucion_series_lista = []

    if distribucion_series:
        try:
            distribucion_series_lista = json.loads(distribucion_series)

            if not isinstance(distribucion_series_lista, list):
                raise ValueError("La distribución de series debe ser una lista.")

            total_series = sum(float(s.get("valor", 0) or 0) for s in distribucion_series_lista)

            if round(total_series, 2) != round(float(punteo_maximo), 2):
                raise HTTPException(
                    status_code=400,
                    detail=f"La suma de las series ({total_series}) no coincide con el punteo máximo ({punteo_maximo}).",
                )

        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="La distribución de series tiene un formato inválido.",
            )

    allowed_images = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    allowed_all    = allowed_images | {".pdf"}

    for archivo in archivos:
        ext = Path(archivo.filename or "").suffix.lower()
        if ext not in allowed_all:
            raise HTTPException(
                status_code=400,
                detail=f"Formato no soportado: {archivo.filename}. Use JPG, PNG, WEBP o PDF.",
            )

    lote_uuid = str(uuid.uuid4())
    lote_dir  = Path(settings.upload_dir) / lote_uuid
    lote_dir.mkdir(parents=True, exist_ok=True)

    all_image_paths: list[str] = []

    for i, archivo in enumerate(archivos):
        ext      = Path(archivo.filename or "").suffix.lower()
        filename = f"archivo_{i + 1:03d}{ext}"
        dest     = lote_dir / filename

        with open(dest, "wb") as f:
            shutil.copyfileobj(archivo.file, f)

        if ext == ".pdf":
            try:
                img_paths = _pdf_to_images(str(dest), lote_dir)
                all_image_paths.extend(img_paths)
            except Exception as exc:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error convirtiendo PDF '{archivo.filename}': {exc}",
                )
        else:
            all_image_paths.append(str(dest))

    nombres_lista: list[str] = []
    if nombres_estudiantes:
        nombres_lista = [n.strip() for n in nombres_estudiantes.split(",") if n.strip()]

    total_imagenes  = len(all_image_paths)
    imgs_por_examen = total_imagenes // examenes_en_lote
    resto           = total_imagenes % examenes_en_lote

    examenes_creados: list[dict] = []

    for i in range(examenes_en_lote):
        inicio          = i * imgs_por_examen + min(i, resto)
        fin             = inicio + imgs_por_examen + (1 if i < resto else 0)
        imagenes_examen = all_image_paths[inicio:fin]

        if not imagenes_examen:
            continue

        nombre_estudiante = nombres_lista[i] if i < len(nombres_lista) else None

        examen = Examen(
            docente_id=docente_id,
            curso_id=curso_id,
            nombre_estudiante=nombre_estudiante,
            serie=serie,
            imagenes_rutas=imagenes_examen,
            nivel_exigencia=nivel_exigencia,
            punteo_maximo=punteo_maximo,
            distribucion_series=distribucion_series_lista,
            estado="pendiente",
        )
        db.add(examen)
        await db.flush()
        examenes_creados.append({
            "examen_id": examen.id,
            "nombre_estudiante": nombre_estudiante,
            "imagenes": len(imagenes_examen),
        })

    await db.commit()

    return {
        "lote_id":         lote_uuid,
        "examenes_creados": len(examenes_creados),
        "examenes":         examenes_creados,
        "total_imagenes":   total_imagenes,
        "mensaje":          f"{len(examenes_creados)} examen(es) listos.",
    }
# ─────────────────────────────────────────────
# Exámenes — Procesar lote
# ─────────────────────────────────────────────

@app.post("/api/process/lote", tags=["Exámenes"])
async def process_lote(
    examen_ids: list[int],
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    docente_id = obtener_docente_id_desde_token(authorization)

    if not examen_ids:
        raise HTTPException(status_code=400, detail="Debe enviar al menos un examen.")

    result = await db.execute(
        select(Examen).where(
            Examen.id.in_(examen_ids),
            Examen.docente_id == docente_id,
        )
    )
    examenes = result.scalars().all()

    if not examenes:
        raise HTTPException(
            status_code=404,
            detail="No se encontraron exámenes válidos para este docente.",
        )

    iniciados: list[int] = []
    omitidos: list[dict] = []

    for examen in examenes:
        if examen.estado == "procesando":
            omitidos.append({"examen_id": examen.id, "motivo": "Ya está procesando"})
            continue

        if examen.estado == "completado":
            omitidos.append({"examen_id": examen.id, "motivo": "Ya está completado"})
            continue

        examen.estado = "procesando"
        iniciados.append(examen.id)

    await db.commit()

    for examen_id in iniciados:
        background_tasks.add_task(_process_exam_task, examen_id)

    return {
        "iniciados": len(iniciados),
        "examen_ids": iniciados,
        "omitidos": omitidos,
        "mensaje": "Procesamiento de lote iniciado.",
    }

# ─────────────────────────────────────────────
# Exámenes — Estado para polling
# ─────────────────────────────────────────────

@app.get("/api/process/estado", tags=["Exámenes"])
async def get_estado_examenes(
    ids: str = Query(..., description="IDs separados por coma: 1,2,3"),
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    docente_id = obtener_docente_id_desde_token(authorization)

    try:
        id_list = [int(x.strip()) for x in ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="IDs inválidos.")

    result = await db.execute(
        select(Examen).where(
            Examen.id.in_(id_list),
            Examen.docente_id == docente_id,
        )
    )
    examenes = result.scalars().all()

    return {
        "examenes": [
            {
                "id":               e.id,
                "nombre_estudiante": e.nombre_estudiante or "Sin nombre",
                "estado":           e.estado,
                "porcentaje":       round(float(e.porcentaje), 1) if e.porcentaje else None,
                "punteo_total":     float(e.punteo_total)  if e.punteo_total  else None,
                "punteo_maximo":    float(e.punteo_maximo) if e.punteo_maximo else None,
            }
            for e in examenes
        ]
    }

# ─────────────────────────────────────────────
# Exámenes — Procesar uno (mantener para compatibilidad)
# ─────────────────────────────────────────────

@app.post("/api/process/{examen_id}", tags=["Exámenes"])
async def process_exam(
    examen_id: int,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    docente_id = obtener_docente_id_desde_token(authorization)

    result = await db.execute(
        select(Examen).where(
            Examen.id == examen_id,
            Examen.docente_id == docente_id,
        )
    )
    examen = result.scalar_one_or_none()

    if not examen:
        raise HTTPException(status_code=404, detail=f"Examen {examen_id} no encontrado.")

    if examen.estado == "procesando":
        raise HTTPException(status_code=409, detail="El examen ya está siendo procesado.")

    if examen.estado == "completado":
        return {"mensaje": "El examen ya fue procesado.", "examen_id": examen_id}

    examen.estado = "procesando"
    await db.commit()

    background_tasks.add_task(_process_exam_task, examen_id)

    return {"examen_id": examen_id, "estado": "procesando"}


@app.post("/api/process/{examen_id}/retry", tags=["Exámenes"])
async def retry_exam(
    examen_id: int,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    docente_id = obtener_docente_id_desde_token(authorization)

    result = await db.execute(
        select(Examen).where(
            Examen.id == examen_id,
            Examen.docente_id == docente_id,
        )
    )
    examen = result.scalar_one_or_none()

    if not examen:
        raise HTTPException(status_code=404, detail="Examen no encontrado.")

    if examen.estado == "procesando":
        raise HTTPException(status_code=409, detail="El examen ya está procesándose.")

    # Limpiar resultados anteriores para reprocesar de forma segura.
    await db.execute(delete(LogConsenso).where(LogConsenso.examen_id == examen_id))
    await db.execute(delete(CalificacionFinal).where(CalificacionFinal.examen_id == examen_id))
    await db.execute(delete(PreguntaExtraida).where(PreguntaExtraida.examen_id == examen_id))

    examen.estado = "procesando"
    examen.texto_extraido_icr = None
    examen.punteo_total = None
    examen.porcentaje = None

    await db.commit()

    background_tasks.add_task(_process_exam_task, examen_id)

    return {
        "mensaje": "Reprocesamiento iniciado.",
        "examen_id": examen_id,
        "estado": "procesando",
    }

# ─────────────────────────────────────────────
# Tarea en background
# ─────────────────────────────────────────────

async def _process_exam_task(examen_id: int) -> None:
    from db.database import AsyncSessionLocal

    async with _lote_semaphore:
        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(select(Examen).where(Examen.id == examen_id))
                examen = result.scalar_one_or_none()

                if not examen:
                    logger.error(f"Examen {examen_id} no encontrado en BD")
                    return

                examen.estado = "procesando"
                await db.commit()
                await db.refresh(examen)

                imagenes_rutas = [
                    str(path)
                    for path in (examen.imagenes_rutas or [])
                    if path and Path(str(path)).exists()
                ]

                if not imagenes_rutas:
                    raise ValueError(f"Ninguna imagen del examen {examen_id} existe en disco")

                # 1. ICR
                logger.info(f"[{examen_id}] Iniciando ICR ({len(imagenes_rutas)} imagen/es)...")
                loop = asyncio.get_running_loop()
                icr_result = await loop.run_in_executor(
                    None,
                    extract_text_from_images,
                    imagenes_rutas,
                )

                tipo_examen = icr_result.get("tipo_examen", "desconocido")
                logger.info(f"[{examen_id}] ICR completado: tipo={tipo_examen}")

                texto_resumen = icr_result.get("texto_resumen") or icr_result.get("raw_text") or ""
                examen.texto_extraido_icr = texto_resumen

                parsed = icr_result.get("parsed", {}) or {}
                preguntas_flat = icr_result.get("preguntas_flat", []) or []

                # Evita duplicados si una tarea quedó a medias y se vuelve a ejecutar.
                await db.execute(delete(PreguntaExtraida).where(PreguntaExtraida.examen_id == examen_id))

                for q in preguntas_flat:
                    respuesta = q.get(
                        "respuesta",
                        q.get("respuesta_marcada", q.get("respuestas_insertadas", "")),
                    )

                    pq = PreguntaExtraida(
                        examen_id=examen_id,
                        numero_pregunta=int(q.get("numero", 0) or 0),
                        serie_pregunta=q.get("serie_seccion", q.get("seccion", "")) or "",
                        texto_pregunta=q.get("enunciado", q.get("enunciado_con_blancos", "")) or "",
                        respuesta_estudiante=str(respuesta or ""),
                        tiene_latex=bool(q.get("tiene_latex", False)),
                    )
                    db.add(pq)

                if not examen.nombre_estudiante:
                    estudiante_info = parsed.get("estudiante", {}) or {}
                    nombre_detectado = (estudiante_info.get("nombre") or "").strip()
                    if nombre_detectado:
                        examen.nombre_estudiante = nombre_detectado

                if not examen.serie:
                    estudiante_info = parsed.get("estudiante", {}) or {}
                    serie_detectada = (estudiante_info.get("serie") or estudiante_info.get("seccion") or "").strip()
                    if serie_detectada:
                        examen.serie = serie_detectada

                await db.flush()

                # 2. RAG: usar enunciados primero, no todo el texto mezclado.
                logger.info(f"[{examen_id}] Buscando contexto RAG...")
                enunciados = [
                    q.get("enunciado", q.get("enunciado_con_blancos", ""))
                    for q in preguntas_flat
                    if q.get("enunciado") or q.get("enunciado_con_blancos")
                ]
                query_rag = " ".join(enunciados[:5]).strip()
                if not query_rag:
                    query_rag = texto_resumen[:500]

                contexto_rag = rag_service.search(
                    query=query_rag,
                    curso_id=examen.curso_id,
                    docente_id=examen.docente_id,
                    k=5,
                )

                # 3. Consenso
                logger.info(f"[{examen_id}] Iniciando consenso (A={settings.provider_calificador_a}/{settings.model_calificador_a}, B={settings.provider_calificador_b}/{settings.model_calificador_b}, Juez={settings.provider_juez}/{settings.model_juez})...")
                consensus = await run_consensus_grading(
                    examen_id=examen_id,
                    texto_icr=texto_resumen,
                    contexto_rag=contexto_rag,
                    nivel_exigencia=examen.nivel_exigencia,
                    punteo_maximo=float(examen.punteo_maximo or 0),
                    distribucion_series=examen.distribucion_series or [],
                )

                logger.info(f"[{examen_id}] Consenso completado. Error consenso: {consensus.error or 'ninguno'}")
                if consensus.resultado_a:
                    logger.info(f"[{examen_id}] Calificador A ({consensus.resultado_a.modelo}): error={consensus.resultado_a.error or 'OK'}, tokens={consensus.resultado_a.tokens}, latencia={consensus.resultado_a.latencia_ms}ms")
                if consensus.resultado_b:
                    logger.info(f"[{examen_id}] Calificador B ({consensus.resultado_b.modelo}): error={consensus.resultado_b.error or 'OK'}, tokens={consensus.resultado_b.tokens}, latencia={consensus.resultado_b.latencia_ms}ms")
                if consensus.resultado_juez:
                    logger.info(f"[{examen_id}] Juez ({consensus.resultado_juez.modelo}): error={consensus.resultado_juez.error or 'OK'}, tokens={consensus.resultado_juez.tokens}, latencia={consensus.resultado_juez.latencia_ms}ms")
                    if consensus.resultado_juez.error:
                        logger.warning(f"[{examen_id}] Juez raw (primeros 500 chars): {(consensus.resultado_juez.respuesta_raw or '')[:500]}")

                # 4. Logs: limpiar logs previos del examen para evitar duplicados.
                await db.execute(delete(LogConsenso).where(LogConsenso.examen_id == examen_id))

                for agente_result in [
                    consensus.resultado_a,
                    consensus.resultado_b,
                    consensus.resultado_juez,
                ]:
                    if not agente_result:
                        continue

                    log = LogConsenso(
                        examen_id=examen_id,
                        agente=agente_result.agente,
                        modelo_usado=agente_result.modelo,
                        nivel_exigencia=examen.nivel_exigencia,
                        respuesta_raw=agente_result.respuesta_raw,
                        respuesta_json=agente_result.respuesta_json,
                        tokens_usados=agente_result.tokens,
                        latencia_ms=agente_result.latencia_ms,
                        error=agente_result.error,
                    )
                    db.add(log)

                # 5. Calificación final
                cf_data = consensus.calificacion_final

                if not cf_data:
                    examen.estado = "error"
                    await db.commit()
                    logger.error(f"[{examen_id}] Consenso no produjo calificación (cf_data vacío). Error consenso: {consensus.error}")
                    return

                punteo_obtenido = float(cf_data.get("punteo_total", 0) or 0)
                punteo_maximo_agente = float(cf_data.get("punteo_maximo_total", 0) or 0)

                punteo_maximo_final = (
                    float(examen.punteo_maximo)
                    if examen.punteo_maximo and float(examen.punteo_maximo) > 0
                    else punteo_maximo_agente
                )

                if punteo_maximo_final > 0:
                    if punteo_maximo_agente > 0 and punteo_maximo_agente != punteo_maximo_final:
                        factor = punteo_maximo_final / punteo_maximo_agente
                        punteo_obtenido_final = round(punteo_obtenido * factor, 2)
                    else:
                        punteo_obtenido_final = round(punteo_obtenido, 2)

                    punteo_obtenido_final = min(punteo_obtenido_final, punteo_maximo_final)
                    porcentaje_final = round((punteo_obtenido_final / punteo_maximo_final) * 100, 2)
                    porcentaje_final = min(porcentaje_final, 100.0)
                else:
                    punteo_obtenido_final = round(punteo_obtenido, 2)
                    porcentaje_final = float(cf_data.get("porcentaje", 0) or 0)

                cf_data_final = dict(cf_data)
                nombre_final = (
                    (examen.nombre_estudiante or "").strip()
                    or (cf_data.get("estudiante") or "").strip()
                    or "Sin nombre"
                )

                cf_data_final["punteo_total"] = punteo_obtenido_final
                cf_data_final["punteo_maximo_total"] = punteo_maximo_final
                cf_data_final["porcentaje"] = porcentaje_final
                cf_data_final["estudiante"] = nombre_final

                pdf_path = ""
                word_path = ""
                try:
                    pdf_path = generate_pdf_report(cf_data_final)
                    word_path = generate_word_report(cf_data_final)
                except Exception as rep_err:
                    logger.warning(f"[{examen_id}] Error generando reporte: {rep_err}")

                preguntas_json = json.dumps(
                    cf_data_final.get("preguntas", []),
                    ensure_ascii=False,
                )

                existing_cf_result = await db.execute(
                    select(CalificacionFinal).where(CalificacionFinal.examen_id == examen_id)
                )
                cf_obj = existing_cf_result.scalar_one_or_none()

                if cf_obj:
                    cf_obj.punteo_obtenido = punteo_obtenido_final
                    cf_obj.punteo_maximo = punteo_maximo_final
                    cf_obj.justificacion_final = preguntas_json
                    cf_obj.conclusion_general = cf_data_final.get("conclusion", "")
                    cf_obj.fortalezas = cf_data_final.get("fortalezas", [])
                    cf_obj.debilidades = cf_data_final.get("debilidades", [])
                    cf_obj.sugerencias = cf_data_final.get("sugerencias", [])
                    cf_obj.ruta_reporte_pdf = pdf_path
                    cf_obj.ruta_reporte_word = word_path
                else:
                    cf_obj = CalificacionFinal(
                        examen_id=examen_id,
                        punteo_obtenido=punteo_obtenido_final,
                        punteo_maximo=punteo_maximo_final,
                        justificacion_final=preguntas_json,
                        conclusion_general=cf_data_final.get("conclusion", ""),
                        fortalezas=cf_data_final.get("fortalezas", []),
                        debilidades=cf_data_final.get("debilidades", []),
                        sugerencias=cf_data_final.get("sugerencias", []),
                        ruta_reporte_pdf=pdf_path,
                        ruta_reporte_word=word_path,
                    )
                    db.add(cf_obj)

                examen.punteo_total = punteo_obtenido_final
                examen.punteo_maximo = punteo_maximo_final
                examen.porcentaje = porcentaje_final
                examen.nombre_estudiante = nombre_final
                examen.estado = "completado"

                await db.commit()

                logger.info(
                    f"[{examen_id}] COMPLETADO: "
                    f"{punteo_obtenido_final}/{punteo_maximo_final} pts ({porcentaje_final}%)"
                )

            except Exception as exc:
                await db.rollback()

                try:
                    result = await db.execute(select(Examen).where(Examen.id == examen_id))
                    ex = result.scalar_one_or_none()
                    if ex:
                        ex.estado = "error"
                        await db.commit()
                except Exception:
                    await db.rollback()

                logger.error(f"[{examen_id}] ERROR al procesar: {exc}", exc_info=True)

# ─────────────────────────────────────────────
# Historial
# ─────────────────────────────────────────────

@app.get("/api/history", tags=["Historial"])
async def get_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    estado: Optional[str] = Query(default=None),
    curso_id: Optional[int] = Query(default=None),
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    docente_id = obtener_docente_id_desde_token(authorization)

    query = select(Examen).where(Examen.docente_id == docente_id)
    if curso_id:
        query = query.where(Examen.curso_id == curso_id)
    if estado:
        query = query.where(Examen.estado == estado)

    query  = query.order_by(Examen.created_at.desc())
    offset = (page - 1) * page_size
    query  = query.offset(offset).limit(page_size)

    result  = await db.execute(query)
    examenes = result.scalars().all()

    return {
        "page":      page,
        "page_size": page_size,
        "items": [
            {
                "id":                e.id,
                "curso_id":          e.curso_id,
                "nombre_estudiante": e.nombre_estudiante,
                "serie":             e.serie,
                "nivel_exigencia":   e.nivel_exigencia,
                "estado":            e.estado,
                "punteo_total":      float(e.punteo_total)  if e.punteo_total  is not None else None,
                "punteo_maximo":     float(e.punteo_maximo) if e.punteo_maximo is not None else None,
                "porcentaje":        float(e.porcentaje)    if e.porcentaje    is not None else None,
                "created_at":        e.created_at.isoformat() if e.created_at else None,
            }
            for e in examenes
        ],
    }


@app.get("/api/history/{examen_id}", tags=["Historial"])
async def get_exam_detail(
    examen_id: int,
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    docente_id = obtener_docente_id_desde_token(authorization)

    result = await db.execute(
        select(Examen).where(Examen.id == examen_id, Examen.docente_id == docente_id)
    )
    examen = result.scalar_one_or_none()
    if not examen:
        raise HTTPException(status_code=404, detail="Examen no encontrado.")

    cf_result   = await db.execute(select(CalificacionFinal).where(CalificacionFinal.examen_id == examen_id))
    cf          = cf_result.scalar_one_or_none()

    logs_result = await db.execute(
        select(LogConsenso).where(LogConsenso.examen_id == examen_id).order_by(LogConsenso.created_at)
    )
    logs = logs_result.scalars().all()

    pregs_result = await db.execute(select(PreguntaExtraida).where(PreguntaExtraida.examen_id == examen_id))
    pregs = pregs_result.scalars().all()

    logs_by_agent: dict[str, dict] = {}
    for log in logs:
        logs_by_agent[log.agente] = {
            "modelo":     log.modelo_usado,
            "respuesta":  log.respuesta_json,
            "tokens":     log.tokens_usados,
            "latencia_ms": log.latencia_ms,
            "error":      log.error,
        }

    return {
        "examen": {
            "id":                examen.id,
            "nombre_estudiante": examen.nombre_estudiante,
            "serie":             examen.serie,
            "nivel_exigencia":   examen.nivel_exigencia,
            "estado":            examen.estado,
            "texto_icr":         examen.texto_extraido_icr,
            "punteo_total":      float(examen.punteo_total)  if examen.punteo_total  else None,
            "punteo_maximo":     float(examen.punteo_maximo) if examen.punteo_maximo else None,
            "porcentaje":        float(examen.porcentaje)    if examen.porcentaje    else None,
            "created_at":        examen.created_at.isoformat() if examen.created_at else None,
        },
        "calificacion_final": {
            "conclusion":  cf.conclusion_general  if cf else None,
            "fortalezas":  cf.fortalezas          if cf else [],
            "debilidades": cf.debilidades         if cf else [],
            "sugerencias": cf.sugerencias         if cf else [],
            "ruta_pdf":    cf.ruta_reporte_pdf    if cf else None,
            "ruta_word":   cf.ruta_reporte_word   if cf else None,
        } if cf else None,
        "preguntas": [
            {
                "numero":    p.numero_pregunta,
                "serie":     p.serie_pregunta,
                "enunciado": p.texto_pregunta,
                "respuesta": p.respuesta_estudiante,
                "tiene_latex": p.tiene_latex,
            }
            for p in pregs
        ],
        "agentes": {
            "calificador_a": logs_by_agent.get("calificador_a"),
            "calificador_b": logs_by_agent.get("calificador_b"),
            "juez":          logs_by_agent.get("juez"),
        },
    }

# ─────────────────────────────────────────────
# Configuración de exigencia
# ─────────────────────────────────────────────

@app.get("/api/config-exigencia", tags=["Configuración"])
async def get_config_exigencia():
    return {
        "nivel":       _nivel_global,
        "descripcion": NIVEL_LABELS.get(_nivel_global, f"Nivel {_nivel_global}"),
        "opciones":    [{"nivel": k, "descripcion": v} for k, v in NIVEL_LABELS.items()],
    }


@app.post("/api/config-exigencia", tags=["Configuración"])
async def set_config_exigencia(body: ConfigExigenciaRequest):
    global _nivel_global
    _nivel_global = body.nivel
    return ConfigExigenciaResponse(
        nivel=body.nivel,
        descripcion=NIVEL_LABELS.get(body.nivel, f"Nivel {body.nivel}"),
        mensaje=f"Nivel de exigencia actualizado a {body.nivel}/10",
    )

# ─────────────────────────────────────────────
# Materiales (RAG)
# ─────────────────────────────────────────────

@app.post("/api/materials/upload", tags=["Materiales"])
async def upload_material(
    archivo: UploadFile = File(...),
    curso_id: int = Form(...),
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    docente_id = obtener_docente_id_desde_token(authorization)

    result = await db.execute(
        select(Curso).where(Curso.id == curso_id, Curso.docente_id == docente_id, Curso.activo == True)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    nombre = archivo.filename or ""
    ext    = Path(nombre).suffix.lower()
    if ext not in {".pdf", ".docx", ".pptx"}:
        raise HTTPException(status_code=400, detail=f"Formato no soportado: '{ext}'. Solo PDF, DOCX y PPTX.")

    mat_dir = Path(settings.materials_dir) / str(docente_id) / str(curso_id)
    mat_dir.mkdir(parents=True, exist_ok=True)
    dest = mat_dir / f"{uuid.uuid4().hex}{ext}"

    with open(dest, "wb") as f:
        shutil.copyfileobj(archivo.file, f)

    material = MaterialCurso(
        docente_id=docente_id,
        curso_id=curso_id,
        nombre_archivo=nombre,
        ruta_almacenamiento=str(dest),
        estado="pendiente",
    )
    db.add(material)
    await db.flush()
    material_id = material.id

    try:
        loop = asyncio.get_running_loop()
        stats = await loop.run_in_executor(
            None,
            rag_service.index_file,
            str(dest),
            docente_id,
            curso_id,
            material_id,
        )
        material.paginas = stats["paginas"]
        material.chunks_indexados = stats["chunks"]
        material.estado = "indexado"
    except Exception as exc:
        material.estado = "error"
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Error indexando archivo: {exc}")

    await db.commit()

    return {
        "material_id":      material_id,
        "curso_id":         curso_id,
        "archivo":          nombre,
        "formato":          ext,
        "paginas":          material.paginas,
        "chunks_indexados": material.chunks_indexados,
        "mensaje":          "Material indexado correctamente.",
    }


@app.get("/api/materials", tags=["Materiales"])
async def listar_materiales(
    curso_id: int = Query(...),
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    docente_id = obtener_docente_id_desde_token(authorization)

    result = await db.execute(
        select(MaterialCurso)
        .where(MaterialCurso.curso_id == curso_id, MaterialCurso.docente_id == docente_id)
        .order_by(MaterialCurso.created_at.desc())
    )
    materiales = result.scalars().all()

    return {
        "materiales": [
            {
                "id":         m.id,
                "nombre":     m.nombre_archivo,
                "paginas":    m.paginas or 0,
                "chunks":     m.chunks_indexados or 0,
                "estado":     m.estado,
                "formato":    Path(m.ruta_almacenamiento or "").suffix.lower(),
                "created_at": m.created_at.isoformat() if m.created_at else "",
            }
            for m in materiales
        ],
        "total": len(materiales),
    }


@app.delete("/api/materials/{material_id}", tags=["Materiales"])
async def eliminar_material(
    material_id: int,
    curso_id: int = Query(...),
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    docente_id = obtener_docente_id_desde_token(authorization)

    result = await db.execute(
        select(MaterialCurso).where(
            MaterialCurso.id == material_id,
            MaterialCurso.curso_id == curso_id,
            MaterialCurso.docente_id == docente_id,
        )
    )
    mat = result.scalar_one_or_none()
    if not mat:
        raise HTTPException(status_code=404, detail="Material no encontrado.")

    chunks_eliminados = rag_service.delete_material(
        material_id=material_id,
        docente_id=docente_id,
        curso_id=curso_id,
    )

    ruta = mat.ruta_almacenamiento
    if ruta and Path(ruta).exists():
        try:
            os.remove(ruta)
        except OSError:
            pass

    await db.delete(mat)
    await db.commit()

    return {"eliminado": True, "chunks_eliminados": chunks_eliminados}

# ─────────────────────────────────────────────
# Descargas
# ─────────────────────────────────────────────

async def _get_calificacion_docente(
    examen_id: int,
    docente_id: int,
    db: AsyncSession,
) -> tuple[Examen, CalificacionFinal]:
    result = await db.execute(
        select(Examen, CalificacionFinal)
        .join(CalificacionFinal, CalificacionFinal.examen_id == Examen.id)
        .where(
            CalificacionFinal.examen_id == examen_id,
            Examen.docente_id == docente_id,
        )
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Reporte no disponible.")

    return row[0], row[1]


def _parse_preguntas_reporte(cf: CalificacionFinal) -> list[dict]:
    if not cf.justificacion_final:
        return []

    try:
        preguntas = json.loads(cf.justificacion_final)
    except Exception:
        return []

    return preguntas if isinstance(preguntas, list) else []


def _build_reporte_data(examen: Examen, cf: CalificacionFinal) -> dict:
    punteo_obtenido = float(cf.punteo_obtenido or examen.punteo_total or 0)
    punteo_maximo = float(cf.punteo_maximo or examen.punteo_maximo or 0)
    porcentaje = (
        round((punteo_obtenido / punteo_maximo) * 100, 2)
        if punteo_maximo > 0
        else float(examen.porcentaje or 0)
    )

    return {
        "examen_id": examen.id,
        "estudiante": examen.nombre_estudiante or "Estudiante",
        "serie": examen.serie or "Sin serie",
        "fecha": examen.created_at.strftime("%d/%m/%Y, %I:%M %p") if examen.created_at else "",
        "nivel_aplicado": examen.nivel_exigencia,
        "estado": examen.estado,
        "punteo_total": punteo_obtenido,
        "punteo_maximo_total": punteo_maximo,
        "porcentaje": porcentaje,
        "preguntas": _parse_preguntas_reporte(cf),
        "conclusion": cf.conclusion_general or "",
        "fortalezas": cf.fortalezas or [],
        "debilidades": cf.debilidades or [],
        "sugerencias": cf.sugerencias or [],
    }


@app.get("/api/download/pdf/{examen_id}", tags=["Descargas"])
async def download_pdf(
    examen_id: int,
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    docente_id = obtener_docente_id_desde_token(authorization)
    examen, cf = await _get_calificacion_docente(examen_id, docente_id, db)

    cf.ruta_reporte_pdf = generate_pdf_report(_build_reporte_data(examen, cf))
    await db.commit()

    return FileResponse(
        cf.ruta_reporte_pdf,
        media_type="application/pdf",
        filename=Path(cf.ruta_reporte_pdf).name,
    )


@app.get("/api/download/word/{examen_id}", tags=["Descargas"])
async def download_word(
    examen_id: int,
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    docente_id = obtener_docente_id_desde_token(authorization)
    examen, cf = await _get_calificacion_docente(examen_id, docente_id, db)

    cf.ruta_reporte_word = generate_word_report(_build_reporte_data(examen, cf))
    await db.commit()

    return FileResponse(
        cf.ruta_reporte_word,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=Path(cf.ruta_reporte_word).name,
    )

# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
