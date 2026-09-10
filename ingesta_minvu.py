import sqlite3
import hashlib
from datetime import datetime
import feedparser
import trafilatura
import requests
import re
import time

# ==============================================================================
# CATÁLOGO NACIONAL COMPLETO: 16 REGIONES, PRENSA, TV NACIONAL Y ÁGORA DIGITAL
# Cada entrada define: (url_feed, tipo_fuente, cluster_editorial, region_cobertura)
# ==============================================================================
FEEDS_MINVU = {
    # --------------------------------------------------------------------------
    # 1. PAUTA CENTRAL, AUTORIDADES Y ALERTAS ESTRATÉGICAS NACIONALES
    # --------------------------------------------------------------------------
    "Alerta MINVU y Autoridades": (
        "https://news.google.com/rss/search?q=(MINVU+OR+%22Ministerio+de+Vivienda%22+OR+%22Subsecretar%C3%ADa+de+Vivienda%22+OR+%22Iv%C3%A1n+Poduje%22+OR+%22Natalia+Aguilar%22)+when:5d&hl=es-419&gl=CL&ceid=CL:es-419",
        "🏛️ Institucional MINVU", "📰 Gran Prensa y Pauta Nacional", "Nacional"
    ),
    "Alerta Plan de Emergencia y Déficit": (
        "https://news.google.com/rss/search?q=(%22d%C3%A9ficit+habitacional%22+OR+%22crisis+habitacional%22+OR+%22emergencia+habitacional%22+OR+%22plan+habitacional%22)+when:5d&hl=es-419&gl=CL&ceid=CL:es-419",
        "🏠 Plan Habitacional", "📰 Gran Prensa y Pauta Nacional", "Nacional"
    ),
    "Alerta Caso Convenios y Probidad": (
        "https://news.google.com/rss/search?q=(%22Caso+Convenios%22+OR+%22Democracia+Viva%22+OR+%22ProCultura%22+OR+%22Urbanismo+Social%22)+(MINVU+OR+SERVIU)+when:7d&hl=es-419&gl=CL&ceid=CL:es-419",
        "⚖️ Probidad y Convenios", "🔎 Investigación y Fiscalización", "Nacional"
    ),
    "Alerta Subsidios y Tasas Hipotecarias": (
        "https://news.google.com/rss/search?q=(CChC+OR+%22subsidio+habitacional%22+OR+DS49+OR+DS19+OR+DS1+OR+%22cr%C3%A9dito+hipotecario%22)+when:5d&hl=es-419&gl=CL&ceid=CL:es-419",
        "💼 Mercado Inmobiliario", "💼 Economía, Inmobiliario y Gremios", "Nacional"
    ),

    # --------------------------------------------------------------------------
    # 2. GRAN PRENSA Y PRENSA RADIAL NACIONAL
    # --------------------------------------------------------------------------
    "La Tercera": ("https://www.latercera.com/arcio/rss/", "📰 Gran Prensa", "📰 Gran Prensa y Pauta Nacional", "Nacional"),
    "Emol": ("https://news.google.com/rss/search?q=site:emol.com/noticias/+when:3d&hl=es-419&gl=CL&ceid=CL:es-419", "📰 Gran Prensa", "📰 Gran Prensa y Pauta Nacional", "Nacional"),
    "La Nación": ("https://www.lanacion.cl/feed/", "📰 Gran Prensa", "📰 Gran Prensa y Pauta Nacional", "Nacional"),
    "Radio Bío-Bío": ("https://news.google.com/rss/search?q=site:biobiochile.cl+when:3d&hl=es-419&gl=CL&ceid=CL:es-419", "📻 Prensa Radial", "📻 Prensa Radial y En Directo", "Nacional"),
    "Radio Cooperativa": ("https://cooperativa.cl/noticias/site/tax/port/all/rss____1.xml", "📻 Prensa Radial", "📻 Prensa Radial y En Directo", "Nacional"),
    "ADN Radio": ("https://news.google.com/rss/search?q=site:adnradio.cl+when:3d&hl=es-419&gl=CL&ceid=CL:es-419", "📻 Prensa Radial", "📻 Prensa Radial y En Directo", "Nacional"),

    # --------------------------------------------------------------------------
    # 3. INVESTIGACIÓN Y ECONOMÍA
    # --------------------------------------------------------------------------
    "CIPER Chile": ("https://www.ciperchile.cl/feed/", "🔎 Investigación", "🔎 Investigación y Fiscalización", "Nacional"),
    "El Mostrador": ("https://news.google.com/rss/search?q=site:elmostrador.cl+when:3d&hl=es-419&gl=CL&ceid=CL:es-419", "🔎 Investigación", "🔎 Investigación y Fiscalización", "Nacional"),
    "The Clinic": ("https://www.theclinic.cl/feed/", "🔎 Investigación", "🔎 Investigación y Fiscalización", "Nacional"),
    "Ex-Ante": ("https://news.google.com/rss/search?q=site:ex-ante.cl+when:5d&hl=es-419&gl=CL&ceid=CL:es-419", "🏛️ Análisis Político", "🔎 Investigación y Fiscalización", "Nacional"),
    "Diario Financiero": ("https://news.google.com/rss/search?q=site:df.cl+when:3d&hl=es-419&gl=CL&ceid=CL:es-419", "💼 Economía y Construcción", "💼 Economía, Inmobiliario y Gremios", "Nacional"),

    # --------------------------------------------------------------------------
    # 4. TELEVISIÓN Y VIDEOPOLÍTICA (Portales y Canales de YouTube)
    # --------------------------------------------------------------------------
    "24 Horas (TVN Digital)": ("https://news.google.com/rss/search?q=site:24horas.cl+when:3d&hl=es-419&gl=CL&ceid=CL:es-419", "📺 TV Digital", "📺 Televisión y Videopolítica", "Nacional"),
    "T13 (Canal 13 Digital)": ("https://news.google.com/rss/search?q=site:t13.cl+when:3d&hl=es-419&gl=CL&ceid=CL:es-419", "📺 TV Digital", "📺 Televisión y Videopolítica", "Nacional"),
    "CHV Noticias (Digital)": ("https://news.google.com/rss/search?q=site:chvnoticias.cl+when:3d&hl=es-419&gl=CL&ceid=CL:es-419", "📺 TV Digital", "📺 Televisión y Videopolítica", "Nacional"),
    "Meganoticias (Digital)": ("https://news.google.com/rss/search?q=site:meganoticias.cl+when:3d&hl=es-419&gl=CL&ceid=CL:es-419", "📺 TV Digital", "📺 Televisión y Videopolítica", "Nacional"),
    "24 Horas TVN (Video)": ("https://www.youtube.com/feeds/videos.xml?channel_id=UC_r4iEfF8Nx6IAIZydux7yg", "📺 Video TV", "📺 Televisión y Videopolítica", "Nacional"),
    "Teletrece T13 (Video)": ("https://www.youtube.com/feeds/videos.xml?channel_id=UCQcmb3lvx7hZCoOXvcCvgBg", "📺 Video TV", "📺 Televisión y Videopolítica", "Nacional"),
    "CHV Noticias (Video)": ("https://www.youtube.com/feeds/videos.xml?channel_id=UCRsUoZYC1ULUspipMRnMhwg", "📺 Video TV", "📺 Televisión y Videopolítica", "Nacional"),
    "Meganoticias (Video)": ("https://www.youtube.com/feeds/videos.xml?channel_id=UCkccyEbqhhM3uKOI6Shm-4Q", "📺 Video TV", "📺 Televisión y Videopolítica", "Nacional"),
    "CNN Chile (Video)": ("https://news.google.com/rss/search?q=site:youtube.com+%22CNN+Chile%22+(MINVU+OR+Poduje+OR+vivienda+OR+socav%C3%B3n)+when:30d&hl=es-419&gl=CL&ceid=CL:es-419", "📺 Video TV", "📺 Televisión y Videopolítica", "Nacional"),
    "BioBio TV (Video)": ("https://news.google.com/rss/search?q=site:youtube.com+BioBioChile+(MINVU+OR+Poduje+OR+vivienda+OR+socav%C3%B3n)+when:30d&hl=es-419&gl=CL&ceid=CL:es-419", "📺 Video TV", "📺 Televisión y Videopolítica", "Nacional"),

    # --------------------------------------------------------------------------
    # 5. COBERTURA BALANCEADA Y ROBUSTA EN LAS 16 REGIONES DE CHILE
    # --------------------------------------------------------------------------
    # XV Arica y Parinacota
    "La Estrella de Arica": ("https://news.google.com/rss/search?q=site:estrellaarica.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Arica y Parinacota"),
    "El Morrocotudo Arica": ("https://news.google.com/rss/search?q=site:elmorrocotudo.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Arica y Parinacota"),
    "Alerta Arica y Parinacota": ("https://news.google.com/rss/search?q=(vivienda+OR+subsidio+OR+SERVIU+OR+campamento+OR+%22suelos+salinos%22)+Arica+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Arica y Parinacota"),

    # I Tarapacá
    "La Estrella de Iquique": ("https://news.google.com/rss/search?q=site:estrellaiquique.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Tarapacá"),
    "El Boyaldía Iquique": ("https://news.google.com/rss/search?q=site:elboyaldia.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Tarapacá"),
    "Alerta Tarapacá (Hospicio)": ("https://news.google.com/rss/search?q=(vivienda+OR+subsidio+OR+SERVIU+OR+campamento)+Iquique+OR+%22Alto+Hospicio%22+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Tarapacá"),

    # II Antofagasta
    "El Mercurio de Antofagasta": ("https://news.google.com/rss/search?q=site:mercurioantofagasta.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Antofagasta"),
    "Timeline Antofagasta": ("https://news.google.com/rss/search?q=site:timeline.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Antofagasta"),
    "Alerta Antofagasta y Calama": ("https://news.google.com/rss/search?q=(vivienda+OR+subsidio+OR+SERVIU+OR+campamento+OR+toma)+Antofagasta+OR+Calama+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Antofagasta"),

    # III Atacama
    "El Diario de Atacama": ("https://news.google.com/rss/search?q=site:diarioatacama.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Atacama"),
    "Nostálgica Atacama": ("https://news.google.com/rss/search?q=site:nostalgica.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Atacama"),
    "Alerta Atacama (Copiapó/Vallenar)": ("https://news.google.com/rss/search?q=(vivienda+OR+subsidio+OR+SERVIU+OR+campamento+OR+toma)+Copiapo+OR+Vallenar+OR+Caldera+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Atacama"),

    # IV Coquimbo
    "Diario El Día (Coquimbo/La Serena)": ("https://news.google.com/rss/search?q=site:diarioeldia.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Coquimbo"),
    "El Ovallino (Limarí)": ("https://news.google.com/rss/search?q=site:elovallino.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Coquimbo"),
    "Alerta Coquimbo y La Serena": ("https://news.google.com/rss/search?q=(vivienda+OR+subsidio+OR+SERVIU+OR+campamento)+%22La+Serena%22+OR+Coquimbo+OR+Ovalle+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Coquimbo"),

    # V Valparaíso
    "El Mercurio de Valparaíso": ("https://news.google.com/rss/search?q=site:mercuriovalpo.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Valparaíso"),
    "La Estrella de Valparaíso": ("https://news.google.com/rss/search?q=site:estrellavalpo.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Valparaíso"),
    "El Líder de San Antonio": ("https://news.google.com/rss/search?q=site:lidersanantonio.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Valparaíso"),
    "Alerta Valparaíso, Viña y Concón": ("https://news.google.com/rss/search?q=(vivienda+OR+socavon+OR+SERVIU+OR+Concon+OR+%22Vi%C3%B1a+del+Mar%22)+when:7d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Valparaíso"),

    # XIII Metropolitana
    "La Voz de Maipú / Cerrillos": ("https://news.google.com/rss/search?q=site:lavozdemaipu.cl+when:7d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Metropolitana"),
    "Puente Alto al Día": ("https://news.google.com/rss/search?q=site:puentealtoaldia.cl+when:7d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Metropolitana"),
    "Chicureo Hoy (Lampa/Colina)": ("https://news.google.com/rss/search?q=site:chicureohoy.cl+when:7d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Metropolitana"),
    "Alerta Santiago y Periferia": ("https://news.google.com/rss/search?q=(vivienda+OR+subsidio+OR+SERVIU+OR+Cerrillos+OR+Maipu+OR+Puente+Alto)+Santiago+when:7d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Metropolitana"),

    # VI O'Higgins
    "El Rancagüino": ("https://news.google.com/rss/search?q=site:elrancaguino.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "O'Higgins"),
    "El Tipógrafo O'Higgins": ("https://news.google.com/rss/search?q=site:eltipografo.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "O'Higgins"),
    "Alerta O'Higgins (Rancagua/San Fernando)": ("https://news.google.com/rss/search?q=(vivienda+OR+subsidio+OR+SERVIU+OR+campamento)+Rancagua+OR+%22San+Fernando%22+OR+Machali+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "O'Higgins"),

    # VII Maule
    "Diario La Prensa (Curicó/Talca)": ("https://news.google.com/rss/search?q=site:diariolaprensa.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Maule"),
    "El Heraldo de Linares": ("https://news.google.com/rss/search?q=site:diarioelheraldo.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Maule"),
    "Diario El Centro (Talca)": ("https://news.google.com/rss/search?q=site:diarioelcentro.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Maule"),
    "Alerta Maule (Talca/Curicó/Linares)": ("https://news.google.com/rss/search?q=(vivienda+OR+subsidio+OR+SERVIU+OR+campamento)+Talca+OR+Curico+OR+Linares+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Maule"),

    # XVI Ñuble
    "La Discusión (Chillán)": ("https://news.google.com/rss/search?q=site:ladiscusion.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Ñuble"),
    "San Carlos Online (Ñuble)": ("https://news.google.com/rss/search?q=site:sancarlosonline.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Ñuble"),
    "Alerta Ñuble (Chillán/San Carlos)": ("https://news.google.com/rss/search?q=(vivienda+OR+subsidio+OR+SERVIU+OR+campamento)+Chillan+OR+%22San+Carlos%22+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Ñuble"),

    # VIII Biobío
    "Diario Concepción": ("https://news.google.com/rss/search?q=site:diarioconcepcion.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Biobío"),
    "Sabes.cl (Concepción)": ("https://news.google.com/rss/search?q=site:sabes.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Biobío"),
    "Resumen (Biobío)": ("https://news.google.com/rss/search?q=site:resumen.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Biobío"),
    "Alerta Biobío (Concepción/Los Ángeles)": ("https://news.google.com/rss/search?q=(vivienda+OR+subsidio+OR+SERVIU+OR+campamento)+Concepcion+OR+Talcahuano+OR+%22Los+Angeles%22+when:7d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Biobío"),

    # IX La Araucanía
    "El Austral de Temuco": ("https://news.google.com/rss/search?q=site:australtemuco.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "La Araucanía"),
    "Araucanía Diario": ("https://news.google.com/rss/search?q=site:araucaniadiario.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "La Araucanía"),
    "Alerta Araucanía (Temuco/Villarrica)": ("https://news.google.com/rss/search?q=(vivienda+OR+subsidio+OR+%22subsidio+rural%22+OR+SERVIU)+Temuco+OR+Villarrica+OR+Angol+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "La Araucanía"),

    # XIV Los Ríos
    "El Austral de Valdivia": ("https://news.google.com/rss/search?q=site:australvaldivia.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Los Ríos"),
    "Diario de Valdivia": ("https://news.google.com/rss/search?q=site:diariodevaldivia.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Los Ríos"),
    "Alerta Los Ríos (Valdivia/La Unión)": ("https://news.google.com/rss/search?q=(vivienda+OR+subsidio+OR+SERVIU+OR+campamento)+Valdivia+OR+%22La+Union%22+OR+Panguipulli+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Los Ríos"),

    # X Los Lagos
    "El Llanquihue (Puerto Montt)": ("https://news.google.com/rss/search?q=site:elllanquihue.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Los Lagos"),
    "El Austral de Osorno": ("https://news.google.com/rss/search?q=site:australosorno.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Los Lagos"),
    "La Estrella de Chiloé": ("https://news.google.com/rss/search?q=site:laestrellachiloe.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Los Lagos"),
    "Alerta Los Lagos (Puerto Montt/Osorno/Chiloé)": ("https://news.google.com/rss/search?q=(vivienda+OR+subsidio+OR+SERVIU)+%22Puerto+Montt%22+OR+Osorno+OR+Castro+OR+Ancud+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Los Lagos"),

    # XI Aysén
    "El Diario de Aysén": ("https://news.google.com/rss/search?q=site:diarioaysen.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Aysén"),
    "Radio Santa María (Coyhaique)": ("https://news.google.com/rss/search?q=site:radiosantamaria.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Aysén"),
    "Alerta Aysén (Coyhaique/Aysén)": ("https://news.google.com/rss/search?q=(vivienda+OR+subsidio+OR+SERVIU+OR+habitabilidad)+Coyhaique+OR+Aysen+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Aysén"),

    # XII Magallanes
    "El Pingüino (Punta Arenas)": ("https://news.google.com/rss/search?q=site:elpinguino.com+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Magallanes"),
    "La Prensa Austral (Punta Arenas)": ("https://news.google.com/rss/search?q=site:laprensaaustral.cl+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Magallanes"),
    "Alerta Magallanes (Punta Arenas/Natales)": ("https://news.google.com/rss/search?q=(vivienda+OR+subsidio+OR+SERVIU)+%22Punta+Arenas%22+OR+Natales+when:14d&hl=es-419&gl=CL&ceid=CL:es-419", "🗺️ Prensa Regional", "🗺️ Prensa Regional Descentralizada", "Magallanes"),

    # --------------------------------------------------------------------------
    # 6. ÁGORA DIGITAL Y SOCIAL LISTENING (VIRALES, REDES Y POBLADORES)
    # --------------------------------------------------------------------------
    "X / Twitter: Viralización MINVU y Poduje": (
        "https://news.google.com/rss/search?q=(%22en+X%22+OR+%22en+Twitter%22+OR+viral+OR+tendencia)+(MINVU+OR+SERVIU+OR+Poduje+OR+%22crisis+habitacional%22+OR+subsidio)+when:7d&hl=es-419&gl=CL&ceid=CL:es-419",
        "💬 Redes y Tendencias", "💬 Ágora Digital y Redes Sociales", "Nacional"
    ),
    "TikTok e Instagram: Virales del Hábitat": (
        "https://news.google.com/rss/search?q=(%22en+TikTok%22+OR+%22en+Instagram%22+OR+%22video+viral%22)+(vivienda+OR+arriendo+OR+subsidio+OR+Poduje+OR+MINVU)+Chile+when:14d&hl=es-419&gl=CL&ceid=CL:es-419",
        "💬 Videos Virales Redes", "💬 Ágora Digital y Redes Sociales", "Nacional"
    ),
    "Redes Sociales: Reclamos y Subsidios": (
        "https://news.google.com/rss/search?q=(%22en+redes+sociales%22+OR+denuncia+OR+funa)+(MINVU+OR+SERVIU+OR+Poduje+OR+postulaci%C3%B3n+OR+arriendo)+when:7d&hl=es-419&gl=CL&ceid=CL:es-419",
        "💬 Reclamos Ciudadanos", "💬 Ágora Digital y Redes Sociales", "Nacional"
    ),
    "Reddit Chile: Hilos de Vivienda y Subsidios": (
        "https://news.google.com/rss/search?q=(site:reddit.com/r/chile+OR+site:reddit.com/r/RepublicadeChile)+(MINVU+OR+SERVIU+OR+Poduje+OR+%22subsidio+DS49%22+OR+%22subsidio+DS1%22+OR+%22toma+de+terreno%22)+when:30d&hl=es-419&gl=CL&ceid=CL:es-419",
        "💬 Debate Comunitario", "💬 Ágora Digital y Redes Sociales", "Nacional"
    ),
    "Movimientos de Pobladores y Comités": (
        "https://news.google.com/rss/search?q=(Ukamau+OR+%22comit%C3%A9+de+vivienda%22+OR+%22comit%C3%A9s+de+allegados%22)+(MINVU+OR+SERVIU+OR+vivienda)+when:14d&hl=es-419&gl=CL&ceid=CL:es-419",
        "💬 Movimientos y Comités", "💬 Ágora Digital y Redes Sociales", "Nacional"
    ),
    "Alertas de Desalojo y Tomas de Terreno": (
        "https://news.google.com/rss/search?q=(%22orden+de+desalojo%22+OR+%22toma+de+terreno%22+OR+%22desalojo+de+toma%22+OR+%22megatoma%22)+(MINVU+OR+SERVIU+OR+comuna)+Chile+when:7d&hl=es-419&gl=CL&ceid=CL:es-419",
        "💬 Alertas Territoriales", "💬 Ágora Digital y Redes Sociales", "Nacional"
    ),
    "Denuncias Vecinales: Loteos Brujos": (
        "https://news.google.com/rss/search?q=(%22loteo+brujo%22+OR+%22loteos+brujos%22+OR+%22loteo+irregular%22+OR+%22estafa+inmobiliaria%22)+Chile+when:14d&hl=es-419&gl=CL&ceid=CL:es-419",
        "💬 Denuncias de Suelo", "💬 Ágora Digital y Redes Sociales", "Nacional"
    ),
    "Piensa Prensa (@piensa.prensa)": (
        "https://news.google.com/rss/search?q=%22Piensa+Prensa%22+(vivienda+OR+toma+OR+desalojo+OR+pobladores)+when:14d&hl=es-419&gl=CL&ceid=CL:es-419",
        "📱 Medios Nativos Digitales", "💬 Ágora Digital y Redes Sociales", "Nacional"
    ),
    "El Ciudadano (Vivienda y Redes)": (
        "https://news.google.com/rss/search?q=site:elciudadano.com+(vivienda+OR+arriendo+OR+toma+OR+subsidio)+when:14d&hl=es-419&gl=CL&ceid=CL:es-419",
        "📱 Medios Nativos Digitales", "💬 Ágora Digital y Redes Sociales", "Nacional"
    ),
    "El Desconcierto (Vivienda y Redes)": (
        "https://news.google.com/rss/search?q=site:eldesconcierto.cl+(vivienda+OR+arriendo+OR+toma+OR+subsidio)+when:14d&hl=es-419&gl=CL&ceid=CL:es-419",
        "📱 Medios Nativos Digitales", "💬 Ágora Digital y Redes Sociales", "Nacional"
    ),
    "Copano.news (@copano)": (
        "https://news.google.com/rss/search?q=site:copano.news+(vivienda+OR+arriendo+OR+MINVU)+when:14d&hl=es-419&gl=CL&ceid=CL:es-419",
        "📱 Medios Nativos Digitales", "💬 Ágora Digital y Redes Sociales", "Nacional"
    )
}

DB_NAME = "monitor_minvu.db"

HEADERS_DEFAULT = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-CL,es;q=0.9,en;q=0.8"
}

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articulos (
            id TEXT PRIMARY KEY,
            medio TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            titulo TEXT NOT NULL,
            bajada TEXT,
            cuerpo TEXT,
            autor TEXT,
            fecha_publicacion TEXT,
            fecha_captura TEXT NOT NULL,
            seccion TEXT,
            eje_tematico TEXT,
            tipo_fuente TEXT,
            cluster_editorial TEXT,
            region TEXT,
            sentimiento TEXT,
            polaridad_score REAL,
            es_minvu INTEGER DEFAULT 0
        )
    """)
    cursor.execute("PRAGMA table_info(articulos)")
    cols = [col[1] for col in cursor.fetchall()]
    if "cluster_editorial" not in cols:
        try: cursor.execute("ALTER TABLE articulos ADD COLUMN cluster_editorial TEXT")
        except Exception: pass
    if "region" not in cols:
        try: cursor.execute("ALTER TABLE articulos ADD COLUMN region TEXT")
        except Exception: pass
    if "sentimiento" not in cols:
        try: cursor.execute("ALTER TABLE articulos ADD COLUMN sentimiento TEXT")
        except Exception: pass
    if "polaridad_score" not in cols:
        try: cursor.execute("ALTER TABLE articulos ADD COLUMN polaridad_score REAL")
        except Exception: pass

    conn.commit()
    conn.close()

def limpiar_texto_video(descripcion):
    if not descripcion:
        return ""
    d = re.sub(r'https?://\S+|www\.\S+', ' ', str(descripcion))
    d = re.sub(r'(?i)(suscríbete|siguenos en|síguenos en|descarga nuestra app|todos los derechos reservados).*', '', d)
    return re.sub(r'\s+', ' ', d).strip()

def procesar_feeds():
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    ahora = datetime.now().isoformat()
    nuevos = 0
    exitosos = 0
    advertencias = 0

    print("==================================================")
    print(" INICIANDO CAPTURA NACIONAL MINVU: PRENSA, TV Y REDES")
    print(f" Total Canales y Endpoints Configurados: {len(FEEDS_MINVU)}")
    print("==================================================")

    for medio, (url_feed, tipologia, cluster_edit, region_cov) in FEEDS_MINVU.items():
        print(f"\n[*] Conectando: [{region_cov} | {cluster_edit}] {medio}...")
        
        try:
            resp = requests.get(url_feed, headers=HEADERS_DEFAULT, timeout=12)
            if resp.status_code != 200:
                print(f"  [!] Alerta HTTP {resp.status_code} en {medio}. Omitiendo feed de forma segura.")
                advertencias += 1
                continue
            feed = feedparser.parse(resp.content)
            exitosos += 1
        except Exception as e:
            print(f"  [!] Error de red con {medio}: {e}. Continuando...")
            advertencias += 1
            continue

        if not feed.entries:
            print(f"  [-] Sin publicaciones recientes detectadas en {medio}.")
            continue

        guardados_medio = 0
        for entry in feed.entries[:15]:
            url = entry.get("link", "").strip()
            titulo = entry.get("title", "").strip()

            if not url or not titulo:
                continue

            art_id = hashlib.sha256(url.encode("utf-8")).hexdigest()

            cursor.execute("SELECT id FROM articulos WHERE id = ?", (art_id,))
            if cursor.fetchone():
                continue

            bajada = entry.get("summary", "")
            if bajada:
                bajada = re.sub(r'<[^>]+>', ' ', bajada).strip()

            cuerpo = ""
            es_video = "youtube.com" in url or "youtu.be" in url or "Video" in medio
            if es_video:
                cuerpo = limpiar_texto_video(entry.get("summary", ""))
            else:
                try:
                    descarga = trafilatura.fetch_url(url)
                    if descarga:
                        extraido = trafilatura.extract(descarga, include_comments=False)
                        if extraido:
                            cuerpo = extraido.strip()
                except Exception:
                    cuerpo = bajada

            fecha_pub = entry.get("published", "") or entry.get("updated", "") or ahora
            autor = entry.get("author", "Redacción")

            cursor.execute("""
                INSERT INTO articulos (
                    id, medio, url, titulo, bajada, cuerpo, autor,
                    fecha_publicacion, fecha_captura, seccion, eje_tematico,
                    tipo_fuente, cluster_editorial, region, es_minvu
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """, (
                art_id, medio, url, titulo, bajada, cuerpo, autor,
                fecha_pub, ahora, "Nacional", "Sin clasificar",
                tipologia, cluster_edit, region_cov
            ))
            guardados_medio += 1
            nuevos += 1

        print(f"  [+] {guardados_medio} registros guardados de {medio}.")
        conn.commit()

    cursor.execute("SELECT COUNT(*) FROM articulos")
    total_db = cursor.fetchone()[0]
    conn.close()

    print("\n==================================================")
    print(f" [RESUMEN DE AUDITORÍA DE INGESTA NACIONAL MINVU]")
    print(f"  - Canales operativos procesados: {exitosos}/{len(FEEDS_MINVU)}")
    print(f"  - Canales con advertencias/reintentos: {advertencias}")
    print(f"  - Nuevos registros ingresados: {nuevos}")
    print(f"  - Total acumulado en base de datos: {total_db}")
    print("==================================================")

if __name__ == "__main__":
    procesar_feeds()
