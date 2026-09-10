import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
from datetime import datetime
from collections import Counter

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA INSTITUCIONAL MINVU
# ==============================================================================
st.set_page_config(
    page_title="Monitor de Medios y Social Listening | MINVU Chile",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 2. ESTILOS VISUALES LIMPIOS (SIN CÓDIGO EXPUESTO NI COLISIONES TIPOGRÁFICAS)
# ==============================================================================
st.markdown("""
<meta name="google" content="notranslate">
<div translate="no" class="notranslate"></div>
<style>
    body, html, .stApp {
        translate: no !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #0F172A;
    }
    p, .stMarkdown p {
        line-height: 1.68 !important;
        margin-bottom: 0.95rem !important;
        font-size: 0.96rem !important;
        color: #334155 !important;
    }
    .minvu-title {
        font-size: 2.15rem;
        font-weight: 800;
        color: #0F3B66;
        margin-bottom: 0.35rem;
        letter-spacing: -0.5px;
    }
    .minvu-subtitle {
        font-size: 1.02rem;
        color: #475569;
        margin-bottom: 1.6rem;
        line-height: 1.5;
    }
    .guia-periodistica {
        background: #F8FAFC;
        border-left: 4px solid #0284C7;
        padding: 0.85rem 1.15rem;
        border-radius: 0 8px 8px 0;
        margin-top: 0.4rem;
        margin-bottom: 1.3rem;
        font-size: 0.88rem;
        color: #1E293B;
        line-height: 1.58;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .guia-periodistica b {
        color: #0F3B66;
    }
    .tag-cruce {
        display: inline-block;
        background: #E0F2FE;
        color: #0369A1;
        font-weight: 700;
        padding: 0.12rem 0.45rem;
        border-radius: 4px;
        font-size: 0.76rem;
        margin-right: 0.3rem;
    }
    .badge-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-bottom: 1.1rem;
        align-items: center;
    }
    .badge-item {
        display: inline-flex;
        align-items: center;
        padding: 0.28rem 0.65rem;
        border-radius: 6px;
        font-size: 0.76rem;
        font-weight: 700;
        line-height: 1.2;
    }
    .badge-minvu { background: #0F3B66; color: #FFFFFF; }
    .badge-positivo { background: #10B981; color: #FFFFFF; }
    .badge-neutro { background: #64748B; color: #FFFFFF; }
    .badge-negativo { background: #EF4444; color: #FFFFFF; }
    .badge-region { background: #0284C7; color: #FFFFFF; }
    .badge-cluster { background: #E2E8F0; color: #1E293B; font-weight: 600; }
    .badge-critico { background: #D92D20; color: #FFFFFF; }

    .noticia-bajada {
        font-size: 0.96rem;
        font-weight: 500;
        color: #475569;
        margin-bottom: 0.85rem;
        line-height: 1.6;
        border-left: 3px solid #CBD5E1;
        padding-left: 0.85rem;
        font-style: italic;
    }
    .noticia-cuerpo {
        font-size: 0.93rem;
        line-height: 1.72;
        color: #1E293B;
        margin-bottom: 1rem;
    }
    .noticia-meta {
        font-size: 0.83rem;
        color: #64748B;
        margin-bottom: 0.5rem;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
        margin-bottom: 1.15rem !important;
        background: #FFFFFF !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
    }
    div[data-testid="stExpander"]:hover {
        border-color: #CBD5E1 !important;
    }
    div[data-testid="stExpander"] > details > summary {
        padding: 0.85rem 1.15rem !important;
        font-size: 1.01rem !important;
        font-weight: 600 !important;
        color: #0F3B66 !important;
    }
    div[data-testid="stExpander"] > details > div {
        padding: 1.1rem 1.35rem !important;
    }
    .verbatim-box-minvu {
        border-left: 4px solid #D92D20;
        background: #FFF1F2;
        padding: 1rem 1.35rem;
        border-radius: 0 8px 8px 0;
        margin-top: 0.6rem;
        margin-bottom: 1rem;
        font-style: italic;
        color: #0F172A;
        line-height: 1.65;
        font-size: 0.98rem;
    }
    .minuta-card {
        background: #F8FAFC;
        border: 1px solid #CBD5E1;
        border-radius: 8px;
        padding: 1.3rem 1.5rem;
        margin-top: 1rem;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
        font-size: 0.92rem;
        line-height: 1.7;
        white-space: pre-wrap;
        color: #0F172A;
    }
</style>
""", unsafe_allow_html=True)

DB_NAME = "monitor_minvu.db"

# ==============================================================================
# 3. LISTA OFICIAL DE LAS 16 REGIONES DE CHILE Y COORDENADAS GEOGRÁFICAS
# ==============================================================================
REGIONES_CHILE = [
    "Arica y Parinacota",
    "Tarapacá",
    "Antofagasta",
    "Atacama",
    "Coquimbo",
    "Valparaíso",
    "Metropolitana",
    "O'Higgins",
    "Maule",
    "Ñuble",
    "Biobío",
    "La Araucanía",
    "Los Ríos",
    "Los Lagos",
    "Aysén",
    "Magallanes"
]

COORDENADAS_REGIONES = {
    "Arica y Parinacota": {"lat": -18.4783, "lon": -70.3126, "capital": "Arica"},
    "Tarapacá": {"lat": -20.2133, "lon": -70.1503, "capital": "Iquique"},
    "Antofagasta": {"lat": -23.6509, "lon": -70.3975, "capital": "Antofagasta"},
    "Atacama": {"lat": -27.3668, "lon": -70.3323, "capital": "Copiapó"},
    "Coquimbo": {"lat": -29.9533, "lon": -71.3436, "capital": "La Serena"},
    "Valparaíso": {"lat": -33.0472, "lon": -71.6127, "capital": "Valparaíso"},
    "Metropolitana": {"lat": -33.4489, "lon": -70.6693, "capital": "Santiago"},
    "O'Higgins": {"lat": -34.1708, "lon": -70.7444, "capital": "Rancagua"},
    "Maule": {"lat": -35.4264, "lon": -71.6554, "capital": "Talca"},
    "Ñuble": {"lat": -36.6067, "lon": -72.1034, "capital": "Chillán"},
    "Biobío": {"lat": -36.8201, "lon": -73.0444, "capital": "Concepción"},
    "La Araucanía": {"lat": -38.7359, "lon": -72.5904, "capital": "Temuco"},
    "Los Ríos": {"lat": -39.8196, "lon": -73.2452, "capital": "Valdivia"},
    "Los Lagos": {"lat": -41.4693, "lon": -72.9424, "capital": "Puerto Montt"},
    "Aysén": {"lat": -45.5752, "lon": -72.0662, "capital": "Coyhaique"},
    "Magallanes": {"lat": -53.1638, "lon": -70.9171, "capital": "Punta Arenas"}
}

# ==============================================================================
# 4. CERROJO DEFENSIVO: ANCLAS INVIOLABLES DE VIVIENDA Y EXCLUSIÓN FORÁNEA
# ==============================================================================
PATRONES_VIVIENDA_CHILE = [
    # 1. Conceptos nucleares de vivienda y habitabilidad
    r'\bvivienda(?:s)?\b',
    r'\bhabitacional(?:es)?\b',
    r'\bsoluci[óo]n(?:es)? habitacional(?:es)?\b',
    r'\bconjunto(?:s)? habitacional(?:es)?\b',
    r'\bcasa(?:s)? propia(?:s)?\b',
    r'\bdepartamento(?:s)? social(?:es)?\b',
    
    # 2. Instituciones y Autoridades
    r'\bminvu\b',
    r'\bserviu\b',
    r'\bservius\b',
    r'\bministerio de vivienda\b',
    r'\bsubsecretar[íi]a de vivienda\b',
    r'\bseremi (?:de )?vivienda\b',
    r'\bseremis (?:de )?vivienda\b',
    r'\bseremi minvu\b',
    r'\biv[áa]n poduje\b',
    r'\bministro poduje\b',
    r'\bpoduje\b',
    r'\bnatalia aguilar\b',
    r'\bsubsecretaria aguilar\b',
    r'\bparquemet\b',
    r'\bparque metropolitano\b',
    r'\bditec\b', r'\bddu\b', r'\bdph\b',
    
    # 3. Subsidios, Créditos y Programas
    r'\bsubsidio(?:s)?\b',
    r'\bds49\b', r'\bds 49\b',
    r'\bds19\b', r'\bds 19\b',
    r'\bds1\b', r'\bds 1\b',
    r'\bds52\b', r'\bds 52\b',
    r'\bds10\b', r'\bds 10\b',
    r'\bds27\b', r'\bds 27\b',
    r'\bcr[ée]dito(?:s)? hipotecario(?:s)?\b',
    r'\btasa(?:s)? hipotecaria(?:s)?\b',
    r'\bdividendo(?:s)?\b',
    r'\bbanco de suelo(?:s)?\b',
    r'\bpostulaci[óo]n (?:al )?subsidio\b',
    r'\bpostulaciones (?:al )?subsidio\b',
    r'\bllamado a postular\b',
    r'\bfogaes\b',
    
    # 4. Crisis, Déficit, Comités y Arriendos
    r'\bd[ée]ficit habitacional\b',
    r'\bcrisis habitacional\b',
    r'\bemergencia habitacional\b',
    r'\bplan (?:de )?emergencia habitacional\b',
    r'\bcomit[ée]s? de vivienda\b',
    r'\bcomit[ée]s? de allegados\b',
    r'\ballegado(?:s)?\b',
    r'\bdeudores habitacionales\b',
    r'\barriendo(?:s)?\b',
    r'\barrendatario(?:s)?\b',
    r'\barrendador(?:es)?\b',
    r'\bprecio(?:s)? de arriendo\b',
    r'\balquiler(?:es)?\b',
    
    # 5. Campamentos, Tomas, Desalojos y Suelo
    r'\bcampamento(?:s)?\b',
    r'\basentamiento(?:s)? precario(?:s)?\b',
    r'\btoma(?:s)? de terreno(?:s)?\b',
    r'\btoma(?:s)? ilegal(?:es)?\b',
    r'\bmegatoma(?:s)?\b',
    r'\bdesalojo(?:s)?\b',
    r'\busurpaci[óo]n (?:de )?terreno(?:s)?\b',
    r'\bocupaci[óo]n(?:es)? (?:ilegal(?:es)?|de terreno(?:s)?)\b',
    r'\bterreno(?:s)? fiscal(?:es)?\b',
    r'\bterreno(?:s)? municipal(?:es)?\b',
    r'\bloteo(?:s)? brujo(?:s)?\b',
    r'\bloteo(?:s)? irregular(?:es)?\b',
    r'\bestafa(?:s)? inmobiliaria(?:s)?\b',
    r'\bcatastro de campamentos\b',
    r'\btecho(?:-chile)?\b',
    r'\bd[ée]ficit cero\b',
    r'\bukamau\b',
    
    # 6. Catástrofes, Socavones y Reconstrucción
    r'\bsocav[óo]n(?:es)?\b',
    r'\bedificio kandinsky\b',
    r'\beuromarina\b',
    r'\bmiramar re[ñn]aca\b',
    r'\bdunas de conc[óo]n\b',
    r'\bcampo dunar\b',
    r'\breconstrucci[óo]n\b',
    r'\bvivienda(?:s)? de emergencia\b',
    r'\bdamnificado(?:s)?\b',
    r'\bsuelos salinos\b',
    r'\bfalla estructural\b',
    
    # 7. Industria de la Construcción y Ciudad
    r'\bcchc\b',
    r'\bc[áa]mara chilena de la construcci[óo]n\b',
    r'\bquiebra(?:s)? de constructora(?:s)?\b',
    r'\bparalizaci[óo]n de obras\b',
    r'\bpermisolog[íi]a\b',
    r'\bpermiso(?:s)? de edificaci[óo]n\b',
    r'\bplan regulador\b',
    r'\bguetos verticales\b',
    r'\bquiero mi barrio\b',
    r'\bpavimentaci[óo]n participativa\b',
    
    # 8. Caso Convenios
    r'\bcaso convenios\b',
    r'\bdemocracia viva\b',
    r'\bprocultura\b',
    r'\burbanismo social\b'
]

# Países y ciudades foráneas para descarte inmediato (salvo mención explícita a MINVU/SERVIU/Poduje)



MARCADORES_EXCLUSION_ARGENTINA = [
    r'\bargentina\b', r'\bargentino(?:s)?\b', r'\bargentina(?:s)?\b',
    r'\bbuenos aires\b', r'\bcaba\b', r'\bconurbano\b', r'\blaplata\b', r'\bla plata\b',
    r'\bmendoza\b', r'\bc[óo]rdoba\b', r'\brosario\b', r'\bsanta fe\b', r'\bsalta\b',
    r'\btucum[áa]n\b', r'\bjujuy\b', r'\bneuqu[ée]n\b', r'\bbariloche\b', r'\bchubut\b',
    r'\br[íi]o gallegos\b', r'\bushuaia\b', r'\bmar del plata\b', r'\bbah[íi]a blanca\b',
    r'\bquilmes\b', r'\bavellaneda\b', r'\blan[úu]s\b', r'\bmor[óo]n\b', r'\bla matanza\b',
    r'\bcorrientes\b', r'\bentre r[íi]os\b', r'\bchaco\b', r'\bformosa\b', r'\bmisiones\b',
    r'\bla pampa\b', r'\bsan juan\b', r'\bsan luis\b', r'\bla rioja\b', r'\bcatamarca\b',
    r'\bsantiago del estero\b', r'\bmilei\b', r'\bjavier milei\b', r'\bkicillof\b',
    r'\baxel kicillof\b', r'\bvillarruel\b', r'\bcasa rosada\b', r'\banses\b', r'\bafip\b',
    r'\barca\b', r'\bindec\b', r'\bd[óo]lar blue\b', r'\bpesos argentinos\b'
]

TOPONIMOS_COMPARTIDOS = {
    "santa cruz": [r'\bcolchagua\b', r"\bo'higgins\b", r'\bchile\b', r'\bvalle de colchagua\b', r'\bserviu\b', r'\bminvu\b'],
    "río negro": [r'\bosorno\b', r'\blos lagos\b', r'\bchile\b', r'\bpurranque\b', r'\bserviu\b', r'\bminvu\b'],
    "rio negro": [r'\bosorno\b', r'\blos lagos\b', r'\bchile\b', r'\bpurranque\b', r'\bserviu\b', r'\bminvu\b'],
    "san rafael": [r'\bmaule\b', r'\btalca\b', r'\bchile\b', r'\bserviu\b', r'\bminvu\b'],
    "san pedro": [r'\bmelipilla\b', r'\bmetropolitana\b', r'\bchile\b', r'\bserviu\b', r'\bminvu\b', r'\bsan pedro de la paz\b', r'\bbiob[íi]o\b'],
    "los andes": [r'\bvalpara[íi]so\b', r'\baconcagua\b', r'\bsan felipe\b', r'\bchile\b', r'\bserviu\b', r'\bminvu\b']
}

DOMINIOS_ARGENTINOS = [
    ".ar", "clarin.com", "lanacion.com.ar", "infobae.com", "pagina12.com.ar",
    "perfil.com", "cronista.com", "ambito.com", "losandes.com.ar", "rionegro.com.ar",
    "lmneuquen.com", "diarioelzonda.com.ar", "cadena3.com", "lacapital.com.ar"
]

ACTORES_PERMITIDOS_MINVU = {
    "Iván Poduje (Ministro MINVU)", "Natalia Aguilar (Subsecretaria MINVU)", "Rodrigo Uribe (SERVIU)",
    "DITEC MINVU", "División de Desarrollo Urbano (DDU)", "División de Política Habitacional (DPH)",
    "Parquemet (Parque Metropolitano)", "MINVU (Central)", "Subsecretaría de Vivienda", "SEREMI MINVU",
    "SERVIU", "SERVIU Metropolitano", "SERVIU Valparaíso", "SERVIU Biobío", "SERVIU Araucanía",
    "SERVIU Antofagasta", "SERVIU Tarapacá", "SERVIU Atacama", "SERVIU Coquimbo", "SERVIU O'Higgins",
    "SERVIU Maule", "SERVIU Ñuble", "SERVIU Los Ríos", "SERVIU Los Lagos", "SERVIU Aysén",
    "SERVIU Magallanes", "SERVIU Arica y Parinacota", "CChC (Cámara Chilena de la Construcción)",
    "TECHO-Chile", "Fundación Déficit Cero", "Movimiento Ukamau", "Comités de Vivienda",
    "Comités de Allegados", "ANDHA Chile", "José Antonio Kast (Presidente)", "Gabriel Boric",
    "Carlos Montes (Ex Ministro MINVU)", "Gabriela Elgueta (Ex Subsecretaria MINVU)", "Tatiana Rojas (Ex Subsecretaria MINVU)",
    "Fidel Espinoza (Senador)", "Comisión de Vivienda (Congreso)", "Ministerio de Bienes Nacionales",
    "Claudio Orrego (Gobernador RM)", "Tomás Vodanovic (Alcalde Maipú)", "Macarena Ripamonti (Alcaldesa Viña del Mar)",
    "Camila Nieto (Alcaldesa Valparaíso)", "Mario Desbordes (Alcalde Santiago)", "Evelyn Matthei",
    "Daniel Andrade (Caso Convenios)", "Carlos Contreras (Ex Seremi)", "Democracia Viva", "ProCultura",
    "Urbanismo Social", "Contraloría General", "Fiscalía Nacional", "Consejo de Defensa del Estado (CDE)", "SENAPRED"
}

PAISES_EXTRANJEROS_RECHAZO = [
    "españa", "espana", "méxico", "mexico", "colombia", "argentina", "perú", "peru",
    "bolivia", "venezuela", "brasil", "ee.uu.", "estados unidos", "madrid", "barcelona",
    "buenos aires", "bogotá", "bogota", "lima", "caracas", "quito", "guayaquil", "montevideo",
    "francia", "alemania", "italia", "ucrania", "rusia", "china"
]

SECCIONES_RECHAZO = [
    "/internacional/", "/mundo/", "/global/", "/exterior/",
    "/deportes/", "/futbol/", "/espectaculos/", "/entretenimiento/", "/tendencias/"
]

MAPEO_REGIONES_COMPLETO = {
    "Arica y Parinacota": ["arica", "parinacota", "putre", "general lagos", "camarones", "valle de azapa", "serviu arica", "seremi arica"],
    "Tarapacá": ["iquique", "alto hospicio", "tarapacá", "tarapaca", "pozo almonte", "pica", "huara", "camiña", "colchane", "alto molle", "el boro", "la pampa", "serviu tarapacá", "serviu tarapaca", "seremi tarapacá"],
    "Antofagasta": ["antofagasta", "calama", "tocopilla", "mejillones", "taltal", "san pedro de atacama", "baquedano", "sierra gorda", "los arenales", "la chimba", "maria elena", "maría elena", "serviu antofagasta", "seremi antofagasta"],
    "Atacama": ["copiapó", "copiapo", "vallenar", "caldera", "chañaral", "chanaral", "atacama", "huasco", "tierra amarilla", "diego de almagro", "alto andacollo", "freirina", "alto del carmen", "serviu atacama", "seremi atacama"],
    "Coquimbo": ["la serena", "coquimbo", "ovalle", "illapel", "salamanca", "limarí", "limari", "choapa", "elqui", "vicuña", "vicuna", "combarbalá", "combarbala", "monte patria", "los vilos", "andacollo", "paihuano", "canela", "punitaqui", "serviu coquimbo", "seremi coquimbo"],
    "Valparaíso": ["valparaíso", "valparaiso", "viña del mar", "vina del mar", "concon", "concón", "quilpué", "quilpue", "villa alemana", "san antonio", "quillota", "los andes", "san felipe", "kandinsky", "euromarina", "el olivar", "campamento manuel bustos", "reñaca", "renaca", "limache", "la calera", "la ligua", "quintero", "puchuncaví", "puchuncavi", "cartagena", "el quisco", "el tabo", "algarrobo", "santo domingo", "casablanca", "llay llay", "llayllay", "rinconada", "calle larga", "san esteban", "putaendo", "santa maría", "santa maria", "catemu", "panquehue", "nogales", "hijuelas", "olmué", "olmue", "cabildo", "petorca", "zapallar", "papudo", "juan fernández", "isla de pascua", "rapa nui", "serviu valparaíso", "serviu valparaiso", "seremi valparaíso"],
    "Metropolitana": ["santiago", "maipú", "maipu", "puente alto", "la florida", "san bernardo", "cerrillos", "estación central", "estacion central", "pudahuel", "quilicura", "colina", "lampa", "nuevo amanecer", "toma dignidad", "parquemet", "providencia", "las condes", "lo espejo", "la pintana", "recoleta", "independencia", "ñuñoa", "nunoa", "peñalolén", "penalolen", "macul", "san joaquín", "san joaquin", "la granja", "san ramón", "san ramon", "la cisterna", "el bosque", "pedro aguirre cerda", "lo prado", "cerro navia", "quinta normal", "renca", "conchalí", "conchali", "huechuraba", "vitacura", "lo barnechea", "san josé de maipo", "san jose de maipo", "pirque", "buin", "paine", "calera de tango", "talagante", "peñaflor", "penaflor", "isla de maipo", "el monte", "padre hurtado", "melipilla", "curacaví", "curacavi", "maría pinto", "maria pinto", "san pedro", "alhué", "alhue", "tiltil", "til til", "serviu metropolitano", "seremi metropolitana"],
    "O'Higgins": ["rancagua", "machalí", "machali", "san fernando", "rengo", "pichilemu", "o'higgins", "ohiggins", "cachapoal", "colchagua", "cardenal caro", "graneros", "mostazal", "santa cruz", "chimbarongo", "san vicente", "peumo", "las cabras", "pichidegua", "requínoa", "requinoa", "olivar", "doñihue", "donihue", "coinco", "coltauco", "malloa", "quinta de tilcoco", "chépica", "chepica", "lolol", "nancagua", "palmilla", "peralillo", "placilla", "pumanque", "la estrella", "litueche", "marchigüe", "marchigue", "navidad", "paredones", "serviu o'higgins", "seremi o'higgins"],
    "Maule": ["talca", "curicó", "curico", "linares", "cauquenes", "constitución", "constitucion", "maule", "parral", "san javier", "molina", "san clemente", "longaví", "longavi", "teno", "rauco", "romeral", "sagrada familia", "hualañé", "hualane", "licantén", "licanten", "vichuquén", "vichuquen", "curepto", "pelarco", "pencahue", "río claro", "rio claro", "san rafael", "colbún", "colbun", "villa alegre", "yerbas buenas", "chanco", "pelluhue", "serviu maule", "seremi maule"],
    "Ñuble": ["chillán", "chillan", "chillán viejo", "chillan viejo", "san carlos", "ñuble", "nuble", "diguillín", "diguillin", "itata", "punilla", "coelemu", "quirihue", "bulnes", "yungay", "el carmen", "pemuco", "pinto", "quillón", "quillon", "san ignacio", "cobquecura", "ninhue", "portezuelo", "ránquil", "ranquil", "treguaco", "coihueco", "ñiquén", "niquen", "san fabián", "san fabian", "san nicolás", "san nicolas", "serviu ñuble", "seremi ñuble"],
    "Biobío": ["concepción", "concepcion", "talcahuano", "coronel", "lota", "san pedro de la paz", "chiguayante", "los ángeles", "los angeles", "biobío", "biobio", "hualpén", "hualpen", "penco", "tomé", "tome", "lebu", "arauco", "cañete", "canete", "curanilahue", "los alamos", "los álamos", "tirúa", "tirua", "contulmo", "mulchén", "mulchen", "nacimiento", "negrete", "quilaco", "quilleco", "san rosendo", "santa bárbara", "santa barbara", "tucapel", "yumbel", "alto biobío", "alto biobio", "cabrero", "laja", "hualqui", "florida", "santa juana", "serviu biobío", "serviu biobio", "seremi biobío"],
    "La Araucanía": ["temuco", "padre las casas", "villarrica", "pucón", "pucon", "angol", "araucanía", "araucania", "cautín", "cautin", "malleco", "victoria", "lautaro", "nueva imperial", "carahue", "cunco", "curarrehue", "freire", "galvarino", "gorbea", "lanco", "lonquimay", "los sauces", "lumaco", "melipeuco", "perquenco", "pitrufquén", "pitrufquen", "puren", "purén", "renaico", "saavedra", "teodoro schmidt", "toltén", "tolten", "traiguén", "traiguen", "vilcún", "vilcun", "cholchol", "serviu araucanía", "serviu araucania", "seremi araucanía"],
    "Los Ríos": ["valdivia", "la unión", "la union", "panguipulli", "los ríos", "los rios", "ranco", "río bueno", "rio bueno", "paillaco", "mariquina", "san josé de la mariquina", "lanco", "futrono", "lago ranco", "corral", "máfil", "mafil", "serviu los ríos", "serviu los rios", "seremi los ríos"],
    "Los Lagos": ["puerto montt", "puerto varas", "osorno", "castro", "ancud", "chiloé", "chiloe", "los lagos", "llanquihue", "palena", "frutillar", "calbuco", "quellón", "quellon", "fresia", "los muermos", "maullín", "maullin", "cochamó", "cochamo", "purranque", "puyehue", "río negro", "rio negro", "san juan de la costa", "san pablo", "chaitén", "chaiten", "futaleufú", "futaleufu", "hualaihué", "hualaihue", "chonchi", "curaco de vélez", "dalcahue", "puqueldón", "queilén", "quemchi", "quinchao", "serviu los lagos", "seremi los lagos"],
    "Aysén": ["coyhaique", "puerto aysén", "puerto aysen", "aysén", "aysen", "cochrane", "chile chico", "puerto cisnes", "río ibáñez", "rio ibanez", "tortel", "o'higgins", "villa o'higgins", "guaitecas", "melinka", "lago verde", "serviu aysén", "serviu aysen", "seremi aysén"],
    "Magallanes": ["punta arenas", "puerto natales", "magallanes", "tierra del fuego", "porvenir", "cabo de hornos", "antártica", "antartica", "puerto williams", "torres del paine", "primavera", "timaukel", "san gregorio", "río verde", "rio verde", "laguna blanca", "serviu magallanes", "seremi magallanes"]
}

def detectar_region_por_contenido_app(texto_eval, region_existente=""):
    t_low = (texto_eval or "").lower()
    puntajes = {reg: 0 for reg in MAPEO_REGIONES_COMPLETO}

    for reg, terminos in MAPEO_REGIONES_COMPLETO.items():
        for term in terminos:
            pat = r'\b' + re.escape(term) + r'\b'
            c = len(re.findall(pat, t_low))
            if c > 0:
                puntajes[reg] += c

    mejor_reg = max(puntajes, key=puntajes.get)
    if puntajes[mejor_reg] > 0:
        return mejor_reg

    if region_existente and region_existente in MAPEO_REGIONES_COMPLETO:
        return region_existente

    return "Nacional"

def es_noticia_estricta_minvu(titulo, bajada, cuerpo, url=""):
    t_full = f"{titulo or ''} {bajada or ''} {(cuerpo or '')[:1200]}".lower()
    u_low = (url or "").lower()

    # 1. Descarte por dominio argentino o sección foránea
    if any(dom in u_low for dom in DOMINIOS_ARGENTINOS) or any(sec in u_low for sec in SECCIONES_RECHAZO):
        return False

    # 2. Descarte por indicadores explícitos de Argentina
    for pat_arg in MARCADORES_EXCLUSION_ARGENTINA:
        if re.search(pat_arg, t_full):
            if not any(k in t_full for k in ["minvu", "serviu", "poduje", "gobierno de chile"]):
                return False

    # 3. Desambiguación de topónimos compartidos (Río Negro, Santa Cruz, etc.)
    for topo, contexto_chile in TOPONIMOS_COMPARTIDOS.items():
        if re.search(r'\b' + re.escape(topo) + r'\b', t_full):
            if not any(re.search(pat, t_full) for pat in contexto_chile):
                return False

    for p in PAISES_EXTRANJEROS_RECHAZO:
        if re.search(r'\b' + re.escape(p) + r'\b', t_full):
            if not any(re.search(pat, t_full) for pat in [r'\bminvu\b', r'\bserviu\b', r'\bpoduje\b', r'\bseremi\b']):
                return False

    for patron in PATRONES_VIVIENDA_CHILE:
        if re.search(patron, t_full):
            return True

    return False

# ==============================================================================
# 5. MOTOR DINÁMICO DE SENTIMIENTO EN TIEMPO REAL (CONEXIÓN EN VIVO)
# ==============================================================================
LEXICO_POS = {
    "entrega": 2.0, "entregaron": 2.0, "solución": 2.5, "soluciones": 2.5, "inauguración": 2.0,
    "inaugura": 2.0, "avance": 2.0, "avanza": 2.0, "reactivación": 2.5, "beneficio": 1.8,
    "beneficia": 1.8, "alianza": 1.8, "acuerdo": 2.0, "histórico": 1.5, "vivienda digna": 3.0,
    "integración": 2.0, "regeneración": 2.0, "mejora": 1.8, "mejoramiento": 1.8, "éxito": 2.0,
    "aprobación": 1.8, "aprueba": 1.8, "desbloqueo": 2.0, "apoyo": 1.5, "financiamiento": 1.5,
    "recuperación": 2.0, "recupera": 2.0, "habitabilidad": 2.0, "cumplimiento": 2.0, "acuerdan": 1.8,
    "logro": 2.2, "solucionar": 2.0, "protección": 1.8, "prioridad": 1.5, "destaca": 1.5
}

LEXICO_NEG = {
    "desalojo": -2.5, "desalojos": -2.5, "usurpación": -3.0, "socavón": -3.0, "socavones": -3.0,
    "quiebra": -3.0, "quiebras": -3.0, "crisis": -2.5, "fraude": -3.5, "corrupción": -3.5,
    "convenios": -2.0, "democracia viva": -3.5, "estafa": -3.5, "loteo brujo": -3.0, "loteos brujos": -3.0,
    "colapso": -3.0, "colapsa": -3.0, "incendio": -3.0, "incendios": -3.0, "inundación": -2.5,
    "aluvión": -3.0, "déficit": -2.0, "hacinamiento": -2.5, "protesta": -2.0, "funa": -2.5,
    "denuncia": -2.0, "formalizado": -3.0, "paralización": -2.5, "paralizan": -2.5, "retraso": -2.0,
    "conflicto": -2.0, "sobreprecio": -3.0, "abandono": -2.5, "riesgo": -1.8, "amenaza": -2.0,
    "irregularidades": -2.5, "molestia": -1.8, "derrumbe": -3.0, "querella": -2.2, "crítica": -1.8,
    "fallas": -2.0, "violenta": -2.5
}

DRIVERS_LEXICON = {
    "Logro y Alivio": [
        "entrega", "entregaron", "inaugura", "inauguración", "avance", "avanzan", "reactivación",
        "beneficio", "alianza", "acuerdo", "vivienda digna", "solución", "soluciones", "éxito",
        "aprobado", "aprueba", "desbloqueo", "apoyo", "financiamiento", "parquemet", "recupera"
    ],
    "Indignación y Conflicto": [
        "desalojo", "desalojos", "usurpación", "violenta", "fraude", "corrupción", "convenios",
        "democracia viva", "estafa", "loteo brujo", "loteos brujos", "funa", "protesta", "formalizado",
        "irregularidades", "querella", "abuso", "arriendo abusivo", "sobreprecio"
    ],
    "Alerta e Incertidumbre": [
        "socavón", "socavones", "socavon", "kandinsky", "euromarina", "colapso", "quiebra",
        "derrumbe", "riesgo geológico", "aluvión", "incendio", "inundación", "hacinamiento",
        "paralización", "retraso", "amenaza", "suelos salinos", "falla estructural", "tasas altas"
    ],
    "Demanda Comunitaria": [
        "postulación", "postulaciones", "comité", "comités", "allegados", "casa propia",
        "exigen", "piden", "asamblea", "vecinos", "reclamo", "llamado a postular", "subsidio ds49", "subsidio ds1"
    ]
}

NEGACIONES = {"no", "sin", "nunca", "jamas", "jamás", "falta", "tampoco", "nada"}
INTENSIFICADORES = {"muy", "gravemente", "masivo", "masiva", "total", "urgente", "critico", "crítico", "severo", "severa"}

def calcular_sentimiento_en_vivo(texto):
    tokens = re.findall(r'\b[a-záéíóúñ]+\b', (texto or "").lower())
    puntaje = 0.0
    i = 0
    while i < len(tokens):
        token = tokens[i]
        es_negado = (i > 0 and tokens[i-1] in NEGACIONES) or (i > 1 and tokens[i-2] in NEGACIONES)
        peso = 1.5 if (i > 0 and tokens[i-1] in INTENSIFICADORES) else 1.0

        if token in LEXICO_POS:
            val = LEXICO_POS[token] * peso
            puntaje += -val if es_negado else val
        elif token in LEXICO_NEG:
            val = LEXICO_NEG[token] * peso
            puntaje += -val if es_negado else val
        i += 1

    if puntaje > 5.0: score = 1.0
    elif puntaje < -5.0: score = -1.0
    else: score = round(puntaje / 5.0, 3)

    if score >= 0.15: etiqueta = "Positivo"
    elif score <= -0.15: etiqueta = "Negativo"
    else: etiqueta = "Neutro"

    return etiqueta, score

def calcular_driver_en_vivo(texto):
    t_low = (texto or "").lower()
    puntajes = {d: 0 for d in DRIVERS_LEXICON}
    for driver, palabras in DRIVERS_LEXICON.items():
        for pal in palabras:
            patron = r'\b' + re.escape(pal) + r'\b'
            puntajes[driver] += len(re.findall(patron, t_low))
    mejor = max(puntajes, key=puntajes.get)
    if puntajes[mejor] > 0:
        return mejor
    return "Institucional / Técnico"

TERMINOS_DEMANDA_CIUDADANA = {
    "Subsidios y Postulaciones (DS49/DS1/DS19)": ["subsidio", "subsidios", "ds49", "ds1", "ds19", "postulación", "postulaciones", "llamado"],
    "Precios de Arriendo y Alquiler": ["arriendo", "arriendos", "alquiler", "arrendatario", "arrendatarios", "precio de arriendo", "arriendo justo"],
    "Tomas de Terreno y Desalojos": ["toma de terreno", "tomas de terreno", "toma ilegal", "tomas ilegales", "desalojo", "desalojos", "usurpación", "megatoma"],
    "Campamentos y Asentamientos": ["campamento", "campamentos", "asentamiento", "asentamientos", "nuevo amanecer", "san antonio", "alto molle", "el boro", "manuel bustos"],
    "Ministro Iván Poduje y Gestión MINVU": ["poduje", "iván poduje", "ivan poduje", "ministro", "minvu", "serviu", "seremi"],
    "Comités de Vivienda y Allegados": ["comité de vivienda", "comités de vivienda", "comite de allegados", "allegados", "casa propia", "vivienda digna"],
    "Socavones y Riesgo Geológico": ["socavón", "socavones", "socavon", "kandinsky", "euromarina", "dunas de concón", "suelo salino"],
    "Loteos Brujos y Estafas de Terrenos": ["loteo brujo", "loteos brujos", "loteo irregular", "loteos irregulares", "estafa inmobiliaria"],
    "Créditos Hipotecarios y Tasas": ["crédito hipotecario", "créditos hipotecarios", "tasa hipotecaria", "tasas hipotecarias", "dividendo", "fogaes"]
}

def formatear_hipervinculo_limpio(medio, url, cluster=""):
    if not url or pd.isna(url):
        return ""
    url_str = str(url).strip()
    medio_str = str(medio).strip() if medio else "Fuente"
    cluster_str = str(cluster)

    if "youtube.com" in url_str or "youtu.be" in url_str:
        return f"[▶️ Ver transmisión en YouTube ↗]({url_str})"
    elif any(k in cluster_str for k in ["Televisión", "TV"]) or any(k in medio_str for k in ["24 Horas", "T13", "CHV", "Mega"]):
        return f"[📺 Ver reportaje en {medio_str} ↗]({url_str})"
    elif "reddit.com" in url_str or "Reddit" in medio_str:
        return f"[💬 Abrir debate en {medio_str} ↗]({url_str})"
    elif any(k in cluster_str for k in ["Instagram", "Nativos", "Redes"]):
        return f"[📱 Ver publicación en {medio_str} ↗]({url_str})"
    else:
        return f"[📰 Leer artículo completo en {medio_str} ↗]({url_str})"

# ==============================================================================
# 6. CARGA DE DATOS: FILTRADO ABSOLUTO Y CÁLCULO DINÁMICO
# ==============================================================================
def cargar_datos():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Auto-crear tablas si la base de datos es nueva
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
            driver_emocional TEXT,
            es_minvu INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            articulo_id TEXT NOT NULL,
            entidad TEXT NOT NULL,
            tipo TEXT NOT NULL,
            medio TEXT NOT NULL,
            fecha TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS citas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            articulo_id TEXT NOT NULL,
            cita TEXT NOT NULL,
            medio TEXT NOT NULL,
            eje_tematico TEXT,
            fecha TEXT
        )
    """)
    conn.commit()

    cursor.execute("PRAGMA table_info(articulos)")
    cols = [col[1] for col in cursor.fetchall()]
    
    col_cluster = "cluster_editorial" if "cluster_editorial" in cols else "tipo_fuente as cluster_editorial"
    col_reg = "region" if "region" in cols else "'Nacional' as region"
    col_sent = "sentimiento" if "sentimiento" in cols else "'Neutro' as sentimiento"
    col_score = "polaridad_score" if "polaridad_score" in cols else "0.0 as polaridad_score"
    col_driver = "driver_emocional" if "driver_emocional" in cols else "'Institucional / Técnico' as driver_emocional"

    df_art = pd.read_sql_query(f"""
        SELECT id, medio, titulo, bajada, cuerpo, autor, fecha_publicacion, fecha_captura, url, 
               eje_tematico, tipo_fuente, {col_cluster}, {col_reg}, {col_sent}, {col_score}, {col_driver}, es_minvu
        FROM articulos 
        WHERE es_minvu = 1
        ORDER BY fecha_captura DESC
    """, conn)
    
    df_ent = pd.read_sql_query("""
        SELECT e.entidad, e.tipo, e.medio, e.articulo_id, a.titulo, a.url, a.fecha_publicacion, a.eje_tematico, a.tipo_fuente, a.es_minvu
        FROM entidades e
        JOIN articulos a ON e.articulo_id = a.id
        WHERE a.es_minvu = 1
    """, conn)
    
    try:
        df_cit = pd.read_sql_query("""
            SELECT c.cita, c.medio, a.eje_tematico, a.tipo_fuente, c.fecha, a.titulo, a.url, a.es_minvu, a.id as articulo_id
            FROM citas c
            JOIN articulos a ON c.articulo_id = a.id
            WHERE a.es_minvu = 1
        """, conn)
    except Exception:
        df_cit = pd.DataFrame()
        
    conn.close()

    # BARRERA DEFENSIVA SECUNDARIA: Asegurar 100% pureza MINVU y Chile con Georreferenciación por Contenido
    if not df_art.empty:
        df_art["es_estricto_valido"] = df_art.apply(
            lambda r: es_noticia_estricta_minvu(r['titulo'], r['bajada'], r['cuerpo'], r['url']),
            axis=1
        )
        df_art = df_art[df_art["es_estricto_valido"] == True]

        # EL CONTENIDO MANDA: Corregir en vivo la región según el texto real de la noticia
        regiones_corregidas = []
        for _, row in df_art.iterrows():
            texto_geo = f"{row['titulo'] or ''} {row['titulo'] or ''} {row['bajada'] or ''} {(row['cuerpo'] or '')[:1000]}"
            reg_real = detectar_region_por_contenido_app(texto_geo, row.get('region', 'Nacional'))
            regiones_corregidas.append(reg_real)
        df_art["region"] = regiones_corregidas

        # GARANTÍA DE SENTIMIENTO CONECTADO EN VIVO
        sentimientos_calculados = []
        scores_calculados = []
        drivers_calculados = []
        for _, row in df_art.iterrows():
            texto_eval = f"{row['titulo'] or ''}. {row['bajada'] or ''}"
            sent_live, score_live = calcular_sentimiento_en_vivo(texto_eval)
            driver_live = calcular_driver_en_vivo(texto_eval)
            sentimientos_calculados.append(sent_live)
            scores_calculados.append(score_live)
            drivers_calculados.append(driver_live)
            
        df_art["sentimiento"] = sentimientos_calculados
        df_art["polaridad_score"] = scores_calculados
        df_art["driver_emocional"] = drivers_calculados

    # Sincronizar entidades y citas con los artículos válidos
    ids_validos = set(df_art["id"].tolist()) if not df_art.empty else set()
    df_ent = df_ent[df_ent["articulo_id"].isin(ids_validos)]
    # CERROJO ABSOLUTO DE ACTORES: Erradicación de celebridades y medios
    if not df_ent.empty:
        df_ent = df_ent[df_ent["entidad"].isin(ACTORES_PERMITIDOS_MINVU)]
    if not df_cit.empty:
        df_cit = df_cit[df_cit["articulo_id"].isin(ids_validos)]

    return df_art, df_ent, df_cit

try:
    df, df_entidades, df_citas = cargar_datos()
except Exception as e:
    st.error(f"Error al leer la base de datos: {e}. Ejecuta 'python actualizar_minvu.py' primero.")
    st.stop()

if df.empty:
    st.warning("La base de datos aún no tiene registros de vivienda clasificados. Ejecuta 'python actualizar_minvu.py' para iniciar la captura.")
    st.stop()

df_base = df.copy()
df_ent_base = df_entidades.copy()
df_cit_base = df_citas.copy()

st.markdown('<div class="minvu-title">🏛️ Monitor de Medios y Social Listening | MINVU Chile</div>', unsafe_allow_html=True)
st.markdown('<div class="minvu-subtitle">Observatorio de Prensa Nacional, Televisión, 16 Regiones y Redes Sociales | <b>Ministro: Iván Poduje · Subsecretaria: Natalia Aguilar</b></div>', unsafe_allow_html=True)

# Banner superior de aceleración noticiosa
if not df_base.empty:
    top_eje_acc = df_base["eje_tematico"].value_counts().index[0] if not df_base.empty else "Pauta General"
    top_cnt_acc = df_base["eje_tematico"].value_counts().iloc[0] if not df_base.empty else 0
    st.markdown(f"""<div style="background: linear-gradient(90deg, #0F3B66 0%, #0369A1 100%); color: #FFFFFF; padding: 0.65rem 1.15rem; border-radius: 8px; margin-bottom: 1.25rem; font-size: 0.9rem; font-weight: 500; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 2px 4px rgba(0,0,0,0.06);">
        <span>⚡ <b>Pauta en Aceleración Máxima:</b> <code>{top_eje_acc}</code> ({top_cnt_acc} impactos detectados)</span>
        <span style="font-size: 0.78rem; background: rgba(255,255,255,0.22); padding: 0.22rem 0.65rem; border-radius: 5px; font-weight: 700; letter-spacing: 0.3px;">🔄 CICLO DE ACTUALIZACIÓN: CADA 15 MINUTOS</span>
    </div>""", unsafe_allow_html=True)

st.sidebar.markdown("### 🎯 Observatorio Exclusivo MINVU")
st.sidebar.info("Muestra 100% depurada: solo publicaciones estrictamente vinculadas al MINVU, vivienda, autoridades y patologías urbanas.")

col_cl = "cluster_editorial" if "cluster_editorial" in df_base.columns else "tipo_fuente"
clusters_disp = ["Todos"] + sorted([c for c in df_base[col_cl].dropna().unique().tolist() if c])
cluster_sel = st.sidebar.selectbox("Clúster Editorial (Macro):", clusters_disp)

df_filtrado = df_base.copy()
if cluster_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado[col_cl] == cluster_sel]

medios_disp = ["Todos"] + sorted([m for m in df_filtrado["medio"].dropna().unique().tolist() if m])
medio_sel = st.sidebar.selectbox("Medio Específico (Micro):", medios_disp)
if medio_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["medio"] == medio_sel]

# SELECTOR PERMANENTE DE LAS 16 REGIONES DE CHILE
col_r = "region" if "region" in df_base.columns else "tipo_fuente"
regiones_disp = ["Todas", "Nacional"] + REGIONES_CHILE
region_sel = st.sidebar.selectbox("Región Territorial (16 Regiones de Chile):", regiones_disp)
if region_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado[col_r] == region_sel]

temas_disp = ["Todos"] + sorted([t for t in df_base["eje_tematico"].dropna().unique().tolist() if t and "General" not in t and "Excluida" not in t])
tema_sel = st.sidebar.selectbox("Eje Estratégico MINVU:", temas_disp)
if tema_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["eje_tematico"] == tema_sel]

if "sentimiento" in df_base.columns:
    sentimientos_disp = ["Todos", "Positivo", "Neutro", "Negativo"]
    sent_sel = st.sidebar.selectbox("Tono de Sentimiento:", sentimientos_disp)
    if sent_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["sentimiento"] == sent_sel]

termino_q = st.sidebar.text_input("Búsqueda específica:", placeholder="ej: Poduje, desalojo, DS49, toma, socavón...")
if termino_q:
    term = termino_q.strip().lower()
    df_filtrado = df_filtrado[
        df_filtrado["titulo"].astype(str).str.lower().str.contains(term, na=False, regex=False) |
        df_filtrado["cuerpo"].astype(str).str.lower().str.contains(term, na=False, regex=False)
    ]

st.sidebar.divider()
st.sidebar.markdown("### 📈 Resumen de Pauta")
st.sidebar.metric("Noticias de Vivienda (MINVU)", len(df_base))
menciones_poduje = len(df_ent_base[df_ent_base["entidad"].str.contains("Poduje", case=False, na=False)]["articulo_id"].unique())
st.sidebar.metric("Menciones Ministro Poduje", menciones_poduje)
st.sidebar.metric("Declaraciones Registradas", len(df_cit_base))

tab_pulso, tab_agenda, tab_territorio, tab_vocerias, tab_social, tab_minutas = st.tabs([
    "📍 Pulso & Titulares", 
    "📊 Agenda & Sentimiento", 
    "🗺️ Despliegue Territorial (16 Regiones)",
    "👥 Vocerías & Encuadres",
    "💬 Social Listening & Redes",
    "🧠 Minuta Ejecutiva de Gabinete"
])

# ------------------------------------------------------------------------------
# PESTAÑA 1: 📍 PULSO & TITULARES
# ------------------------------------------------------------------------------
with tab_pulso:
    st.subheader(f"Pauta Informativa en Vivo ({len(df_filtrado)} publicaciones)")
    st.markdown("""<div class="guia-periodistica">
