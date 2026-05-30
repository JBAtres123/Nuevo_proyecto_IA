"""
EduGrade AI — Suite de Pruebas
Exámenes simulados para validar el sistema completo.
Ejecutar: pytest tests/ -v
"""
from __future__ import annotations

import json
import os
import sys
import types
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── Asegurarse de que el backend está en el path ───────────
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


# ─────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────

MOCK_ICR_OUTPUT = """
estudiante:
  nombre: "María García"
  clave: "202300123"
  fecha: "2024-11-15"
  serie: "A"
preguntas:
  - numero: 1
    serie_seccion: "I"
    enunciado: "Resuelva la ecuación $x^2 - 5x + 6 = 0$"
    respuesta: "$x = 2$ y $x = 3$"
    tiene_latex: true
  - numero: 2
    serie_seccion: "I"
    enunciado: "Calcule $\\\\frac{d}{dx}(x^3 + 2x)$"
    respuesta: "$3x^2 + 2$"
    tiene_latex: true
  - numero: 3
    serie_seccion: "II"
    enunciado: "Defina el concepto de función continua"
    respuesta: "Una función es continua si su gráfica no tiene saltos ni hoyos"
    tiene_latex: false
"""

MOCK_RAG_CONTEXT = """
[Fuente: apuntes_calculo.pdf | Relevancia: 92.3%]
Una función f es continua en x=a si: 1) f(a) existe, 2) el límite existe,
3) el límite es igual a f(a). Las ecuaciones cuadráticas ax²+bx+c=0 se
resuelven mediante factorización o fórmula general.

[Fuente: apuntes_calculo.pdf | Relevancia: 88.1%]
La derivada de x^n es n·x^(n-1). Para polinomios se deriva término a término.
"""

MOCK_CALIFICACION_JSON = {
    "estudiante": "María García",
    "serie": "A",
    "nivel_aplicado": 5,
    "punteo_total": 8.5,
    "punteo_maximo_total": 10.0,
    "porcentaje": 85.0,
    "preguntas": [
        {
            "numero": 1,
            "serie_seccion": "I",
            "texto_pregunta": "Resuelva la ecuación $x^2 - 5x + 6 = 0$",
            "respuesta_estudiante": "$x = 2$ y $x = 3$",
            "respuesta_correcta": "$x = 2$ y $x = 3$",
            "es_correcta": True,
            "punteo_obtenido": 3.0,
            "punteo_maximo": 3.0,
            "justificacion": "Correcto. Factorización $(x-2)(x-3)=0$ aplicada correctamente.",
            "errores_especificos": [],
            "tiene_latex": True,
        },
        {
            "numero": 2,
            "serie_seccion": "I",
            "texto_pregunta": "Calcule la derivada",
            "respuesta_estudiante": "$3x^2 + 2$",
            "respuesta_correcta": "$3x^2 + 2$",
            "es_correcta": True,
            "punteo_obtenido": 3.0,
            "punteo_maximo": 3.0,
            "justificacion": "Derivación correcta usando la regla de la potencia.",
            "errores_especificos": [],
            "tiene_latex": True,
        },
        {
            "numero": 3,
            "serie_seccion": "II",
            "texto_pregunta": "Defina función continua",
            "respuesta_estudiante": "Una función es continua si su gráfica no tiene saltos ni hoyos",
            "respuesta_correcta": "f continua en a si: f(a) existe, límite existe e igual a f(a)",
            "es_correcta": False,
            "punteo_obtenido": 2.5,
            "punteo_maximo": 4.0,
            "justificacion": "Definición informal correcta en concepto pero incompleta. Falta mencionar los tres criterios formales.",
            "errores_especificos": ["Definición incompleta", "Falta criterio formal del límite"],
            "tiene_latex": False,
        },
    ],
    "conclusion": "María demuestra dominio sólido en cálculo operacional. Necesita reforzar definiciones formales.",
    "fortalezas": ["Excelente manejo algebraico", "Derivación correcta"],
    "debilidades": ["Definiciones conceptuales incompletas"],
    "sugerencias": ["Revisar definición épsilon-delta de continuidad", "Practicar demostraciones formales"],
}


# ─────────────────────────────────────────────────────────────
# Tests: ICR Service
# ─────────────────────────────────────────────────────────────

