"""
EduGrade AI / DeepGrader AI — Sistema de Consenso con 3 Agentes IA
==================================================================

FLUJO MEJORADO (4 etapas):

  [1] PRE-ANÁLISIS (nuevo)
      └─ Un modelo ligero lee el ICR y extrae la estructura real del examen:
         preguntas detectadas, respuestas escritas, series identificadas.
         Esto desacopla la extracción de la calificación.

  [2] CALIFICADORES PARALELOS (A y B con modelos distintos)
      ├─ Calificador A: recibe el pre-análisis + RAG → califica
      └─ Calificador B: recibe el pre-análisis + RAG → califica
         Cada calificador SOLO decide es_correcta y punteo.
         No hacen extracción — eso ya lo hizo el paso 1.

  [3] JUEZ / SUPERVISOR
      └─ Compara A vs B pregunta a pregunta.
         Si coinciden → acepta.
         Si difieren → re-lee el ICR y RAG y decide con criterio propio.
         El juez NUNCA promedia — elige y justifica.

  [4] POST-PROCESO DETERMINISTA
      └─ Ajusta punteos a la distribución oficial del docente.
         Preserva es_correcta del juez sin sobreescribirla.

Cambios clave vs versión anterior:
- Pre-análisis desacopla extracción de calificación (modelos se enfocann en razonar).
- Juez usa modelo más potente (configurable por provider).
- es_correcta del modelo se preserva; post-proceso NO la sobreescribe.
- Fallback de merge usa lógica de mayoría, no promedio.
- Prompts más cortos y directivos → menos alucinación.
- Soporte completo groq / openai / gemini.

Exporta:
    run_consensus_grading(...)
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from groq import Groq

from config import get_settings

settings = get_settings()

AGENT_TIMEOUT_SECONDS = 75
MAX_RETRIES = 3
DEFAULT_MAX_TOKENS = 6000

# ─── Clientes lazy por proveedor ──────────────────────────
_groq_client: Groq | None = None
_gemini_client = None
_openai_client = None
_nvidia_client = None


def _get_groq_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=settings.groq_api_key)
    return _groq_client


def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        from google import genai as _genai
        _gemini_client = _genai.Client(api_key=settings.gemini_api_key)
    return _gemini_client


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        import openai as _openai
        _openai_client = _openai.OpenAI(api_key=settings.openai_api_key)
    return _openai_client


def _get_nvidia_client():
    global _nvidia_client
    if _nvidia_client is None:
        import openai as _openai
        _nvidia_client = _openai.OpenAI(
            api_key=settings.nvidia_api_key,
            base_url="https://integrate.api.nvidia.com/v1",
        )
    return _nvidia_client



# ─────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────

@dataclass
class PreAnalisis:
    """Resultado del paso 0: extracción estructurada del ICR."""
    preguntas_detectadas: list[dict] = field(default_factory=list)
    series_detectadas: list[str] = field(default_factory=list)
    estudiante: str = ""
    raw: str = ""
    error: Optional[str] = None


@dataclass
class ResultadoAgente:
    agente: str
    modelo: str
    respuesta_json: dict
    respuesta_raw: str
    tokens: int = 0
    latencia_ms: int = 0
    error: Optional[str] = None


@dataclass
class ResultadoConsenso:
    examen_id: int
    nivel_exigencia: int
    pre_analisis: Optional[PreAnalisis] = None
    resultado_a: Optional[ResultadoAgente] = None
    resultado_b: Optional[ResultadoAgente] = None
    resultado_juez: Optional[ResultadoAgente] = None
    calificacion_final: dict = field(default_factory=dict)
    discrepancias: list[dict] = field(default_factory=list)
    error: Optional[str] = None


# ─────────────────────────────────────────────
# Utilidades generales
# ─────────────────────────────────────────────

def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


def _truncate_text(text: str | None, max_chars: int) -> str:
    text = str(text or "")
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n[... texto truncado ...]"


def _clean_model_response(raw: str) -> str:
    cleaned = str(raw or "").strip()
    cleaned = re.sub(r"```(?:json)?", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.replace("```", "")
    cleaned = cleaned.strip().strip("`").strip()
    return cleaned


def _extract_json_object(text: str) -> dict:
    cleaned = _clean_model_response(text)

    try:
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else {"_value": parsed}
    except Exception:
        pass

    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", cleaned):
        start = match.start()
        try:
            obj, _ = decoder.raw_decode(cleaned[start:])
            if isinstance(obj, dict):
                return obj
        except Exception:
            continue

    raise json.JSONDecodeError("No se encontró un objeto JSON válido", cleaned, 0)


def _json_dumps_compacto(data: Any, max_chars: int = 12000) -> str:
    txt = json.dumps(data or {}, ensure_ascii=False)
    return _truncate_text(txt, max_chars)


def _normalizar_lista(value: Any) -> list:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


# ─────────────────────────────────────────────
# Descripción de nivel de exigencia
# ─────────────────────────────────────────────

def _nivel_descripcion(nivel: int) -> str:
    if nivel <= 2:
        return (
            "MUY INDULGENTE: valora esfuerzo y proceso. Tolera errores menores de "
            "notación o signos. Otorga puntaje parcial generosamente."
        )
    if nivel <= 4:
        return (
            "INDULGENTE: valora el procedimiento aunque el resultado final sea "
            "incorrecto. Da crédito por pasos correctos."
        )
    if nivel <= 6:
        return (
            "BALANCEADO: evalúa objetivamente resultado y procedimiento. Errores "
            "menores descuentan menos del 30% del puntaje de la pregunta."
        )
    if nivel <= 8:
        return (
            "ESTRICTO: penaliza errores de signos, exponentes incorrectos y "
            "procedimientos incompletos. Requiere respuesta y procedimiento correctos."
        )
    return (
        "MUY ESTRICTO / EXPERTO: evaluación académica rigurosa. Penaliza cualquier "
        "error conceptual o de procedimiento. Solo da puntaje completo si todo es correcto."
    )


# ─────────────────────────────────────────────
# Schema JSON de calificación
# ─────────────────────────────────────────────

SCHEMA_CALIFICACION = """
{
  "estudiante": "Nombre detectado en el examen",
  "serie": "Serie o código del examen",
  "nivel_aplicado": 5,
  "punteo_total": 0.0,
  "punteo_maximo_total": 0.0,
  "porcentaje": 0.0,
  "preguntas": [
    {
      "numero": 1,
      "serie_seccion": "Serie I",
      "item": 1,
      "texto_pregunta": "Enunciado de la pregunta",
      "respuesta_estudiante": "Lo que escribió el estudiante",
      "respuesta_correcta": "La respuesta esperada según los materiales",
      "es_correcta": false,
      "punteo_obtenido": 0.0,
      "punteo_maximo": 0.0,
      "justificacion": "Explicación breve y clara",
      "errores_especificos": ["error 1", "error 2"],
      "tiene_latex": false
    }
  ],
  "conclusion": "Resumen del desempeño general del estudiante",
  "fortalezas": ["fortaleza 1"],
  "debilidades": ["debilidad 1"],
  "sugerencias": ["sugerencia 1"],
  "discrepancias_resueltas": []
}
"""

SCHEMA_PRE_ANALISIS = """
{
  "estudiante": "Nombre del estudiante o vacío si no se detecta",
  "series_detectadas": ["Serie I", "Serie II"],
  "preguntas": [
    {
      "numero": 1,
      "serie_seccion": "Serie I",
      "item": 1,
      "tipo": "matematicas|seleccion_multiple|verdadero_falso|desarrollo|relacionar|completar|otro",
      "texto_pregunta": "Enunciado completo de la pregunta como aparece en el examen impreso",
      "respuesta_estudiante": "Exactamente lo que escribió/marcó el estudiante, sin modificar",
      "tiene_latex": false
    }
  ]
}
"""


# ─────────────────────────────────────────────
# Utilidades de nombres de series
# ─────────────────────────────────────────────

def _normalizar_nombre_serie(nombre: str | None, index: int | None = None) -> str:
    if not nombre:
        return f"Serie {index + 1}" if index is not None else "Sin serie"

    texto = str(nombre).strip()
    if not texto:
        return f"Serie {index + 1}" if index is not None else "Sin serie"

    if texto.lower().startswith(("serie", "sección", "seccion")):
        return (
            texto
            .replace("Sección", "Serie")
            .replace("sección", "Serie")
            .replace("seccion", "Serie")
        )

    if re.fullmatch(r"[ivxlcdm]+", texto, flags=re.IGNORECASE):
        return f"Serie {texto.upper()}"

    return texto


def _serie_key(nombre: str | None) -> str:
    """
    Normaliza nombres de series a una clave canónica.
    Maneja todos los formatos: "Serie I", "I SERIE", "III SERIE", "SERIE III",
    "Serie 1", "1", "I", etc.
    """
    if not nombre:
        return "sin serie"

    texto = str(nombre).strip().lower()
    texto = texto.replace("sección", "serie").replace("seccion", "serie")
    texto = re.sub(r"[\.:_\-]+$", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

    # Extraer el número romano o arábigo que identifica la serie
    # Formato "I SERIE", "II SERIE", "III SERIE", etc. — romano al inicio
    m = re.match(r"^([ivxlcdm]+)\s+serie", texto, flags=re.IGNORECASE)
    if m:
        return f"serie {m.group(1).lower()}"

    # Formato "SERIE I", "Serie II", "serie iii" — serie + romano
    m = re.match(r"^serie\s+([ivxlcdm]+)$", texto, flags=re.IGNORECASE)
    if m:
        return f"serie {m.group(1).lower()}"

    # Formato "Serie 1", "serie 2" — serie + número
    m = re.match(r"^serie\s+(\d+)$", texto, flags=re.IGNORECASE)
    if m:
        return f"serie {m.group(1)}"

    # Solo romano: "I", "II", "III"
    if re.fullmatch(r"[ivxlcdm]+", texto, flags=re.IGNORECASE):
        return f"serie {texto}"

    # Solo número: "1", "2"
    if re.fullmatch(r"\d+", texto):
        return f"serie {texto}"

    # Cualquier otro texto que empiece con "serie"
    if texto.startswith("serie"):
        return texto

    return texto or "sin serie"


def _formatear_distribucion(distribucion_series: list) -> str:
    if not distribucion_series:
        return "No se definió distribución por series. Usa el punteo máximo total."

    lineas = []
    for i, serie in enumerate(distribucion_series):
        if not isinstance(serie, dict):
            continue
        nombre = _normalizar_nombre_serie(serie.get("nombre"), i)
        valor = _safe_float(serie.get("valor"), 0.0)
        lineas.append(f"- {nombre}: {valor} puntos")

    return "\n".join(lineas) if lineas else "No se definió distribución válida."


# ─────────────────────────────────────────────
# PASO 0 — Prompt de Pre-Análisis
# ─────────────────────────────────────────────

def _build_pre_analisis_prompt(texto_icr: str) -> str:
    texto_icr = _truncate_text(texto_icr, 20000)
    return f"""
