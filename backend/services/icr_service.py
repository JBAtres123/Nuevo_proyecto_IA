"""
DeepGrader AI — Servicio ICR adaptativo (v2)
============================================
Fase 1: Detecta el tipo de examen y sus dinámicas (F/V, selección múltiple,
        desarrollo, subrayado, matemáticas, código, etc.)
Fase 2: Extrae el contenido con un prompt y schema específico para cada tipo.

Exporta: extract_text_from_images(image_paths) → dict
"""
from __future__ import annotations

import base64
import json
import re
from enum import Enum
from pathlib import Path
from typing import Optional

from groq import Groq

from config import get_settings

settings = get_settings()

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.groq_api_key)
    return _client


# ─────────────────────────────────────────────────────────
# Tipos de dinámica de examen
# ─────────────────────────────────────────────────────────

class ExamDynamic(str, Enum):
    MATEMATICAS      = "matematicas"       # Álgebra, cálculo, física — LaTeX + procedimiento
    SELECCION_MULTIPLE = "seleccion_multiple"  # A/B/C/D o a/b/c/d
    VERDADERO_FALSO  = "verdadero_falso"   # V/F, Cierto/Falso, T/F, checkboxes
    COMPLETAR        = "completar"         # Llenar blancos / espacios en blanco
    SUBRAYADO        = "subrayado"         # Subrayar palabra correcta de una lista
    RELACIONAR       = "relacionar"        # Unir columnas / flechas
    ORDENAR          = "ordenar"           # Ordenar pasos / secuencia
    DESARROLLO       = "desarrollo"        # Respuesta abierta, ensayo, explicación
    CODIGO           = "codigo"            # Fragmentos de código (cualquier lenguaje)
    MIXTO            = "mixto"             # Combinación de varios tipos


# ─────────────────────────────────────────────────────────
# Utilidades de imagen
# ─────────────────────────────────────────────────────────

def _encode_image_b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _get_mime_type(path: str) -> str:
    ext = Path(path).suffix.lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
    }.get(ext, "image/jpeg")


def _build_image_content(image_paths: list[str]) -> tuple[list, list[str]]:
    """Construye el payload multimodal y retorna (content_list, b64_list)."""
    b64_list: list[str] = []
    content: list = []
    for path in image_paths:
        b64 = _encode_image_b64(path)
        b64_list.append(b64)
        mime = _get_mime_type(path)
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{b64}"},
        })
    return content, b64_list


# ─────────────────────────────────────────────────────────
# FASE 1 — Detección del tipo de examen
# ─────────────────────────────────────────────────────────

PROMPT_DETECTION = """
Eres un sistema ICR experto en exámenes académicos escritos en español.

TAREA:
Analiza la imagen del examen y detecta qué dinámica o dinámicas contiene.
No resuelvas el examen. Solo identifica el tipo de preguntas y la materia aproximada.

IDIOMA:
- El examen puede estar en español guatemalteco.
- Abreviaturas como Pts., No., Resp., Cte., F/V deben interpretarse como español estándar.
- Responde siempre en español.

DINÁMICAS POSIBLES (lee con atención las pistas visuales):
- matematicas: álgebra, cálculo, física, geometría, fórmulas, operaciones, fracciones, raíces, exponentes, binomios, polinomios.
- seleccion_multiple: opciones A/B/C/D o a/b/c/d claramente enumeradas.
- verdadero_falso: marcar V/F, Cierto/Falso, T/F, checkboxes, sí/no.
- completar: espacios en blanco, líneas o guiones para llenar.
- subrayado: subrayar/circular/resaltar la opción correcta en un texto.
- relacionar: DOS COLUMNAS conectadas con flechas de colores, líneas trazadas a mano, o letras/números que emparejan elementos. Si ves líneas o flechas cruzadas uniendo elementos de columnas, ES relacionar.
- ordenar: numerar, secuenciar pasos o colocar en orden.
- desarrollo: preguntas abiertas, definiciones, explicación o ensayo.
- codigo: código fuente, pseudocódigo, algoritmos, SQL, HTML, Java, Python, etc.
- mixto: si hay varios tipos diferentes en distintas secciones/series.

CRITERIO ESTRICTO:
- Si el examen tiene secciones (I SERIE, II SERIE, III SERIE, SECCIÓN A, etc.) con DIFERENTES tipos, SIEMPRE usa "mixto" y lista cada tipo en "tipos_presentes".
- Si hay DOS COLUMNAS con flechas o líneas conectando elementos, agrega "relacionar" a "tipos_presentes".
- Si hay matemáticas en una sección Y relacionar/completar/selección en otra, usa "mixto".
- Si no estás seguro, usa "mixto".
- Revisa TODA la imagen antes de responder, incluyendo la parte inferior.

Responde ÚNICAMENTE con JSON válido, sin markdown:
{
  "tipo_principal": "matematicas|seleccion_multiple|verdadero_falso|completar|subrayado|relacionar|ordenar|desarrollo|codigo|mixto",
  "tipos_presentes": ["tipo1", "tipo2"],
  "materia_estimada": "Matemáticas|Literatura|Programación|Ciencias|Historia|Otro",
  "num_preguntas_estimado": 10,
  "tiene_metadatos": true,
  "notas": "observación breve"
}
"""