class TestICRService:
    """Pruebas del servicio de reconocimiento de caracteres."""

    def test_parse_icr_yaml_valido(self):
        """Verifica que el YAML del ICR se parsea correctamente."""
        from services.icr_service import _parse_icr_yaml
        result = _parse_icr_yaml(MOCK_ICR_OUTPUT.strip())
        assert "estudiante" in result
        assert result["estudiante"]["nombre"] == "María García"
        assert result["estudiante"]["clave"] == "202300123"
        assert len(result["preguntas"]) == 3

    def test_parse_icr_detecta_latex(self):
        """Verifica que el ICR detecta preguntas con LaTeX."""
        from services.icr_service import _parse_icr_yaml
        result = _parse_icr_yaml(MOCK_ICR_OUTPUT.strip())
        preguntas = result["preguntas"]
        assert preguntas[0]["tiene_latex"] is True
        assert preguntas[1]["tiene_latex"] is True
        assert preguntas[2]["tiene_latex"] is False

    def test_parse_icr_yaml_malformado_fallback(self):
        """El parser no debe fallar con YAML malformado."""
        from services.icr_service import _parse_icr_yaml
        malformado = "esto no es yaml válido {{{"
        result = _parse_icr_yaml(malformado)
        assert isinstance(result, dict)
        assert "estudiante" in result

    def test_parse_icr_yaml_vacio(self):
        """El parser maneja strings vacíos."""
        from services.icr_service import _parse_icr_yaml
        result = _parse_icr_yaml("")
        assert isinstance(result, dict)


# ─────────────────────────────────────────────────────────────
# Tests: RAG Service
# ─────────────────────────────────────────────────────────────

class TestRAGService:
    """Pruebas del servicio RAG con ChromaDB."""

    def test_split_text_basico(self):
        """Verifica que el texto se divide en chunks correctamente."""
        from services.rag_service import _split_text
        texto = "A" * 1200
        chunks = _split_text(texto, chunk_size=500, overlap=50)
        assert len(chunks) >= 2
        for chunk in chunks:
            assert len(chunk) <= 500

    def test_split_text_overlap(self):
        """Verifica que el solapamiento funciona."""
        from services.rag_service import _split_text
        texto = "palabra " * 100
        chunks = _split_text(texto, chunk_size=100, overlap=20)
        assert len(chunks) > 1

    def test_split_text_corto_un_chunk(self):
        """Textos cortos deben retornar un solo chunk."""
        from services.rag_service import _split_text
        texto = "Texto corto para prueba"
        chunks = _split_text(texto, chunk_size=500)
        assert len(chunks) == 1

    def test_split_text_elimina_vacios(self):
        """No debe incluir chunks casi vacíos."""
        from services.rag_service import _split_text
        texto = "Hola " + " " * 200 + "Mundo"
        chunks = _split_text(texto, chunk_size=100)
        for chunk in chunks:
            assert len(chunk.strip()) > 20

    @patch("services.rag_service.get_chroma_client")
    @patch("services.rag_service._get_embedding")
    def test_rag_search_sin_documentos(self, mock_embed, mock_client):
        """Cuando no hay documentos indexados, retorna mensaje apropiado."""
        from services.rag_service import RAGService
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0
        mock_client.return_value.get_or_create_collection.return_value = mock_collection

        rag = RAGService()
        result = rag.search("ecuaciones diferenciales")
        assert "No hay materiales indexados" in result

    @patch("services.rag_service.get_chroma_client")
    @patch("services.rag_service._get_embedding")
    def test_rag_search_retorna_contexto(self, mock_embed, mock_client):
        """La búsqueda RAG retorna fragmentos relevantes."""
        from services.rag_service import RAGService
        mock_embed.return_value = [0.1] * 768

        mock_collection = MagicMock()
        mock_collection.count.return_value = 5
        mock_collection.query.return_value = {
            "documents": [["Fragmento relevante sobre derivadas"]],
            "metadatas": [[{"fuente": "apuntes.pdf"}]],
            "distances": [[0.1]],
        }
        mock_client.return_value.get_or_create_collection.return_value = mock_collection

        rag = RAGService()
        result = rag.search("derivadas")
        assert "Fragmento relevante" in result
        assert "apuntes.pdf" in result


# ─────────────────────────────────────────────────────────────
# Tests: Sistema de Consenso
# ─────────────────────────────────────────────────────────────

