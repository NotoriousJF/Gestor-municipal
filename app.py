"""
Gestor Documental Municipal - Versión Web
Municipalidad de El Tabo
Optimizado para servidor público (Render.com)
"""

from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
import os
import re
import gc
import fitz
import easyocr
import pandas as pd
from datetime import datetime
import sqlite3
import json
from pathlib import Path

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB max

# Configuración de carpetas
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
PROCESSED_DIR = DATA_DIR / "processed"
DB_PATH = DATA_DIR / "documentos.db"

for d in [DATA_DIR, UPLOAD_DIR, PROCESSED_DIR]:
    d.mkdir(exist_ok=True, parents=True)

# Inicializar OCR (solo una vez)
print("⏳ Cargando EasyOCR...")
reader = easyocr.Reader(['es'], gpu=False, verbose=False)
print("✅ OCR listo")

# ═══════════════════════════════════════════════════════════════
# BASE DE DATOS
# ═══════════════════════════════════════════════════════════════

def init_db():
    """Inicializa la base de datos SQLite"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            archivo TEXT NOT NULL,
            tipo TEXT,
            origen TEXT,
            destino TEXT,
            asunto TEXT,
            metodo TEXT,
            fecha_procesado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ruta_pdf TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ═══════════════════════════════════════════════════════════════
# DICCIONARIO DE DEPARTAMENTOS
# ═══════════════════════════════════════════════════════════════

DEPTOS_MAP = {
    "ADMINISTRACION": "ADMINISTRACIÓN MUNICIPAL",
    "ADMINISTRADOR": "ADMINISTRACIÓN MUNICIPAL",
    "FINANZAS": "DIRECCIÓN DE ADM. Y FINANZAS (DAF)",
    "DAF": "DIRECCIÓN DE ADM. Y FINANZAS (DAF)",
    "INFORMATICA": "INFORMÁTICA",
    "INFORMÁTICO": "INFORMÁTICA",
    "TI": "INFORMÁTICA",
    "COMUNICACIONES": "COMUNICACIONES",
    "ADQUISICIONES": "ADQUISICIONES",
    "OBRAS": "DIRECCIÓN DE OBRAS (DOM)",
    "DOM": "DIRECCIÓN DE OBRAS (DOM)",
    "CONTROL": "DIRECCIÓN DE CONTROL",
    "JURIDICA": "ASESORÍA JURÍDICA",
    "SECPLA": "SECPLA",
    "DIDECO": "DIDECO",
    "ALCALDE": "ALCALDÍA",
    "ALCALDIA": "ALCALDÍA",
    "SALUD": "DEPARTAMENTO DE SALUD",
    "EDUCACION": "DAEM (EDUCACIÓN)",
    "DAEM": "DAEM (EDUCACIÓN)",
    "RRHH": "RECURSOS HUMANOS",
}

# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE ANÁLISIS (Optimizadas para CPU bajo)
# ═══════════════════════════════════════════════════════════════

def identificar_depto(texto):
    if not texto or len(texto.strip()) < 3:
        return "---"
    tu = texto.upper().strip()
    for clave, oficial in DEPTOS_MAP.items():
        if clave in tu:
            return oficial
    patterns = [
        r"DIRECTOR[A]?\s+(?:DE\s+)?([A-Z\s]+)",
        r"JEFE[A]?\s+(?:DE\s+)?([A-Z\s]+)",
        r"ENCARGAD[OA]\s+(?:DE\s+)?([A-Z\s]+)",
    ]
    for p in patterns:
        m = re.search(p, tu)
        if m:
            d = re.sub(r"MUNICIPALIDAD.*$", "", m.group(1)).strip()
            for clave, oficial in DEPTOS_MAP.items():
                if clave in d:
                    return oficial
            if len(d) > 3:
                return d[:40].title()
    return "---"


def extraer_texto_pdf(ruta):
    """Extracción híbrida optimizada"""
    try:
        doc = fitz.open(ruta)
        page = doc[0]
        tn = page.get_text()
        
        if len(tn.strip()) > 50:
            doc.close()
            lineas = [l.strip() for l in tn.split("\n") if l.strip()]
            return lineas, "NATIVO"
        
        # OCR con DPI bajo (optimizado)
        pix = page.get_pixmap(dpi=100, colorspace=fitz.csGRAY)
        img = pix.tobytes("png")
        doc.close()
        
        lineas = reader.readtext(img, detail=0, paragraph=False)
        lineas = [l.strip() for l in lineas if l.strip()]
        return lineas, "OCR"
    except Exception as e:
        print(f"Error extrayendo: {e}")
        return [], "ERROR"


def generar_titulo(texto, tipo):
    """Genera título automático breve"""
    up = texto.upper()
    
    if tipo == "ACTA DE ENTREGA":
        if "NOTEBOOK" in up or "COMPUTADOR" in up:
            return "Entrega: Notebook"
        elif "IPHONE" in up or "CELULAR" in up:
            return "Entrega: Celular"
        elif "CHIP" in up:
            return "Entrega: Chips"
        return "Entrega: Equipo"
    
    # Memorándum/Oficio
    if "SOLICITA" in up:
        return "Solicitud"
    elif "INFORMA" in up:
        return "Información"
    elif "AUTORIZA" in up:
        return "Autorización"
    
    return "Documento administrativo"


def analizar_documento(lineas, tipo):
    """Análisis simplificado"""
    info = {"origen": "---", "destino": "---", "asunto": "---"}
    texto = " ".join(lineas)
    info["asunto"] = generar_titulo(texto, tipo)
    
    # Buscar deptos en orden
    deptos = []
    for linea in lineas[:20]:  # Solo primeras 20 líneas
        r = identificar_depto(linea)
        if r != "---" and r not in [d for _, d in deptos]:
            deptos.append((0, r))
    
    if len(deptos) >= 2:
        info["origen"] = deptos[0][1]
        info["destino"] = deptos[1][1]
    elif len(deptos) == 1:
        info["destino"] = deptos[0][1]
    
    return info


def analizar_archivo(ruta):
    """Análisis completo con prioridad en nombre"""
    nombre = Path(ruta).name
    info = {
        "archivo": nombre,
        "tipo": "OTRO",
        "origen": "---",
        "destino": "---",
        "asunto": "---",
        "metodo": ""
    }
    
    try:
        lineas, metodo = extraer_texto_pdf(ruta)
        info["metodo"] = metodo
        
        if not lineas:
            return info
        
        nombre_up = nombre.upper()
        texto_up = " ".join(lineas[:5]).upper()
        
        # Detección por nombre (prioridad)
        if "ACTA" in nombre_up:
            info["tipo"] = "ACTA DE ENTREGA"
        elif "MEMO" in nombre_up:
            info["tipo"] = "MEMORÁNDUM"
        elif "OFICIO" in nombre_up:
            info["tipo"] = "OFICIO"
        elif "DECRETO" in nombre_up:
            info["tipo"] = "DECRETO"
        elif "INFORME" in nombre_up:
            info["tipo"] = "INFORME"
        # Fallback por contenido
        elif "ACTA" in texto_up and "ENTREGA" in texto_up:
            info["tipo"] = "ACTA DE ENTREGA"
        elif "MEMORANDUM" in texto_up or "MEMORÁNDUM" in texto_up:
            info["tipo"] = "MEMORÁNDUM"
        elif "OFICIO" in texto_up:
            info["tipo"] = "OFICIO"
        elif "DECRETO" in texto_up:
            info["tipo"] = "DECRETO"
        elif "INFORME" in texto_up:
            info["tipo"] = "INFORME"
        
        datos = analizar_documento(lineas, info["tipo"])
        info.update(datos)
        
        print(f"✓ {nombre}: {info['tipo']} [{metodo}]")
        
    except Exception as e:
        print(f"✗ Error en {nombre}: {e}")
    
    return info


# ═══════════════════════════════════════════════════════════════
# RUTAS WEB
# ═══════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/process", methods=["POST"])
def process_file():
    """Procesa un PDF y guarda en BD"""
    if "file" not in request.files:
        return jsonify({"error": "Sin archivo"}), 400
    
    file = request.files["file"]
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Solo PDF"}), 400
    
    # Guardar archivo
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{timestamp}_{filename}"
    filepath = UPLOAD_DIR / unique_filename
    file.save(filepath)
    
    # Procesar
    info = analizar_archivo(filepath)
    
    # Mover a processed
    processed_path = PROCESSED_DIR / unique_filename
    filepath.rename(processed_path)
    
    # Guardar en BD
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO documentos (archivo, tipo, origen, destino, asunto, metodo, ruta_pdf)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        info["archivo"],
        info["tipo"],
        info["origen"],
        info["destino"],
        info["asunto"],
        info["metodo"],
        str(processed_path)
    ))
    doc_id = c.lastrowid
    conn.commit()
    conn.close()
    
    info["id"] = doc_id
    gc.collect()
    
    return jsonify(info)


@app.route("/api/documentos")
def listar_documentos():
    """Lista todos los documentos procesados"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''
        SELECT id, archivo, tipo, origen, destino, asunto, metodo, 
               datetime(fecha_procesado, 'localtime') as fecha
        FROM documentos
        ORDER BY fecha_procesado DESC
        LIMIT 1000
    ''')
    docs = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(docs)


@app.route("/api/stats")
def estadisticas():
    """Estadísticas generales"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM documentos")
    total = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM documentos WHERE metodo = 'OCR'")
    ocr = c.fetchone()[0]
    
    c.execute("SELECT tipo, COUNT(*) as n FROM documentos GROUP BY tipo")
    por_tipo = dict(c.fetchall())
    
    conn.close()
    
    return jsonify({
        "total": total,
        "via_ocr": ocr,
        "por_tipo": por_tipo
    })


@app.route("/download/<int:doc_id>")
def descargar_pdf(doc_id):
    """Descarga un PDF procesado"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT archivo, ruta_pdf FROM documentos WHERE id = ?", (doc_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return "Documento no encontrado", 404
    
    archivo, ruta = row
    if not Path(ruta).exists():
        return "Archivo no existe en disco", 404
    
    return send_file(ruta, as_attachment=True, download_name=archivo)


@app.route("/api/export")
def exportar_excel():
    """Exporta todos los documentos a Excel"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('''
        SELECT archivo as "Archivo",
               tipo as "Tipo",
               origen as "Origen",
               destino as "Destino",
               asunto as "Asunto",
               metodo as "Método",
               datetime(fecha_procesado, 'localtime') as "Fecha Procesado"
        FROM documentos
        ORDER BY fecha_procesado DESC
    ''', conn)
    conn.close()
    
    # Generar Excel
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Documentos_Municipales_{timestamp}.xlsx"
    filepath = DATA_DIR / filename
    
    df.to_excel(filepath, index=False, engine='openpyxl')
    
    return send_file(filepath, as_attachment=True, download_name=filename)


if __name__ == "__main__":
    # Configuración para producción
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