def _detect_exam_type(image_paths: list[str]) -> dict:
    """Fase 1: detecta el tipo de examen desde la(s) primera(s) imagen(es)."""
    client = _get_client()

    # Solo necesitamos la primera imagen (o las dos primeras) para detectar el tipo
    sample_paths = image_paths[:2]
    image_content, _ = _build_image_content(sample_paths)

    content = [{"type": "text", "text": PROMPT_DETECTION}] + image_content

    try:
        response = client.chat.completions.create(
            model=settings.model_icr,
            messages=[{"role": "user", "content": content}],
            temperature=0.0,
            max_tokens=512,
        )
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"```(?:json)?", "", raw, flags=re.IGNORECASE).strip().strip("`")
        return json.loads(raw)
    except Exception as exc:
        return {
            "tipo_principal": ExamDynamic.MIXTO.value,
            "tipos_presentes": [ExamDynamic.MIXTO.value],
            "materia_estimada": "Otro",
            "num_preguntas_estimado": 0,
            "tiene_metadatos": True,
            "notas": f"Detección automática falló, usando modo mixto: {exc}",
        }


# ─────────────────────────────────────────────────────────
# FASE 2 — Prompts por tipo de dinámica
# ─────────────────────────────────────────────────────────

# Schema base compartido por todos los tipos
_SCHEMA_BASE_METADATA = """
"estudiante": {
  "nombre": "",
  "clave_carne": "",
  "fecha": "",
  "serie": "",
  "curso": "",
  "docente": ""
},
"""

_SCHEMA_PREGUNTA_HEADER = """
  {
    "numero": 1,
    "seccion": "",
    "tipo": "<nombre del tipo>",
    "enunciado": "Texto completo del enunciado",
"""


def _prompt_matematicas() -> str:
    schema = """{
""" + _SCHEMA_BASE_METADATA + """
  "preguntas": [
    {
      "numero": 1,
      "seccion": "I SERIE",
      "tipo": "matematicas",
      "enunciado": "$y^2 - 15y^2 + 75y - 125$",
      "respuesta": "$(y - 5)^3$",
      "procedimiento": "Pasos escritos por el estudiante si existen",
      "tiene_latex": true,
      "unidad": "sin unidad"
    }
  ]
}"""
    return f"""
Eres un experto en ICR para exámenes matemáticos/científicos escritos en español.
Extrae TODAS las preguntas con máxima fidelidad, aunque las respuestas sean incorrectas.
No resuelvas el examen: transcribe lo que aparece y lo que respondió el estudiante.

REGLA CRÍTICA — SIN DUPLICADOS:
- Escribe cada expresión matemática UNA SOLA VEZ en formato LaTeX.
- NUNCA escribas la misma expresión en Unicode Y en LaTeX al mismo tiempo.
- NUNCA pongas saltos de línea dentro de una expresión matemática en un campo de texto.
- CORRECTO: "enunciado": "$y^2 - 15y^2 + 75y - 125$"
- INCORRECTO: "enunciado": "y\\n2\\n−\\n15y²+75y−125 y 2 −15y 2 +75y−125"

REGLAS DE LaTeX:
- Inline: $expresión$   Ej: $x^2 + 2x + 1$
- Exponentes: $x^2$, $b^{{3}}$, $6x^2 - 3x$
- Fracción: $\\frac{{a}}{{b}}$  Raíz: $\\sqrt[n]{{x}}$
- Nunca escribas "rac" para raíz o fracción. Usa siempre \\sqrt o \\frac.
- Si hay texto ilegible usa [ILEGIBLE]

SECCIÓN:
- Extrae el encabezado de la sección a la que pertenece cada pregunta (ej: "I SERIE", "II SERIE").

FORMATO JSON (sin texto adicional, sin markdown):
{schema}
"""


def _prompt_seleccion_multiple() -> str:
    schema = """{
""" + _SCHEMA_BASE_METADATA + """
  "preguntas": [
    {
      "numero": 1,
      "seccion": "",
      "tipo": "seleccion_multiple",
      "enunciado": "Texto de la pregunta",
      "opciones": {
        "A": "Texto opción A",
        "B": "Texto opción B",
        "C": "Texto opción C",
        "D": "Texto opción D"
      },
      "respuesta_marcada": "A",
      "como_marcó": "circulo|tache|subrayado|checkbox|otro"
    }
  ]
}"""
    return f"""
Eres un experto en ICR para exámenes de selección múltiple.
Transcribe EXACTAMENTE lo que el estudiante marcó, no lo que es correcto.

IMPORTANTE:
- Si la letra de la opción no es clara, describe la marca: [ILEGIBLE]
- Detecta cómo marcó el estudiante (círculo, tache X, subrayado, checkbox)
- Si hay más de 4 opciones, inclúyelas todas (E, F, etc.)

FORMATO JSON (sin texto adicional, sin markdown):
{schema}
"""