<b>🧭 Guía de Uso Periodístico | Monitoreo en Vivo del Hábitat</b><br>
<b>🎯 Propósito de pauta:</b> Permite al equipo de comunicaciones vigilar el flujo noticioso en tiempo real, identificar qué medios acaban de publicar y aislar alertas rojas inmediatas (tomas, desalojos, socavones, convenios) con acceso íntegro al texto y video.<br>
<b>🔍 Cómo operar este panel:</b> Cada tarjeta presenta badges de color (Eje, Sentimiento, Región y Clúster). Las noticias con marco rojo indican contingencias de alta tensión. Haz clic en <i>'📖 Desplegar texto completo de la noticia'</i> para leer la crónica sin salir de la app, o reproduce el video si proviene de YouTube o noticieros de televisión.<br>
<b>🔄 Cruces recomendados para reporteo:</b>
<br>• <span class="tag-cruce">Cruce por Eje</span> Filtra en la barra lateral por <i>'Campamentos y Tomas'</i> para monitorear órdenes judiciales de desalojo activas.
<br>• <span class="tag-cruce">Cruce Territorial</span> Selecciona una región específica (ej: <i>Valparaíso</i> o <i>Tarapacá</i>) para compilar una minuta previa a visitas a terreno del Ministro o Subsecretaria.
<br><b>💡 Tip Periodístico:</b> Si una noticia de televisión cuenta con reproductor embebido, revisa el tono audiovisual antes de responder consultas de prensa; la videopolítica suele acentuar el dramatismo vecinal con mayor fuerza que la crónica escrita.
</div>""", unsafe_allow_html=True)
    
    if df_filtrado.empty:
        st.info("No se encontraron publicaciones con los filtros aplicados.")
    else:
        for idx, row in df_filtrado.head(35).iterrows():
            titulo = row['titulo'] if pd.notna(row['titulo']) else "Sin título"
            medio = row['medio'] if pd.notna(row['medio']) else "S/I"
            cluster_tag = row[col_cl] if pd.notna(row.get(col_cl)) else "Canal"
            region_tag = row[col_r] if pd.notna(row.get(col_r)) else "Nacional"
            tema_badge = row['eje_tematico'] if pd.notna(row['eje_tematico']) else "General"
            sent_tag = row.get('sentimiento', 'Neutro')
            
            badge_sent_class = "badge-positivo" if sent_tag == "Positivo" else ("badge-negativo" if sent_tag == "Negativo" else "badge-neutro")
            es_critico = any(k in titulo.lower() for k in ["toma", "desalojo", "socavón", "convenios", "usurpación", "incendio"])
            badge_class = "badge-critico" if es_critico else "badge-minvu"
            
            with st.expander(f"**[{medio}]** {titulo}"):
                st.markdown(f"""<div class="badge-container">
