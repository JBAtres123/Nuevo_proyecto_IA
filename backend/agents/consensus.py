"""
EduGrade AI / DeepGrader AI — Sistema de Consenso con 3 Agentes IA
==================================================================

Agente 1 (Calificador A) ─┐
                          ├─→ Agente 3 (Juez/Supervisor) → Calificación Final
Agente 2 (Calificador B) ─┘

Objetivo:
- Evaluar exámenes transcritos por ICR.
- Comparar contra contexto RAG del curso.
- Respetar el punteo máximo y la distribución oficial por series.
- Evitar que un fallo del juez rompa todo el procesamiento.

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

_client: Groq | None = None

# Reducido según la auditoría: 90s x 3 agentes podía volver muy lento el lote.
AGENT_TIMEOUT_SECONDS = 60
MAX_RETRIES = 3
DEFAULT_MAX_TOKENS = 6000


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.groq_api_key)
    return _client


# ─────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────

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
    return text[:max_chars].rstrip() + "\n[... texto truncado para mantener estable el modelo ...]"


def _clean_model_response(raw: str) -> str:
    cleaned = str(raw or "").strip()
    cleaned = re.sub(r"```(?:json)?", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.replace("```", "")
    cleaned = cleaned.strip().strip("`").strip()
    return cleaned


def _extract_json_object(text: str) -> dict:
    """
    Intenta extraer un JSON válido aunque el modelo agregue texto extra.
    Evita depender únicamente de una regex codiciosa.
    """
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
# Prompts / Utilidades
# ─────────────────────────────────────────────

def _nivel_descripcion(nivel: int) -> str:
    if nivel <= 2:
        return (
            "MUY INDULGENTE: valora el esfuerzo y el proceso. Tolera errores "
            "menores de notación o signos. Otorga puntaje parcial generosamente."
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
        "MUY ESTRICTO / EXPERTO: evaluación académica rigurosa. Penaliza errores "
        "conceptuales o de procedimiento. Solo da puntaje completo si todo es correcto."
    )


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
  "fortalezas": ["fortaleza 1", "fortaleza 2"],
  "debilidades": ["debilidad 1", "debilidad 2"],
  "sugerencias": ["sugerencia 1", "sugerencia 2"],
  "discrepancias_resueltas": []
}
"""


def _normalizar_nombre_serie(nombre: str | None, index: int | None = None) -> str:
    if not nombre:
        return f"Serie {index + 1}" if index is not None else "Sin serie"

    texto = str(nombre).strip()

    if not texto:
        return f"Serie {index + 1}" if index is not None else "Sin serie"

    if texto.lower().startswith(("serie", "sección", "seccion")):
        return texto.replace("Sección", "Serie").replace("sección", "Serie").replace("seccion", "Serie")

    if re.fullmatch(r"[ivxlcdm]+", texto, flags=re.IGNORECASE):
        return f"Serie {texto.upper()}"

    return texto