def _prompt_verdadero_falso() -> str:
    schema = """{
""" + _SCHEMA_BASE_METADATA + """
  "preguntas": [
    {
      "numero": 1,
      "seccion": "",
      "tipo": "verdadero_falso",
      "enunciado": "Afirmación completa",
      "respuesta_marcada": "V",
      "valor_normalizado": true,
      "como_marcó": "letra V/F|palabra|checkbox|subrayado|circulo"
    }
  ]
}"""
    return f"""
Eres un experto en ICR para exámenes de Verdadero/Falso.
- "valor_normalizado" debe ser true si es Verdadero/Cierto/T, false si es Falso/F.
- Si la marca es ambigua escribe null en "valor_normalizado".
- Transcribe el enunciado completo aunque sea largo.

FORMATO JSON (sin texto adicional, sin markdown):
{schema}
"""


def _prompt_completar() -> str:
    schema = """{
""" + _SCHEMA_BASE_METADATA + """
  "preguntas": [
    {
      "numero": 1,
      "seccion": "",
      "tipo": "completar",
      "enunciado_con_blancos": "El ___ es la unidad de ___ en el SI.",
      "respuestas_insertadas": ["Newton", "fuerza"],
      "transcripcion_completa": "El Newton es la unidad de fuerza en el SI."
    }
  ]
}"""
    return f"""
Eres un experto en ICR para exámenes de completar espacios en blanco.
- Transcribe el enunciado original usando ___ para los blancos.
- En "respuestas_insertadas" lista exactamente lo que escribió el estudiante, en orden.
- En "transcripcion_completa" arma el texto final con las respuestas insertadas.
- Si un blanco está vacío, usa "" en la lista.

FORMATO JSON (sin texto adicional, sin markdown):
{schema}
"""


def _prompt_subrayado() -> str:
    schema = """{
""" + _SCHEMA_BASE_METADATA + """
  "preguntas": [
    {
      "numero": 1,
      "seccion": "",
      "tipo": "subrayado",
      "enunciado": "Instrucción o contexto de la pregunta",
      "opciones_en_texto": ["opción1", "opción2", "opción3"],
      "respuesta_subrayada": "opción2",
      "como_marcó": "subrayado|circulo|resaltado|tache"
    }
  ]
}"""
    return f"""
Eres un experto en ICR para exámenes donde se subraya la respuesta correcta.
- Detecta cuál palabra/frase subrayó, circuló o resaltó el estudiante.
- Lista TODAS las opciones que aparecen en el texto, aunque no estén marcadas.
- Si hay ambigüedad en qué se marcó, escribe [AMBIGUO].

FORMATO JSON (sin texto adicional, sin markdown):
{schema}
"""


def _prompt_relacionar() -> str:
    schema = """{
""" + _SCHEMA_BASE_METADATA + """
  "preguntas": [
    {
      "numero": 1,
      "seccion": "",
      "tipo": "relacionar",
      "instruccion": "Relacione la columna A con la columna B",
      "columna_a": ["Concepto 1", "Concepto 2", "Concepto 3"],
      "columna_b": ["Definición X", "Definición Y", "Definición Z"],
      "respuestas": [
        {"izquierda": "Concepto 1", "derecha": "Definición Y"},
        {"izquierda": "Concepto 2", "derecha": "Definición Z"}
      ]
    }
  ]
}"""
    return f"""
Eres un experto en ICR para exámenes de relacionar columnas.
- Transcribe exactamente ambas columnas.
- En "respuestas" registra cada flecha o línea que trazó el estudiante.
- Si una relación no tiene flecha (sin respuesta), no la incluyas en "respuestas".

FORMATO JSON (sin texto adicional, sin markdown):
{schema}
"""


def _prompt_ordenar() -> str:
    schema = """{
""" + _SCHEMA_BASE_METADATA + """
  "preguntas": [
    {
      "numero": 1,
      "seccion": "",
      "tipo": "ordenar",
      "instruccion": "Ordene los pasos del proceso",
      "items_originales": ["Paso C", "Paso A", "Paso B"],
      "orden_estudiante": ["Paso A", "Paso B", "Paso C"],
      "numeros_escritos": [2, 3, 1]
    }
  ]
}"""
    return f"""
Eres un experto en ICR para exámenes de ordenar secuencias.
- Transcribe los ítems tal como aparecen en el papel.
- "orden_estudiante" es el orden resultante según los números escritos.
- "numeros_escritos" son los números que el estudiante anotó junto a cada ítem.

FORMATO JSON (sin texto adicional, sin markdown):
{schema}
"""