<span class="badge-item {badge_class}">{tema_badge}</span>
<span class="badge-item {badge_sent_class}">● {sent_tag}</span>
<span class="badge-item badge-region">📍 {region_tag}</span>
<span class="badge-item badge-cluster">{cluster_tag}</span>
</div>""", unsafe_allow_html=True)
                
                col1, col2 = st.columns([3.2, 1.2])
                with col1:
                    url_raw = str(row['url'])
                    if "youtube.com" in url_raw or "youtu.be" in url_raw:
                        st.video(url_raw)
                        st.markdown("<div style='margin-bottom: 0.8rem;'></div>", unsafe_allow_html=True)
                        
                    if pd.notna(row['bajada']) and str(row['bajada']).strip():
                        st.markdown(f'<div class="noticia-bajada">{row["bajada"]}</div>', unsafe_allow_html=True)
                        
                    if pd.notna(row['cuerpo']) and str(row['cuerpo']).strip():
                        cuerpo = str(row['cuerpo'])
                        resumen_cuerpo = cuerpo[:420] + "..." if len(cuerpo) > 420 else cuerpo
                        st.markdown(f'<div class="noticia-cuerpo">{resumen_cuerpo}</div>', unsafe_allow_html=True)
                
                with col2:
                    fecha = str(row['fecha_publicacion'])[:16] if pd.notna(row['fecha_publicacion']) else "S/I"
                    st.markdown(f'<div class="noticia-meta"><b>Publicado:</b><br>{fecha}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="noticia-meta"><b>Fuente:</b><br>{medio}</div>', unsafe_allow_html=True)
                    link_limpio = formatear_hipervinculo_limpio(medio, row['url'], cluster_tag)
                    if link_limpio:
                        st.markdown(link_limpio)
                
                if pd.notna(row['cuerpo']) and len(str(row['cuerpo']).strip()) > 420:
                    with st.expander("📖 Desplegar texto completo de la noticia"):
                        st.markdown(f'<div class="noticia-cuerpo" style="font-size:0.95rem; line-height:1.75;">{row["cuerpo"]}</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# PESTAÑA 2: 📊 AGENDA & SENTIMIENTO (100% CONECTADA Y REACTIVA)
# ------------------------------------------------------------------------------
with tab_agenda:
    st.subheader("Estructura de la Agenda y Balance de Sentimiento")
    st.markdown("""<div class="guia-periodistica">
