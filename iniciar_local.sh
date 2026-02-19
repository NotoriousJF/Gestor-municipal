#!/bin/bash
echo "════════════════════════════════════════════════════"
echo "  Gestor Documental - Modo Local"
echo "════════════════════════════════════════════════════"
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado"
    exit 1
fi

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "[1/3] Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno
source venv/bin/activate

# Instalar dependencias
echo "[2/3] Instalando dependencias..."
pip install -q -r requirements.txt

# Iniciar servidor
echo "[3/3] Iniciando servidor..."
echo ""
echo "✅ Servidor corriendo en:"
echo "   http://localhost:10000"
echo ""
echo "Presiona Ctrl+C para detener"
echo ""

python app.py