Eres un extractor de datos de exámenes académicos. Tu ÚNICA tarea es leer el texto
transcrito de un examen (ICR) y extraer su estructura completa.

NO califiques. NO corrijas. NO interpretes si la respuesta es correcta o no.
Extrae FIELMENTE y COMPLETAMENTE todo lo que está escrito.

TEXTO DEL EXAMEN (transcripción ICR):
{texto_icr}

INSTRUCCIONES CRÍTICAS:
1. Detecta el nombre del estudiante si aparece.
2. Identifica TODAS las series o secciones del examen (Serie I, Serie II, III SERIE, etc.).
3. Dentro de cada serie, extrae TODOS los ítems/preguntas — no omitas ninguno.
   - Cuenta los ítems en el examen y verifica que los extraes todos.
4. Para cada ítem copia:
   - "texto_pregunta": el enunciado completo tal como aparece en el examen impreso.
   - "respuesta_estudiante": exactamente lo que escribió/marcó el estudiante.
     * Para selección múltiple: la letra o texto de la opción marcada (ej: "A", "Democracia").
     * Para verdadero/falso: la letra marcada (V o F).
     * Para desarrollo: el texto completo escrito por el estudiante.
     * Para matemáticas: la expresión o resultado escrito por el estudiante (en LaTeX si aplica).
     * Para relacionar columnas: lista de pares {{izquierda, derecha}} según las líneas trazadas.
     * Si el estudiante dejó en blanco: "".
5. Incluye el tipo de pregunta en "tipo": matematicas | seleccion_multiple | verdadero_falso | desarrollo | relacionar | completar | otro.
6. No inventes respuestas. Si el ICR no muestra respuesta, usa "".
7. Incluye fórmulas y expresiones matemáticas en LaTeX ($...$) tal como aparecen en el ICR.

IMPORTANTE: Devuelve ÚNICAMENTE JSON válido. Sin markdown. Sin texto fuera del JSON.