def _prompt_desarrollo() -> str:
    schema = """{
""" + _SCHEMA_BASE_METADATA + """
  "preguntas": [
    {
      "numero": 1,
      "seccion": "",
      "tipo": "desarrollo",
      "enunciado": "Pregunta completa",
      "respuesta": "Texto completo que escribió el estudiante, párrafo por párrafo",
      "palabras_clave_detectadas": ["palabra1", "palabra2"],
      "longitud_estimada": "corta|media|larga",
      "ilegible": false
    }
  ]
}"""
    return f"""
Eres un experto en ICR para exámenes de desarrollo/ensayo.
- Transcribe la respuesta COMPLETA del estudiante, palabra por palabra.
- Si hay partes ilegibles, usa [ILEGIBLE: descripción de lo que podría decir].
- Detecta las palabras clave conceptuales más importantes en la respuesta.
- "longitud_estimada": corta (<50 palabras), media (50-150), larga (>150).

FORMATO JSON (sin texto adicional, sin markdown):
{schema}
"""


def _prompt_codigo() -> str:
    schema = """{
""" + _SCHEMA_BASE_METADATA + """
  "preguntas": [
    {
      "numero": 1,
      "seccion": "",
      "tipo": "codigo",
      "enunciado": "Descripción del problema o instrucción",
      "lenguaje_detectado": "Python|Java|C++|JavaScript|SQL|HTML|Pseudocódigo|Otro",
      "codigo_transcrito": "def suma(a, b):\\n    return a + b",
      "errores_sintaxis_visibles": ["falta punto y coma en línea 3"],
      "comentarios_estudiante": "Notas o comentarios escritos fuera del código"
    }
  ]
}"""
    return f"""
Eres un experto en ICR para exámenes de programación.
- Transcribe el código EXACTAMENTE como está escrito, aunque tenga errores.
- Usa \\n para saltos de línea dentro de "codigo_transcrito".
- Detecta el lenguaje de programación o pseudocódigo.
- Lista solo errores de SINTAXIS visibles (no errores de lógica).
- Si hay partes ilegibles en el código, usa # [ILEGIBLE].

FORMATO JSON (sin texto adicional, sin markdown):
{schema}
"""