def _serie_key(nombre: str | None) -> str:
    if not nombre:
        return "sin serie"

    texto = str(nombre).strip().lower()
    texto = texto.replace("sección", "serie")
    texto = texto.replace("seccion", "serie")
    texto = re.sub(r"[\.:_-]+$", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

    if not texto.startswith("serie"):
        if re.fullmatch(r"[ivxlcdm]+", texto, flags=re.IGNORECASE):
            texto = f"serie {texto.upper()}".lower()
        elif re.fullmatch(r"\d+", texto):
            texto = f"serie {texto}"

    return texto or "sin serie"


def _formatear_distribucion(distribucion_series: list) -> str:
    if not distribucion_series:
        return "No se definió distribución por series. Usa el punteo máximo total del examen."

    lineas = []

    for i, serie in enumerate(distribucion_series):
        if not isinstance(serie, dict):
            continue
        nombre = _normalizar_nombre_serie(serie.get("nombre"), i)
        valor = _safe_float(serie.get("valor"), 0.0)
        lineas.append(f"- {nombre}: {valor} puntos")

    return "\n".join(lineas) if lineas else "No se definió distribución por series válida."


def _build_calificador_prompt(
    texto_icr: str,
    contexto_rag: str,
    nivel: int,
    agente_id: str,
    punteo_maximo: float,
    distribucion_series: list,
) -> str:
    nivel_desc = _nivel_descripcion(nivel)
    distribucion_texto = _formatear_distribucion(distribucion_series)

    texto_icr = _truncate_text(texto_icr, 18000)
    contexto_rag = _truncate_text(contexto_rag, 10000)

    return f"""
Eres {agente_id}, un agente evaluador de exámenes académicos de DeepGrader AI.

IDIOMA:
Responde siempre en español claro. El examen puede contener abreviaturas comunes en Guatemala como Pts., Cte., No. o Resp.

NIVEL DE EXIGENCIA: {nivel}/10
Descripción: {nivel_desc}

INFORMACIÓN OFICIAL DEL DOCENTE:
Punteo máximo total del examen: {punteo_maximo} puntos.

Distribución oficial por series:
{distribucion_texto}

REGLAS OBLIGATORIAS DE PUNTEO:
1. Respeta exactamente el punteo máximo total definido por el docente: {punteo_maximo}.
2. Si existe distribución por series, respétala por encima de cualquier suposición.
3. No califiques automáticamente cada pregunta sobre 1 punto.
4. Identifica cuántos items pertenecen a cada serie.
5. Divide el valor total de cada serie entre los items detectados en esa serie.
6. Si una serie vale 10 puntos y tiene 2 items, cada item vale 5 puntos.
7. Si una serie vale 10 puntos y tiene 5 items, cada item vale 2 puntos.
8. Cada pregunta debe incluir "serie_seccion", "item", "punteo_maximo", "punteo_obtenido" y "es_correcta".
9. La suma de "punteo_maximo" debe coincidir con {punteo_maximo}.
10. El campo "punteo_maximo_total" debe ser exactamente {punteo_maximo}.
11. Si el ICR no detecta claramente una serie, asígnala según el orden del examen.
12. No inventes respuestas correctas si el RAG no tiene contexto suficiente; en ese caso, evalúa con criterio académico general y acláralo en la justificación.

CONTEXTO DOCENTE / RAG:
{contexto_rag}

TEXTO TRANSCRITO DEL EXAMEN / ICR:
{texto_icr}

INSTRUCCIONES DE EVALUACIÓN:
1. Compara cada respuesta del estudiante con el material del curso cuando el RAG lo permita.
2. Para matemáticas en LaTeX, verifica resultado y procedimiento.
3. Da punteo parcial cuando el procedimiento tenga partes correctas.
4. Justifica cada calificación con precisión pedagógica.
5. Mantén la organización por series mediante "serie_seccion".

IMPORTANTE:
Devuelve ÚNICAMENTE JSON válido.
No uses markdown.
No agregues explicación fuera del JSON.
No uses comillas simples para JSON.

Formato obligatorio:
{SCHEMA_CALIFICACION}
"""


def _build_juez_prompt(
    texto_icr: str,
    contexto_rag: str,
    nivel: int,
    resultado_a: dict,
    resultado_b: dict,
    punteo_maximo: float,
    distribucion_series: list,
) -> str:
    nivel_desc = _nivel_descripcion(nivel)
    distribucion_texto = _formatear_distribucion(distribucion_series)

    texto_icr = _truncate_text(texto_icr, 14000)
    contexto_rag = _truncate_text(contexto_rag, 8000)
    resultado_a_txt = _json_dumps_compacto(resultado_a, 11000)
    resultado_b_txt = _json_dumps_compacto(resultado_b, 11000)

    return f"""
Eres el Agente Juez/Supervisor de DeepGrader AI. Tu rol es revisar dos evaluaciones
independientes, resolver discrepancias y emitir la calificación final.

IDIOMA:
Responde siempre en español claro.

NIVEL DE EXIGENCIA ACORDADO: {nivel}/10 — {nivel_desc}

INFORMACIÓN OFICIAL DEL DOCENTE:
Punteo máximo total del examen: {punteo_maximo} puntos.

Distribución oficial por series:
{distribucion_texto}

REGLAS OBLIGATORIAS PARA LA CALIFICACIÓN FINAL:
1. "punteo_maximo_total" debe ser exactamente {punteo_maximo}.
2. La suma de "punteo_maximo" de todas las preguntas debe ser exactamente {punteo_maximo}.
3. Respeta la distribución oficial por series.
4. Si A o B calificaron cada pregunta sobre 1 punto por error, corrige usando la distribución oficial.
5. Organiza el resultado final por series.
6. Cada pregunta debe tener "serie_seccion", "item", "punteo_maximo", "punteo_obtenido" y "es_correcta".
7. Para cada serie, divide el valor de la serie entre la cantidad de items detectados en esa serie.
8. No inventes respuestas correctas no respaldadas por RAG o por conocimiento académico básico.

EVALUACIÓN DEL CALIFICADOR A:
{resultado_a_txt}

EVALUACIÓN DEL CALIFICADOR B:
{resultado_b_txt}

TEXTO ORIGINAL DEL EXAMEN / ICR:
{texto_icr}

MATERIALES DEL CURSO / RAG:
{contexto_rag}

PROTOCOLO DE DECISIÓN:
1. Si A y B coinciden, acepta el criterio, pero ajusta el punteo a la distribución oficial.
2. Si difieren en más del 20% del punteo máximo de una pregunta, revisa ICR y RAG.
3. En caso de duda, usa el nivel de exigencia como desempate.
4. La justificación final debe ser clara, breve y pedagógica.
5. Llena "discrepancias_resueltas" con objetos:
   {{"pregunta": N, "punteo_a": X, "punteo_b": Y, "punteo_final": Z, "razon": "..."}}

IMPORTANTE:
Devuelve ÚNICAMENTE JSON válido.
No uses markdown.
No agregues texto fuera del JSON.
No uses comillas simples para JSON.

Formato obligatorio:
{SCHEMA_CALIFICACION}
"""


# ─────────────────────────────────────────────
# Agentes
# ─────────────────────────────────────────────

def _calcular_max_tokens(prompt: str) -> int:
    """
    Max tokens adaptativo simple:
    - Prompts largos suelen producir respuestas largas.
    - Se limita para evitar tiempos excesivos.
    """
    if len(prompt) > 30000:
        return 7000
    if len(prompt) > 18000:
        return 6000
    return DEFAULT_MAX_TOKENS


def _call_agent(
    model: str,
    prompt: str,
    agente_nombre: str,
) -> ResultadoAgente:
    """Llama a un agente de Groq y parsea el JSON de respuesta."""
    client = _get_client()
    start = time.monotonic()

    error: str | None = None
    raw = ""
    parsed: dict = {}
    tokens = 0
    max_tokens = _calcular_max_tokens(prompt)

    for intento in range(MAX_RETRIES):
        try:
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
            if usage:
                tokens = int(getattr(usage, "total_tokens", 0) or 0)

            parsed = _extract_json_object(raw)
            error = None
            break

        except TypeError:
            # Algunos modelos/SDKs pueden no aceptar response_format.
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.10,
                    max_tokens=max_tokens,
                    timeout=AGENT_TIMEOUT_SECONDS,
                )

                raw = (response.choices[0].message.content or "").strip()

                usage = getattr(response, "usage", None)
                if usage:
                    tokens = int(getattr(usage, "total_tokens", 0) or 0)

                parsed = _extract_json_object(raw)
                error = None
                break
            except Exception as exc:
                error = str(exc)

        except json.JSONDecodeError as exc:
            error = f"JSON inválido del agente {agente_nombre}: {exc}"
            break

        except Exception as exc:
            error = str(exc)

        # Reintentos controlados para 429, timeouts o fallos temporales.
        should_retry = (
            intento < MAX_RETRIES - 1
            and (
                "429" in str(error)
                or "rate" in str(error).lower()
                or "timeout" in str(error).lower()
                or "temporarily" in str(error).lower()
                or "503" in str(error)
            )
        )

        if should_retry:
            wait = min(8 * (intento + 1), 20)
            print(
                f"⏳ Error temporal en {agente_nombre}: {error}. "
                f"Reintentando en {wait}s ({intento + 1}/{MAX_RETRIES})..."
            )
            time.sleep(wait)
            continue

        break

    latency = int((time.monotonic() - start) * 1000)

    return ResultadoAgente(
        agente=agente_nombre,
        modelo=model,
        respuesta_json=parsed if isinstance(parsed, dict) else {},
        respuesta_raw=raw,
        tokens=tokens,
        latencia_ms=latency,
        error=error,
    )