Formato requerido:
{SCHEMA_PRE_ANALISIS}
"""


# ─────────────────────────────────────────────
# PASO 1 — Prompt de Calificadores A y B
# ─────────────────────────────────────────────

def _calcular_tabla_punteos(distribucion_series: list, preguntas: list) -> str:
    """Genera una tabla explícita de punteo por serie e ítem para incluir en el prompt."""
    if not distribucion_series or not preguntas:
        return ""

    lineas = ["TABLA DE PUNTEO POR SERIE (USA ESTOS VALORES EXACTOS):"]

    for i, serie in enumerate(distribucion_series):
        if not isinstance(serie, dict):
            continue
        nombre = _normalizar_nombre_serie(serie.get("nombre"), i)
        valor_serie = _safe_float(serie.get("valor"), 0.0)
        if valor_serie <= 0:
            continue

        key = _serie_key(nombre)
        items_serie = [
            p for p in preguntas
            if _serie_key(p.get("serie_seccion") or p.get("serie") or "") == key
        ]
        n_items = len(items_serie) if items_serie else 1
        valor_item = round(valor_serie / n_items, 2)

        lineas.append(f"  {nombre}: {valor_serie} pts total ÷ {n_items} ítem(s) = {valor_item} pts por ítem")

    return "\n".join(lineas)


def _build_calificador_prompt(
    pre_analisis: dict,
    contexto_rag: str,
    nivel: int,
    agente_id: str,
    punteo_maximo: float,
    distribucion_series: list,
) -> str:
    nivel_desc = _nivel_descripcion(nivel)
    distribucion_texto = _formatear_distribucion(distribucion_series)
    contexto_rag = _truncate_text(contexto_rag, 10000)
    preguntas_icr = pre_analisis.get("preguntas") or []
    n_preguntas = len(preguntas_icr)
    tabla_punteos = _calcular_tabla_punteos(distribucion_series, preguntas_icr)
    pre_analisis_txt = _json_dumps_compacto(pre_analisis, 14000)

    return f"""
Eres {agente_id}, calificador académico experto de DeepGrader AI.

IDIOMA: Responde siempre en español.
NIVEL DE EXIGENCIA: {nivel}/10 — {nivel_desc}

═══════════════════════════════════════════════
REGLA FUNDAMENTAL — CANTIDAD DE PREGUNTAS
═══════════════════════════════════════════════
El pre-análisis ICR contiene exactamente {n_preguntas} ítem(s).
DEBES calificar EXACTAMENTE {n_preguntas} ítems — ni uno más, ni uno menos.
Cada ítem del pre-análisis debe tener su entrada en "preguntas" en el JSON de salida.
NO omitas ítems aunque la respuesta esté en blanco (califica como 0 con justificación).

═══════════════════════════════════════════════
PUNTEO OFICIAL
═══════════════════════════════════════════════
PUNTEO MÁXIMO TOTAL: {punteo_maximo} puntos
DISTRIBUCIÓN POR SERIES:
{distribucion_texto}

{tabla_punteos}

REGLAS DE PUNTEO (obligatorias):
1. "punteo_maximo_total" = exactamente {punteo_maximo}.
2. Suma de todos los "punteo_maximo" de las preguntas = exactamente {punteo_maximo}.
3. Usa los valores de la tabla anterior para "punteo_maximo" de cada ítem.
4. "punteo_obtenido" nunca puede superar "punteo_maximo" de ese ítem.
5. Si es_correcta: true → punteo_obtenido = punteo_maximo (o punteo parcial si procede).
6. Si es_correcta: true → punteo_obtenido NUNCA puede ser 0.
7. Si es_correcta: false y respuesta está en blanco → punteo_obtenido = 0.

═══════════════════════════════════════════════
REGLAS DE CORRECCIÓN POR TIPO DE ÍTEM
═══════════════════════════════════════════════
MATEMÁTICAS / DESARROLLO:
  - Compara la respuesta del estudiante con la respuesta correcta (consulta el RAG).
  - Para punteo parcial: si el procedimiento es correcto pero el resultado tiene un error menor,
    otorga entre 50%-80% del punteo según el nivel de exigencia.
  - Acepta notaciones equivalentes (ej: (y-5)^3 equivale a $(y-5)^3$).

SELECCIÓN MÚLTIPLE:
  - Correcta solo si la opción marcada coincide exactamente con la respuesta correcta.
  - No hay punteo parcial en selección múltiple.

VERDADERO / FALSO:
  - Correcta solo si V/F coincide con la respuesta real de la afirmación.
  - No hay punteo parcial en V/F.

RELACIONAR COLUMNAS:
  - El ICR detecta las líneas/flechas trazadas por el estudiante como pares {{izquierda, derecha}}.
  - Verifica si CADA par coincide con el par correcto según el RAG o el enunciado.
  - Si el estudiante relacionó correctamente TODOS los pares → es_correcta: true, punteo completo.
  - Si relacionó ALGUNOS correctamente → es_correcta: false, punteo parcial proporcional
    (ej: 3 de 5 correctos → 60% del punteo de ese ítem).
  - Si la respuesta_estudiante está vacía o no hay líneas detectadas → es_correcta: false, punteo = 0.

COMPLETAR:
  - Correcta si las respuestas insertadas son correctas según el RAG.
  - Punteo parcial si solo algunas respuestas son correctas.

GENERAL:
  - No penalices por ortografía ni presentación salvo nivel >= 9.
  - Si el RAG no tiene información, usa criterio académico y acláralo en la justificación.
  - Respuesta en blanco = siempre es_correcta: false, punteo_obtenido: 0.

═══════════════════════════════════════════════
MATERIALES DEL CURSO (RAG — respuestas correctas esperadas)
═══════════════════════════════════════════════
{contexto_rag}

═══════════════════════════════════════════════
ESTRUCTURA DEL EXAMEN (pre-extraída por ICR — {n_preguntas} ítems)
═══════════════════════════════════════════════
{pre_analisis_txt}

IMPORTANTE: Devuelve ÚNICAMENTE JSON válido. Sin markdown. Sin texto fuera del JSON.
Verifica antes de responder: ¿tu JSON contiene exactamente {n_preguntas} entradas en "preguntas"?

Formato obligatorio:
{SCHEMA_CALIFICACION}
"""


# ─────────────────────────────────────────────
# PASO 2 — Prompt del Juez
# ─────────────────────────────────────────────

def _build_juez_prompt(
    pre_analisis: dict,
    contexto_rag: str,
    nivel: int,
    resultado_b: dict,
    punteo_maximo: float,
    distribucion_series: list,
) -> str:
    nivel_desc = _nivel_descripcion(nivel)
    distribucion_texto = _formatear_distribucion(distribucion_series)
    contexto_rag = _truncate_text(contexto_rag, 8000)
    preguntas_icr = pre_analisis.get("preguntas") or []
    n_preguntas = len(preguntas_icr)
    tabla_punteos = _calcular_tabla_punteos(distribucion_series, preguntas_icr)
    pre_analisis_txt = _json_dumps_compacto(pre_analisis, 10000)
    resultado_b_txt = _json_dumps_compacto(resultado_b, 9000)

    return f"""
Eres el Juez/Supervisor de DeepGrader AI. Recibes la calificación del Calificador,
la revisas ítem por ítem y emites la calificación FINAL y DEFINITIVA.