def _prompt_mixto(tipos_detectados: list[str]) -> str:
    tipos_str = ", ".join(tipos_detectados)
    schema = """{
""" + _SCHEMA_BASE_METADATA + """
  "secciones": [
    {
      "id_seccion": "I SERIE",
      "titulo_seccion": "I SERIE: valor 10 puntos — binomios al cubo",
      "tipo_dinamica": "matematicas",
      "instrucciones": "Desarrolla los siguientes binomios al cubo",
      "preguntas": [
        {
          "numero": 1,
          "tipo": "matematicas",
          "enunciado": "$y^3 - 15y^2 + 75y - 125$",
          "respuesta": "$(y - 5)^3$",
          "procedimiento": "",
          "datos_extra": {}
        }
      ]
    },
    {
      "id_seccion": "II SERIE",
      "titulo_seccion": "II SERIE: Preguntas de desarrollo",
      "tipo_dinamica": "desarrollo",
      "instrucciones": "Responde con tus propias palabras",
      "preguntas": [
        {
          "numero": 1,
          "tipo": "desarrollo",
          "enunciado": "¿En qué consistió la Revolución Industrial?",
          "respuesta": "Fue el cambio de producción artesanal a industrial usando máquinas de vapor.",
          "palabras_clave_detectadas": ["Revolución Industrial", "máquinas de vapor"],
          "datos_extra": {}
        }
      ]
    },
    {
      "id_seccion": "III SERIE",
      "titulo_seccion": "III SERIE: Verdadero o Falso",
      "tipo_dinamica": "verdadero_falso",
      "instrucciones": "Escriba V o F",
      "preguntas": [
        {
          "numero": 1,
          "tipo": "verdadero_falso",
          "enunciado": "Los Derechos Humanos son universales e inalienables.",
          "respuesta": "V",
          "respuesta_marcada": "V",
          "valor_normalizado": true,
          "datos_extra": {}
        }
      ]
    },
    {
      "id_seccion": "IV SERIE",
      "titulo_seccion": "IV SERIE: Selección Múltiple",
      "tipo_dinamica": "seleccion_multiple",
      "instrucciones": "Marque la respuesta correcta",
      "preguntas": [
        {
          "numero": 1,
          "tipo": "seleccion_multiple",
          "enunciado": "Sistema político donde el pueblo elige a sus gobernantes:",
          "respuesta": "A",
          "opciones": {"A": "Democracia", "B": "Monarquía Absoluta", "C": "Dictadura"},
          "respuesta_marcada": "A",
          "datos_extra": {}
        }
      ]
    },
    {
      "id_seccion": "V SERIE",
      "titulo_seccion": "V SERIE: valor 10 puntos — diferencias de cuadrados",
      "tipo_dinamica": "relacionar",
      "instrucciones": "Relaciona correctamente las diferencias de cuadrados",
      "preguntas": [
        {
          "numero": 1,
          "tipo": "relacionar",
          "enunciado": "Relaciona cada expresión con su factorización",
          "columna_a": ["$100x^2 - 49$", "$\\\\frac{1}{4}x^{30} - x^6$"],
          "columna_b": ["$(10x + 7)(10x - 7)$", "$(\\\\frac{1}{2}x^{15} - x^3)(\\\\frac{1}{2}x^{15} + x^3)$"],
          "respuestas": [
            {"izquierda": "$100x^2 - 49$", "derecha": "$(10x + 7)(10x - 7)$"}
          ],
          "datos_extra": {}
        }
      ]
    }
  ]
}"""
    return f"""
Eres un experto en ICR para exámenes con múltiples tipos de preguntas escritos en español.
No resuelvas el examen: extrae el contenido y la respuesta escrita/marcada por el estudiante.
Se detectaron estas dinámicas en el examen: {tipos_str}

REGLA CRÍTICA — SIN DUPLICADOS EN LATEX:
- Escribe cada expresión matemática UNA SOLA VEZ en formato LaTeX: $expresión$
- NUNCA escribas la misma expresión en texto plano Y en LaTeX.
- NUNCA pongas saltos de línea dentro de un valor de campo JSON.
- CORRECTO: "enunciado": "$y^3 - 15y^2 + 75y - 125$"
- INCORRECTO: "enunciado": "y³−15y²+75y−125\\n$(y)^3$..."

REGLAS DE EXTRACCIÓN:
- Organiza las preguntas por SECCIÓN (I SERIE, II SERIE, III SERIE, etc. según aparezcan en el examen).
- Captura el título/encabezado COMPLETO de cada sección.
- Captura las instrucciones de cada sección.
- OBLIGATORIO EN TODAS LAS PREGUNTAS: incluye siempre "enunciado" con el texto completo de la pregunta/afirmación/enunciado tal como aparece impreso en el examen, y "respuesta" con lo que marcó o escribió el estudiante.
- En cada pregunta, adapta ADEMÁS los campos específicos según su tipo:
  * matematicas → "enunciado" en LaTeX, "respuesta" en LaTeX, "procedimiento" si aplica
  * seleccion_multiple → "enunciado" (texto de la pregunta), "opciones" dict {{A,B,C,D}}, "respuesta_marcada" (letra seleccionada)
  * verdadero_falso → "enunciado" (afirmación completa tal como aparece), "respuesta_marcada" (V o F), "valor_normalizado" (true/false/null)
  * completar → "enunciado" (oración con ___ en los blancos), "respuestas_insertadas" lista
  * subrayado → "enunciado" (instrucción o contexto), "opciones_en_texto" lista y "respuesta_subrayada"
  * relacionar → "enunciado" (instrucción de la actividad), "columna_a" lista, "columna_b" lista, "respuestas" lista de {{izquierda, derecha}} según las flechas/líneas trazadas
  * desarrollo → "enunciado" (pregunta completa tal como está escrita), "respuesta" (lo que escribió el estudiante), "palabras_clave_detectadas" lista
  * codigo → "enunciado" (descripción del problema), "lenguaje_detectado" y "codigo_transcrito"

RELACIONAR — INSTRUCCIONES ESPECIALES:
- Si ves dos columnas con líneas de colores o flechas trazadas entre elementos, eso es "relacionar".
- Transcribe TODOS los elementos de columna_a y columna_b aunque no estén conectados.
- En "respuestas" registra SOLO las conexiones que trazó el estudiante (flecha izquierda→derecha).
- Las expresiones matemáticas en columnas también van en LaTeX.

LaTeX GENERAL:
- Inline: $expresión$
- Fracción: $\\frac{{a}}{{b}}$
- Raíz: $\\sqrt{{x}}$ o $\\sqrt[n]{{x}}$
- Exponente: $x^{{2}}$, $6x^2 - 3x$
- Nunca escribas "rac" para raíces o fracciones.
- Si hay partes ilegibles usa [ILEGIBLE].

FORMATO JSON (sin texto adicional, sin markdown):
{schema}
"""


# Mapa de tipo → función de prompt
_PROMPT_MAP = {
    ExamDynamic.MATEMATICAS:        _prompt_matematicas,
    ExamDynamic.SELECCION_MULTIPLE: _prompt_seleccion_multiple,
    ExamDynamic.VERDADERO_FALSO:    _prompt_verdadero_falso,
    ExamDynamic.COMPLETAR:          _prompt_completar,
    ExamDynamic.SUBRAYADO:          _prompt_subrayado,
    ExamDynamic.RELACIONAR:         _prompt_relacionar,
    ExamDynamic.ORDENAR:            _prompt_ordenar,
    ExamDynamic.DESARROLLO:         _prompt_desarrollo,
    ExamDynamic.CODIGO:             _prompt_codigo,
}


def _normalizar_tipo(valor) -> str:
    """Convierte Enum/None/str a texto simple compatible con los mapas."""
    if isinstance(valor, Enum):
        return str(valor.value)
    if valor is None:
        return ExamDynamic.MIXTO.value
    texto = str(valor).strip().lower()
    texto = texto.replace(" ", "_").replace("-", "_")
    return texto or ExamDynamic.MIXTO.value