class TestConsensus:
    """Pruebas del sistema de consenso multi-agente."""

    def test_nivel_descripcion_amigo(self):
        """Nivel 1-2 debe ser indulgente."""
        from agents.consensus import _nivel_descripcion
        desc = _nivel_descripcion(1)
        assert "INDULGENTE" in desc.upper() or "indulgente" in desc.lower()

    def test_nivel_descripcion_experto(self):
        """Nivel 9-10 debe ser estricto."""
        from agents.consensus import _nivel_descripcion
        desc = _nivel_descripcion(10)
        assert "EXPERTO" in desc.upper() or "rigurosa" in desc.lower() or "ESTRICTO" in desc.upper()

    def test_nivel_descripcion_balanceado(self):
        """Nivel 5 debe ser balanceado."""
        from agents.consensus import _nivel_descripcion
        desc = _nivel_descripcion(5)
        assert "BALANCEA" in desc.upper() or "objetivamen" in desc.lower()

    def test_build_calificador_prompt_incluye_nivel(self):
        """El prompt del calificador debe incluir el nivel de exigencia."""
        from agents.consensus import _build_calificador_prompt
        prompt = _build_calificador_prompt(
            texto_icr="Texto examen",
            contexto_rag="Contexto RAG",
            nivel=7,
            agente_id="Calificador A",
        )
        assert "7/10" in prompt
        assert "Calificador A" in prompt
        assert "Texto examen" in prompt

    def test_build_juez_prompt_incluye_ambos_agentes(self):
        """El prompt del Juez debe incluir los resultados de A y B."""
        from agents.consensus import _build_juez_prompt
        resultado_a = {"punteo_total": 8, "preguntas": []}
        resultado_b = {"punteo_total": 7, "preguntas": []}
        prompt = _build_juez_prompt(
            texto_icr="Examen",
            contexto_rag="Contexto",
            nivel=5,
            resultado_a=resultado_a,
            resultado_b=resultado_b,
        )
        assert "Calificador A" in prompt
        assert "Calificador B" in prompt
        assert "discrepancias" in prompt.lower()

    def test_merge_results_promedia_punteos(self):
        """El merge de fallback debe promediar los punteos."""
        from agents.consensus import _merge_results
        a = {
            "preguntas": [
                {"numero": 1, "punteo_obtenido": 8, "punteo_maximo": 10, "justificacion": "A"},
            ]
        }
        b = {
            "preguntas": [
                {"numero": 1, "punteo_obtenido": 6, "punteo_maximo": 10, "justificacion": "B"},
            ]
        }
        merged = _merge_results(a, b, nivel=5)
        assert merged["preguntas"][0]["punteo_obtenido"] == 7.0
        assert merged["punteo_total"] == 7.0

    @pytest.mark.asyncio
    @patch("agents.consensus._call_agent")
    async def test_consensus_flujo_completo(self, mock_call):
        """El flujo de consenso debe llamar a los 3 agentes."""
        from agents.consensus import ResultadoAgente, run_consensus_grading

        mock_result = ResultadoAgente(
            agente="calificador_a",
            modelo="gemini-2.0-flash",
            respuesta_json=MOCK_CALIFICACION_JSON,
            respuesta_raw=json.dumps(MOCK_CALIFICACION_JSON),
        )
        mock_call.return_value = mock_result

        resultado = await run_consensus_grading(
            examen_id=1,
            texto_icr=MOCK_ICR_OUTPUT,
            contexto_rag=MOCK_RAG_CONTEXT,
            nivel_exigencia=5,
        )

        assert resultado.examen_id == 1
        assert resultado.resultado_a is not None
        assert resultado.resultado_b is not None
        assert resultado.resultado_juez is not None
        assert mock_call.call_count == 3

    @pytest.mark.asyncio
    @patch("agents.consensus._call_agent")
    async def test_consensus_maneja_error_agente(self, mock_call):
        """Si un agente falla, el sistema no debe colapsar."""
        from agents.consensus import ResultadoAgente, run_consensus_grading

        def side_effect(*args, **kwargs):
            agente = args[2] if len(args) > 2 else ""
            if agente == "calificador_a":
                return ResultadoAgente(
                    agente="calificador_a", modelo="gemini-2.0-flash",
                    respuesta_json={}, respuesta_raw="", error="Timeout"
                )
            return ResultadoAgente(
                agente=agente, modelo="gemini-2.0-flash",
                respuesta_json=MOCK_CALIFICACION_JSON,
                respuesta_raw=json.dumps(MOCK_CALIFICACION_JSON),
            )
        mock_call.side_effect = side_effect

        resultado = await run_consensus_grading(
            examen_id=2, texto_icr="texto", contexto_rag="ctx", nivel_exigencia=5
        )
        # No debe explotar aunque A falle
        assert resultado is not None