IDIOMA: Responde siempre en español.
NIVEL DE EXIGENCIA: {nivel}/10 — {nivel_desc}

═══════════════════════════════════════════════
REGLA FUNDAMENTAL — CANTIDAD DE PREGUNTAS
═══════════════════════════════════════════════
El examen tiene exactamente {n_preguntas} ítem(s).
Tu JSON de salida DEBE contener exactamente {n_preguntas} entradas en "preguntas".
Si el Calificador omitió algún ítem, agrégalo tú con la corrección correspondiente.

═══════════════════════════════════════════════
PUNTEO OFICIAL
═══════════════════════════════════════════════
PUNTEO MÁXIMO TOTAL: {punteo_maximo} puntos
DISTRIBUCIÓN POR SERIES:
{distribucion_texto}

{tabla_punteos}

REGLAS ABSOLUTAS DE PUNTEO:
- "punteo_maximo_total" = exactamente {punteo_maximo}.
- Suma de "punteo_maximo" de todas las preguntas = exactamente {punteo_maximo}.
- Si es_correcta: true → punteo_obtenido = punteo_maximo (o punteo parcial justificado).
- Si es_correcta: true → punteo_obtenido NUNCA puede ser 0.
- Si es_correcta: false → punteo_obtenido puede ser 0 o parcial, nunca igual a punteo_maximo.
- Respuesta en blanco = siempre es_correcta: false, punteo_obtenido: 0.

═══════════════════════════════════════════════
PROTOCOLO DE REVISIÓN
═══════════════════════════════════════════════
Para cada ítem del pre-análisis:
1. Lee la respuesta_estudiante en el ICR.
2. Consulta el RAG para la respuesta correcta esperada.
3. Verifica si la decisión del Calificador (es_correcta + punteo) es correcta:
   - RELACIONAR: ¿cada par {{izquierda, derecha}} coincide con el par correcto? Si el
     Calificador marcó "no respondió" pero el ICR sí muestra pares → corrígelo.
   - MATEMÁTICAS: ¿el resultado/procedimiento es matemáticamente correcto?
   - SELECCIÓN MÚLTIPLE / V-F: ¿la opción marcada es la correcta?
   - DESARROLLO: ¿la respuesta aborda correctamente la pregunta?
4. Si el Calificador se equivocó → corrige es_correcta y punteo_obtenido, y registra
   la corrección en "discrepancias_resueltas".
5. Si el Calificador acertó → confirma sin cambios.

═══════════════════════════════════════════════
ESTRUCTURA DEL EXAMEN (referencia ICR — {n_preguntas} ítems)
═══════════════════════════════════════════════
{pre_analisis_txt}

═══════════════════════════════════════════════
MATERIALES DEL CURSO (RAG)
═══════════════════════════════════════════════
{contexto_rag}

═══════════════════════════════════════════════
CALIFICACIÓN DEL CALIFICADOR (para revisar)
═══════════════════════════════════════════════
{resultado_b_txt}

IMPORTANTE: Devuelve ÚNICAMENTE JSON válido. Sin markdown. Sin texto fuera del JSON.
Verifica: ¿tu JSON tiene exactamente {n_preguntas} entradas en "preguntas"?

