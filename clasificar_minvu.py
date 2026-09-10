import sqlite3
import re

DB_NAME = "monitor_minvu.db"

# ==============================================================================
# 1. ANCLAS INVIOLABLES DE RELEVANCIA SECTORIAL MINVU Y VIVIENDA CHILE
# Una noticia SOLO puede ser calificada con es_minvu = 1 si contiene al menos
# una de estas anclas explícitas e inequívocas del sector.
# ==============================================================================
PATRONES_VIVIENDA_CHILE = [
    # 1. Conceptos nucleares de vivienda y habitabilidad
    r'vivienda(?:s)?',
    r'habitacional(?:es)?',
    r'soluci[óo]n(?:es)? habitacional(?:es)?',
    r'conjunto(?:s)? habitacional(?:es)?',
    r'casa(?:s)? propia(?:s)?',
    r'departamento(?:s)? social(?:es)?',
    
    # 2. Instituciones y Autoridades
    r'minvu',
    r'serviu',
    r'servius',
    r'ministerio de vivienda',
    r'subsecretar[íi]a de vivienda',
    r'seremi (?:de )?vivienda',
    r'seremis (?:de )?vivienda',
    r'seremi minvu',
    r'iv[áa]n poduje',
    r'ministro poduje',
    r'poduje',
    r'natalia aguilar',
    r'subsecretaria aguilar',
    r'parquemet',
    r'parque metropolitano',
    r'ditec', r'ddu', r'dph',
    
    # 3. Subsidios, Créditos y Programas
    r'subsidio(?:s)?',
    r'ds49', r'ds 49',
    r'ds19', r'ds 19',
    r'ds1', r'ds 1',
    r'ds52', r'ds 52',
    r'ds10', r'ds 10',
    r'ds27', r'ds 27',
    r'cr[ée]dito(?:s)? hipotecario(?:s)?',
    r'tasa(?:s)? hipotecaria(?:s)?',
    r'dividendo(?:s)?',
    r'banco de suelo(?:s)?',
    r'postulaci[óo]n (?:al )?subsidio',
    r'postulaciones (?:al )?subsidio',
    r'llamado a postular',
    r'fogaes',
    
    # 4. Crisis, Déficit, Comités y Arriendos
    r'd[ée]ficit habitacional',
    r'crisis habitacional',
    r'emergencia habitacional',
    r'plan (?:de )?emergencia habitacional',
    r'comit[ée]s? de vivienda',
    r'comit[ée]s? de allegados',
    r'allegado(?:s)?',
    r'deudores habitacionales',
    r'arriendo(?:s)?',
    r'arrendatario(?:s)?',
    r'arrendador(?:es)?',
    r'precio(?:s)? de arriendo',
    r'alquiler(?:es)?',
    
    # 5. Campamentos, Tomas, Desalojos y Suelo
    r'campamento(?:s)?',
    r'asentamiento(?:s)? precario(?:s)?',
    r'toma(?:s)? de terreno(?:s)?',
    r'toma(?:s)? ilegal(?:es)?',
    r'megatoma(?:s)?',
    r'desalojo(?:s)?',
    r'usurpaci[óo]n (?:de )?terreno(?:s)?',
    r'ocupaci[óo]n(?:es)? (?:ilegal(?:es)?|de terreno(?:s)?)',
    r'terreno(?:s)? fiscal(?:es)?',
    r'terreno(?:s)? municipal(?:es)?',
    r'loteo(?:s)? brujo(?:s)?',
    r'loteo(?:s)? irregular(?:es)?',
    r'estafa(?:s)? inmobiliaria(?:s)?',
    r'catastro de campamentos',
    r'techo(?:-chile)?',
    r'd[ée]ficit cero',
    r'ukamau',
    
    # 6. Catástrofes, Socavones y Reconstrucción
    r'socav[óo]n(?:es)?',
    r'edificio kandinsky',
    r'euromarina',
    r'miramar re[ñn]aca',
    r'dunas de conc[óo]n',
    r'campo dunar',
    r'reconstrucci[óo]n',
    r'vivienda(?:s)? de emergencia',
    r'damnificado(?:s)?',
    r'suelos salinos',
    r'falla estructural',
    
    # 7. Industria de la Construcción y Ciudad
    r'cchc',
    r'c[áa]mara chilena de la construcci[óo]n',
    r'quiebra(?:s)? de constructora(?:s)?',
    r'paralizaci[óo]n de obras',
    r'permisolog[íi]a',
    r'permiso(?:s)? de edificaci[óo]n',
    r'plan regulador',
    r'guetos verticales',
    r'quiero mi barrio',
    r'pavimentaci[óo]n participativa',
    
    # 8. Caso Convenios
    r'caso convenios',
    r'democracia viva',
    r'procultura',
    r'urbanismo social'
]

