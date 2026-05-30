const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageNumber, PageBreak, LevelFormat,
  TableOfContents, ExternalHyperlink
} = require('docx');
const fs = require('fs');

const BLUE      = '1E3A8A';
const BLUE_LIGHT = '3B82F6';
const GRAY_BG   = 'F1F5F9';
const WHITE     = 'FFFFFF';
const border    = { style: BorderStyle.SINGLE, size: 1, color: 'CBD5E1' };
const borders   = { top: border, bottom: border, left: border, right: border };
const noBorder  = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };

// ── Helpers ──────────────────────────────────────────────────

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 160 },
    children: [new TextRun({ text, bold: true, size: 32, color: BLUE, font: 'Arial' })],
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BLUE_LIGHT, space: 4 } },
  });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 120 },
    children: [new TextRun({ text, bold: true, size: 26, color: BLUE, font: 'Arial' })],
  });
}
function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 80 },
    children: [new TextRun({ text, bold: true, size: 22, color: '334155', font: 'Arial' })],
  });
}
function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 120 },
    children: [new TextRun({ text, size: 22, font: 'Arial', ...opts })],
  });
}
function bullet(text, bold = false) {
  return new Paragraph({
    numbering: { reference: 'bullets', level: 0 },
    spacing: { after: 80 },
    children: [new TextRun({ text, size: 22, font: 'Arial', bold })],
  });
}
function numbered(text) {
  return new Paragraph({
    numbering: { reference: 'numbers', level: 0 },
    spacing: { after: 80 },
    children: [new TextRun({ text, size: 22, font: 'Arial' })],
  });
}
function code(text) {
  return new Paragraph({
    spacing: { after: 60 },
    shading: { fill: 'F8FAFC', type: ShadingType.CLEAR },
    children: [new TextRun({ text, size: 18, font: 'Courier New', color: '1E293B' })],
  });
}
function spacer(lines = 1) {
  return new Paragraph({ spacing: { after: 160 * lines }, children: [new TextRun('')] });
}
function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}

// ── Tabla de 2 columnas ───────────────────────────────────────
function table2(rows, header = null) {
  const COL = [4680, 4680];
  const tableRows = [];
  if (header) {
    tableRows.push(new TableRow({
      tableHeader: true,
      children: header.map((h, i) => new TableCell({
        borders, width: { size: COL[i], type: WidthType.DXA },
        shading: { fill: BLUE, type: ShadingType.CLEAR },
        margins: { top: 80, bottom: 80, left: 120, right: 120 },
        children: [new Paragraph({ children: [new TextRun({ text: h, bold: true, color: WHITE, size: 20, font: 'Arial' })] })],
      }))
    }));
  }
  rows.forEach(([c1, c2], idx) => {
    const fill = idx % 2 === 0 ? WHITE : GRAY_BG;
    tableRows.push(new TableRow({
      children: [c1, c2].map((txt, i) => new TableCell({
        borders, width: { size: COL[i], type: WidthType.DXA },
        shading: { fill, type: ShadingType.CLEAR },
        margins: { top: 80, bottom: 80, left: 120, right: 120 },
        children: [new Paragraph({ children: [new TextRun({ text: txt, size: 20, font: 'Arial' })] })],
      }))
    }));
  });
  return new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: COL, rows: tableRows });
}

// ── Tabla de 3 columnas ───────────────────────────────────────
function table3(rows, header = null) {
  const COL = [2160, 3600, 3600];
  const tableRows = [];
  if (header) {
    tableRows.push(new TableRow({
      tableHeader: true,
      children: header.map((h, i) => new TableCell({
        borders, width: { size: COL[i], type: WidthType.DXA },
        shading: { fill: BLUE, type: ShadingType.CLEAR },
        margins: { top: 80, bottom: 80, left: 120, right: 120 },
        children: [new Paragraph({ children: [new TextRun({ text: h, bold: true, color: WHITE, size: 20, font: 'Arial' })] })],
      }))
    }));
  }
  rows.forEach(([c1, c2, c3], idx) => {
    const fill = idx % 2 === 0 ? WHITE : GRAY_BG;
    tableRows.push(new TableRow({
      children: [[c1, 0], [c2, 1], [c3, 2]].map(([txt, i]) => new TableCell({
        borders, width: { size: COL[i], type: WidthType.DXA },
        shading: { fill, type: ShadingType.CLEAR },
        margins: { top: 80, bottom: 80, left: 120, right: 120 },
        children: [new Paragraph({ children: [new TextRun({ text: txt, size: 20, font: 'Arial' })] })],
      }))
    }));
  });
  return new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: COL, rows: tableRows });
}

