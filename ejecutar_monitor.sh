#!/bin/bash
echo "==================================================="
echo " MONITOR MINVU CHILE - ACTUALIZANDO BASE DE DATOS"
echo "==================================================="
python3 -m pip install -r requirements.txt
python3 -m pip install feedparser trafilatura spacy
python3 -m spacy download es_core_news_sm
python3 actualizar_minvu.py
echo "==================================================="
echo " INICIANDO PANEL STREAMLIT..."
echo "==================================================="
python3 -m streamlit run app_minvu.py