# Países y ciudades foráneas para descarte inmediato (salvo mención explícita a MINVU/SERVIU/Poduje)
PAISES_EXTRANJEROS_RECHAZO = [
    "españa", "espana", "méxico", "mexico", "colombia", "argentina", "perú", "peru",
    "bolivia", "venezuela", "brasil", "ee.uu.", "estados unidos", "madrid", "barcelona",
    "buenos aires", "bogotá", "bogota", "lima", "caracas", "quito", "guayaquil", "montevideo",
    "paraguay", "uruguay", "francia", "alemania", "italia", "ucrania", "rusia", "china"
]


# ==============================================================================
# FILTRO BLINDADO ANTI-ARGENTINA Y DESAMBIGUACIÓN DE HOMÓNIMOS
# ==============================================================================
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
    "santa cruz": [r'\bcolchagua\b', r"\bo\'higgins\b", r'\bchile\b', r'\bvalle de colchagua\b', r'\bserviu\b', r'\bminvu\b'],
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

SECCIONES_RECHAZO = [
    "/internacional/", "/mundo/", "/global/", "/exterior/",
    "/deportes/", "/futbol/", "/espectaculos/", "/entretenimiento/", "/tendencias/", "/estilodevida/"
]

# ==============================================================================
# 2. MAPEO EXHAUSTIVO DE LAS 16 REGIONES DE CHILE
# ==============================================================================
MAPEO_REGIONES_COMPLETO = {
    "Arica y Parinacota": ["arica", "parinacota", "putre", "general lagos", "camarones"],
    "Tarapacá": ["iquique", "alto hospicio", "tarapacá", "tarapaca", "pozo almonte", "pica", "huara", "camiña", "colchane", "alto molle", "el boro"],
    "Antofagasta": ["antofagasta", "calama", "tocopilla", "mejillones", "taltal", "san pedro de atacama", "baquedano", "sierra gorda", "los arenales", "la chimba"],
    "Atacama": ["copiapó", "copiapo", "vallenar", "caldera", "chañaral", "atacama", "huasco", "tierra amarilla", "diego de almagro", "alto andacollo"],
    "Coquimbo": ["la serena", "coquimbo", "ovalle", "illapel", "salamanca", "limarí", "limari", "choapa", "elqui", "vicuña", "vicuna", "combarbalá", "combarbala", "monte patria", "los vilos"],
    "Valparaíso": ["valparaíso", "valparaiso", "viña del mar", "concon", "concón", "quilpué", "quilpue", "villa alemana", "san antonio", "quillota", "los andes", "san felipe", "kandinsky", "euromarina", "el olivar", "manuel bustos", "reñaca", "renaca"],
    "Metropolitana": ["santiago", "maipú", "maipu", "puente alto", "la florida", "san bernardo", "cerrillos", "estación central", "estacion central", "pudahuel", "quilicura", "colina", "lampa", "nuevo amanecer", "toma dignidad", "parquemet", "providencia", "las condes", "lo espejo", "la pintana", "recoleta", "independencia"],
    "O'Higgins": ["rancagua", "machalí", "machali", "san fernando", "rengo", "pichilemu", "o'higgins", "ohiggins", "cachapoal", "colchagua", "cardenal caro", "graneros", "mostazal", "santa cruz"],
    "Maule": ["talca", "curicó", "curico", "linares", "cauquenes", "constitución", "constitucion", "maule", "parral", "san javier", "molina", "san clemente"],
    "Ñuble": ["chillán", "chillan", "san carlos", "ñuble", "nuble", "diguillín", "diguillin", "itata", "punilla", "coelemu", "quirihue", "bulnes"],
    "Biobío": ["concepción", "concepcion", "talcahuano", "coronel", "lota", "san pedro de la paz", "chiguayante", "los ángeles", "los angeles", "biobío", "biobio", "hualpén", "hualpen", "penco", "tomé", "tome", "lebu", "arauco", "cañete", "canete"],
    "La Araucanía": ["temuco", "padre las casas", "villarrica", "pucón", "pucon", "angol", "araucanía", "araucania", "cautín", "cautin", "malleco", "victoria", "lautaro", "nueva imperial"],
    "Los Ríos": ["valdivia", "la unión", "la union", "panguipulli", "los ríos", "los rios", "ranco", "río bueno", "rio bueno", "paillaco", "mariquina", "lanco", "futrono", "lago ranco", "corral"],
    "Los Lagos": ["puerto montt", "puerto varas", "osorno", "castro", "ancud", "chiloé", "chiloe", "los lagos", "llanquihue", "palena", "frutillar", "calbuco", "quellón", "quellon"],
    "Aysén": ["coyhaique", "puerto aysén", "puerto aysen", "aysén", "aysen", "cochrane", "chile chico"],
    "Magallanes": ["punta arenas", "puerto natales", "magallanes", "tierra del fuego", "porvenir", "cabo de hornos", "antártica", "antartica"]
}

