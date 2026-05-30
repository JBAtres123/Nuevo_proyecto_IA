const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageNumber, PageBreak, LevelFormat,
} = require('docx');
const fs = require('fs');

const BLUE      = '1E3A8A';
const TEAL      = '0D9488';
const GREEN     = '16A34A';
const ORANGE    = 'EA580C';
const GRAY_BG   = 'F1F5F9';
const BLUE_BG   = 'EFF6FF';
const GREEN_BG  = 'F0FDF4';
const ORANGE_BG = 'FFF7ED';
const WHITE     = 'FFFFFF';
const border    = { style: BorderStyle.SINGLE, size: 1, color: 'CBD5E1' };
const borders   = { top: border, bottom: border, left: border, right: border };

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 160 },
    children: [new TextRun({ text, bold: true, size: 32, color: BLUE, font: 'Arial' })],
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: '3B82F6', space: 4 } },
  });
}
function h2(text, color = BLUE) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 120 },
    children: [new TextRun({ text, bold: true, size: 26, color, font: 'Arial' })],
  });
}
function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 180, after: 80 },
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
    spacing: { after: 100 },
    children: [new TextRun({ text, size: 22, font: 'Arial' })],
  });
}
function spacer(n = 1) {
  return new Paragraph({ spacing: { after: 160 * n }, children: [new TextRun('')] });
}
function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}
function tip(icon, title, text, fill = BLUE_BG, titleColor = BLUE) {
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [640, 8720],
    rows: [new TableRow({
      children: [
        new TableCell({
          borders, width: { size: 640, type: WidthType.DXA },
          shading: { fill, type: ShadingType.CLEAR },
          margins: { top: 100, bottom: 100, left: 120, right: 60 },
          verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: icon, size: 28, font: 'Arial' })] })],
        }),
        new TableCell({
          borders, width: { size: 8720, type: WidthType.DXA },
          shading: { fill, type: ShadingType.CLEAR },
          margins: { top: 100, bottom: 100, left: 120, right: 120 },
          children: [
            new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: title, bold: true, size: 22, color: titleColor, font: 'Arial' })] }),
            new Paragraph({ children: [new TextRun({ text, size: 20, font: 'Arial', color: '334155' })] }),
          ],
        }),
      ]
    })]
  });
}
function step(num, title, desc) {
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [640, 8720],
    rows: [new TableRow({
      children: [
        new TableCell({
          borders: { top: { style: BorderStyle.NONE, size: 0 }, bottom: { style: BorderStyle.NONE, size: 0 }, left: { style: BorderStyle.NONE, size: 0 }, right: { style: BorderStyle.NONE, size: 0 } },
          width: { size: 640, type: WidthType.DXA },
          shading: { fill: BLUE, type: ShadingType.CLEAR },
          margins: { top: 120, bottom: 120, left: 60, right: 60 },
          verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: num, bold: true, size: 26, color: WHITE, font: 'Arial' })] })],
        }),
        new TableCell({
          borders: { top: { style: BorderStyle.NONE, size: 0 }, bottom: { style: BorderStyle.NONE, size: 0 }, left: { style: BorderStyle.NONE, size: 0 }, right: { style: BorderStyle.NONE, size: 0 } },
          width: { size: 8720, type: WidthType.DXA },
          shading: { fill: BLUE_BG, type: ShadingType.CLEAR },
          margins: { top: 120, bottom: 120, left: 180, right: 120 },
          children: [
            new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: title, bold: true, size: 22, color: BLUE, font: 'Arial' })] }),
            new Paragraph({ children: [new TextRun({ text: desc, size: 20, font: 'Arial', color: '475569' })] }),
          ],
        }),
      ]
    })]
  });
}
function tableSimple(rows, header, colWidths = [3120, 6240]) {
  const tableRows = [];
  if (header) {
    tableRows.push(new TableRow({
      tableHeader: true,
      children: header.map((h, i) => new TableCell({
        borders, width: { size: colWidths[i], type: WidthType.DXA },
        shading: { fill: BLUE, type: ShadingType.CLEAR },
        margins: { top: 80, bottom: 80, left: 120, right: 120 },
        children: [new Paragraph({ children: [new TextRun({ text: h, bold: true, color: WHITE, size: 20, font: 'Arial' })] })]
      }))
    }));
  }
  rows.forEach(([c1, c2], idx) => {
    const fill = idx % 2 === 0 ? WHITE : GRAY_BG;
    tableRows.push(new TableRow({
      children: [[c1, 0], [c2, 1]].map(([txt, i]) => new TableCell({
        borders, width: { size: colWidths[i], type: WidthType.DXA },
        shading: { fill, type: ShadingType.CLEAR },
        margins: { top: 80, bottom: 80, left: 120, right: 120 },
        children: [new Paragraph({ children: [new TextRun({ text: txt, size: 20, font: 'Arial' })] })]
      }))
    }));
  });
  return new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: colWidths, rows: tableRows });
}