def _normalizar_lista_tipos(tipos_presentes) -> list[str]:
    if not isinstance(tipos_presentes, list):
        return [ExamDynamic.MIXTO.value]

    validos = {item.value for item in ExamDynamic}
    normalizados: list[str] = []

    for tipo in tipos_presentes:
        t = _normalizar_tipo(tipo)
        if t in validos and t not in normalizados:
            normalizados.append(t)

    return normalizados or [ExamDynamic.MIXTO.value]


def _get_extraction_prompt(tipo_principal: str, tipos_presentes: list[str]) -> str:
    """Selecciona el prompt de extracción según el tipo detectado."""
    tipo_principal = _normalizar_tipo(tipo_principal)
    tipos_presentes = _normalizar_lista_tipos(tipos_presentes)

    tipos_significativos = [t for t in tipos_presentes if t != ExamDynamic.MIXTO.value]

    if tipo_principal == ExamDynamic.MIXTO.value or len(tipos_significativos) > 1:
        return _prompt_mixto(tipos_significativos or tipos_presentes)

    try:
        tipo_enum = ExamDynamic(tipo_principal)
    except ValueError:
        return _prompt_mixto(tipos_presentes or [tipo_principal])

    prompt_fn = _PROMPT_MAP.get(tipo_enum)
    if prompt_fn:
        return prompt_fn()

    return _prompt_mixto(tipos_presentes or [tipo_principal])



# ─────────────────────────────────────────────────────────
# FASE 2 — Extracción adaptada
# ─────────────────────────────────────────────────────────

def _extract_json_from_text(raw: str) -> dict:
    """Extrae JSON aunque el modelo agregue markdown o texto alrededor."""
    cleaned = re.sub(r"```(?:json)?", "", raw, flags=re.IGNORECASE).strip().strip("`").strip()

    try:
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else {"_parse_error": True, "raw": raw}
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start != -1 and end != -1 and end > start:
        fragment = cleaned[start:end + 1]
        try:
            parsed = json.loads(fragment)
            return parsed if isinstance(parsed, dict) else {"_parse_error": True, "raw": raw}
        except Exception:
            pass

    return {"_parse_error": True, "raw": raw}


def _extract_with_prompt(
    image_paths: list[str],
    prompt: str,
) -> tuple[str, dict]:
    """Llama a Groq con el prompt específico y parsea el JSON."""
    client = _get_client()
    image_content, _ = _build_image_content(image_paths)
    content = [{"type": "text", "text": prompt}] + image_content

    kwargs = {
        "model": settings.model_icr,
        "messages": [{"role": "user", "content": content}],
        "temperature": 0.0,
        "max_tokens": 6000,
    }

    try:
        response = client.chat.completions.create(
            **kwargs,
            response_format={"type": "json_object"},
        )
    except TypeError:
        response = client.chat.completions.create(**kwargs)
    except Exception:
        response = client.chat.completions.create(**kwargs)

    raw = response.choices[0].message.content.strip()
    parsed = _extract_json_from_text(raw)

    return raw, parsed


# ─────────────────────────────────────────────────────────
# Normalización para el pipeline de consenso
# ─────────────────────────────────────────────────────────

def _safe_text(value) -> str:
    """Convierte valores complejos del JSON del modelo a texto seguro."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        return str(value)


def _as_list(value) -> list:
    """Normaliza un valor a lista sin romper si el modelo devuelve string/dict."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _normalize_to_flat_questions(parsed: dict, tipo_principal: str) -> list[dict]:
    """
    Convierte cualquier estructura JSON a una lista plana de preguntas.
    Es tolerante a respuestas imperfectas del modelo: strings donde se esperaban dicts,
    secciones mal formadas o campos anidados inconsistentes.
    """
    questions: list[dict] = []

    if not isinstance(parsed, dict):
        return questions

    contador = 1

    # Caso mixto: tiene "secciones"
    for seccion in _as_list(parsed.get("secciones")):
        if not isinstance(seccion, dict):
            continue

        tipo_seccion = _safe_text(seccion.get("tipo_dinamica") or tipo_principal or "desconocido")
        seccion_id = _safe_text(seccion.get("id_seccion") or seccion.get("titulo_seccion") or "")

        for p in _as_list(seccion.get("preguntas")):
            if isinstance(p, dict):
                q = dict(p)
            else:
                q = {"numero": contador, "enunciado": _safe_text(p)}

            q.setdefault("numero", contador)
            q.setdefault("seccion", seccion_id)
            q.setdefault("serie_seccion", seccion_id)
            q.setdefault("tipo", tipo_seccion)

            # Homologar enunciado/respuesta para main.py y consensus.py
            if not q.get("enunciado"):
                q["enunciado"] = q.get("enunciado_con_blancos") or q.get("instruccion") or ""
            if "respuesta" not in q:
                q["respuesta"] = (
                    q.get("respuesta_marcada")
                    or q.get("respuesta_subrayada")
                    or q.get("respuestas_insertadas")
                    or q.get("orden_estudiante")
                    or q.get("codigo_transcrito")
                    or ""
                )

            q["enunciado"] = _safe_text(q.get("enunciado"))
            q["respuesta"] = _safe_text(q.get("respuesta"))
            q["tipo"] = _safe_text(q.get("tipo") or tipo_principal or "desconocido")
            q["tiene_latex"] = bool(q.get("tiene_latex") or "$" in q["enunciado"] or "$" in q["respuesta"] or "\\frac" in q["enunciado"] or "\\sqrt" in q["enunciado"])

            questions.append(q)
            contador += 1

    # Caso con lista "preguntas"
    if not questions:
        for p in _as_list(parsed.get("preguntas")):
            if isinstance(p, dict):
                q = dict(p)
            else:
                q = {"numero": contador, "enunciado": _safe_text(p)}

            q.setdefault("numero", contador)
            q.setdefault("tipo", tipo_principal or "desconocido")
            q.setdefault("seccion", q.get("serie_seccion", ""))
            q.setdefault("serie_seccion", q.get("seccion", ""))

            if not q.get("enunciado"):
                q["enunciado"] = q.get("enunciado_con_blancos") or q.get("instruccion") or ""
            if "respuesta" not in q:
                q["respuesta"] = (
                    q.get("respuesta_marcada")
                    or q.get("respuesta_subrayada")
                    or q.get("respuestas_insertadas")
                    or q.get("orden_estudiante")
                    or q.get("codigo_transcrito")
                    or ""
                )

            q["enunciado"] = _safe_text(q.get("enunciado"))
            q["respuesta"] = _safe_text(q.get("respuesta"))
            q["tipo"] = _safe_text(q.get("tipo") or tipo_principal or "desconocido")
            q["tiene_latex"] = bool(q.get("tiene_latex") or "$" in q["enunciado"] or "$" in q["respuesta"] or "\\frac" in q["enunciado"] or "\\sqrt" in q["enunciado"])

            questions.append(q)
            contador += 1

    return questions


