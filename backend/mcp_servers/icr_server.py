"""
EduGrade AI — MCP Server para ICR (Intelligent Character Recognition)
=====================================================================
Servidor MCP que expone herramientas de extracción de texto avanzada
con soporte LaTeX para imágenes de exámenes académicos.

Ejecución:
    python mcp_servers/icr_server.py
"""
from __future__ import annotations

import asyncio
import base64
import io
import os
import re
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from google import genai
from google.genai import types as genai_types
from PIL import Image

# ── Configuración ──────────────────────────────────────────
API_KEY = os.environ.get("GEMINI_API_KEY", "")
ICR_MODEL = os.environ.get("MODEL_ICR", "gemini-2.0-flash")

client = genai.Client(api_key=API_KEY)
server = Server("edugrade-icr-server")

# ── Prompts especializados ──────────────────────────────────
PROMPT_ICR_MATEMATICO = """
Eres un sistema experto en ICR (Intelligent Character Recognition) especializado
en manuscritos matemáticos y documentos académicos. Tu tarea es extraer con
máxima fidelidad el contenido de esta imagen de examen.

REGLAS DE ORO:
1. NOTACIÓN MATEMÁTICA: Transcribe TODAS las expresiones matemáticas en LaTeX.
   - Inline: $expresión$  (ej: $x^2 + 2x + 1$)
   - Display: $$expresión$$ para fórmulas en su propia línea
   - Fracciones: $\\frac{numerador}{denominador}$
   - Exponentes: $x^{n}$, subíndices: $x_{i}$
   - Raíces: $\\sqrt{x}$, $\\sqrt[n]{x}$
   - Productos notables: $(a+b)^2 = a^2 + 2ab + b^2$

2. FIDELIDAD ABSOLUTA: Transcribe exactamente lo que escribió el estudiante,
   aunque sea incorrecto. Si algo es ilegible, escribe [ILEGIBLE].

3. ESTRUCTURA: Mantén el orden y numeración original del examen.

4. VINCULACIÓN FRENTE-DORSO: Si se envían múltiples imágenes, vincula los
   procedimientos del dorso con los ejercicios del frente.

FORMATO DE SALIDA OBLIGATORIO:
---
DATOS_ESTUDIANTE:
  nombre: [nombre completo si aparece]
  clave: [número de carné/ID si aparece]
  fecha: [fecha si aparece]
  serie: [letra/número de serie si aparece]

PREGUNTAS:
  - numero: 1
    serie: [I, II, III, etc.]
    enunciado: [texto del enunciado en LaTeX si aplica]
    respuesta: [respuesta del estudiante en LaTeX si aplica]
    procedimiento: [pasos mostrados en el dorso si aplica]
    tiene_latex: [true/false]

  - numero: 2
    ...
---
"""

PROMPT_ICR_GENERAL = """
Eres un experto en OCR/ICR para documentos académicos. Extrae todo el contenido
de esta imagen de examen con precisión.

1. Identifica el nombre del estudiante, fecha, y código de examen si aparecen.
2. Extrae cada pregunta con su número y la respuesta del estudiante.
3. Para fórmulas matemáticas, usa formato LaTeX ($...$).
4. Si el texto es ilegible, indica [ILEGIBLE].
5. Mantén el orden original.

Responde en el siguiente formato YAML:
---
estudiante:
  nombre: ""
  clave: ""
  fecha: ""
preguntas:
  - numero: 1
    texto: ""
    respuesta: ""
    tiene_latex: false
---
"""


# ── Tool handlers ───────────────────────────────────────────

@server.list_tools()
async def listar_herramientas() -> list[Tool]:
    return [
        Tool(
            name="extraer_texto_examen",
            description=(
                "Extrae texto manuscrito e impreso de imágenes de exámenes académicos "
                "usando Gemini Vision con ICR avanzado. Soporta expresiones matemáticas "
                "en LaTeX, reconoce escritura a mano y texto impreso."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "imagenes_base64": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de imágenes del examen en base64 (frente, dorso, etc.)"
                    },
                    "modo": {
                        "type": "string",
                        "enum": ["matematico", "general"],
                        "description": "Modo de extracción: 'matematico' para exámenes con fórmulas, 'general' para texto",
                        "default": "matematico"
                    },
                    "instrucciones_extra": {
                        "type": "string",
                        "description": "Instrucciones adicionales específicas del docente"
                    }
                },
                "required": ["imagenes_base64"]
            }
        ),
        Tool(
            name="detectar_formulas_latex",
            description=(
                "Analiza una imagen y detecta si contiene fórmulas matemáticas, "
                "extrayéndolas como LaTeX. Útil para verificar el soporte LaTeX."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "imagen_base64": {
                        "type": "string",
                        "description": "Imagen en base64"
                    }
                },
                "required": ["imagen_base64"]
            }
        ),
        Tool(
            name="verificar_servidor",
            description="Verifica que el servidor ICR está operativo.",
            inputSchema={"type": "object", "properties": {}}
        ),
    ]


@server.call_tool()
async def ejecutar_herramienta(name: str, arguments: dict) -> list[TextContent]:

    if name == "verificar_servidor":
        return [TextContent(
            type="text",
            text=f"✅ Servidor MCP-ICR operativo | Modelo: {ICR_MODEL} | API: {'configurada' if API_KEY else 'FALTA'}"
        )]

    if name == "extraer_texto_examen":
        imagenes_b64: list[str] = arguments["imagenes_base64"]
        modo: str = arguments.get("modo", "matematico")
        extra: str = arguments.get("instrucciones_extra", "")

        prompt = PROMPT_ICR_MATEMATICO if modo == "matematico" else PROMPT_ICR_GENERAL
        if extra:
            prompt += f"\n\nINSTRUCCIONES ADICIONALES DEL DOCENTE:\n{extra}"

        # Construir partes del mensaje
        parts: list = [prompt]
        for b64 in imagenes_b64:
            img_bytes = base64.b64decode(b64)
            img = Image.open(io.BytesIO(img_bytes))
            parts.append(img)

        response = client.models.generate_content(
            model=ICR_MODEL,
            contents=parts,
        )
        return [TextContent(type="text", text=response.text)]

    if name == "detectar_formulas_latex":
        b64 = arguments["imagen_base64"]
        img_bytes = base64.b64decode(b64)
        img = Image.open(io.BytesIO(img_bytes))

        response = client.models.generate_content(
            model=ICR_MODEL,
            contents=[
                "Detecta y extrae TODAS las fórmulas y expresiones matemáticas "
                "de esta imagen. Conviértelas a formato LaTeX. "
                "Si no hay fórmulas, responde: 'Sin fórmulas matemáticas detectadas'.",
                img
            ],
        )
        return [TextContent(type="text", text=response.text)]

    return [TextContent(type="text", text=f"❌ Herramienta desconocida: {name}")]


# ── Entry point ─────────────────────────────────────────────

async def main() -> None:
    async with stdio_server() as streams:
        await server.run(*streams)


if __name__ == "__main__":
    asyncio.run(main())