# ==============================================================================
# 3. LOS 7 EJES ESTRATÉGICOS MINVU
# ==============================================================================
CAMPOS_MINVU = {
    "🏠 Plan Habitacional, Subsidios y Reestructuración": [
        "subsidio", "subsidios", "ds49", "ds1", "ds19", "ds27", "ds52", "ds10", "vivienda social",
        "allegados", "comité de vivienda", "comites de vivienda", "entrega de llaves", "primera piedra",
        "déficit habitacional", "vivienda digna", "banco de suelo", "arriendo a precio justo",
        "plan habitacional", "soluciones habitacionales", "secretaría de vivienda", "subsidio rural",
        "emergencia habitacional", "solución habitacional", "iván poduje", "ivan poduje", "poduje",
        "natalia aguilar", "minvu", "serviu"
    ],
    "⛺ Campamentos, Tomas de Terreno y Desalojos": [
        "campamento", "campamentos", "toma de terreno", "tomas de terreno", "toma ilegal", "tomas ilegales",
        "asentamiento precario", "asentamientos precarios", "desalojo", "desalojos", "megatoma", "megatomas",
        "erradicación", "radicación", "catastro de campamentos", "techo", "techo chile", "déficit cero",
        "toma dignidad", "toma nuevo amanecer", "usurpación", "usurpación de terreno", "ocupación ilegal",
        "loteo brujo", "loteos brujos", "mafia de terrenos", "orden de desalojo", "san antonio"
    ],
    "⚖️ Probidad, Auditorías y Caso Convenios": [
        "caso convenios", "convenios", "democracia viva", "procultura", "urbanismo social",
        "fundación", "fundaciones", "seremi de vivienda", "traspaso de fondos", "contraloría",
        "fiscalía", "formalizado", "formalización", "comisión investigadora", "fraude al fisco",
        "tráfico de influencias", "cde", "consejo de defensa del estado", "daniel andrade", "andrade",
        "carlos contreras", "paz fuenzalida", "auditoría minvu", "rendición de cuentas"
    ],
    "🏙️ Ciudad, Parques Urbanos y Regeneración": [
        "parquemet", "parque metropolitano", "parque urbano", "parques urbanos", "espacio público",
        "espacios públicos", "regeneración urbana", "quiero mi barrio", "vialidad urbana", "ciclovía",
        "ciclovías", "ciudades justas", "urbanismo", "plan regulador", "densificación", "guetos verticales",
        "patrimonio urbano", "áreas verdes", "infraestructura urbana", "conectividad urbana"
    ],
    "🌧️ Reconstrucción, Catástrofes y Socavones": [
        "reconstrucción", "incendio", "incendios", "senapred", "vivienda de emergencia",
        "viviendas de emergencia", "damnificados", "inundación", "inundaciones", "socavón", "socavones",
        "dunas de concón", "zona de catástrofe", "edificio kandinsky", "frente de mal tiempo",
        "aluvión", "riesgo geológico", "euromarina", "miramar reñaca"
    ],
    "💼 Mercado Inmobiliario, Permisología y Costos": [
        "cchc", "cámara chilena de la construcción", "constructora", "constructoras", "quiebra constructora",
        "crédito hipotecario", "créditos hipotecarios", "tasa hipotecaria", "tasas hipotecarias",
        "permisología", "permisos de edificación", "mercado inmobiliario", "precio de la vivienda",
        "costo de construcción", "bancoestado", "paralización de obras", "inversión inmobiliaria",
        "sobreoferta", "stock de viviendas", "fogaes", "subsidio a la tasa"
    ],
    "💬 Debate Ciudadano, Redes y Arriendos": [
        "arriendo", "arriendos", "arrendatario", "arrendatarios", "arrendadores", "precio de arriendo",
        "postulación", "postulaciones", "registro social de hogares", "rsh", "comité", "vecinos",
        "barrio", "protesta vivienda", "acceso a la vivienda", "crisis habitacional", "piensa prensa",
        "prensa opal", "reddit", "denuncia vecinal", "molestia vecinal"
    ]
}