def _build_icr_summary(parsed: dict, tipo_principal: str) -> str:
    """
    Genera un resumen de texto legible del ICR para pasarle al agente de consenso.
    Nunca debe romper el procesamiento aunque Groq devuelva listas/strings inesperados.
    """
    lines: list[str] = []

    if not isinstance(parsed, dict):
        return _safe_text(parsed) or "[No se pudo construir resumen del ICR]"

    est = parsed.get("estudiante", {})
    if isinstance(est, dict) and est:
        lines.append("=== DATOS DEL ESTUDIANTE ===")
        for k, v in est.items():
            if v:
                lines.append(f"  {k}: {_safe_text(v)}")

    preguntas = _normalize_to_flat_questions(parsed, tipo_principal)

    if parsed.get("_parse_error"):
        lines.append("=== TEXTO ICR SIN JSON VÁLIDO ===")
        raw = _safe_text(parsed.get("raw", ""))
        lines.append(raw[:3000] if raw else "[Sin texto reconocido]")

    if preguntas:
        lines.append(f"\n=== PREGUNTAS ({len(preguntas)} detectadas) ===")
        for p in preguntas:
            if not isinstance(p, dict):
                continue

            num = p.get("numero", "?")
            tipo = _safe_text(p.get("tipo", "desconocido"))
            seccion = _safe_text(p.get("seccion") or p.get("serie_seccion") or "")
            enunciado = _safe_text(p.get("enunciado", p.get("enunciado_con_blancos", "")))
            seccion_label = f" | {seccion}" if seccion else ""
            lines.append(f"\n[Pregunta {num}{seccion_label} — {tipo}]")
            if enunciado:
                lines.append(f"  Enunciado: {enunciado}")

            if tipo == "matematicas":
                if p.get("procedimiento"):
                    lines.append(f"  Procedimiento: {_safe_text(p.get('procedimiento'))}")
                if p.get("respuesta"):
                    lines.append(f"  Respuesta: {_safe_text(p.get('respuesta'))}")

            elif tipo == "seleccion_multiple":
                opciones = p.get("opciones", {})
                if isinstance(opciones, dict):
                    for letra, texto in opciones.items():
                        lines.append(f"    {letra}) {_safe_text(texto)}")
                elif opciones:
                    lines.append(f"  Opciones: {_safe_text(opciones)}")
                marcada = p.get("respuesta_marcada", "")
                if marcada:
                    lines.append(f"  ► Marcó: {_safe_text(marcada)}")

            elif tipo == "verdadero_falso":
                marcada = p.get("respuesta_marcada", "")
                normalizado = p.get("valor_normalizado")
                lines.append(f"  ► Marcó: {_safe_text(marcada)} (normalizado: {_safe_text(normalizado)})")

            elif tipo == "completar":
                respuestas = p.get("respuestas_insertadas", [])
                lines.append(f"  ► Respuestas insertadas: {_safe_text(respuestas)}")
                if p.get("transcripcion_completa"):
                    lines.append(f"  Transcripción: {_safe_text(p.get('transcripcion_completa'))}")

            elif tipo == "subrayado":
                lines.append(f"  Opciones: {_safe_text(p.get('opciones_en_texto', []))}")
                lines.append(f"  ► Subrayó: {_safe_text(p.get('respuesta_subrayada', ''))}")

            elif tipo == "relacionar":
                relaciones = _as_list(p.get("respuestas"))
                if not relaciones and (p.get("respuesta") or p.get("relaciones")):
                    relaciones = _as_list(p.get("respuesta") or p.get("relaciones"))

                for rel in relaciones:
                    if isinstance(rel, dict):
                        izq = rel.get("izquierda") or rel.get("columna_a") or rel.get("a") or rel.get("concepto") or ""
                        der = rel.get("derecha") or rel.get("columna_b") or rel.get("b") or rel.get("respuesta") or ""
                        if izq or der:
                            lines.append(f"  ► {_safe_text(izq)} → {_safe_text(der)}")
                        else:
                            lines.append(f"  ► {_safe_text(rel)}")
                    else:
                        lines.append(f"  ► {_safe_text(rel)}")

            elif tipo == "ordenar":
                lines.append(f"  ► Orden del estudiante: {_safe_text(p.get('orden_estudiante', []))}")

            elif tipo == "desarrollo":
                resp = _safe_text(p.get("respuesta", ""))
                if len(resp) > 300:
                    resp = resp[:300] + "…"
                lines.append(f"  ► Respuesta: {resp}")
                if p.get("palabras_clave_detectadas"):
                    lines.append(f"  Palabras clave: {_safe_text(p.get('palabras_clave_detectadas'))}")

            elif tipo == "codigo":
                lang = _safe_text(p.get("lenguaje_detectado", ""))
                codigo = _safe_text(p.get("codigo_transcrito", ""))
                lines.append(f"  Lenguaje: {lang}")
                if len(codigo) > 400:
                    codigo = codigo[:400] + "\n  [... truncado ...]"
                lines.append(f"  Código:\n{codigo}")

            else:
                respuesta = _safe_text(p.get("respuesta", ""))
                if respuesta:
                    lines.append(f"  ► Respuesta: {respuesta}")

    resumen = "\n".join(lines).strip()
    return resumen or "[No se pudo construir resumen del ICR]"