<b>🧭 Guía de Uso Periodístico | Radiografía Macro y Termómetro Emocional</b><br>
<b>🎯 Propósito de pauta:</b> Conocer la composición real de la agenda pública sobre vivienda y diagnosticar el clima de opinión. Revela si la conversación del día está capturada por crisis reputacionales o si existe espacio para instalar hitos de gestión y logros.<br>
<b>🔍 Cómo interpretar los componentes:</b>
<br>1. <b>Treemap de Pauta:</b> El tamaño de cada bloque refleja el volumen de cobertura. Haz clic sobre cualquier clúster para hacer zoom y explorar qué medios específicos lideran la discusión.
<br>2. <b>Participación Porcentual (Donut):</b> Muestra la distribución real en los 7 Ejes del MINVU (100% sectorial, sin distorsión de pauta general).
<br>3. <b>Velocímetro Net Sentiment Score (NSS):</b> Métrica estándar internacional (-100 a +100). Bajo -20 es zona de alerta roja; sobre +20 es zona de favorabilidad y respaldo.
<br>4. <b>Barras por Clúster o Medio:</b> Permite contrastar de inmediato qué medios tienen una cobertura mayoritariamente crítica (rojo) frente a los que destacan avances (verde).
<br>5. <b>Matriz de Favorabilidad:</b> Los ejes ubicados bajo la línea punteada (NSS negativo) son tus flancos de riesgo; los ubicados arriba son tu capital político.<br>
<b>🔄 Cruces recomendados para reporteo:</b>
<br>• <span class=\"tag-cruce\">Auditoría de Hostilidad</span> Alterna el selector de barras a <i>'Medio Individual'</i> y observa qué medios presentan más del 50% de notas críticas hacia el ministerio.
<br>• <span class=\"tag-cruce\">Cruce Temático de Capital Político</span> Filtra por <i>'Plan Habitacional y Subsidios'</i> para evaluar la efectividad de las vocerías sobre entrega de viviendas.
<br><b>💡 Tip Periodístico:</b> Si el NSS global cae bajo los -25 puntos, el ministerio está enfrentando un ciclo reactivo; se aconseja no lanzar anuncios secundarios y concentrar la vocería en contención técnica.
</div>""", unsafe_allow_html=True)

    col_ag1, col_ag2 = st.columns([1.2, 1])
    with col_ag1:
        df_tree = df_base.groupby([col_cl, "eje_tematico", "medio"]).size().reset_index(name="Noticias")
        fig_tree = px.treemap(
            df_tree,
            path=[col_cl, "eje_tematico", "medio"],
            values="Noticias",
            title="Mapa Jerárquico de Pauta (Haz clic para hacer zoom)",
            color=col_cl,
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig_tree.update_layout(margin=dict(t=40, b=10, l=10, r=10), height=390)
        st.plotly_chart(fig_tree, use_container_width=True)

    with col_ag2:
        df_temas_clean = df_base[df_base["eje_tematico"].notna() & ~df_base["eje_tematico"].str.contains("General|Excluida", case=False, na=False)]
        conteo_temas = df_temas_clean["eje_tematico"].value_counts().reset_index()
        conteo_temas.columns = ["Eje Estratégico", "Publicaciones"]
        
        fig_temas = px.pie(
            conteo_temas,
            names="Eje Estratégico",
            values="Publicaciones",
            title="Participación Porcentual Real en los 7 Ejes MINVU",
            hole=0.45,
            template="plotly_white",
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig_temas.update_traces(textinfo='percent', hoverinfo='label+value+percent')
        fig_temas.update_layout(height=390, margin=dict(t=40, b=10, l=10, r=10), legend=dict(orientation="v", yanchor="top", y=1.0, xanchor="left", x=1.05))
        st.plotly_chart(fig_temas, use_container_width=True)

    st.markdown("<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True)
    st.divider()

    # CÁLCULO DINÁMICO REACTIVO DE SENTIMIENTO EN TIEMPO REAL
    total_eval = len(df_filtrado)
    conteo_s = df_filtrado["sentimiento"].value_counts()
    pos = conteo_s.get("Positivo", 0)
    neu = conteo_s.get("Neutro", 0)
    neg = conteo_s.get("Negativo", 0)
    pct_pos = round((pos / total_eval) * 100, 1) if total_eval > 0 else 0.0
    pct_neu = round((neu / total_eval) * 100, 1) if total_eval > 0 else 0.0
    pct_neg = round((neg / total_eval) * 100, 1) if total_eval > 0 else 0.0
    nss_score = round(pct_pos - pct_neg, 1)

    col_g1, col_g2 = st.columns([1.1, 1])
    with col_g1:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=nss_score,
            title={'text': "Net Sentiment Score (NSS) Sectorial", 'font': {'size': 18, 'color': '#0F3B66'}},
            delta={'reference': 0, 'increasing': {'color': "#10B981"}, 'decreasing': {'color': "#EF4444"}},
            gauge={
                'axis': {'range': [-100, 100], 'tickwidth': 1, 'tickcolor': "#475569"},
                'bar': {'color': "#0F3B66"},
                'steps': [
                    {'range': [-100, -20], 'color': "#FEE2E2"},
                    {'range': [-20, 20], 'color': "#F1F5F9"},
                    {'range': [20, 100], 'color': "#D1FAE5"}
                ],
                'threshold': {'line': {'color': "#D92D20", 'width': 3}, 'thickness': 0.75, 'value': nss_score}
            }
        ))
        fig_gauge.update_layout(height=320, margin=dict(t=40, b=10, l=30, r=30))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_g2:
        st.markdown("#### Balance de Opinión en el Segmento Activo:")
        col_k1, col_k2, col_k3 = st.columns(3)
        col_k1.metric("🟢 Favorable", f"{pct_pos:.1f}%", f"{pos} notas")
        col_k2.metric("⚪ Neutro", f"{pct_neu:.1f}%", f"{neu} notas")
        col_k3.metric("🔴 Crítico", f"{pct_neg:.1f}%", f"-{neg} notas")

        clima_texto = "🟢 **Clima Favorable**: Predominan anuncios de entrega de viviendas, acuerdos de subsidio y reactivación." if nss_score > 20 else (
            "🔴 **Clima Crítico / Alerta**: Fuerte presión por tomas de terreno, desalojos, socavones o Caso Convenios." if nss_score < -20 else
            "⚪ **Clima Balanceado**: Cobertura técnica o institucional regular sin polarización marcada."
        )
        st.info(clima_texto)

    # SHARE OF VOICE Y DRIVERS EMOCIONALES
    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
    col_sov1, col_sov2 = st.columns([1, 1.1])
    with col_sov1:
        st.markdown("#### 📢 Share of Voice por Familia de Medios:")
        df_sov = df_base[col_cl].value_counts().reset_index()
        df_sov.columns = ["Familia de Medios", "Volumen"]
        fig_sov = px.pie(
            df_sov,
            names="Familia de Medios",
            values="Volumen",
            hole=0.42,
            title="Participación de Cobertura por Canal (Share of Voice)",
            template="plotly_white",
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig_sov.update_traces(textinfo='percent')
        fig_sov.update_layout(height=340, margin=dict(t=30, b=10, l=10, r=10), legend=dict(orientation="h", yanchor="top", y=-0.1))
        st.plotly_chart(fig_sov, use_container_width=True)

    with col_sov2:
        st.markdown("#### 🎭 Drivers Emocionales de la Pauta Pública:")
        conteo_drivers = df_filtrado["driver_emocional"].value_counts().reset_index()
        conteo_drivers.columns = ["Driver Emocional", "Impactos"]
        
        color_map_drivers = {
            "Logro y Alivio": "#10B981",
            "Indignación y Conflicto": "#EF4444",
            "Alerta e Incertidumbre": "#F59E0B",
            "Demanda Comunitaria": "#0284C7",
            "Institucional / Técnico": "#64748B"
        }
        
        fig_drivers = px.bar(
            conteo_drivers,
            x="Impactos",
            y="Driver Emocional",
            orientation="h",
            color="Driver Emocional",
            color_discrete_map=color_map_drivers,
            title="¿Qué Emociones Conduce la Conversación Pública sobre MINVU?",
            template="plotly_white"
        )
        fig_drivers.update_layout(yaxis=dict(title="", autorange="reversed"), coloraxis_showscale=False, height=340, margin=dict(t=30, b=10, l=10, r=10), showlegend=False)
        st.plotly_chart(fig_drivers, use_container_width=True)

    # BARRAS DE DISTRIBUCIÓN DE SENTIMIENTO
    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
    st.markdown("#### Distribución de Sentimiento por Clúster o Medio")
    agrupador_sent = st.radio("Nivel de agrupación:", ["Clúster Editorial (Macro)", "Medio Individual (Micro)"], horizontal=True)
    col_agrup = col_cl if "Clúster" in agrupador_sent else "medio"

    cruce_sent = df_filtrado.groupby([col_agrup, "sentimiento"]).size().unstack(fill_value=0).reset_index()
    for col_faltante in ["Positivo", "Neutro", "Negativo"]:
        if col_faltante not in cruce_sent.columns:
            cruce_sent[col_faltante] = 0

    cruce_sent["Total"] = cruce_sent["Positivo"] + cruce_sent["Neutro"] + cruce_sent["Negativo"]
    cruce_sent = cruce_sent[cruce_sent["Total"] >= 1].sort_values(by="Total", ascending=True)

    cruce_sent["Pct_Pos"] = (cruce_sent["Positivo"] / cruce_sent["Total"]) * 100
    cruce_sent["Pct_Neu"] = (cruce_sent["Neutro"] / cruce_sent["Total"]) * 100
    cruce_sent["Pct_Neg"] = (cruce_sent["Negativo"] / cruce_sent["Total"]) * 100

    fig_bar_sent = go.Figure()
    fig_bar_sent.add_trace(go.Bar(
        y=cruce_sent[col_agrup], x=cruce_sent["Pct_Neg"], name="Crítico",
        orientation='h', marker=dict(color='#EF4444')
    ))
    fig_bar_sent.add_trace(go.Bar(
        y=cruce_sent[col_agrup], x=cruce_sent["Pct_Neu"], name="Neutro",
        orientation='h', marker=dict(color='#94A3B8')
    ))
    fig_bar_sent.add_trace(go.Bar(
        y=cruce_sent[col_agrup], x=cruce_sent["Pct_Pos"], name="Favorable",
        orientation='h', marker=dict(color='#10B981')
    ))
    fig_bar_sent.update_layout(
        barmode='stack',
        xaxis=dict(title="Porcentaje (%)", range=[0, 100]),
        yaxis=dict(title=""),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=370,
        template="plotly_white",
        margin=dict(t=30, b=20, l=10, r=10)
    )
    st.plotly_chart(fig_bar_sent, use_container_width=True)

    # MATRIZ DE FAVORABILIDAD
    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
    st.markdown("#### Matriz de Favorabilidad Temática: ¿Qué temas son crisis y cuáles son capital político?")
    resumen_ejes = []
    for eje in df_base["eje_tematico"].dropna().unique():
        if "General" in eje or "Excluida" in eje:
            continue
        df_eje = df_base[df_base["eje_tematico"] == eje]
        cnt = len(df_eje)
        if cnt > 0:
            p = len(df_eje[df_eje["sentimiento"] == "Positivo"])
            n = len(df_eje[df_eje["sentimiento"] == "Negativo"])
            nss_e = round(((p - n) / cnt) * 100, 1)
            resumen_ejes.append({"Eje": eje, "Volumen": cnt, "NSS": nss_e})

    df_res_ejes = pd.DataFrame(resumen_ejes)
    if not df_res_ejes.empty:
        fig_matriz_ejes = px.scatter(
            df_res_ejes,
            x="Volumen",
            y="NSS",
            size="Volumen",
            text="Eje",
            color="NSS",
            color_continuous_scale="RdYlGn",
            range_color=[-60, 60],
            template="plotly_white"
        )
        fig_matriz_ejes.add_hline(y=0, line_dash="dash", line_color="#64748B", annotation_text="Punto Neutro")
        fig_matriz_ejes.update_traces(textposition="top center")
        fig_matriz_ejes.update_layout(height=410, yaxis_title="Net Sentiment Score (NSS)", xaxis_title="Volumen de Notas")
        st.plotly_chart(fig_matriz_ejes, use_container_width=True)

# ------------------------------------------------------------------------------
# PESTAÑA 3: 🗺️ DESPLIEGUE TERRITORIAL (16 REGIONES DE CHILE)
# ------------------------------------------------------------------------------
with tab_territorio:
    st.subheader("Despliegue Territorial: Mapa de las 16 Regiones de Chile")
    st.markdown("""<div class="guia-periodistica">