# ─────────────────────────────────────────────
# Ajuste de punteo por series
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

    if "es_correcta" not in pregunta:
        pregunta["es_correcta"] = pregunta["punteo_obtenido"] > 0 and pregunta["punteo_obtenido"] >= pregunta["punteo_maximo"]

    return pregunta


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

    # Si el agente no asignó punteos máximos válidos, divide el punteo total.
    if total_maximo_detectado <= 0 and punteo_maximo > 0:
        valor_item = round(float(punteo_maximo) / len(preguntas), 2)
        for p in preguntas:
            p["punteo_maximo"] = valor_item
            if bool(p.get("es_correcta")) and _safe_float(p.get("punteo_obtenido")) <= 0:
                p["punteo_obtenido"] = valor_item

    total_maximo_detectado = round(sum(_safe_float(p.get("punteo_maximo")) for p in preguntas), 2)

    # Si el total detectado no coincide con el oficial, escala.
    if punteo_maximo > 0 and total_maximo_detectado > 0 and abs(total_maximo_detectado - punteo_maximo) > 0.05:
        factor = float(punteo_maximo) / total_maximo_detectado
        for p in preguntas:
            p["punteo_maximo"] = round(_safe_float(p.get("punteo_maximo")) * factor, 2)
            p["punteo_obtenido"] = round(_safe_float(p.get("punteo_obtenido")) * factor, 2)

    total_obtenido = round(sum(_safe_float(p.get("punteo_obtenido")) for p in preguntas), 2)
    total_maximo = round(sum(_safe_float(p.get("punteo_maximo")) for p in preguntas), 2)

    diferencia = round(float(punteo_maximo or total_maximo) - total_maximo, 2)
    if preguntas and punteo_maximo > 0 and abs(diferencia) > 0 and abs(diferencia) <= 0.10:
        preguntas[-1]["punteo_maximo"] = round(_safe_float(preguntas[-1].get("punteo_maximo")) + diferencia, 2)
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