# ─────────────────────────────────────────────────────────
# Función pública principal
# ─────────────────────────────────────────────────────────

def extract_text_from_images(image_paths: list[str]) -> dict:
    """
    Extrae texto e información estructurada de imágenes de examen.

    Esta versión conserva el flujo que mejor funcionaba:
    1. Detecta el tipo de examen.
    2. Usa un prompt especializado para extraer mejor el contenido.
    3. Normaliza todo hacia preguntas_flat para main.py.
    """
    if not image_paths:
        raise ValueError("Se requiere al menos una imagen.")

    valid_paths: list[str] = []

    for path in image_paths:
        if not path:
            continue
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"No existe la imagen del examen: {path}")
        valid_paths.append(str(p))

    if not valid_paths:
        raise ValueError("No hay imágenes válidas para procesar.")

    # Fase 1: detectar tipo de examen
    detection = _detect_exam_type(valid_paths)

    tipo_principal = _normalizar_tipo(
        detection.get("tipo_principal", ExamDynamic.MIXTO.value)
    )
    tipos_presentes = _normalizar_lista_tipos(
        detection.get("tipos_presentes", [tipo_principal])
    )
    materia = str(detection.get("materia_estimada", "Otro") or "Otro")

    # Fase 2: extraer con prompt adaptado
    prompt = _get_extraction_prompt(tipo_principal, tipos_presentes)
    raw_text, parsed = _extract_with_prompt(valid_paths, prompt)

    # Si la extracción especializada falla o no detecta preguntas, hacemos fallback mixto.
    preguntas_flat = _normalize_to_flat_questions(parsed, tipo_principal)
    if parsed.get("_parse_error") or not preguntas_flat:
        fallback_prompt = _prompt_mixto(tipos_presentes or [ExamDynamic.MIXTO.value])
        raw_fallback, parsed_fallback = _extract_with_prompt(valid_paths, fallback_prompt)
        preguntas_fallback = _normalize_to_flat_questions(parsed_fallback, ExamDynamic.MIXTO.value)
        if not parsed_fallback.get("_parse_error") and preguntas_fallback:
            raw_text = raw_fallback
            parsed = parsed_fallback
            tipo_principal = ExamDynamic.MIXTO.value if tipo_principal == "desconocido" else tipo_principal
            preguntas_flat = preguntas_fallback

    detection_info = dict(detection) if isinstance(detection, dict) else {}
    detection_info["tipo_principal"] = tipo_principal
    detection_info["tipos_presentes"] = tipos_presentes

    texto_resumen = _build_icr_summary(parsed, tipo_principal)

    return {
        "raw_text": raw_text,
        "parsed": parsed,
        "images_b64": [],
        "num_images": len(valid_paths),
        "tipo_examen": tipo_principal,
        "tipos_presentes": tipos_presentes,
        "materia": materia,
        "preguntas_flat": preguntas_flat,
        "texto_resumen": texto_resumen,
        "detection_info": detection_info,
    }
