# 🏛️ Gestor Documental - Municipalidad de El Tabo

Sistema web centralizado para procesamiento automático de documentos municipales con OCR.

## ✨ Características

- 📤 **Carga masiva** de PDFs (hasta 50 archivos)
- 🔍 **OCR automático** para documentos escaneados
- 📊 **Clasificación inteligente**: Memorándum, Acta, Oficio, Decreto, Informe
- 💾 **Base de datos** con historial completo
- 🔎 **Búsqueda** en tiempo real
- 📥 **Descarga** de PDFs originales
- 📈 **Estadísticas** centralizadas
- 🎨 **Diseño institucional** (colores azul marino)

## 🚀 Despliegue en Render.com (GRATIS)

### Paso 1: Crear cuenta en Render

1. Ir a https://render.com
2. Crear cuenta (puede ser con GitHub)

### Paso 2: Subir código a GitHub

```bash
# En tu computador
cd GestorWeb
git init
git add .
git commit -m "Sistema Gestor Documental"

# Crear repositorio en GitHub y subir
git remote add origin https://github.com/TU-USUARIO/gestor-municipal.git
git push -u origin main
```

### Paso 3: Crear Web Service en Render

1. En Render.com, clic en **"New +"** → **"Web Service"**
2. Conectar tu repositorio de GitHub
3. Configuración:
   - **Name**: `gestor-documental-eltabo`
   - **Region**: Oregon (US West)
   - **Branch**: main
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --timeout 300`
   - **Instance Type**: Free

4. Agregar Persistent Disk:
   - Nombre: `data`
   - Mount Path: `/opt/render/project/src/data`
   - Size: 1 GB (gratis)

5. Clic en **"Create Web Service"**

### Paso 4: Esperar deployment

- Primera vez tarda ~10-15 minutos (descarga dependencias OCR)
- Render te dará una URL: `https://gestor-documental-eltabo.onrender.com`

¡Listo! Ahora todos los funcionarios pueden acceder desde cualquier PC.

## 🔗 URLs de acceso

Una vez desplegado, el sistema estará en:
- **Página principal**: `https://tu-app.onrender.com`
- **Cargar documentos**: `https://tu-app.onrender.com` (pestaña "Cargar")
- **Historial**: `https://tu-app.onrender.com` (pestaña "Historial")
- **Estadísticas**: `https://tu-app.onrender.com` (pestaña "Estadísticas")

## 💻 Desarrollo local (opcional)

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
python app.py

# Abrir navegador en:
http://localhost:10000
```

## 📊 Uso del sistema

### Para funcionarios:

1. **Acceder** a la URL del sistema
2. **Arrastrar** PDFs o clic para seleccionar
3. **Clic "Procesar"** y esperar
4. Los documentos se guardan automáticamente en la base de datos

### Pestaña "Historial":
- Ver todos los documentos procesados
- Buscar por nombre, tipo, departamento
- Descargar PDFs originales
- Exportar a Excel

### Pestaña "Estadísticas":
- Total de documentos
- Cantidad procesados con OCR
- Documentos por tipo

## 🔒 Seguridad

**IMPORTANTE**: Esta versión no tiene login. Para producción, recomendamos:

1. Agregar autenticación de usuarios
2. Configurar HTTPS (Render lo hace automático)
3. Limitar acceso por IP de la municipalidad
4. Agregar roles (admin, usuario, lectura)

## 📈 Ventajas vs .bat local

| Aspecto | .bat local | Web centralizada |
|---------|-----------|------------------|
| Instalación | En cada PC | 1 sola vez |
| Actualizaciones | PC por PC | Instantáneas |
| CPU usuario | 25-40% | 0% |
| Historial | Solo local | Compartido |
| Búsqueda | No | Sí |
| Costo | $500k+ | $0 (gratis) |

## 🛠️ Tecnologías

- **Backend**: Flask (Python)
- **OCR**: EasyOCR
- **Base de datos**: SQLite
- **Frontend**: HTML + JavaScript (vanilla)
- **Hosting**: Render.com (gratis)

## 📞 Soporte

Para consultas técnicas, contactar a:
- Departamento de Informática
- Municipalidad de El Tabo

---

**Desarrollado con ❤️ para la Municipalidad de El Tabo**