<b>🧭 Guía de Uso Periodístico | Matriz Territorial Descentralizada (16 Regiones)</b><br>
<b>🎯 Propósito de pauta:</b> Romper el centralismo informativo de la Región Metropolitana y auditar el estado del hábitat a nivel regional. Permite detectar focos de conflicto locales antes de que escalen a la pauta de los canales nacionales.<br>
<b>🔍 Cómo operar el mapa geográfico, matriz y auditor:</b>
<br>1. <b>Mapa Geográfico Interactivo:</b> Representación física de Chile de norte a sur. Los círculos indican la ubicación de las 16 capitales regionales; su tamaño representa el volumen de noticias y su color el clima afectivo (verde = favorable, rojo = crítico).
<br>2. <b>Matriz de Calor (Heatmap):</b> Cruza permanentemente las 16 regiones oficiales con los 7 ejes estratégicos del MINVU.
<br>3. <b>Auditor Regional:</b> Menú desplegable para aislar los titulares de una región específica y revisar qué reporta la prensa local.<br>
<b>🔄 Cruces recomendados para reporteo:</b>
<br>• <span class="tag-cruce">Briefing de Gira Ministerial</span> Si el Ministro viaja a Coquimbo o Tarapacá, selecciona la región en el auditor para revisar los reclamos locales antes de su punto de prensa.
<br>• <span class="tag-cruce">Detección de Vacíos Comunicacionales</span> Si una región con alta emergencia habitacional aparece con pocas notas, la SEREMI regional no está colocando pauta y requiere instrucción de visibilidad.
<br><b>💡 Tip Periodístico:</b> La prensa regional suele publicar las primeras denuncias de loteos brujos o socavones días antes de que lleguen a los noticieros centrales de Santiago.
</div>""", unsafe_allow_html=True)

    # 1. MAPA GEOGRÁFICO INTERACTIVO DE CHILE (16 REGIONES)
    st.markdown("#### 🇨🇱 Mapa Geográfico Interactivo de Chile (16 Regiones):")
    data_mapa = []
    for reg, coords in COORDENADAS_REGIONES.items():
        df_sub_reg = df_base[df_base[col_r] == reg]
        cnt_reg = len(df_sub_reg)
        if cnt_reg > 0:
            p_reg = len(df_sub_reg[df_sub_reg["sentimiento"] == "Positivo"])
            n_reg = len(df_sub_reg[df_sub_reg["sentimiento"] == "Negativo"])
            nss_reg = round(((p_reg - n_reg) / cnt_reg) * 100, 1)
        else:
            nss_reg = 0.0

        data_mapa.append({
            "Región": reg,
            "Capital": coords["capital"],
            "lat": coords["lat"],
            "lon": coords["lon"],
            "Noticias": max(cnt_reg, 1),
            "Impactos Reales": cnt_reg,
            "NSS": nss_reg
        })

    df_geo_map = pd.DataFrame(data_mapa)
    fig_mapa = px.scatter_geo(
        df_geo_map,
        lat="lat",
        lon="lon",
        size="Noticias",
        color="NSS",
        hover_name="Región",
        hover_data={"Capital": True, "Impactos Reales": True, "NSS": True, "lat": False, "lon": False, "Noticias": False},
        color_continuous_scale="RdYlGn",
        range_color=[-60, 60],
        title="Distribución Geográfica Nacional: Volumen y Clima Afectivo en las 16 Regiones"
    )
    fig_mapa.update_geos(
        scope="south america",
        showcountries=True,
        countrycolor="#CBD5E1",
        showland=True,
        landcolor="#F8FAFC",
        fitbounds="locations",
        visible=True
    )
    fig_mapa.update_layout(height=480, margin=dict(t=40, b=10, l=10, r=10))
    st.plotly_chart(fig_mapa, use_container_width=True)

    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
    st.divider()

    # 2. HEATMAP TERRITORIAL REINDEXADO CON LAS 16 REGIONES PERMANENTES
    st.markdown("#### 🗺️ Matriz de Concentración Territorial (16 Regiones x 7 Ejes):")
    df_reg_clean = df_base[df_base[col_r].isin(REGIONES_CHILE)]
    if not df_reg_clean.empty:
        df_heat = df_reg_clean.pivot_table(index=col_r, columns="eje_tematico", aggfunc="size", fill_value=0)
        df_heat = df_heat.reindex(index=REGIONES_CHILE, fill_value=0)
        
        fig_heat = px.imshow(
            df_heat,
            labels=dict(x="Eje Estratégico MINVU", y="Región de Chile", color="Notas"),
            x=df_heat.columns,
            y=df_heat.index,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="Teal",
            title="Concentración Territorial de Noticias (Región vs. Eje)"
        )
        fig_heat.update_layout(height=520, xaxis_tickangle=-25, margin=dict(t=40, b=20, l=10, r=10))
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.info("Sin registros regionales específicos.")

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    st.divider()

    col_t1, col_t2 = st.columns([1, 1.2])
    with col_t1:
        st.markdown("#### Volumen Acumulado por Región:")
        reg_conteo = df_base[col_r].value_counts().reset_index()
        reg_conteo.columns = ["Región / Macro", "Noticias"]
        fig_reg_bar = px.bar(
            reg_conteo,
            x="Noticias",
            y="Región / Macro",
            orientation="h",
            color="Noticias",
            color_continuous_scale="Blues",
            template="plotly_white"
        )
        fig_reg_bar.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False, height=400)
        st.plotly_chart(fig_reg_bar, use_container_width=True)

    with col_t2:
        st.markdown("#### 🔍 Auditoría Directa por Región:")
        reg_elegida = st.selectbox("Selecciona una de las 16 regiones para auditar titulares locales:", REGIONES_CHILE)
        if reg_elegida:
            df_reg_sel = df_base[df_base[col_r] == reg_elegida]
            st.caption(f"Mostrando **{len(df_reg_sel)} noticias** registradas en **{reg_elegida}**:")
            if df_reg_sel.empty:
                st.info(f"Actualmente no hay noticias críticas recientes en {reg_elegida}.")
            else:
                for _, r_not in df_reg_sel.head(7).iterrows():
                    link_reg = formatear_hipervinculo_limpio(r_not['medio'], r_not['url'], str(r_not.get(col_cl, '')))
                    st.markdown(f"- **[{r_not['medio']}]** [{r_not['titulo']}]({r_not['url']}) · {link_reg}")

# ------------------------------------------------------------------------------
# PESTAÑA 4: 👥 VOCERÍAS & ENCUADRES
# ------------------------------------------------------------------------------
with tab_vocerias:
    st.subheader("Mapa de Actores, Encuadres en Espejo y Declaraciones Textuales")
    st.markdown("""<div class="guia-periodistica">