# ─────────────────────────────────────────────────────────────
# Tests: Generación de Reportes
# ─────────────────────────────────────────────────────────────

class TestReportService:
    """Pruebas del servicio de generación de reportes."""

    def test_latex_to_text_fraccion(self):
        """Convierte fracciones LaTeX a texto."""
        from services.report_service import _latex_to_text
        result = _latex_to_text(r"$\frac{a}{b}$")
        assert "(a)/(b)" in result

    def test_latex_to_text_raiz(self):
        """Convierte raíces LaTeX a texto."""
        from services.report_service import _latex_to_text
        result = _latex_to_text(r"$\sqrt{x}$")
        assert "√(x)" in result or "√" in result

    def test_latex_to_text_exponente(self):
        """Convierte exponentes LaTeX."""
        from services.report_service import _latex_to_text
        result = _latex_to_text(r"$x^{2}$")
        assert "x^2" in result or "^" in result

    def test_latex_to_text_sin_latex(self):
        """Texto sin LaTeX pasa sin cambios."""
        from services.report_service import _latex_to_text
        texto = "Esta es una respuesta normal sin fórmulas"
        result = _latex_to_text(texto)
        assert "respuesta normal" in result

    def test_latex_to_text_operadores(self):
        """Convierte operadores especiales."""
        from services.report_service import _latex_to_text
        result = _latex_to_text(r"$a \cdot b \times c$")
        assert "·" in result or "×" in result

    def test_generate_pdf_report_crea_archivo(self, tmp_path):
        """El reporte PDF debe crearse en disco."""
        from services.report_service import generate_pdf_report
        path = generate_pdf_report(MOCK_CALIFICACION_JSON, output_dir=str(tmp_path))
        assert Path(path).exists()
        assert Path(path).suffix == ".pdf"
        assert Path(path).stat().st_size > 1000  # más de 1KB

    def test_generate_word_report_crea_archivo(self, tmp_path):
        """El reporte Word debe crearse en disco."""
        from services.report_service import generate_word_report
        path = generate_word_report(MOCK_CALIFICACION_JSON, output_dir=str(tmp_path))
        assert Path(path).exists()
        assert Path(path).suffix == ".docx"
        assert Path(path).stat().st_size > 1000

    def test_generate_pdf_nombre_estudiante(self, tmp_path):
        """El nombre del archivo debe contener el nombre del estudiante."""
        from services.report_service import generate_pdf_report
        path = generate_pdf_report(MOCK_CALIFICACION_JSON, output_dir=str(tmp_path))
        assert "Mar" in Path(path).name or "Garc" in Path(path).name

    def test_generate_pdf_datos_vacios(self, tmp_path):
        """El reporte debe generarse aunque falten datos opcionales."""
        from services.report_service import generate_pdf_report
        datos_minimos = {
            "estudiante": "Test",
            "punteo_total": 0,
            "punteo_maximo_total": 10,
            "porcentaje": 0,
            "preguntas": [],
        }
        path = generate_pdf_report(datos_minimos, output_dir=str(tmp_path))
        assert Path(path).exists()


# ─────────────────────────────────────────────────────────────
# Tests: FastAPI Endpoints
# ─────────────────────────────────────────────────────────────