def _normalizar_preguntas_por_series(
    cf: dict,
    punteo_maximo: float,
    distribucion_series: list,
) -> dict:
    """
    Refuerza el resultado final para que las preguntas queden agrupadas por serie
    y con punteo real por item según la distribución configurada por el docente.
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

    grupos: dict[str, list[dict]] = {s["key"]: [] for s in series_config}
    preguntas_sin_serie: list[dict] = []

    for p in preguntas_originales:
        serie_detectada = (
            p.get("serie_seccion")
            or p.get("serie")
            or p.get("seccion")
            or ""
        )
        key = _serie_key(serie_detectada)
        if key in grupos:
            grupos[key].append(p)
        else:
            preguntas_sin_serie.append(p)

    # Si los agentes no lograron series, se asigna todo a la primera serie.
    # Si sí hay algunas series detectadas, las preguntas sueltas se anexan a la última serie con contenido.
    if preguntas_sin_serie:
        series_con_contenido = [s for s in series_config if grupos.get(s["key"])]
        if series_con_contenido:
            destino = series_con_contenido[-1]["key"]
        else:
            destino = series_config[0]["key"]
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

        valor_item = round(valor_serie / len(items), 2) if len(items) > 0 else 0.0

        for item_index, p in enumerate(items, start=1):
            pregunta = dict(p)

            punteo_obtenido_original = _safe_float(pregunta.get("punteo_obtenido"), 0.0)
            punteo_maximo_original = _safe_float(pregunta.get("punteo_maximo"), 0.0)
            es_correcta = bool(pregunta.get("es_correcta", False))

            if punteo_maximo_original > 0:
                proporcion = punteo_obtenido_original / punteo_maximo_original
                proporcion = max(0.0, min(proporcion, 1.0))
                punteo_obtenido = round(valor_item * proporcion, 2)
            else:
                punteo_obtenido = valor_item if es_correcta else 0.0

            if es_correcta and punteo_obtenido <= 0:
                punteo_obtenido = valor_item

            punteo_obtenido = max(0.0, min(punteo_obtenido, valor_item))

            pregunta["numero"] = numero_global
            pregunta["serie_seccion"] = nombre_serie
            pregunta["item"] = item_index
            pregunta["punteo_maximo"] = valor_item
            pregunta["punteo_obtenido"] = round(punteo_obtenido, 2)
            pregunta["es_correcta"] = bool(
                pregunta.get("es_correcta")
                or (valor_item > 0 and round(punteo_obtenido, 2) >= round(valor_item, 2))
            )

            preguntas_finales.append(pregunta)
            numero_global += 1

    total_obtenido = round(
        sum(_safe_float(p.get("punteo_obtenido"), 0.0) for p in preguntas_finales),
        2,
    )

    total_maximo = round(
        sum(_safe_float(p.get("punteo_maximo"), 0.0) for p in preguntas_finales),
        2,
    )

    objetivo_maximo = float(punteo_maximo or sum(s["valor"] for s in series_config) or total_maximo or 0)

    # Ajuste por redondeos.
    diferencia = round(objetivo_maximo - total_maximo, 2)
    if preguntas_finales and abs(diferencia) > 0 and abs(diferencia) <= 0.10:
        preguntas_finales[-1]["punteo_maximo"] = round(
            _safe_float(preguntas_finales[-1].get("punteo_maximo"), 0.0) + diferencia,
            2,
        )
        total_maximo = round(
            sum(_safe_float(p.get("punteo_maximo"), 0.0) for p in preguntas_finales),
            2,
        )

    # Si por mala asignación de series faltó puntaje grande, escala para no romper el total.
    if preguntas_finales and objetivo_maximo > 0 and total_maximo > 0 and abs(objetivo_maximo - total_maximo) > 0.10:
        factor = objetivo_maximo / total_maximo
        for p in preguntas_finales:
            p["punteo_maximo"] = round(_safe_float(p.get("punteo_maximo"), 0.0) * factor, 2)
            p["punteo_obtenido"] = round(_safe_float(p.get("punteo_obtenido"), 0.0) * factor, 2)

        total_obtenido = round(
            sum(_safe_float(p.get("punteo_obtenido"), 0.0) for p in preguntas_finales),
            2,
        )
        total_maximo = round(
            sum(_safe_float(p.get("punteo_maximo"), 0.0) for p in preguntas_finales),
            2,
        )

    total_obtenido = min(total_obtenido, objetivo_maximo)

    cf["preguntas"] = preguntas_finales
    cf["punteo_total"] = round(total_obtenido, 2)
    cf["punteo_maximo_total"] = round(objetivo_maximo, 2)
    cf["porcentaje"] = (
        round((total_obtenido / objetivo_maximo) * 100, 2)
        if objetivo_maximo > 0
        else 0.0
    )

    return cf


# ─────────────────────────────────────────────
# Fallback de consenso
# ─────────────────────────────────────────────

def _merge_results(
    a: dict,
    b: dict,
    nivel: int,
    punteo_maximo: float = 100.0,
    distribucion_series: list | None = None,
) -> dict:
    """Fallback: promedia A/B y luego normaliza por series."""
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

        punteo_a = _safe_float((pa or {}).get("punteo_obtenido"), 0.0)
        punteo_b = _safe_float((pb or {}).get("punteo_obtenido"), 0.0)

        if pa and pb:
            punteo = round((punteo_a + punteo_b) / 2, 2)
        elif pa:
            punteo = punteo_a
        else:
            punteo = punteo_b

        merged_q = dict(referencia)
        merged_q["numero"] = num
        merged_q["punteo_obtenido"] = punteo
        merged_q["justificacion"] = (
            "[Fallback promedio A/B] "
            f"A: {(pa or {}).get('justificacion', 'sin respuesta')} | "
            f"B: {(pb or {}).get('justificacion', 'sin respuesta')}"
        )

        preguntas_final.append(merged_q)

    base["preguntas"] = preguntas_final
    base.setdefault("conclusion", "Calificación generada por fallback porque el juez no produjo una respuesta válida.")
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
    Ejecuta el consenso:
    1. Calificador A y B en paralelo.
    2. Juez con los resultados de ambos.
    3. Si falla el juez, fallback con promedio A/B.
    """
    del pil_images  # Se conserva en la firma por compatibilidad.

    resultado = ResultadoConsenso(
        examen_id=examen_id,
        nivel_exigencia=nivel_exigencia,
    )

    distribucion_series = distribucion_series or []
    punteo_maximo = float(punteo_maximo or 0)

    try:
        prompt_a = _build_calificador_prompt(
            texto_icr=texto_icr,
            contexto_rag=contexto_rag,
            nivel=nivel_exigencia,
            agente_id="Calificador A",
            punteo_maximo=punteo_maximo,
            distribucion_series=distribucion_series,
        )

        prompt_b = _build_calificador_prompt(
            texto_icr=texto_icr,
            contexto_rag=contexto_rag,
            nivel=nivel_exigencia,
            agente_id="Calificador B",
            punteo_maximo=punteo_maximo,
            distribucion_series=distribucion_series,
        )

        loop = asyncio.get_running_loop()

        tarea_a = loop.run_in_executor(
            None,
            _call_agent,
            settings.model_calificador_a,
            prompt_a,
            "calificador_a",
        )

        tarea_b = loop.run_in_executor(
            None,
            _call_agent,
            settings.model_calificador_b,
            prompt_b,
            "calificador_b",
        )

        resultado_a, resultado_b = await asyncio.gather(tarea_a, tarea_b)

        resultado.resultado_a = resultado_a
        resultado.resultado_b = resultado_b

        json_a = resultado_a.respuesta_json if resultado_a and not resultado_a.error else {}
        json_b = resultado_b.respuesta_json if resultado_b and not resultado_b.error else {}

        if not json_a and resultado_a and resultado_a.respuesta_json:
            json_a = resultado_a.respuesta_json

        if not json_b and resultado_b and resultado_b.respuesta_json:
            json_b = resultado_b.respuesta_json

        if not json_a and not json_b:
            resultado.error = "Ambos calificadores fallaron o devolvieron JSON inválido."
            resultado.calificacion_final = _normalizar_preguntas_por_series(
                cf={
                    "nivel_aplicado": nivel_exigencia,
                    "punteo_total": 0.0,
                    "punteo_maximo_total": punteo_maximo,
                    "porcentaje": 0.0,
                    "preguntas": [],
                    "conclusion": "No fue posible calificar porque ambos agentes fallaron.",
                    "fortalezas": [],
                    "debilidades": ["No se obtuvo una evaluación válida."],
                    "sugerencias": ["Revisar la calidad del ICR y volver a procesar el examen."],
                    "discrepancias_resueltas": [],
                },
                punteo_maximo=punteo_maximo,
                distribucion_series=distribucion_series,
            )
            return resultado

        if not json_a:
            json_a = json_b

        if not json_b:
            json_b = json_a

        prompt_juez = _build_juez_prompt(
            texto_icr=texto_icr,
            contexto_rag=contexto_rag,
            nivel=nivel_exigencia,
            resultado_a=json_a,
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
        )

        resultado.resultado_juez = resultado_juez

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
            return resultado

        # Si el juez devuelve JSON aunque tenga error de parseo parcial, se intenta usar.
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
            return resultado

        cf = _merge_results(
            a=json_a,
            b=json_b,
            nivel=nivel_exigencia,
            punteo_maximo=punteo_maximo,
            distribucion_series=distribucion_series,
        )
        resultado.calificacion_final = cf
        resultado.discrepancias = cf.get("discrepancias_resueltas", [])
        resultado.error = f"Juez falló; se usó fallback A/B. Error juez: {(resultado_juez.error if resultado_juez else 'sin respuesta')}"
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
                "sugerencias": ["Revisar logs del backend y reintentar el procesamiento."],
                "discrepancias_resueltas": [],
            },
            punteo_maximo=punteo_maximo,
            distribucion_series=distribucion_series,
        )
        return resultado