<b>🧭 Guía de Uso Periodístico | Vocerías, Encuadres en Espejo y Citas Textuales</b><br>
<b>🎯 Propósito de pauta:</b> Auditar la narrativa política y el encuadre de las fuentes. Revela quiénes son las voces predominantes en la discusión, cómo titula cada línea editorial sobre un mismo hecho y recopila declaraciones textuales para insumo de prensa.<br>
<b>🔍 Cómo aprovechar cada sección:</b>
<br>1. <b>Radar de Actores (Burbujas):</b> Las figuras situadas en el cuadrante superior derecho (como el Ministro Iván Poduje) tienen alta cobertura y transversalidad temática. Los ubicados abajo a la derecha son actores hiperfocalizados en un solo tema.
<br>2. <b>Auditor de Huella Individual:</b> Selecciona un vocero en el menú para ver su gráfico de torta temático.
<br>3. <b>Encuadres en Espejo (Framing):</b> Escribe cualquier concepto (ej: <i>'Poduje'</i>, <i>'desalojo'</i>, <i>'subsidio'</i>) para contrastar cómo titulan la Gran Prensa, Televisión, Prensa Regional y Redes.
<br>4. <b>Banco de Citas (Verbatims):</b> Repositorio de frases entrecomilladas de ministros, parlamentarios y alcaldes.<br>
<b>🔄 Cruces recomendados para reporteo:</b>
<br>• <span class="tag-cruce">Contraste de Framing</span> Busca <i>'toma de terreno'</i> y compara cómo la prensa económica titula desde la propiedad privada mientras las redes titulan desde la falta de vivienda digna.
<br>• <span class="tag-cruce">Preparación de Réplicas</span> Busca por apellido en el banco de citas para contrastar declaraciones contradictorias antes de emitir un comunicado de respuesta.
</div>""", unsafe_allow_html=True)

    if not df_ent_base.empty:
        df_act_radar = df_ent_base.groupby("entidad").agg(
            noticias_unicas=('articulo_id', 'nunique'),
            diversidad_ejes=('eje_tematico', 'nunique')
        ).reset_index().sort_values(by="noticias_unicas", ascending=True).tail(12)

        col_rad1, col_rad2 = st.columns([1.3, 1])
        with col_rad1:
            fig_bar_act = px.bar(
                df_act_radar,
                x="noticias_unicas",
                y="entidad",
                orientation="h",
                color="noticias_unicas",
                color_continuous_scale="Blues",
                title="Ranking de Vocerías e Instituciones con Mayor Presencia en Pauta",
                labels={"noticias_unicas": "Presencia en Noticias Únicas", "entidad": ""},
                template="plotly_white"
            )
            fig_bar_act.update_layout(height=420, coloraxis_showscale=False, margin=dict(t=40, b=20, l=10, r=10))
            st.plotly_chart(fig_bar_act, use_container_width=True)

        with col_rad2:
            st.markdown("#### 👤 Huella Temática por Actor:")
            actor_sel = st.selectbox("Seleccionar vocería o institución:", df_act_radar["entidad"].tolist())
            if actor_sel:
                datos_act = df_ent_base[df_ent_base["entidad"] == actor_sel]
                temas_act = datos_act["eje_tematico"].value_counts().reset_index()
                temas_act.columns = ["Eje Temático", "Menciones"]
                fig_act_pie = px.pie(
                    temas_act,
                    names="Eje Temático",
                    values="Menciones",
                    title=f"¿A qué agenda del MINVU está asociado '{actor_sel}'?",
                    hole=0.4,
                    template="plotly_white",
                    color_discrete_sequence=px.colors.qualitative.Prism
                )
                fig_act_pie.update_layout(height=350, margin=dict(t=40, b=0, l=0, r=0))
                st.plotly_chart(fig_act_pie, use_container_width=True)

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    st.divider()

    st.markdown("#### ⚖️ Encuadres en Espejo: Contraste Inter-Clúster")
    concepto_f = st.text_input("Buscar hito sectorial para contrastar encuadres:", value="Iván Poduje")
    if concepto_f:
        term_f = concepto_f.strip().lower()
        sub_df = df_base[
            df_base["titulo"].astype(str).str.lower().str.contains(term_f, na=False, regex=False) |
            df_base["cuerpo"].astype(str).str.lower().str.contains(term_f, na=False, regex=False)
        ]
        if not sub_df.empty:
            st.caption(f"Se encontraron **{len(sub_df)} publicaciones** sobre '{concepto_f}'.")
            for cl in sub_df[col_cl].unique().tolist():
                sub_cl = sub_df[sub_df[col_cl] == cl]
                st.markdown(f"##### {cl} ({len(sub_cl)} notas)")
                for _, t_row in sub_cl.head(4).iterrows():
                    link_framing = formatear_hipervinculo_limpio(t_row['medio'], t_row['url'], cl)
                    st.markdown(f"- **[{t_row['medio']}]** {t_row['titulo']} · {link_framing} *(📍 {t_row.get(col_r, 'Nacional')})*")
        else:
            st.info(f"No hay registros específicos sobre '{concepto_f}'.")

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    st.divider()

    st.markdown("#### 🗣️ Banco de Declaraciones Textuales (Verbatims)")
    if not df_cit_base.empty:
        filtro_c = st.text_input("Filtrar declaraciones por palabra clave (ej: Poduje, subsidio, desalojo, convenio):")
        citas_ver = df_cit_base.copy()
        if filtro_c:
            citas_ver = citas_ver[citas_ver["cita"].str.lower().str.contains(filtro_c.lower(), na=False, regex=False)]
        st.caption(f"Mostrando **{len(citas_ver)} declaraciones** encontradas:")
        for _, c_row in citas_ver.head(10).iterrows():
            st.markdown(f'<div class="verbatim-box-minvu">«{c_row["cita"]}»</div>', unsafe_allow_html=True)
            link_c = formatear_hipervinculo_limpio(c_row['medio'], c_row['url'], str(c_row.get('tipo_fuente', '')))
            st.caption(f"**Medio:** `{c_row['medio']}` | **Eje:** `{c_row['eje_tematico']}` | **Noticia:** [{c_row['titulo']}]({c_row['url']}) · {link_c}")

# ------------------------------------------------------------------------------
# PESTAÑA 5: 💬 SOCIAL LISTENING & REDES (100% MINVU Y DEMANDAS CIUDADANAS)
# ------------------------------------------------------------------------------
with tab_social:
    st.subheader("Social Listening: Pulso Ciudadano, Redes e Instagram")
    st.markdown("""<div class="guia-periodistica">
