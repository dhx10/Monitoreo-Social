@echo off
title Monitor MINVU Chile (2026)
echo ===================================================
echo  MONITOR MINVU CHILE - DETECTANDO ENTORNO PYTHON
echo ===================================================

where py >nul 2>nul
if %errorlevel%==0 (
    set PY_CMD=py
    goto :found
)

where python >nul 2>nul
if %errorlevel%==0 (
    set PY_CMD=python
    goto :found
)

echo [ERROR] No se detecto Python instalado en tu sistema.
echo Descarga e instala Python desde https://www.python.org/
echo IMPORTANTE: Marca la casilla "Add python.exe to PATH".
pause
exit /b

:found
echo [OK] Usando interprete: %PY_CMD%
echo.

echo ===================================================
echo  PASO 1: VERIFICANDO E INSTALANDO LIBRERIAS...
echo ===================================================
%PY_CMD% -m pip install -r requirements.txt
%PY_CMD% -m pip install feedparser trafilatura spacy
%PY_CMD% -m spacy download es_core_news_sm >nul 2>nul

echo.
echo ===================================================
echo  PASO 2: ACTUALIZANDO NOTICIAS, 16 REGIONES Y REDES...
echo ===================================================
%PY_CMD% actualizar_minvu.py

echo.
echo ===================================================
echo  PASO 3: INICIANDO PANEL STREAMLIT...
echo ===================================================
%PY_CMD% -m streamlit run app_minvu.py
pause