// ── Documento ─────────────────────────────────────────────────
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
          children: [new TextRun({ text: 'EduGrade AI \u2014 Manual de Usuario', size: 18, color: '94A3B8', font: 'Arial' })],
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: 'CBD5E1', space: 4 } },
        })]
      })
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: 'EduGrade AI    P\u00e1gina ', size: 18, color: '94A3B8', font: 'Arial' }),
            new TextRun({ children: [PageNumber.CURRENT], size: 18, color: '94A3B8', font: 'Arial' }),
          ],
        })]
      })
    },
    children: [
      // ── PORTADA ────────────────────────────────────────────
      spacer(3),
      new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: '\uD83C\uDF93', size: 96, font: 'Arial' })] }),
      spacer(),
      new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: 'EduGrade AI', bold: true, size: 72, color: BLUE, font: 'Arial' })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [new TextRun({ text: 'Manual de Usuario', size: 36, color: '475569', font: 'Arial' })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 600 }, children: [new TextRun({ text: 'Guia paso a paso para calificar examenes con Inteligencia Artificial', size: 22, color: '94A3B8', font: 'Arial' })] }),
      tip('\u2139\uFE0F', 'Para qui\u00e9n es este manual',
        'Este manual est\u00e1 dirigido a docentes que usar\u00e1n EduGrade AI para calificar ex\u00e1menes. No se requieren conocimientos t\u00e9cnicos de programaci\u00f3n o inteligencia artificial.', BLUE_BG, BLUE),
      pageBreak(),

      // ── CAP 1: PRIMEROS PASOS ──────────────────────────────
      h1('Cap\u00edtulo 1: Primeros Pasos'),
      h2('1.1 Acceso al Sistema'),
      p('Abra su navegador web (Chrome, Firefox o Edge recomendados) y navegue a la direcci\u00f3n del sistema. La p\u00e1gina principal muestra el panel de inicio con un resumen de las funcionalidades disponibles.'),
      spacer(0.5),
      tip('\uD83D\uDCBB', 'URL del sistema', 'http://localhost (instalaci\u00f3n local) o la direcci\u00f3n que le proporcione su administrador.', BLUE_BG, BLUE),
      spacer(),

      h2('1.2 Navegaci\u00f3n Principal'),
      p('La barra de navegaci\u00f3n superior tiene las siguientes secciones:'),
      tableSimple([
        ['\uD83C\uDFE0 Inicio', 'Panel principal con resumen del sistema y acceso r\u00e1pido.'],
        ['\uD83D\uDCDD Calificar', 'Subir im\u00e1genes de ex\u00e1menes y configurar la calificaci\u00f3n.'],
        ['\uD83D\uDCCB Historial', 'Ver todos los ex\u00e1menes calificados y sus resultados.'],
        ['\uD83D\uDCDA Materiales', 'Subir PDFs del curso para el sistema de contexto (RAG).'],
        ['\u2699\uFE0F Configuraci\u00f3n', 'Ajustar el nivel de exigencia global y verificar el estado.'],
      ], ['Secci\u00f3n', 'Funci\u00f3n']),
      spacer(),

      h2('1.3 Indicador de Nivel de Exigencia'),
      p('En la esquina superior derecha siempre aparece el nivel de exigencia activo (ej. "5/10"). Este valor afecta c\u00f3mo los agentes IA calificar\u00e1n las respuestas de los estudiantes.'),
      pageBreak(),

      // ── CAP 2: SUBIR MATERIALES ────────────────────────────
      h1('Cap\u00edtulo 2: Subir Materiales del Curso'),
      p('Antes de calificar ex\u00e1menes, se recomienda subir los materiales del curso (apuntes, presentaciones, libros de texto en PDF). Esto permite al sistema calificar con el contexto espec\u00edfico de su clase.'),
      spacer(0.5),
      tip('\uD83D\uDCA1', 'Por qu\u00e9 es importante', 'Los materiales indexados permiten al sistema RAG recuperar el contenido relevante del curso al evaluar cada respuesta, mejorando significativamente la precisi\u00f3n y relevancia de las justificaciones.', GREEN_BG, GREEN),
      spacer(),

      h2('2.1 Subir un PDF'),
      step('1', 'Ir a Materiales', 'Haga clic en "Materiales" en la barra de navegaci\u00f3n superior.'),
      spacer(0.3),
      step('2', 'Seleccionar el archivo', 'Arrastre su PDF al \u00e1rea de carga o haga clic en ella para abrir el explorador de archivos. Solo se aceptan archivos .pdf.'),
      spacer(0.3),
      step('3', 'Indexar', 'Haga clic en "Indexar Material". El sistema procesar\u00e1 el PDF, lo dividir\u00e1 en fragmentos y crear\u00e1 embeddings vectoriales en ChromaDB.'),
      spacer(0.3),
      step('4', 'Confirmar', 'Aparecer\u00e1 un mensaje de \u00e9xito indicando el n\u00famero de p\u00e1ginas y fragmentos indexados.'),
      spacer(),
      tip('\u26A0\uFE0F', 'Tiempo de procesamiento', 'PDFs grandes (100+ p\u00e1ginas) pueden tardar 1-3 minutos en indexarse completamente. La barra de progreso indica el estado.', ORANGE_BG, ORANGE),
      spacer(),

      h2('2.2 Ver Materiales Indexados'),
      p('La tabla inferior de la p\u00e1gina "Materiales" muestra todos los PDFs indexados, indicando el n\u00famero de p\u00e1ginas, fragmentos creados y el estado del \u00edndice.'),
      pageBreak(),

      // ── CAP 3: CALIFICAR EXAMEN ────────────────────────────
      h1('Cap\u00edtulo 3: Calificar un Ex\u00e1men'),
      h2('3.1 Preparaci\u00f3n de las Im\u00e1genes'),
      p('Para mejores resultados con el sistema ICR, siga estas recomendaciones al fotografiar o escanear los ex\u00e1menes:'),
      bullet('Im\u00e1genes en formato JPG, PNG o WEBP (hasta 50 MB por archivo).'),
      bullet('Resoluci\u00f3n m\u00ednima recomendada: 300 DPI para escritura a mano.'),
      bullet('Buena iluminaci\u00f3n, sin sombras sobre el texto.'),
      bullet('La hoja debe estar recta, sin rotaci\u00f3n excesiva.'),
      bullet('Si el ex\u00e1men tiene frente y dorso, suba ambas im\u00e1genes.'),
      spacer(),

      h2('3.2 Subir el Ex\u00e1men'),
      step('1', 'Ir a Calificar', 'Haga clic en "Calificar" o en el bot\u00f3n "+ Calificar" de la barra superior.'),
      spacer(0.3),
      step('2', 'Subir im\u00e1genes', 'Arrastre las im\u00e1genes al \u00e1rea de carga o haga clic para seleccionarlas. Puede subir m\u00faltiples im\u00e1genes (frente y dorso del ex\u00e1men).'),
      spacer(0.3),
      step('3', 'Datos opcionales', 'Si lo desea, ingrese el nombre del estudiante y la serie del ex\u00e1men. Si los deja vac\u00edos, el sistema ICR los detectar\u00e1 autom\u00e1ticamente.'),
      spacer(0.3),
      step('4', 'Configurar exigencia', 'Ajuste el slider de nivel de exigencia (1-10) seg\u00fan su criterio acad\u00e9mico.'),
      spacer(0.3),
      step('5', 'Calificar', 'Haga clic en "Calificar Ex\u00e1men". El sistema mostrar\u00e1 el progreso en tiempo real.'),
      spacer(),

      h2('3.3 El Nivel de Exigencia'),
      p('El slider de exigencia controla qu\u00e9 tan estrictamente los agentes IA evaluar\u00e1n las respuestas:'),
      tableSimple([
        ['1-2 \uD83D\uDE0A Amigo', 'Ideal para primeras evaluaciones o cursos introductorios. Valora el esfuerzo y los procedimientos aunque el resultado final sea incorrecto.'],
        ['3-4 \uD83D\uDE42 Comprensivo', 'Da cr\u00e9dito parcial generoso por pasos correctos. Bueno para ex\u00e1menes formativos.'],
        ['5-6 \u2696\uFE0F Balanceado', 'Evaluaci\u00f3n objetiva est\u00e1ndar. Considera tanto el proceso como el resultado.'],
        ['7-8 \uD83C\uDFAF Estricto', 'Penaliza errores de signos, exponentes incorrectos y procedimientos incompletos.'],
        ['9-10 \uD83D\uDD2C Experto', 'Evaluaci\u00f3n acad\u00e9mica m\u00e1xima. Solo puntaje completo si todo es correcto.'],
      ], ['Nivel', 'Comportamiento'], [2000, 7360]),
      spacer(),

      h2('3.4 Durante el Procesamiento'),
      p('El sistema mostrar\u00e1 el progreso en tres etapas:'),
      bullet('Subiendo im\u00e1genes: carga de archivos al servidor.'),
      bullet('ICR \u2014 Extrayendo texto: Gemini Vision analiza las im\u00e1genes y extrae preguntas, respuestas y f\u00f3rmulas LaTeX.'),
      bullet('Agentes IA calificando: los tres agentes (Calificador A, Calificador B y Juez) eval\u00faan el ex\u00e1men en paralelo.'),
      spacer(),
      tip('\u23F1\uFE0F', 'Tiempo de procesamiento', 'El proceso completo tarda entre 30 segundos y 3 minutos, dependiendo del n\u00famero de preguntas y la complejidad del ex\u00e1men.', BLUE_BG, BLUE),
      pageBreak(),

      // ── CAP 4: VER RESULTADOS ──────────────────────────────
      h1('Cap\u00edtulo 4: Ver y Descargar Resultados'),
      h2('4.1 Vista de Resultado Final'),
      p('Una vez completado el procesamiento, puede ver el resultado completo en tres pesta\u00f1as:'),
      tableSimple([
        ['\u2696\uFE0F Resultado Final', 'Muestra el punteo total, detalle por pregunta con justificaciones, conclusi\u00f3n general, fortalezas, \u00e1reas de mejora y sugerencias.'],
        ['\uD83D\uDD2C Comparaci\u00f3n Agentes', 'Compara los punteos del Calificador A, Calificador B y el Juez. Muestra las discrepancias detectadas y c\u00f3mo se resolvieron.'],
        ['\uD83D\uDCC4 Texto ICR', 'Muestra el texto raw extra\u00eddo por el sistema ICR, \u00fatil para verificar la calidad de la extracci\u00f3n.'],
      ], ['Pesta\u00f1a', 'Contenido']),
      spacer(),

      h2('4.2 Interpretaci\u00f3n del Punteo'),
      tableSimple([
        ['70% - 100%', 'Calificaci\u00f3n exitosa (verde). El estudiante demuestra dominio del tema.'],
        ['60% - 69%', 'Calificaci\u00f3n de aprobado m\u00ednimo (amarillo). Requiere refuerzo en algunos temas.'],
        ['0% - 59%', 'Calificaci\u00f3n insuficiente (rojo). El estudiante necesita revisi\u00f3n profunda del material.'],
      ], ['Rango', 'Significado']),
      spacer(),

      h2('4.3 Descargar Reportes'),
      p('En la esquina superior derecha de la vista de detalle, encontrar\u00e1 dos botones de descarga:'),
      bullet('\u2B07 PDF: Genera un informe profesional en formato PDF con colores y formato estructurado.'),
      bullet('\u2B07 Word: Genera el mismo informe en formato .docx editable con Microsoft Word o LibreOffice.'),
      spacer(),
      tip('\uD83D\uDCCB', 'Contenido del reporte', 'Ambos reportes incluyen: datos del estudiante, punteo total y porcentaje, detalle por pregunta con justificaciones, conclusi\u00f3n general, fortalezas, \u00e1reas de mejora y sugerencias de estudio.', GREEN_BG, GREEN),
      spacer(),

      h2('4.4 Comparaci\u00f3n de Agentes'),
      p('La pesta\u00f1a "Comparaci\u00f3n Agentes" es especialmente \u00fatil para entender c\u00f3mo el sistema lleg\u00f3 a la calificaci\u00f3n final:'),
      bullet('Calificador A y B: muestran sus punteos individuales, tokens usados y latencia.'),
      bullet('Juez: muestra el razonamiento final y c\u00f3mo resolvi\u00f3 las discrepancias.'),
      bullet('Tabla de discrepancias: indica qu\u00e9 preguntas tuvieron diferencias entre A y B, y cu\u00e1l fue la decisi\u00f3n final.'),
      pageBreak(),

      // ── CAP 5: HISTORIAL ───────────────────────────────────
      h1('Cap\u00edtulo 5: Historial de Calificaciones'),
      h2('5.1 Navegar el Historial'),
      p('La secci\u00f3n "Historial" muestra todos los ex\u00e1menes calificados en orden cronol\u00f3gico inverso (el m\u00e1s reciente primero).'),
      p('Puede filtrar por estado:'),
      bullet('\u2705 Completados: ex\u00e1menes procesados exitosamente.'),
      bullet('\u23F3 Procesando: ex\u00e1menes actualmente siendo calificados.'),
      bullet('\u274C Con error: ex\u00e1menes que no pudieron procesarse (generalmente por problemas con la imagen).'),
      spacer(),

      h2('5.2 Columnas del Historial'),
      tableSimple([
        ['#', 'ID interno del ex\u00e1men para referencia.'],
        ['Estudiante', 'Nombre detectado por ICR o ingresado manualmente.'],
        ['Serie', 'C\u00f3digo o serie del ex\u00e1men.'],
        ['Exigencia', 'Nivel 1-10 aplicado al momento de calificar.'],
        ['Punteo', 'Barra visual y porcentaje con c\u00f3digo de colores.'],
        ['Estado', 'Indicador de estado: completado / procesando / error.'],
        ['Fecha', 'Fecha y hora de carga del ex\u00e1men.'],
      ], ['Columna', 'Significado']),
      spacer(),
      tip('\uD83D\uDD0D', 'Acceder al detalle', 'Pase el cursor sobre cualquier fila del historial y haga clic en "Ver \u2192" para abrir el resultado completo del ex\u00e1men.', BLUE_BG, BLUE),
      pageBreak(),

      // ── CAP 6: PREGUNTAS FRECUENTES ────────────────────────
      h1('Cap\u00edtulo 6: Preguntas Frecuentes'),
      h3('\u00bfQu\u00e9 pasa si el ICR no reconoce bien la escritura?'),
      p('Si el texto extra\u00eddo (pesta\u00f1a "Texto ICR") contiene errores, puede deberse a:'),
      bullet('Imagen de baja resoluci\u00f3n o iluminaci\u00f3n deficiente.'),
      bullet('Escritura extremadamente ilegible.'),
      bullet('M\u00faltiples estudiantes en la misma imagen.'),
      p('Soluci\u00f3n: vuelva a subir el ex\u00e1men con una imagen de mejor calidad.'),
      spacer(),

      h3('\u00bfPuedo cambiar el nivel de exigencia despu\u00e9s de calificar?'),
      p('No. El nivel de exigencia se aplica en el momento del procesamiento y queda registrado en el historial. Para recalificar con un nivel diferente, debe volver a subir el ex\u00e1men.'),
      spacer(),

      h3('\u00bfPor qu\u00e9 los punteos del Calificador A y B difieren?'),
      p('Es normal y esperado. Usan modelos ligeramente diferentes y procesan el ex\u00e1men de forma independiente. El Agente Juez analiza ambas evaluaciones para producir una calificaci\u00f3n final m\u00e1s objetiva. La tabla de discrepancias muestra exactamente d\u00f3nde difirieron y c\u00f3mo se resolvi\u00f3.'),
      spacer(),

      h3('\u00bfCu\u00e1ntos materiales puedo subir?'),
      p('No hay l\u00edmite fijo de materiales. Sin embargo, para mejores resultados se recomienda que los materiales sean espec\u00edficos del tema del ex\u00e1men. El sistema selecciona autom\u00e1ticamente los 5 fragmentos m\u00e1s relevantes para cada evaluaci\u00f3n.'),
      spacer(),

      h3('\u00bfLos reportes PDF y Word son id\u00e9nticos?'),
      p('S\u00ed en contenido, pero difieren en formato: el PDF es el definitivo para imprimir o compartir digitalmente, mientras que el Word es editable y permite al docente agregar comentarios adicionales antes de entregar al estudiante.'),
      spacer(),
      pageBreak(),

      // ── CAP 7: SOLUCION DE PROBLEMAS ──────────────────────
      h1('Cap\u00edtulo 7: Soluci\u00f3n de Problemas'),
      tableSimple([
        ['El ex\u00e1men queda en estado "procesando" por m\u00e1s de 5 minutos.', 'Verifique el estado del sistema en Configuraci\u00f3n > Verificar API. Si hay error, contacte al administrador.'],
        ['El ICR extrae texto incorrecto o ilegible.', 'Suba una nueva imagen de mayor calidad y vuelva a procesar. Use 300 DPI o superior.'],
        ['Error al indexar un material PDF.', 'Verifique que el PDF no est\u00e9 protegido con contrase\u00f1a y que contenga texto seleccionable (no solo im\u00e1genes escaneadas).'],
        ['El porcentaje del ex\u00e1men parece incorrecto.', 'Revise la pesta\u00f1a "Comparaci\u00f3n Agentes" para entender el razonamiento. Si hay un error claro, el docente puede ajustar el punteo en el reporte Word.'],
        ['No se pueden descargar los reportes.', 'El ex\u00e1men debe estar en estado "completado". Si el bot\u00f3n no funciona, intente recargar la p\u00e1gina.'],
      ], ['Problema', 'Soluci\u00f3n'], [3500, 5860]),
      spacer(),
      tip('\uD83D\uDCDE', 'Soporte t\u00e9cnico', 'Para problemas no resueltos, contacte al administrador del sistema con el ID del ex\u00e1men (#) para diagn\u00f3stico r\u00e1pido.', ORANGE_BG, ORANGE),
      spacer(),
    ]
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync('/mnt/user-data/outputs/manual_usuario.docx', buf);
  console.log('OK: manual_usuario.docx');
});