<b>🧭 Guía de Uso Periodístico | Social Listening y Detección Temprana de Conflictos</b><br>
<b>🎯 Propósito de pauta:</b> Escuchar el pulso ciudadano directo en redes sociales (X/Twitter, Reddit, Instagram, TikTok) sin el filtro de las líneas editoriales tradicionales. Revela el desacople (Agenda-Gap) entre lo que la prensa cubre y lo que la gente realmente demanda en los barrios.<br>
<b>🔍 Cómo leer las métricas ciudadanas:</b>
<br>1. <b>Demandas Ciudadanas en Redes:</b> Gráfico horizontal depurado que mide menciones de problemáticas concretas (arriendos abusivos, demoras en el DS49, deudores habitacionales, tomas, loteos brujos).
<br>2. <b>Brecha de Agenda (Agenda-Gap):</b> Compara la barra roja (Redes Sociales) con la barra azul (Prensa Tradicional). Si la barra roja supera ampliamente a la azul en un tema, hay una tensión soterrada lista para estallar en la pauta masiva.
<br>3. <b>Hilos de Debate y Virales:</b> Casos reales y testimonios ciudadanos filtrados estrictamente en el perímetro de vivienda.<br>
<b>🔄 Cruces recomendados para reporteo:</b>
<br>• <span class="tag-cruce">Alerta Temprana de Agenda-Gap</span> Revisa si <i>'Precios de Arriendo'</i> o <i>'Comités de Allegados'</i> lideran en redes pero casi no aparecen en la prensa escrita; esa brecha representa una oportunidad para anticiparse con vocería pedagógica.
<br>• <span class="tag-cruce">Monitoreo de Movilizaciones</span> Filtra las publicaciones de movimientos de pobladores para detectar convocatorias a marchas con 24-48 horas de anticipación.
<br><b>💡 Tip Periodístico:</b> Utiliza los reclamos de redes sociales como termómetro de campo para actualizar las minutas de preguntas difíciles (Q&A) de la vocería ministerial.
</div>""", unsafe_allow_html=True)
    
    df_social = df_base[df_base[col_cl].str.contains("Redes|Social|Instagram|Reddit|Nativos", case=False, na=False)]
    
    if df_social.empty:
        st.info("Aún no hay publicaciones de redes sociales capturadas en esta pasada.")
    else:
        col_s1, col_s2 = st.columns([1.1, 1.3])
        with col_s1:
            st.metric("Publicaciones en Redes y Medios Nativos", len(df_social))
            
            titulos_social = df_social["titulo"].dropna().tolist()
            t_low = " ".join(titulos_social).lower()
            conteo_demandas = {}
            for cat, palabras in TERMINOS_DEMANDA_CIUDADANA.items():
                tot_c = sum(len(re.findall(r'\\b' + re.escape(p) + r'\\b', t_low)) for p in palabras)
                if tot_c > 0:
                    conteo_demandas[cat] = tot_c
            
            df_dem = pd.DataFrame(list(conteo_demandas.items()), columns=["Demanda Ciudadana", "Menciones"])
            df_dem = df_dem.sort_values(by="Menciones", ascending=True)
            
            if not df_dem.empty:
                fig_demandas = px.bar(
                    df_dem,
                    x="Menciones",
                    y="Demanda Ciudadana",
                    orientation="h",
                    title="Principales Demandas Ciudadanas en Redes",
                    color="Menciones",
                    color_continuous_scale="Oranges",
                    template="plotly_white"
                )
                fig_demandas.update_layout(yaxis=dict(title=""), coloraxis_showscale=False, height=390, margin=dict(t=40, b=20, l=10, r=10))
                st.plotly_chart(fig_demandas, use_container_width=True)
            else:
                st.info("Detectando conceptos ciudadanos...")
            
        with col_s2:
            st.markdown("#### Brecha de Agenda: Prensa Tradicional vs. Redes Sociales")
            df_comp = df_base.copy()
            df_comp["Canal Macro"] = df_comp[col_cl].apply(
                lambda x: "💬 Redes Sociales" if any(k in str(x) for k in ["Redes", "Instagram", "Reddit", "Nativos"]) else "📰 Prensa Tradicional y Radios"
            )
            df_comp_clean = df_comp[df_comp["eje_tematico"].notna() & ~df_comp["eje_tematico"].str.contains("General|Excluida", case=False, na=False)]
            comp_ejes = df_comp_clean.groupby(["Canal Macro", "eje_tematico"]).size().reset_index(name="Notas")
            
            fig_gap = px.bar(
                comp_ejes,
                y="eje_tematico",
                x="Notas",
                color="Canal Macro",
                orientation="h",
                barmode="group",
                title="¿De qué habla la Prensa vs. De qué habla la Gente en Redes?",
                color_discrete_map={"💬 Redes Sociales": "#E11D48", "📰 Prensa Tradicional y Radios": "#0F3B66"},
                template="plotly_white"
            )
            fig_gap.update_layout(
                yaxis=dict(title="", autorange="reversed"),
                xaxis=dict(title="Cantidad de Publicaciones"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=390,
                margin=dict(t=40, b=20, l=10, r=10)
            )
            st.plotly_chart(fig_gap, use_container_width=True)
            
        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
        st.markdown("#### Hilos de Conversación Ciudadana y Reportes de Redes:")
        for _, s_row in df_social.head(15).iterrows():
            with st.expander(f"**[{s_row['medio']}]** {s_row['titulo']}"):
                st.caption(f"**Canal:** `{s_row.get(col_cl, s_row['tipo_fuente'])}` | **Eje:** `{s_row['eje_tematico']}` | 📍 `{s_row.get(col_r, 'Nacional')}`")
                if "youtube.com" in str(s_row['url']) or "youtu.be" in str(s_row['url']):
                    st.video(str(s_row['url']))
                if s_row['bajada']:
                    st.markdown(f'<div class="noticia-cuerpo">{s_row["bajada"]}</div>', unsafe_allow_html=True)
                link_soc = formatear_hipervinculo_limpio(s_row['medio'], s_row['url'], str(s_row.get(col_cl, '')))
                st.markdown(link_soc)

# ------------------------------------------------------------------------------
# PESTAÑA 6: 🧠 MINUTA EJECUTIVA (INFORME AUTOMATIZADO 1-CLICK DE GABINETE)
# ------------------------------------------------------------------------------
with tab_minutas:
    st.subheader("Minuta Ejecutiva de Comunicaciones para Gabinete")
    st.markdown("""<div class="guia-periodistica">
