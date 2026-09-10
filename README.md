# Monitor de Medios y Social Listening | MINVU Chile (2026)

Observatorio estratégico de prensa nacional, televisión abierta, 16 regiones de Chile y redes sociales para el Ministerio de Vivienda y Urbanismo.
Autoridades vigentes: **Ministro Iván Poduje · Subsecretaria Natalia Aguilar**.

---

## 🏛️ Características de Esta Versión de Producción

1. **Pureza 100% Sectorial**: Solo ingresan noticias estrictamente relacionadas con vivienda, subsidios, tomas de terreno, socavones y el MINVU. Todo contenido ajeno o internacional es descartado automáticamente.
2. **Cobertura Real de las 16 Regiones**: Mapa físico interactivo de Chile con marcadores en las 16 capitales regionales y Matriz de Calor con las 16 regiones oficiales reindexadas de forma permanente.
3. **Termómetro de Sentimiento en Vivo**: Net Sentiment Score (NSS) y cálculo de polaridad reactivo en tiempo real ante cualquier filtro.
4. **Ranking Limpio de Actores (Sin Ruido)**: Whitelist estricta de autoridades e instituciones de vivienda (sin celebridades ni medios de comunicación clasificados como personas).
5. **Social Listening Enfocado**: Gráfico de Demandas Ciudadanas y Brecha de Agenda (Agenda-Gap) en barras horizontales sin superposición de texto.
6. **Minuta Ejecutiva 1-Click**: Reporte estructurado para gabinete en 6 dimensiones sustantivas, descargable en `.txt`.
7. **Cadencia Continua Cada 15 Minutos**: Automatización en GitHub Actions programada con `*/15 * * * *` (24/7).

---

## 🚀 Cómo Crear y Activar el Nuevo Repositorio en GitHub (Paso a Paso)

### 1. Crear el Repositorio en GitHub
1. Entra a [github.com](https://github.com) e inicia sesión.
2. Haz clic en el botón verde **New** (o en el icono `+` arriba a la derecha $\rightarrow$ **New repository**).
3. Escribe un nombre para tu nuevo repositorio (por ejemplo: `monitor-minvu-2026` o `monitor-minvu-oficial`).
4. Selecciona **Public**.
5. Marca la casilla **Add a README file**.
6. Haz clic en **Create repository**.

### 2. Subir los Archivos de este Paquete
1. Descarga y descomprime el archivo `Monitor_MINVU_Nuevo_Repositorio_2026.zip`.
2. En la página principal de tu nuevo repositorio en GitHub, haz clic en **Add file** $\rightarrow$ **Upload files**.
3. Arrastra **todos los archivos y la carpeta `.github`** hacia la ventana de GitHub.
4. En el campo inferior escribe *"Versión final de producción MINVU 2026"* y presiona el botón verde **Commit changes**.

### 3. Activar Permisos para la Actualización Cada 15 Minutos (¡CRUCIAL!)
Para que el bot de GitHub Actions pueda actualizar y guardar la base de datos automáticamente cada 15 minutos:
1. En tu nuevo repositorio, haz clic en la pestaña **Settings** (arriba a la derecha).
2. En el menú lateral izquierdo, haz clic en **Actions** $\rightarrow$ **General**.
3. Baja hasta la sección **Workflow permissions**.
4. Selecciona la opción: **Read and write permissions**.
5. Haz clic en el botón verde **Save**.

### 4. Lanzar la Primera Ingesta de Datos
1. Haz clic en la pestaña **Actions** (arriba al centro en GitHub).
2. En la lista de la izquierda, selecciona *"Actualizador Continuo Monitor MINVU (Cada 15 Minutos)"*.
3. Verás un botón gris a la derecha que dice **Run workflow**. Presiónalo y confirma con el botón verde.
4. El proceso tardará unos 2 minutos en capturar todas las fuentes y generar la base de datos `monitor_minvu.db`. A partir de ahí, correrá automáticamente cada 15 minutos exactos.

### 5. Desplegar en Streamlit Cloud
1. Entra a [share.streamlit.io](https://share.streamlit.io) e inicia sesión con tu cuenta de GitHub.
2. Haz clic en el botón azul **Create app** (o **New app**).
3. Selecciona:
   - **Repository**: Tu nuevo repositorio (ej: `dhx10/monitor-minvu-2026`).
   - **Branch**: `main` (o `master`).
   - **Main file path**: `app_minvu.py`.
4. Haz clic en **Deploy**. En 1 minuto tu monitor estará en vivo y actualizándose cada 15 minutos.