// ── Documento principal ───────────────────────────────────────
const doc = new Document({
  numbering: {
    config: [
      { reference: 'bullets', levels: [{ level: 0, format: LevelFormat.BULLET, text: '\u2022',
          alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: 'numbers', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.',
          alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ]
  },
  styles: {
    default: { document: { run: { font: 'Arial', size: 22 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 32, bold: true, font: 'Arial', color: BLUE },
        paragraph: { spacing: { before: 360, after: 160 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 26, bold: true, font: 'Arial', color: BLUE },
        paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 1 } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 22, bold: true, font: 'Arial', color: '334155' },
        paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 2 } },
    ]
  },
  sections: [{
    properties: {
      page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } }
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: 'EduGrade AI — Documento Técnico de Diseño', size: 18, color: '94A3B8', font: 'Arial' })],
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: 'CBD5E1', space: 4 } },
        })]
      })
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: 'Universidad — Inteligencia Artificial    Pg. ', size: 18, color: '94A3B8', font: 'Arial' }),
            new TextRun({ children: [PageNumber.CURRENT], size: 18, color: '94A3B8', font: 'Arial' }),
          ],
        })]
      })
    },
    children: [
      // ── PORTADA ────────────────────────────────────────────
      spacer(4),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: 'EduGrade AI', bold: true, size: 72, color: BLUE, font: 'Arial' })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 200 },
        children: [new TextRun({ text: 'Sistema Inteligente Multimodal para la', size: 32, color: '475569', font: 'Arial' })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 480 },
        children: [new TextRun({ text: 'Calificaci\u00f3n Aut\u00f3noma de Ex\u00e1menes', size: 32, color: '475569', font: 'Arial' })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 120 },
        children: [new TextRun({ text: 'Documento T\u00e9cnico de Dise\u00f1o e Implementaci\u00f3n', size: 24, bold: true, color: '64748B', font: 'Arial' })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 600 },
        children: [new TextRun({ text: 'Versi\u00f3n 1.0 \u2014 2024', size: 22, color: '94A3B8', font: 'Arial' })],
      }),
      table2([
        ['Curso', 'Inteligencia Artificial'],
        ['Proyecto', 'Proyecto 1 \u2014 Agente IA Multimodal'],
        ['Stack', 'FastAPI \u00b7 Google GenAI SDK \u00b7 Vue.js 3 \u00b7 MySQL \u00b7 ChromaDB'],
        ['Modelos', 'Gemini 2.0 Flash \u00b7 Flash-Exp \u00b7 text-embedding-004'],
      ]),
      pageBreak(),

      // ── RESUMEN EJECUTIVO ──────────────────────────────────
      h1('1. Resumen Ejecutivo'),
      p('EduGrade AI es un sistema inteligente multimodal dise\u00f1ado para automatizar el proceso de evaluaci\u00f3n de ex\u00e1menes escritos. El sistema integra tres tecnolog\u00edas principales de inteligencia artificial: un modelo de lenguaje grande (LLM) mediante el SDK de Google GenAI (Gemini 2.0), algoritmos de visi\u00f3n por computadora para el ICR, y una arquitectura RAG para contextualizaci\u00f3n con los materiales del docente.'),
      p('La caracter\u00edstica diferenciadora del sistema es su arquitectura de consenso con tres agentes: dos calificadores independientes y un agente Juez que resuelve discrepancias y genera la justificaci\u00f3n pedag\u00f3gica final. Este dise\u00f1o emula el proceso humano de doble evaluaci\u00f3n con \u00e1rbitro, garantizando objetividad y trazabilidad completa.'),
      spacer(),

      // ── ARQUITECTURA ───────────────────────────────────────
      h1('2. Arquitectura del Sistema'),
      h2('2.1 Componentes Tecnol\u00f3gicos'),
      table2([
        ['Backend', 'Python 3.11 \u00b7 FastAPI \u00b7 Uvicorn'],
        ['IA SDK', 'Google GenAI SDK (google-genai) \u2014 sin LangChain'],
        ['Modelos LLM', 'gemini-2.0-flash \u00b7 gemini-2.0-flash-exp'],
        ['Modelo Embeddings', 'models/text-embedding-004'],
        ['Vector DB (RAG)', 'ChromaDB (persistente, b\u00fasqueda coseno)'],
        ['Base de Datos', 'MySQL 8.0 (SQLAlchemy async \u00b7 aiomysql)'],
        ['MCP Server', 'Servidor propio ICR \u2014 Model Context Protocol'],
        ['Frontend', 'Vue.js 3 \u00b7 Composition API \u00b7 Pinia \u00b7 Tailwind CSS v3'],
        ['Reportes', 'fpdf2 (PDF) \u00b7 python-docx (Word)'],
        ['Contenedores', 'Docker \u00b7 Docker Compose \u00b7 Nginx'],
      ], ['Capa', 'Tecnolog\u00eda']),
      spacer(),

      h2('2.2 Flujo de Procesamiento'),
      numbered('El usuario sube las im\u00e1genes del ex\u00e1men (frente/dorso) v\u00eda POST /api/upload.'),
      numbered('El Servicio ICR (icr_service.py) llama a Gemini Vision para extraer texto y f\u00f3rmulas LaTeX, devolviendo un YAML estructurado.'),
      numbered('El Servicio RAG consulta ChromaDB con un embedding del texto extra\u00eddo y recupera los 5 fragmentos m\u00e1s relevantes de los materiales del docente.'),
      numbered('El sistema de consenso lanza los tres agentes:'),
      bullet('Calificador A (gemini-2.0-flash) eval\u00faa independientemente.'),
      bullet('Calificador B (gemini-2.0-flash-exp) eval\u00faa independientemente.'),
      bullet('Agente Juez compara ambos, resuelve discrepancias y genera la justificaci\u00f3n final.'),
      numbered('Se generan reportes PDF y Word y se persisten en MySQL con logs completos de auditor\u00eda.'),
      spacer(),

      h2('2.3 Arquitectura del Servidor MCP (ICR)'),
      p('El servidor MCP (mcp_servers/icr_server.py) expone tres herramientas est\u00e1ndar del Model Context Protocol:'),
      table3([
        ['extraer_texto_examen', 'Extrae texto e im\u00e1genes de ex\u00e1menes. Soporta m\u00faltiples im\u00e1genes y modo matem\u00e1tico/general.', 'Modo matem\u00e1tico activa prompt especializado en LaTeX'],
        ['detectar_formulas_latex', 'Detecta y convierte f\u00f3rmulas matem\u00e1ticas a LaTeX desde una imagen.', 'Retorna expresiones como $\\frac{a}{b}$'],
        ['verificar_servidor', 'Verifica disponibilidad del servidor ICR.', 'Retorna modelo y estado de la API key'],
      ], ['Herramienta MCP', 'Descripci\u00f3n', 'Notas']),
      spacer(),
      pageBreak(),

      // ── BASE DE DATOS ──────────────────────────────────────
      h1('3. Esquema de Base de Datos (MySQL)'),
      h2('3.1 Tablas Principales'),
      table3([
        ['docentes', 'Usuarios del sistema (docentes)', 'id, nombre, email, password_hash, institucion'],
        ['estudiantes', 'Alumnos vinculados a docentes', 'id, nombre, clave, email, docente_id'],
        ['materiales_curso', 'PDFs indexados en ChromaDB', 'id, nombre_archivo, estado, chunks_indexados'],
        ['examenes', 'Metadata de cada ex\u00e1men', 'id, imagenes_rutas (JSON), nivel_exigencia, estado'],
        ['preguntas_extraidas', 'Preguntas/respuestas del ICR', 'id, examen_id, texto_pregunta, respuesta_estudiante, tiene_latex'],
        ['calificaciones_finales', 'Resultado del agente Juez', 'id, punteo_obtenido, conclusion, fortalezas, sugerencias'],
        ['logs_consenso', 'Auditor\u00eda de los 3 agentes', 'agente, modelo_usado, prompt_enviado, respuesta_json, tokens_usados'],
      ], ['Tabla', 'Prop\u00f3sito', 'Columnas Clave']),
      spacer(),
      h2('3.2 Consideraciones de Dise\u00f1o'),
      bullet('imagenes_rutas se almacena como JSON array para soportar m\u00faltiples p\u00e1ginas por ex\u00e1men.'),
      bullet('logs_consenso registra prompt_enviado, respuesta_raw, respuesta_json, tokens_usados y latencia_ms para auditor\u00eda completa.'),
      bullet('El campo estado en examenes (pendiente/procesando/completado/error) permite monitoreo en tiempo real y reintentos.'),
      bullet('Todos los campos de tiempo usan DATETIME para compatibilidad universal con MySQL.'),
      spacer(),
      pageBreak(),

      // ── SISTEMA DE AGENTES ─────────────────────────────────
      h1('4. Sistema de Consenso Multi-Agente'),
      h2('4.1 Agente Calificador A'),
      p('Modelo: gemini-2.0-flash. Eval\u00faa el ex\u00e1men de forma independiente usando el contexto RAG y el nivel de exigencia configurado. Genera un JSON estructurado con punteo por pregunta, justificaci\u00f3n y errores espec\u00edficos detectados.'),
      h2('4.2 Agente Calificador B'),
      p('Modelo: gemini-2.0-flash-exp. Id\u00e9ntica tarea que el Calificador A pero operando con un modelo distinto para garantizar diversidad de perspectivas. Usa el mismo prompt base pero produce evaluaciones independientes.'),
      h2('4.3 Agente Juez / Supervisor'),
      p('Modelo: gemini-2.0-flash. Recibe los JSON completos de A y B, el texto ICR original y el contexto RAG. Aplica el siguiente protocolo de decisi\u00f3n:'),
      bullet('Si A y B coinciden en punteo de una pregunta: acepta ese valor sin modificaci\u00f3n.'),
      bullet('Si difieren en m\u00e1s del 20% del punteo m\u00e1ximo de la pregunta: analiza el texto original y el RAG para decidir.'),
      bullet('El nivel de exigencia act\u00faa como desempate cuando la discrepancia no se puede resolver por contexto.'),
      bullet('Genera la justificaci\u00f3n pedag\u00f3gica final m\u00e1s completa que cualquier calificador individual.'),
      bullet('Documenta cada discrepancia resuelta en el campo discrepancias_resueltas del JSON de salida.'),
      spacer(),
      h2('4.4 Niveles de Exigencia'),
      table2([
        ['1-2', 'Modo Amigo \u2014 Valora el esfuerzo. Tolera errores menores de notaci\u00f3n o signos.'],
        ['3-4', 'Comprensivo \u2014 Da cr\u00e9dito por pasos correctos aunque el resultado final falle.'],
        ['5-6', 'Balanceado \u2014 Eval\u00faa resultado y procedimiento objetivamente.'],
        ['7-8', 'Estricto \u2014 Penaliza errores de signos, exponentes y procedimientos incompletos.'],
        ['9-10', 'Experto \u2014 Solo puntaje completo si resultado y procedimiento son correctos.'],
      ], ['Nivel', 'Comportamiento']),
      spacer(),
      pageBreak(),

      // ── ICR Y LaTeX ────────────────────────────────────────
      h1('5. ICR y Soporte LaTeX'),
      h2('5.1 Alcance del ICR vs OCR'),
      p('A diferencia del OCR tradicional (que solo detecta caracteres sin contexto sem\u00e1ntico), el ICR implementado usa Gemini Vision que comprende el contexto matem\u00e1tico completo:'),
      table2([
        ['OCR Tradicional', 'Detecta caracteres individuales sin contexto sem\u00e1ntico'],
        ['ICR (EduGrade AI)', 'Comprende estructura matem\u00e1tica y contexto acad\u00e9mico'],
        ['Escritura a mano', 'Soportada nativamente por Gemini Vision'],
        ['Texto impreso', 'Alta precisi\u00f3n con cualquier fuente'],
        ['F\u00f3rmulas LaTeX', 'Generaci\u00f3n autom\u00e1tica de marcado LaTeX'],
        ['Vinculaci\u00f3n frente/dorso', 'Asocia procedimientos del dorso con ejercicios del frente'],
      ], ['Caracter\u00edstica', 'Capacidad']),
      spacer(),
      h2('5.2 Expresiones LaTeX Soportadas'),
      table2([
        ['Fracciones', '$\\frac{numerador}{denominador}$'],
        ['Ra\u00edz cuadrada', '$\\sqrt{x}$ / $\\sqrt[n]{x}$'],
        ['Exponentes', '$x^{n}$ / $x^{2n+1}$'],
        ['Sub\u00edndices', '$x_{i}$ / $a_{ij}$'],
        ['Productos notables', '$(a+b)^2 = a^2 + 2ab + b^2$'],
        ['Integrales', '$\\int_{a}^{b} f(x)dx$'],
        ['Sum\u00e1torias', '$\\sum_{i=1}^{n} x_i$'],
        ['Matrices', 'Entorno matrix con corchetes'],
      ], ['Expresi\u00f3n', 'Formato LaTeX Generado']),
      spacer(),
      pageBreak(),

      // ── API ────────────────────────────────────────────────
      h1('6. API REST (FastAPI)'),
      table3([
        ['POST', '/api/upload', 'Sube im\u00e1genes del ex\u00e1men. Params: imagenes[], nivel_exigencia, nombre_estudiante, serie'],
        ['POST', '/api/process/{id}', 'Inicia ICR + RAG + Consenso en background. Retorna inmediatamente.'],
        ['GET', '/api/history', 'Lista historial paginado. Params: page, page_size, estado'],
        ['GET', '/api/history/{id}', 'Detalle completo: comparaci\u00f3n A vs B vs Juez, discrepancias, logs.'],
        ['GET/POST', '/api/config-exigencia', 'Obtiene/actualiza nivel global 1-10.'],
        ['POST', '/api/materials/upload', 'Sube e indexa un PDF en ChromaDB.'],
        ['GET', '/api/materials', 'Lista materiales indexados y fuentes RAG.'],
        ['GET', '/api/download/pdf/{id}', 'Descarga reporte PDF del ex\u00e1men.'],
        ['GET', '/api/download/word/{id}', 'Descarga reporte Word del ex\u00e1men.'],
        ['GET', '/api/health', 'Estado del sistema y versi\u00f3n.'],
      ], ['M\u00e9todo', 'Endpoint', 'Descripci\u00f3n']),
      spacer(),
      pageBreak(),

      // ── PRUEBAS ────────────────────────────────────────────
      h1('7. Plan de Pruebas'),
      h2('7.1 Cobertura de Tests'),
      table3([
        ['TestICRService', '4 tests', 'Parseo YAML, detecci\u00f3n LaTeX, manejo de errores'],
        ['TestRAGService', '5 tests', 'Split de texto, b\u00fasqueda vectorial, estado vac\u00edo'],
        ['TestConsensus', '7 tests', 'Prompts por nivel, merge fallback, flujo completo'],
        ['TestReportService', '8 tests', 'LaTeX\u2192texto, generaci\u00f3n PDF/Word, datos vac\u00edos'],
        ['TestAPIEndpoints', '5 tests', 'Health, config, validaciones de esquema'],
        ['TestExamenesSimulados', '6 tests', 'Pipelines completos con ex\u00e1menes simulados'],
        ['TestMCPServer', '3 tests', 'Prompts, herramientas registradas'],
      ], ['Suite', 'Tests', 'Cobertura']),
      spacer(),
      h2('7.2 Ex\u00e1menes Simulados'),
      p('Se incluyen dos ex\u00e1menes simulados para validar el pipeline completo:'),
      bullet('Examen de Matem\u00e1tica Discreta: preguntas de l\u00f3gica proposicional, combinatoria y teor\u00eda de grafos.'),
      bullet('Examen de Programaci\u00f3n I: definici\u00f3n de conceptos y escritura de c\u00f3digo Python.'),
      spacer(),
      pageBreak(),

      // ── ENTREGABLES ────────────────────────────────────────
      h1('8. Entregables del Proyecto'),
      table2([
        ['Documento t\u00e9cnico', 'Presente documento (DOCX)'],
        ['Manual de usuario', 'manual_usuario.docx'],
        ['C\u00f3digo fuente', 'examgrader/ (backend + frontend)'],
        ['Esquema SQL', 'backend/db/schema.sql'],
        ['Suite de pruebas', 'backend/tests/test_suite.py (38 tests)'],
        ['Docker Compose', 'docker-compose.yml (MySQL + FastAPI + Nginx/Vue)'],
        ['README', 'README.md con instrucciones de instalaci\u00f3n completas'],
      ], ['Entregable', 'Archivo / Ubicaci\u00f3n']),
      spacer(),

      // ── MEJORAS PROPUESTAS ─────────────────────────────────
      h1('9. Mejoras Propuestas'),
      bullet('Autenticaci\u00f3n JWT completa con roles: administrador, docente, estudiante.'),
      bullet('Soporte PPTX y DOCX como materiales adicionales para el RAG (adem\u00e1s de PDF).'),
      bullet('Panel de administrador con estad\u00edsticas agrupadas por curso y distribuci\u00f3n de notas.'),
      bullet('Modo batch: calificar m\u00faltiples ex\u00e1menes en una sola operaci\u00f3n con notificaciones por email.'),
      bullet('Anotaciones visuales sobre la imagen original del ex\u00e1men marcando errores detectados.'),
      bullet('Fine-tuning del modelo ICR con dataset propio de escritura a mano en espa\u00f1ol.'),
      bullet('Cache de embeddings RAG para evitar re-indexar fragmentos ya procesados.'),
      bullet('Webhooks para integraci\u00f3n con LMS (Moodle, Canvas, Google Classroom).'),
      spacer(),
    ]
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync('/mnt/user-data/outputs/documento_tecnico.docx', buf);
  console.log('OK: documento_tecnico.docx');
});