<b>🧭 Guía de Uso Periodístico | Informe Ejecutivo Automatizado para Gabinete</b><br>
<b>🎯 Propósito de pauta:</b> Elaborar al instante el informe de inteligencia de medios definitivo para la reunión matutina de gabinete del Ministro Iván Poduje y su equipo directivo, listo para copiar a WhatsApp, correo institucional o imprimir.<br>
<b>🔍 Cómo operar el informe:</b>
Presiona el botón para compilar al instante un reporte completo estructurado en 6 dimensiones: dimensionamiento de pauta por canal, clima de opinión NSS, desglose por ejes del MINVU, alertas críticas de desalojos y socavones, cuñas textuales y 3 recomendaciones tácticas de acción. Descárgalo en formato <code>.txt</code>.<br>
<b>💡 Tip Periodístico:</b> Genera la minuta automática a las 07:30 AM para que el Ministro y la Subsecretaria conozcan el tono de la pauta y los focos rojos antes de entrar a las entrevistas radiales matinales.
</div>""", unsafe_allow_html=True)
    
    st.markdown("#### 📋 Compilar Minuta Ejecutiva del Día (1-Click)")
    if st.button("Generar Minuta Ejecutiva de Gabinete"):
        tot = len(df_base)
        conteo_s = df_base["sentimiento"].value_counts()
        pos = conteo_s.get("Positivo", 0)
        neu = conteo_s.get("Neutro", 0)
        neg = conteo_s.get("Negativo", 0)
        pct_p = round((pos / tot) * 100, 1) if tot > 0 else 0
        pct_n = round((neu / tot) * 100, 1) if tot > 0 else 0
        pct_g = round((neg / tot) * 100, 1) if tot > 0 else 0
        nss = round(pct_p - pct_g, 1)

        c_counts = df_base[col_cl].value_counts()
        eje_counts = df_base[df_base["eje_tematico"].notna() & ~df_base["eje_tematico"].str.contains("General|Excluida", case=False, na=False)]["eje_tematico"].value_counts()
        
        nss_por_eje = {}
        for eje in eje_counts.index:
            sub = df_base[df_base["eje_tematico"] == eje]
            p = len(sub[sub["sentimiento"] == "Positivo"])
            n = len(sub[sub["sentimiento"] == "Negativo"])
            nss_por_eje[eje] = round(((p - n) / len(sub)) * 100, 1) if len(sub) > 0 else 0

        eje_mejor = max(nss_por_eje, key=nss_por_eje.get) if nss_por_eje else "N/A"
        eje_peor = min(nss_por_eje, key=nss_por_eje.get) if nss_por_eje else "N/A"

        diag_clima = "🟢 Favorable (predominan entregas de viviendas y avances)" if nss > 20 else (
            "🔴 Crítico (alta tensión por desalojos, tomas o socavones)" if nss < -20 else
            "⚪ Balanceado / Institucional (cobertura técnica regular)"
        )

        top_reg = ", ".join([f"{reg} ({cnt})" for reg, cnt in df_base[col_r].value_counts().head(3).items()])

        minuta_texto = f"""================================================================================
🏛️ MINUTA EJECUTIVA DE INTELIGENCIA DE MEDIOS | GABINETE MINVU
FECHA DE EMISIÓN: {datetime.now().strftime('%d/%m/%Y %H:%M')}
AUTORIDADES: Ministro Iván Poduje · Subsecretaria Natalia Aguilar
UNIVERSO: 100% Pauta Sectorial MINVU ({tot} publicaciones analizadas)
================================================================================

1. DIMENSIONAMIENTO Y DIRECCIONALIDAD DE LA PAUTA:
   * Total de impactos en vivienda y ciudad: {tot} notas.
   * Hacia dónde va la cobertura por Familia de Medios:
"""
        for cl, cnt in c_counts.items():
            pct_cl = round((cnt / tot) * 100, 1)
            minuta_texto += f"     - {cl}: {cnt} notas ({pct_cl}%)\\n"

        minuta_texto += f"""   * Focos Territoriales con Mayor Cobertura: {top_reg}.

2. TERMÓMETRO DE SENTIMIENTO Y CLIMA DE OPINIÓN:
   * Net Sentiment Score (NSS) Global: {nss:+0.1f} puntos (Escala: -100 a +100).
   * Diagnóstico de Gabinete: {diag_clima}.
   * Balance Proporcional:
     - 🟢 Favorable / Logro: {pct_p}% ({pos} notas)
     - ⚪ Neutro / Institucional: {pct_n}% ({neu} notas)
     - 🔴 Crítico / Tensión: {pct_g}% ({neg} notas)
   * Eje con Mayor Respaldo: '{eje_mejor}' ({nss_por_eje.get(eje_mejor, 0):+0.1f} NSS).
   * Eje con Mayor Presión Crítica: '{eje_peor}' ({nss_por_eje.get(eje_peor, 0):+0.1f} NSS).

3. CLASIFICACIÓN POR EJES ESTRATÉGICOS MINVU:
"""
        for eje, cnt in eje_counts.items():
            pct_e = round((cnt / tot) * 100, 1)
            minuta_texto += f"   * {eje}: {cnt} notas ({pct_e}%) | Clima: {nss_por_eje.get(eje, 0):+0.1f} NSS\\n"

        minuta_texto += f"""
4. ALERTAS CRÍTICAS Y FOCOS DE CONFLICTO PRIORITARIOS:
"""
        criticas = df_base[df_base["sentimiento"] == "Negativo"].head(4)
        if not criticas.empty:
            for _, r in criticas.iterrows():
                minuta_texto += f"   - [{r['medio']} | 📍 {r[col_r]}] {r['titulo']}\\n"
        else:
            minuta_texto += "   - Sin focos de alta criticidad en la pasada activa.\\n"

        minuta_texto += f"""
5. MATRIZ DE VOCERÍAS Y DECLARACIONES TEXTUALES (VERBATIMS):
"""
        if not df_cit_base.empty:
            for _, c in df_cit_base.head(3).iterrows():
                minuta_texto += f"   - [{c['medio']}]: «{c['cita']}»\\n"
        else:
            minuta_texto += "   - Sin declaraciones entrecomilladas en la pasada activa.\\n"

        minuta_texto += f"""
6. RECOMENDACIONES TÁCTICAS PARA EL EQUIPO DE COMUNICACIONES:
   * Vocería Proactiva: Reforzar y visibilizar hitos en '{eje_mejor}' para consolidar capital político de gestión.
   * Contención y Aclaración Técnica: Activar despliegue de voceros SERVIU en '{eje_peor}' para mitigar escalamiento de conflicto.
   * Pulso Digital: Monitorear consultas ciudadanas sobre arriendos y subsidios para anticipar reclamos de comités de vivienda.
================================================================================
"""
        st.markdown(f'<div class="minuta-card">{minuta_texto}</div>', unsafe_allow_html=True)
        st.download_button("Descargar Minuta (.txt)", minuta_texto, file_name=f"minuta_ejecutiva_minvu_{datetime.now().strftime('%Y%m%d')}.txt")