Formato obligatorio:
{SCHEMA_CALIFICACION}
"""


# ─────────────────────────────────────────────
# Invocaciones por proveedor
# ─────────────────────────────────────────────

def _calcular_max_tokens(prompt: str) -> int:
    if len(prompt) > 30000:
        return 7000
    if len(prompt) > 18000:
        return 6000
    return DEFAULT_MAX_TOKENS


def _invoke_groq(model: str, prompt: str, max_tokens: int) -> tuple[str, int]:
    client = _get_groq_client()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.10,
            max_tokens=max_tokens,
            timeout=AGENT_TIMEOUT_SECONDS,
            response_format={"type": "json_object"},
        )
    except TypeError:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.10,
            max_tokens=max_tokens,
            timeout=AGENT_TIMEOUT_SECONDS,
        )
    raw = (response.choices[0].message.content or "").strip()
    usage = getattr(response, "usage", None)
    tokens = int(getattr(usage, "total_tokens", 0) or 0)
    return raw, tokens


def _invoke_gemini(model: str, prompt: str, max_tokens: int) -> tuple[str, int]:
    from google.genai import types as _genai_types
    client = _get_gemini_client()
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=_genai_types.GenerateContentConfig(
            temperature=0.10,
            max_output_tokens=max_tokens,
            response_mime_type="application/json",
        ),
    )
    raw = (response.text or "").strip()
    usage = getattr(response, "usage_metadata", None)
    tokens = int(getattr(usage, "total_token_count", 0) or 0)
    return raw, tokens


def _invoke_openai(model: str, prompt: str, max_tokens: int) -> tuple[str, int]:
    client = _get_openai_client()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.10,
        max_tokens=max_tokens,
        timeout=AGENT_TIMEOUT_SECONDS,
        response_format={"type": "json_object"},
    )
    raw = (response.choices[0].message.content or "").strip()
    usage = getattr(response, "usage", None)
    tokens = int(getattr(usage, "total_tokens", 0) or 0)
    return raw, tokens


def _invoke_nvidia(model: str, prompt: str, max_tokens: int) -> tuple[str, int]:
    client = _get_nvidia_client()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.10,
            max_tokens=max_tokens,
            timeout=AGENT_TIMEOUT_SECONDS,
            response_format={"type": "json_object"},
        )
    except Exception:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.10,
            max_tokens=max_tokens,
            timeout=AGENT_TIMEOUT_SECONDS,
        )
    raw = (response.choices[0].message.content or "").strip()
    usage = getattr(response, "usage", None)
    tokens = int(getattr(usage, "total_tokens", 0) or 0)
    return raw, tokens



def _call_agent(
    model: str,
    prompt: str,
    agente_nombre: str,
    provider: str = "groq",
) -> ResultadoAgente:
    """
    Llama al proveedor indicado con reintentos y parsea el JSON de respuesta.
    provider: "groq" | "gemini" | "openai" | "nvidia"
    """
    start = time.monotonic()
    error: str | None = None
    raw = ""
    parsed: dict = {}
    tokens = 0
    max_tokens = _calcular_max_tokens(prompt)

    for intento in range(MAX_RETRIES):
        try:
            if provider == "gemini":
                raw, tokens = _invoke_gemini(model, prompt, max_tokens)
            elif provider == "openai":
                raw, tokens = _invoke_openai(model, prompt, max_tokens)
            elif provider == "nvidia":
                raw, tokens = _invoke_nvidia(model, prompt, max_tokens)
            else:
                raw, tokens = _invoke_groq(model, prompt, max_tokens)

            parsed = _extract_json_object(raw)
            error = None
            break

        except json.JSONDecodeError as exc:
            error = f"JSON inválido del agente {agente_nombre}: {exc}"
            break

        except Exception as exc:
            error = str(exc)

        should_retry = (
            intento < MAX_RETRIES - 1
            and (
                "429" in str(error)
                or "rate" in str(error).lower()
                or "quota" in str(error).lower()
                or "timeout" in str(error).lower()
                or "temporarily" in str(error).lower()
                or "overloaded" in str(error).lower()
                or "503" in str(error)
            )
        )

        if should_retry:
            wait = min(8 * (intento + 1), 20)
            print(
                f"⏳ Error temporal en {agente_nombre} ({provider}): {error}. "
                f"Reintentando en {wait}s ({intento + 1}/{MAX_RETRIES})..."
            )
            time.sleep(wait)
            continue

        break

    latency = int((time.monotonic() - start) * 1000)

    return ResultadoAgente(
        agente=agente_nombre,
        modelo=f"{provider}:{model}",
        respuesta_json=parsed if isinstance(parsed, dict) else {},
        respuesta_raw=raw,
        tokens=tokens,
        latencia_ms=latency,
        error=error,
    )


# ─────────────────────────────────────────────
# Pre-análisis ICR (Paso 0)
# ─────────────────────────────────────────────

def _ejecutar_pre_analisis(texto_icr: str) -> PreAnalisis:
    """
    Paso 0: extrae la estructura del examen del ICR con un modelo rápido.
    Usa el provider/modelo del Calificador B.
    """
    prompt = _build_pre_analisis_prompt(texto_icr)

    resultado = _call_agent(
        model=settings.model_calificador_b,
        prompt=prompt,
        agente_nombre="pre_analisis",
        provider=settings.provider_calificador_b,
    )

    if resultado.error or not resultado.respuesta_json:
        print(f"⚠️  Pre-análisis falló: {resultado.error}. Se usará el ICR crudo en los calificadores.")
        return PreAnalisis(
            error=resultado.error,
            raw=resultado.respuesta_raw,
        )

    rj = resultado.respuesta_json
    return PreAnalisis(
        preguntas_detectadas=rj.get("preguntas") or [],
        series_detectadas=rj.get("series_detectadas") or [],
        estudiante=rj.get("estudiante") or "",
        raw=resultado.respuesta_raw,
    )


# ─────────────────────────────────────────────
# Normalización de preguntas base
# ─────────────────────────────────────────────

def _normalizar_pregunta_base(p: dict, numero: int) -> dict:
    pregunta = dict(p or {})

    pregunta["numero"] = _safe_int(pregunta.get("numero"), numero) or numero

    if not pregunta.get("texto_pregunta"):
        pregunta["texto_pregunta"] = (
            pregunta.get("enunciado")
            or pregunta.get("pregunta")
            or pregunta.get("instruccion")
            or ""
        )

    if not pregunta.get("respuesta_estudiante"):
        pregunta["respuesta_estudiante"] = (
            pregunta.get("respuesta")
            or pregunta.get("respuesta_marcada")
            or pregunta.get("respuesta_subrayada")
            or pregunta.get("respuestas_insertadas")
            or ""
        )

    pregunta["errores_especificos"] = _normalizar_lista(pregunta.get("errores_especificos"))
    pregunta["fortalezas"] = _normalizar_lista(pregunta.get("fortalezas"))
    pregunta["tiene_latex"] = bool(
        pregunta.get("tiene_latex")
        or "$" in str(pregunta.get("texto_pregunta", ""))
        or "$" in str(pregunta.get("respuesta_estudiante", ""))
    )

    pregunta["punteo_obtenido"] = _safe_float(pregunta.get("punteo_obtenido"), 0.0)
    pregunta["punteo_maximo"] = _safe_float(pregunta.get("punteo_maximo"), 0.0)

    # CRÍTICO: solo inferir es_correcta si el modelo NO la incluyó en absoluto.
    # No sobreescribir una decisión explícita del modelo.
    if "es_correcta" not in pregunta:
        pregunta["es_correcta"] = (
            pregunta["punteo_obtenido"] > 0
            and pregunta["punteo_obtenido"] >= pregunta["punteo_maximo"]
        )

    return pregunta


# ─────────────────────────────────────────────
# Normalización sin distribución por series
# ─────────────────────────────────────────────

def _normalizar_sin_distribucion(cf: dict, punteo_maximo: float) -> dict:
    preguntas = [
        _normalizar_pregunta_base(p, i)
        for i, p in enumerate(cf.get("preguntas") or [], start=1)
        if isinstance(p, dict)
    ]

    if not preguntas:
        cf["preguntas"] = []
        cf["punteo_total"] = 0.0
        cf["punteo_maximo_total"] = float(punteo_maximo or 0)
        cf["porcentaje"] = 0.0
        return cf

    total_obtenido = round(sum(_safe_float(p.get("punteo_obtenido")) for p in preguntas), 2)
    total_maximo_detectado = round(sum(_safe_float(p.get("punteo_maximo")) for p in preguntas), 2)

    if total_maximo_detectado <= 0 and punteo_maximo > 0:
        valor_item = round(float(punteo_maximo) / len(preguntas), 2)
        for p in preguntas:
            p["punteo_maximo"] = valor_item
            if bool(p.get("es_correcta")) and _safe_float(p.get("punteo_obtenido")) <= 0:
                p["punteo_obtenido"] = valor_item

    total_maximo_detectado = round(sum(_safe_float(p.get("punteo_maximo")) for p in preguntas), 2)

    if punteo_maximo > 0 and total_maximo_detectado > 0 and abs(total_maximo_detectado - punteo_maximo) > 0.05:
        factor = float(punteo_maximo) / total_maximo_detectado
        for p in preguntas:
            p["punteo_maximo"] = round(_safe_float(p.get("punteo_maximo")) * factor, 2)
            p["punteo_obtenido"] = round(_safe_float(p.get("punteo_obtenido")) * factor, 2)

    total_obtenido = round(sum(_safe_float(p.get("punteo_obtenido")) for p in preguntas), 2)
    total_maximo = round(sum(_safe_float(p.get("punteo_maximo")) for p in preguntas), 2)

    diferencia = round(float(punteo_maximo or total_maximo) - total_maximo, 2)
    if preguntas and punteo_maximo > 0 and abs(diferencia) > 0 and abs(diferencia) <= 0.10:
        preguntas[-1]["punteo_maximo"] = round(
            _safe_float(preguntas[-1].get("punteo_maximo")) + diferencia, 2
        )
        total_maximo = round(sum(_safe_float(p.get("punteo_maximo")) for p in preguntas), 2)

    cf["preguntas"] = preguntas
    cf["punteo_total"] = min(total_obtenido, float(punteo_maximo or total_maximo or total_obtenido))
    cf["punteo_maximo_total"] = float(punteo_maximo or total_maximo or 0)
    cf["porcentaje"] = (
        round((cf["punteo_total"] / cf["punteo_maximo_total"]) * 100, 2)
        if cf["punteo_maximo_total"] > 0
        else 0.0
    )

    return cf


# ─────────────────────────────────────────────
# Normalización con distribución por series
# (preserva es_correcta del modelo)
# ─────────────────────────────────────────────

def _normalizar_preguntas_por_series(
    cf: dict,
    punteo_maximo: float,
    distribucion_series: list,
) -> dict:
    """
    Ajusta los punteos a la distribución oficial del docente.

    CAMBIO CRÍTICO vs versión anterior:
    - es_correcta del modelo SE PRESERVA siempre.
    - Solo se recalcula punteo_obtenido proporcionalmente al nuevo punteo_maximo.
    - No se sobreescribe es_correcta basándose en el punteo resultante.
    """
    if not isinstance(cf, dict):
        cf = {}

    cf.setdefault("estudiante", "")
    cf.setdefault("serie", "")
    cf.setdefault("conclusion", "")
    cf["fortalezas"] = _normalizar_lista(cf.get("fortalezas"))
    cf["debilidades"] = _normalizar_lista(cf.get("debilidades"))
    cf["sugerencias"] = _normalizar_lista(cf.get("sugerencias"))
    cf["discrepancias_resueltas"] = _normalizar_lista(cf.get("discrepancias_resueltas"))

    preguntas_originales = [
        _normalizar_pregunta_base(p, i)
        for i, p in enumerate(cf.get("preguntas") or [], start=1)
        if isinstance(p, dict)
    ]
    cf["preguntas"] = preguntas_originales

    if not distribucion_series:
        return _normalizar_sin_distribucion(cf, float(punteo_maximo or 0))

    series_config = []
    for i, serie in enumerate(distribucion_series):
        if not isinstance(serie, dict):
            continue
        nombre = _normalizar_nombre_serie(serie.get("nombre"), i)
        valor = _safe_float(serie.get("valor"), 0.0)
        if valor <= 0:
            continue
        series_config.append({
            "nombre": nombre,
            "valor": valor,
            "key": _serie_key(nombre),
            "index": i,
        })

    if not series_config:
        return _normalizar_sin_distribucion(cf, float(punteo_maximo or 0))

    if not preguntas_originales:
        cf["preguntas"] = []
        cf["punteo_total"] = 0.0
        cf["punteo_maximo_total"] = float(punteo_maximo or sum(s["valor"] for s in series_config))
        cf["porcentaje"] = 0.0
        return cf

    # Agrupar preguntas por serie
    grupos: dict[str, list[dict]] = {s["key"]: [] for s in series_config}
    preguntas_sin_serie: list[dict] = []

    for p in preguntas_originales:
        serie_detectada = (
            p.get("serie_seccion") or p.get("serie") or p.get("seccion") or ""
        )
        key = _serie_key(serie_detectada)
        if key in grupos:
            grupos[key].append(p)
        else:
            preguntas_sin_serie.append(p)

    # Asignar preguntas sin serie detectada
    if preguntas_sin_serie:
        series_con_contenido = [s for s in series_config if grupos.get(s["key"])]
        destino = series_con_contenido[-1]["key"] if series_con_contenido else series_config[0]["key"]
        grupos[destino].extend(preguntas_sin_serie)

    preguntas_finales: list[dict] = []
    numero_global = 1

    for serie_conf in series_config:
        key = serie_conf["key"]
        nombre_serie = serie_conf["nombre"]
        valor_serie = _safe_float(serie_conf["valor"], 0.0)
        items = grupos.get(key, [])

        if not items:
            continue

        valor_item = round(valor_serie / len(items), 2) if items else 0.0

        for item_index, p in enumerate(items, start=1):
            pregunta = dict(p)

            # Preservar la decisión del modelo sobre corrección
            es_correcta_modelo = bool(pregunta.get("es_correcta", False))

            punteo_obtenido_original = _safe_float(pregunta.get("punteo_obtenido"), 0.0)
            punteo_maximo_original = _safe_float(pregunta.get("punteo_maximo"), 0.0)

            # Recalcular punteo_obtenido proporcionalmente al nuevo valor_item
            if punteo_maximo_original > 0:
                proporcion = punteo_obtenido_original / punteo_maximo_original
                proporcion = max(0.0, min(proporcion, 1.0))
                punteo_obtenido = round(valor_item * proporcion, 2)
            elif es_correcta_modelo:
                punteo_obtenido = valor_item
            else:
                punteo_obtenido = 0.0

            # Garantizar coherencia: correcta → punteo completo; incorrecta → no completo
            if es_correcta_modelo and punteo_obtenido <= 0:
                punteo_obtenido = valor_item
            if not es_correcta_modelo and punteo_obtenido >= valor_item and valor_item > 0:
                # El modelo dijo incorrecta pero la proporción da 100% → respetar modelo
                # Solo si es punteo parcial explícito, mantenerlo; si no, forzar < máximo
                if punteo_maximo_original > 0 and proporcion >= 1.0:
                    punteo_obtenido = round(valor_item * 0.5, 2)  # punteo parcial conservador

            punteo_obtenido = max(0.0, min(punteo_obtenido, valor_item))

            pregunta["numero"] = numero_global
            pregunta["serie_seccion"] = nombre_serie
            pregunta["item"] = item_index
            pregunta["punteo_maximo"] = valor_item
            pregunta["punteo_obtenido"] = round(punteo_obtenido, 2)
            # PRESERVAR es_correcta del modelo — NO sobreescribir con lógica de punteo
            pregunta["es_correcta"] = es_correcta_modelo

            preguntas_finales.append(pregunta)
            numero_global += 1

    total_obtenido = round(
        sum(_safe_float(p.get("punteo_obtenido"), 0.0) for p in preguntas_finales), 2
    )
    total_maximo = round(
        sum(_safe_float(p.get("punteo_maximo"), 0.0) for p in preguntas_finales), 2
    )

    objetivo_maximo = float(punteo_maximo or sum(s["valor"] for s in series_config) or total_maximo or 0)

    # Ajuste menor por redondeos (≤ 0.10 pts)
    diferencia = round(objetivo_maximo - total_maximo, 2)
    if preguntas_finales and abs(diferencia) > 0 and abs(diferencia) <= 0.10:
        preguntas_finales[-1]["punteo_maximo"] = round(
            _safe_float(preguntas_finales[-1].get("punteo_maximo"), 0.0) + diferencia, 2
        )
        total_maximo = round(
            sum(_safe_float(p.get("punteo_maximo"), 0.0) for p in preguntas_finales), 2
        )

    # Escala solo si hay error grande por mala agrupación de series
    if preguntas_finales and objetivo_maximo > 0 and total_maximo > 0 and abs(objetivo_maximo - total_maximo) > 0.10:
        factor = objetivo_maximo / total_maximo
        for p in preguntas_finales:
            p["punteo_maximo"] = round(_safe_float(p.get("punteo_maximo"), 0.0) * factor, 2)
            p["punteo_obtenido"] = round(_safe_float(p.get("punteo_obtenido"), 0.0) * factor, 2)

        total_obtenido = round(
            sum(_safe_float(p.get("punteo_obtenido"), 0.0) for p in preguntas_finales), 2
        )
        total_maximo = round(
            sum(_safe_float(p.get("punteo_maximo"), 0.0) for p in preguntas_finales), 2
        )

    total_obtenido = min(total_obtenido, objetivo_maximo)

    cf["preguntas"] = preguntas_finales
    cf["punteo_total"] = round(total_obtenido, 2)
    cf["punteo_maximo_total"] = round(objetivo_maximo, 2)
    cf["porcentaje"] = (
        round((total_obtenido / objetivo_maximo) * 100, 2) if objetivo_maximo > 0 else 0.0
    )

    return cf


# ─────────────────────────────────────────────
# Fallback de consenso (sin juez)
# Usa mayoría en lugar de promedio
# ─────────────────────────────────────────────

def _merge_results(
    a: dict,
    b: dict,
    nivel: int,
    punteo_maximo: float = 100.0,
    distribucion_series: list | None = None,
) -> dict:
    """
    Fallback cuando el juez falla.

    CAMBIO vs versión anterior:
    - Ya NO promedia punteos cuando hay discrepancia en es_correcta.
    - Lógica de mayoría: si uno dice correcta y otro incorrecta,
      el nivel de exigencia decide (bajo → favorece al estudiante; alto → penaliza).
    - Si ambos coinciden en es_correcta, toma el punteo del que marcó correcta.
    """
    distribucion_series = distribucion_series or []
    a = a if isinstance(a, dict) else {}
    b = b if isinstance(b, dict) else {}

    base = dict(b or a)
    base["nivel_aplicado"] = nivel

    preguntas_a = {
        _safe_int(p.get("numero"), index + 1) or index + 1: p
        for index, p in enumerate(a.get("preguntas", []) or [])
        if isinstance(p, dict)
    }
    preguntas_b = {
        _safe_int(p.get("numero"), index + 1) or index + 1: p
        for index, p in enumerate(b.get("preguntas", []) or [])
        if isinstance(p, dict)
    }

    preguntas_final: list[dict] = []
    todas = sorted(set(preguntas_a.keys()) | set(preguntas_b.keys()))

    for num in todas:
        pa = preguntas_a.get(num)
        pb = preguntas_b.get(num)
        referencia = pb or pa or {}

        correcta_a = bool((pa or {}).get("es_correcta", False))
        correcta_b = bool((pb or {}).get("es_correcta", False))
        punteo_a = _safe_float((pa or {}).get("punteo_obtenido"), 0.0)
        punteo_b = _safe_float((pb or {}).get("punteo_obtenido"), 0.0)
        max_a = _safe_float((pa or {}).get("punteo_maximo"), 0.0)
        max_b = _safe_float((pb or {}).get("punteo_maximo"), 0.0)

        merged_q = dict(referencia)
        merged_q["numero"] = num

        if pa and pb:
            if correcta_a == correcta_b:
                # Ambos coinciden → toma el promedio solo de punteos, respeta correcta
                es_correcta = correcta_a
                if correcta_a:
                    # Ambos correctos: usa el mayor punteo
                    punteo = max(punteo_a, punteo_b)
                else:
                    # Ambos incorrectos: usa el mayor (puede haber punteo parcial)
                    punteo = max(punteo_a, punteo_b)
            else:
                # Discrepancia: el nivel de exigencia decide
                # Nivel bajo (1-5): beneficio de la duda → favorece correcta
                # Nivel alto (6-10): criterio estricto → favorece incorrecta
                if nivel <= 5:
                    es_correcta = True
                    punteo = max(punteo_a, punteo_b)
                else:
                    es_correcta = False
                    punteo = min(punteo_a, punteo_b)
        elif pa:
            es_correcta = correcta_a
            punteo = punteo_a
        else:
            es_correcta = correcta_b
            punteo = punteo_b

        merged_q["es_correcta"] = es_correcta
        merged_q["punteo_obtenido"] = round(punteo, 2)
        merged_q["justificacion"] = (
            "[Fallback A/B — juez no disponible] "
            f"A: {(pa or {}).get('justificacion', 'sin respuesta')} | "
            f"B: {(pb or {}).get('justificacion', 'sin respuesta')}"
        )

        preguntas_final.append(merged_q)

    base["preguntas"] = preguntas_final
    base.setdefault("conclusion", "Calificación generada por fallback A/B porque el juez no respondió.")
    base.setdefault("fortalezas", [])
    base.setdefault("debilidades", [])
    base.setdefault("sugerencias", [])
    base.setdefault("discrepancias_resueltas", [])

    return _normalizar_preguntas_por_series(
        cf=base,
        punteo_maximo=float(punteo_maximo or 0),
        distribucion_series=distribucion_series,
    )


# ─────────────────────────────────────────────
# Orquestador principal
# ─────────────────────────────────────────────

async def run_consensus_grading(
    examen_id: int,
    texto_icr: str,
    contexto_rag: str,
    nivel_exigencia: int,
    punteo_maximo: float = 100.0,
    distribucion_series: list | None = None,
    pil_images: list | None = None,
) -> ResultadoConsenso:
    """
    Ejecuta el consenso mejorado de 3 etapas:

    Etapa 0 — Pre-análisis: extrae la estructura real del examen del ICR.
    Etapa 1 — Calificador B: califica usando el pre-análisis.
    Etapa 2 — Juez: revisa y valida la calificación final.
    Etapa 3 — Post-proceso determinista: normaliza punteos por distribución oficial.
    """
    del pil_images  # Conservado en la firma por compatibilidad.

    resultado = ResultadoConsenso(
        examen_id=examen_id,
        nivel_exigencia=nivel_exigencia,
    )

    distribucion_series = distribucion_series or []
    punteo_maximo = float(punteo_maximo or 0)

    try:
        loop = asyncio.get_running_loop()

        # ── ETAPA 0: Pre-análisis ICR ──────────────────────────
        print(f"🔍 [Examen {examen_id}] Ejecutando pre-análisis ICR...")
        pre_analisis = await loop.run_in_executor(
            None,
            _ejecutar_pre_analisis,
            texto_icr,
        )
        resultado.pre_analisis = pre_analisis

        # Si el pre-análisis falló, usamos un dict vacío y los calificadores
        # leerán el ICR crudo desde el prompt (construido con fallback abajo).
        pre_analisis_dict: dict = {}
        if pre_analisis and not pre_analisis.error and pre_analisis.preguntas_detectadas:
            pre_analisis_dict = {
                "estudiante": pre_analisis.estudiante,
                "series_detectadas": pre_analisis.series_detectadas,
                "preguntas": pre_analisis.preguntas_detectadas,
            }
            print(
                f"✅ Pre-análisis OK: {len(pre_analisis.preguntas_detectadas)} preguntas, "
                f"{len(pre_analisis.series_detectadas)} series detectadas."
            )
        else:
            print("⚠️  Pre-análisis sin datos; calificadores usarán ICR crudo.")
            # Fallback: incluir el ICR crudo como pre-análisis para que los modelos no queden ciegos
            pre_analisis_dict = {
                "estudiante": "",
                "series_detectadas": [],
                "preguntas": [],
                "_nota": "Pre-análisis no disponible. Lee el ICR directamente desde el contexto del examen.",
                "_icr_crudo": _truncate_text(texto_icr, 8000),
            }

        # ── ETAPA 1: Calificador B ─────────────────────────────
        print(f"📝 [Examen {examen_id}] Lanzando Calificador B...")

        prompt_b = _build_calificador_prompt(
            pre_analisis=pre_analisis_dict,
            contexto_rag=contexto_rag,
            nivel=nivel_exigencia,
            agente_id="Calificador B",
            punteo_maximo=punteo_maximo,
            distribucion_series=distribucion_series,
        )

        resultado_b = await loop.run_in_executor(
            None,
            _call_agent,
            settings.model_calificador_b,
            prompt_b,
            "calificador_b",
            settings.provider_calificador_b,
        )

        resultado.resultado_a = None
        resultado.resultado_b = resultado_b

        json_b = resultado_b.respuesta_json if resultado_b and not resultado_b.error else {}

        # Recuperar JSON aunque haya error de parseo parcial
        if not json_b and resultado_b and resultado_b.respuesta_json:
            json_b = resultado_b.respuesta_json

        # Calificador B falló
        if not json_b:
            resultado.error = "El calificador falló o devolvió JSON inválido."
            resultado.calificacion_final = _normalizar_preguntas_por_series(
                cf={
                    "nivel_aplicado": nivel_exigencia,
                    "punteo_total": 0.0,
                    "punteo_maximo_total": punteo_maximo,
                    "porcentaje": 0.0,
                    "preguntas": [],
                    "conclusion": "No fue posible calificar porque el calificador falló.",
                    "fortalezas": [],
                    "debilidades": ["No se obtuvo una evaluación válida."],
                    "sugerencias": ["Revisar la calidad del ICR y volver a procesar."],
                    "discrepancias_resueltas": [],
                },
                punteo_maximo=punteo_maximo,
                distribucion_series=distribucion_series,
            )
            return resultado

        # ── ETAPA 2: Juez ──────────────────────────────────────
        print(f"⚖️  [Examen {examen_id}] Ejecutando Juez/Supervisor...")

        prompt_juez = _build_juez_prompt(
            pre_analisis=pre_analisis_dict,
            contexto_rag=contexto_rag,
            nivel=nivel_exigencia,
            resultado_b=json_b,
            punteo_maximo=punteo_maximo,
            distribucion_series=distribucion_series,
        )

        resultado_juez = await loop.run_in_executor(
            None,
            _call_agent,
            settings.model_juez,
            prompt_juez,
            "juez",
            settings.provider_juez,
        )

        resultado.resultado_juez = resultado_juez

        # ── ETAPA 3: Post-proceso determinista ─────────────────
        if resultado_juez and resultado_juez.respuesta_json and not resultado_juez.error:
            cf = dict(resultado_juez.respuesta_json)
            cf["nivel_aplicado"] = nivel_exigencia
            cf = _normalizar_preguntas_por_series(
                cf=cf,
                punteo_maximo=punteo_maximo,
                distribucion_series=distribucion_series,
            )
            resultado.discrepancias = cf.get("discrepancias_resueltas", [])
            resultado.calificacion_final = cf
            print(f"✅ [Examen {examen_id}] Calificación final por Juez. Punteo: {cf.get('punteo_total')}/{cf.get('punteo_maximo_total')}")
            return resultado

        # Juez respondió con error de parseo parcial pero tiene JSON
        if resultado_juez and resultado_juez.respuesta_json:
            cf = dict(resultado_juez.respuesta_json)
            cf["nivel_aplicado"] = nivel_exigencia
            cf = _normalizar_preguntas_por_series(
                cf=cf,
                punteo_maximo=punteo_maximo,
                distribucion_series=distribucion_series,
            )
            resultado.discrepancias = cf.get("discrepancias_resueltas", [])
            resultado.calificacion_final = cf
            resultado.error = f"Juez con advertencia: {resultado_juez.error}"
            print(f"⚠️  [Examen {examen_id}] Juez con advertencia. Punteo: {cf.get('punteo_total')}/{cf.get('punteo_maximo_total')}")
            return resultado

        # Fallback: usar resultado de B directamente
        print(f"⚠️  [Examen {examen_id}] Juez falló; usando resultado del Calificador B como fallback.")
        cf = dict(json_b)
        cf["nivel_aplicado"] = nivel_exigencia
        cf.setdefault("conclusion", "Calificación generada por Calificador B (juez no disponible).")
        cf.setdefault("fortalezas", [])
        cf.setdefault("debilidades", [])
        cf.setdefault("sugerencias", [])
        cf.setdefault("discrepancias_resueltas", [])
        cf = _normalizar_preguntas_por_series(
            cf=cf,
            punteo_maximo=punteo_maximo,
            distribucion_series=distribucion_series,
        )
        resultado.calificacion_final = cf
        resultado.discrepancias = cf.get("discrepancias_resueltas", [])
        resultado.error = (
            f"Juez falló; se usó resultado del Calificador B. "
            f"Error juez: {(resultado_juez.error if resultado_juez else 'sin respuesta')}"
        )
        return resultado

    except Exception as exc:
        resultado.error = str(exc)
        resultado.calificacion_final = _normalizar_preguntas_por_series(
            cf={
                "nivel_aplicado": nivel_exigencia,
                "punteo_total": 0.0,
                "punteo_maximo_total": punteo_maximo,
                "porcentaje": 0.0,
                "preguntas": [],
                "conclusion": f"Error durante el consenso: {exc}",
                "fortalezas": [],
                "debilidades": ["No se pudo completar la calificación automática."],
                "sugerencias": ["Revisar logs del backend y reintentar."],
                "discrepancias_resueltas": [],
            },
            punteo_maximo=punteo_maximo,
            distribucion_series=distribucion_series,
        )
        return resultado