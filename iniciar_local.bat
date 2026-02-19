@echo off
echo ========================================================
echo   Gestor Documental - Modo Local
echo ========================================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado
    pause
    exit /b 1
)

REM Crear entorno virtual
if not exist "venv\" (
    echo [1/3] Creando entorno virtual...
    python -m venv venv
)

REM Activar entorno
call venv\Scripts\activate.bat

REM Instalar dependencias
echo [2/3] Instalando dependencias...
pip install -q -r requirements.txt

REM Iniciar servidor
echo [3/3] Iniciando servidor...
echo.
echo Servidor corriendo en:
echo    http://localhost:10000
echo.
echo Presiona Ctrl+C para detener
echo.

python app.py
pause