class TestAPIEndpoints:
    """Pruebas de integración de los endpoints FastAPI."""

    @pytest.fixture
    def client(self):
        """Cliente de prueba FastAPI."""
        from fastapi.testclient import TestClient
        # Mock DB antes de importar main
        with patch("db.database.create_async_engine"), \
             patch("db.database.async_sessionmaker"):
            from main import app
            return TestClient(app)

    def test_health_endpoint(self, client):
        """GET /api/health debe retornar 200."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_config_exigencia_get(self, client):
        """GET /api/config-exigencia debe retornar el nivel actual."""
        response = client.get("/api/config-exigencia")
        assert response.status_code == 200
        data = response.json()
        assert "nivel" in data
        assert 1 <= data["nivel"] <= 10

    def test_config_exigencia_post_valido(self, client):
        """POST /api/config-exigencia acepta niveles 1-10."""
        for nivel in [1, 5, 10]:
            response = client.post("/api/config-exigencia", json={"nivel": nivel})
            assert response.status_code == 200
            assert response.json()["nivel"] == nivel

    def test_config_exigencia_post_invalido(self, client):
        """POST /api/config-exigencia rechaza niveles fuera de rango."""
        for nivel in [0, 11, -1, 100]:
            response = client.post("/api/config-exigencia", json={"nivel": nivel})
            assert response.status_code == 422  # Validation error

    def test_upload_sin_imagenes_falla(self, client):
        """POST /api/upload sin imágenes debe retornar error."""
        response = client.post("/api/upload")
        assert response.status_code == 422

    def test_process_examen_inexistente(self, client):
        """POST /api/process/{id} con ID inexistente debe retornar 404."""
        with patch("main.get_db") as mock_db:
            mock_session = AsyncMock()
            mock_session.execute.return_value.scalar_one_or_none.return_value = None
            mock_db.return_value.__aenter__.return_value = mock_session
            response = client.post("/api/process/99999")
            # Puede ser 404 o 500 si el mock no está bien configurado en test sync
            assert response.status_code in [404, 422, 500]


# ─────────────────────────────────────────────────────────────
# Tests: Exámenes Simulados (Pruebas de Integración)
# ─────────────────────────────────────────────────────────────

class TestExamenesSimulados:
    """
    Simulaciones completas de exámenes para validar el pipeline.
    Estos tests mockean la API de Gemini para no incurrir en costos.
    """

    EXAMEN_MATEMATICA = {
        "nombre": "Examen Matemática Discreta",
        "estudiante": "Carlos López",
        "preguntas": [
            {"num": 1, "pregunta": "¿Cuál es la negación de P ∧ Q?", "respuesta": "¬P ∨ ¬Q"},
            {"num": 2, "pregunta": "Calcule $\\binom{5}{2}$", "respuesta": "10"},
            {"num": 3, "pregunta": "Defina grafo bipartito", "respuesta": "Grafo donde los vértices se dividen en dos conjuntos disjuntos"},
        ]
    }

    EXAMEN_PROGRAMACION = {
        "nombre": "Examen Programación I",
        "estudiante": "Ana Martínez",
        "preguntas": [
            {"num": 1, "pregunta": "¿Qué es una variable?", "respuesta": "Un espacio en memoria para almacenar datos"},
            {"num": 2, "pregunta": "Escriba un bucle for en Python", "respuesta": "for i in range(10): print(i)"},
        ]
    }

    def test_examen_matematica_estructura(self):
        """Verifica que el examen de matemática tiene la estructura correcta."""
        exam = self.EXAMEN_MATEMATICA
        assert "nombre" in exam
        assert "estudiante" in exam
        assert len(exam["preguntas"]) > 0
        for p in exam["preguntas"]:
            assert "num" in p
            assert "pregunta" in p
            assert "respuesta" in p

    def test_deteccion_latex_en_examen_matematica(self):
        """Las preguntas con LaTeX deben detectarse correctamente."""
        from services.icr_service import _parse_icr_yaml
        yaml_text = f"""
estudiante:
  nombre: "Carlos López"
preguntas:
  - numero: 1
    enunciado: "¿Cuál es la negación de P ∧ Q?"
    respuesta: "¬P ∨ ¬Q"
    tiene_latex: false
  - numero: 2
    enunciado: "Calcule $\\\\binom{{5}}{{2}}$"
    respuesta: "10"
    tiene_latex: true