# ==============================================================================
# 4. MOTOR DE SENTIMIENTO Y DRIVERS EMOCIONALES
# ==============================================================================
LEXICO_POSITIVO = {
    "entrega": 2.0, "entregaron": 2.0, "solución": 2.5, "soluciones": 2.5, "inauguración": 2.0,
    "inaugura": 2.0, "avance": 2.0, "avanza": 2.0, "reactivación": 2.5, "beneficio": 1.8,
    "beneficia": 1.8, "alianza": 1.8, "acuerdo": 2.0, "histórico": 1.5, "vivienda digna": 3.0,
    "integración": 2.0, "regeneración": 2.0, "mejora": 1.8, "mejoramiento": 1.8, "éxito": 2.0,
    "aprobación": 1.8, "aprueba": 1.8, "desbloqueo": 2.0, "apoyo": 1.5, "financiamiento": 1.5,
    "recuperación": 2.0, "recupera": 2.0, "habitabilidad": 2.0, "cumplimiento": 2.0, "acuerdan": 1.8,
    "logro": 2.2, "solucionar": 2.0, "protección": 1.8, "prioridad": 1.5, "destaca": 1.5
}

LEXICO_NEGATIVO = {
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

def analizar_sentimiento(texto):
    tokens = re.findall(r'\b[a-záéíóúñ]+\b', (texto or "").lower())
    puntaje = 0.0

    i = 0
    while i < len(tokens):
        token = tokens[i]
        es_negado = False
        if i > 0 and tokens[i-1] in NEGACIONES:
            es_negado = True
        elif i > 1 and tokens[i-2] in NEGACIONES:
            es_negado = True
            
        peso_multiplicador = 1.5 if (i > 0 and tokens[i-1] in INTENSIFICADORES) else 1.0

        if token in LEXICO_POSITIVO:
            val = LEXICO_POSITIVO[token] * peso_multiplicador
            puntaje += -val if es_negado else val
        elif token in LEXICO_NEGATIVO:
            val = LEXICO_NEGATIVO[token] * peso_multiplicador
            puntaje += -val if es_negado else val

        i += 1

    if puntaje > 6.0: score = 1.0
    elif puntaje < -6.0: score = -1.0
    else: score = round(puntaje / 6.0, 3)

    if score >= 0.15: etiqueta = "Positivo"
    elif score <= -0.15: etiqueta = "Negativo"
    else: etiqueta = "Neutro"

    return etiqueta, score

def clasificar_driver_emocional(texto):
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

def detectar_region_exhaustiva(texto_eval, region_existente=""):
    """
    EL CONTENIDO MANDA (Georreferenciación Inviolable):
    Analiza el texto de la noticia buscando comunas, capitales, provincias y SERVIUs.
    Solo si el texto NO contiene ningún anclaje regional, se recurre a la región del medio.
    """
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

    # Fallback: solo si el texto es genérico o institucional sin comuna específica
    if region_existente and region_existente in MAPEO_REGIONES_COMPLETO:
        return region_existente

    return "Nacional"

def validar_filtro_estricto_chile_minvu(titulo, bajada, cuerpo, url="", seccion=""):
    t_full = f"{titulo or ''} {bajada or ''} {(cuerpo or '')[:1200]}".lower()
    u_low = (url or "").lower()
    s_low = (seccion or "").lower()

    # 0. Descarte inmediato por dominios o medios argentinos
    if any(dom in u_low for dom in DOMINIOS_ARGENTINOS):
        return False, "Rechazo: Dominio argentino"

    # 0.1 Descarte por indicadores de Argentina
    for pat_arg in MARCADORES_EXCLUSION_ARGENTINA:
        if re.search(pat_arg, t_full):
            if not any(k in t_full for k in ["minvu", "serviu", "poduje", "gobierno de chile"]):
                return False, f"Rechazo: Contexto argentino ({pat_arg})"

    # 0.2 Desambiguación de topónimos compartidos (Río Negro, Santa Cruz, San Rafael, etc.)
    for topo, contexto_chile in TOPONIMOS_COMPARTIDOS.items():
        if re.search(r'\b' + re.escape(topo) + r'\b', t_full):
            tiene_anclaje_chile = any(re.search(pat, t_full) for pat in contexto_chile)
            if not tiene_anclaje_chile:
                return False, f"Rechazo: Topónimo homónimo '{topo}' sin contexto chileno" 

    # 1. Descarte inmediato por sección internacional o deportes
    if any(sec in u_low for sec in SECCIONES_RECHAZO) or any(sec in s_low for sec in SECCIONES_RECHAZO):
        return False, "Rechazo por sección internacional o no sectorial"

    # 2. Descarte por país extranjero salvo ancla ministerial explícita
    for p in PAISES_EXTRANJEROS_RECHAZO:
        if re.search(r'\b' + re.escape(p) + r'\b', t_full):
            if not any(re.search(pat, t_full) for pat in [r'\bminvu\b', r'\bserviu\b', r'\bpoduje\b', r'\bseremi\b']):
                return False, f"Rechazo por contexto foráneo ({p})"

    # 3. Validación del Ecosistema de Vivienda, Ciudad y Hábitat en Chile
    for patron in PATRONES_VIVIENDA_CHILE:
        if re.search(patron, t_full):
            return True, patron

    return False, "Rechazo: Sin temática habitacional"

def clasificar_minvu(titulo, bajada, cuerpo, url="", seccion="", reg_existente=""):
    """
    Clasifica una noticia bajo el cerrojo absoluto MINVU y Chile.
    Retorna (eje_asignado, es_minvu, region_inferida).
    """
    pasa_filtro, motivo = validar_filtro_estricto_chile_minvu(titulo, bajada, cuerpo, url, seccion)
    texto_geo = f"{titulo or ''} {titulo or ''} {bajada or ''} {(cuerpo or '')[:1000]}"
    region_det = detectar_region_exhaustiva(texto_geo, reg_existente)

    if not pasa_filtro:
        return "📰 Pauta General (Excluida)", 0, region_det

    t_tit = (titulo or "").lower()
    t_baj = (bajada or "").lower()
    t_cue = (cuerpo or "")[:800].lower()

    puntajes = {tema: 0 for tema in CAMPOS_MINVU}
    for tema, palabras in CAMPOS_MINVU.items():
        for palabra in palabras:
            patron = r'\b' + re.escape(palabra) + r'\b'
            c_tit = len(re.findall(patron, t_tit))
            c_baj = len(re.findall(patron, t_baj))
            c_cue = len(re.findall(patron, t_cue))
            puntajes[tema] += (c_tit * 4) + (c_baj * 2) + (c_cue * 1)

    mejor_tema = max(puntajes, key=puntajes.get)
    if puntajes[mejor_tema] > 0:
        tema_asignado = mejor_tema
    else:
        if "socav" in t_tit or "kandinsky" in t_tit or "euromarina" in t_tit:
            tema_asignado = "🌧️ Reconstrucción, Catástrofes y Socavones"
        elif "toma" in t_tit or "campamento" in t_tit or "desalojo" in t_tit:
            tema_asignado = "⛺ Campamentos, Tomas de Terreno y Desalojos"
        elif "convenio" in t_tit or "democracia viva" in t_tit:
            tema_asignado = "⚖️ Probidad, Auditorías y Caso Convenios"
        else:
            tema_asignado = "🏠 Plan Habitacional, Subsidios y Reestructuración"

    return tema_asignado, 1, region_det

def procesar():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(articulos)")
    cols = [col[1] for col in cursor.fetchall()]
    if "sentimiento" not in cols:
        try: cursor.execute("ALTER TABLE articulos ADD COLUMN sentimiento TEXT")
        except Exception: pass
    if "polaridad_score" not in cols:
        try: cursor.execute("ALTER TABLE articulos ADD COLUMN polaridad_score REAL")
        except Exception: pass
    if "driver_emocional" not in cols:
        try: cursor.execute("ALTER TABLE articulos ADD COLUMN driver_emocional TEXT")
        except Exception: pass

    cursor.execute("SELECT id, titulo, bajada, cuerpo, url, seccion, region FROM articulos")
    articulos = cursor.fetchall()

    print(f"[*] Clasificando {len(articulos)} publicaciones bajo el CERROJO ABSOLUTO MINVU...")

    minvu_count = 0
    descartadas = 0
    for art_id, titulo, bajada, cuerpo, url, seccion, reg_existente in articulos:
        tema, es_minvu, reg_inferida = clasificar_minvu(titulo, bajada, cuerpo, url, seccion, reg_existente)
        if es_minvu == 1:
            minvu_count += 1
        else:
            descartadas += 1

        texto_analisis = f"{titulo or ''}. {bajada or ''}. {(cuerpo or '')[:500]}"
        sent_etiqueta, sent_score = analizar_sentimiento(texto_analisis)
        driver_emo = clasificar_driver_emocional(texto_analisis)

        cursor.execute("""
            UPDATE articulos 
            SET eje_tematico = ?, es_minvu = ?, region = ?, sentimiento = ?, polaridad_score = ?, driver_emocional = ?
            WHERE id = ?
        """, (tema, es_minvu, reg_inferida, sent_etiqueta, sent_score, driver_emo, art_id))

    conn.commit()

    cursor.execute("SELECT eje_tematico, COUNT(*) FROM articulos WHERE es_minvu = 1 GROUP BY eje_tematico ORDER BY COUNT(*) DESC")
    conteo_minvu = cursor.fetchall()
    
    cursor.execute("SELECT region, COUNT(*) FROM articulos WHERE es_minvu = 1 GROUP BY region ORDER BY COUNT(*) DESC")
    conteo_reg = cursor.fetchall()
    conn.close()

    print(f"\n[OK] Clasificación con Cerrojo Absoluto completada:")
    print(f"  - Total muestra estricta MINVU: {minvu_count}")
    print(f"  - Pauta general excluida: {descartadas}")
    print("\nDesglose Regional MINVU:")
    for reg, cant in conteo_reg:
        print(f"  - {reg}: {cant} registros")
    print("\nDistribución de Ejes MINVU:")
    for tema, cant in conteo_minvu:
        print(f"  - {tema}: {cant} registros")

if __name__ == "__main__":
    procesar()