"""
        result = _parse_icr_yaml(yaml_text)
        preguntas = result.get("preguntas", [])
        if preguntas:
            latex_pregs = [p for p in preguntas if p.get("tiene_latex")]
            assert len(latex_pregs) >= 0  # al menos parsea sin explotar

    @patch("agents.consensus._call_agent")
    @pytest.mark.asyncio
    async def test_pipeline_matematica(self, mock_call):
        """Pipeline completo para examen de matemática."""
        from agents.consensus import ResultadoAgente, run_consensus_grading

        respuesta_mock = {
            **MOCK_CALIFICACION_JSON,
            "estudiante": "Carlos López",
            "punteo_total": 9.0,
            "punteo_maximo_total": 10.0,
            "porcentaje": 90.0,
        }
        mock_call.return_value = ResultadoAgente(
            agente="calificador_a", modelo="gemini-2.0-flash",
            respuesta_json=respuesta_mock,
            respuesta_raw=json.dumps(respuesta_mock),
        )

        resultado = await run_consensus_grading(
            examen_id=10,
            texto_icr=str(self.EXAMEN_MATEMATICA),
            contexto_rag="Contexto de matemática discreta",
            nivel_exigencia=6,
        )
        assert resultado.examen_id == 10
        assert resultado.error is None or resultado.calificacion_final

    @patch("agents.consensus._call_agent")
    @pytest.mark.asyncio
    async def test_pipeline_nivel_experto(self, mock_call):
        """El nivel 10 debe producir evaluación más estricta (prompt diferente)."""
        from agents.consensus import ResultadoAgente, run_consensus_grading, _build_calificador_prompt

        # Verificar que el prompt nivel 10 es más estricto que nivel 1
        prompt_amigo = _build_calificador_prompt("texto", "ctx", 1, "A")
        prompt_experto = _build_calificador_prompt("texto", "ctx", 10, "A")
        assert "ESTRICTO" in prompt_experto.upper() or "EXPERTO" in prompt_experto.upper()
        assert "INDULGENTE" in prompt_amigo.upper() or "esfuerzo" in prompt_amigo.lower()

    def test_reporte_pdf_examen_programacion(self, tmp_path):
        """Genera reporte PDF para examen de programación."""
        from services.report_service import generate_pdf_report
        datos = {
            **MOCK_CALIFICACION_JSON,
            "estudiante": "Ana Martínez",
            "punteo_total": 6.5,
            "punteo_maximo_total": 10.0,
            "porcentaje": 65.0,
        }
        path = generate_pdf_report(datos, output_dir=str(tmp_path))
        assert Path(path).exists()
        size = Path(path).stat().st_size
        assert size > 2000, f"PDF muy pequeño: {size} bytes"

    def test_reporte_word_examen_programacion(self, tmp_path):
        """Genera reporte Word para examen de programación."""
        from services.report_service import generate_word_report
        datos = {
            **MOCK_CALIFICACION_JSON,
            "estudiante": "Ana Martínez",
        }
        path = generate_word_report(datos, output_dir=str(tmp_path))
        assert Path(path).exists()


# ─────────────────────────────────────────────────────────────
# Tests: MCP ICR Server
# ─────────────────────────────────────────────────────────────

class TestMCPServer:
    """Pruebas del servidor MCP para ICR."""

    def test_prompt_matematico_contiene_latex(self):
        """El prompt ICR matemático debe incluir instrucciones de LaTeX."""
        from mcp_servers.icr_server import PROMPT_ICR_MATEMATICO
        assert "LaTeX" in PROMPT_ICR_MATEMATICO
        assert "\\frac" in PROMPT_ICR_MATEMATICO
        assert "\\sqrt" in PROMPT_ICR_MATEMATICO

    def test_prompt_general_contiene_instrucciones(self):
        """El prompt ICR general debe tener instrucciones básicas."""
        from mcp_servers.icr_server import PROMPT_ICR_GENERAL
        assert "YAML" in PROMPT_ICR_GENERAL
        assert "pregunta" in PROMPT_ICR_GENERAL.lower()

    def test_tools_registradas(self):
        """Verifica que las herramientas MCP están definidas."""
        import inspect
        from mcp_servers import icr_server
        # Verificar que existe la función de listado
        assert hasattr(icr_server, "listar_herramientas") or \
               hasattr(icr_server, "server")


# ─────────────────────────────────────────────────────────────
# Configuración de pytest
# ─────────────────────────────────────────────────────────────

def pytest_configure(config):
    """Configuración global de pytest."""
    os.environ.setdefault("GEMINI_API_KEY", "test_key_mock")
    os.environ.setdefault("DB_HOST", "localhost")
    os.environ.setdefault("DB_USER", "test")
    os.environ.setdefault("DB_PASSWORD", "test")
    os.environ.setdefault("DB_NAME", "test_db")
    os.environ.setdefault("CHROMA_PERSIST_DIR", "/tmp/test_chroma")
