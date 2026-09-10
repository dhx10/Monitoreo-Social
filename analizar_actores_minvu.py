import sqlite3
import spacy
import re
import html

DB_NAME = "monitor_minvu.db"

# ==============================================================================
# WHITELIST CANÓNICA EXCLUSIVA DEL ECOSISTEMA MINVU Y HÁBITAT (CHILE 2026)
# ÚNICAMENTE actores pertenecientes a esta lista serán indexados.
# Se descartan automáticamente celebridades, medios de comunicación y términos no relevantes.
# ==============================================================================
WHITELIST_ACTORES_MINVU = {
    # 1. Autoridades Centrales MINVU (2026)
    "ivan poduje": "Iván Poduje (Ministro MINVU)",
    "iván poduje": "Iván Poduje (Ministro MINVU)",
    "poduje": "Iván Poduje (Ministro MINVU)",
    "ministro poduje": "Iván Poduje (Ministro MINVU)",
    "ministro ivan poduje": "Iván Poduje (Ministro MINVU)",
    "ministro iván poduje": "Iván Poduje (Ministro MINVU)",
    "natalia aguilar": "Natalia Aguilar (Subsecretaria MINVU)",
    "natalia aguilar bravo": "Natalia Aguilar (Subsecretaria MINVU)",
    "aguilar": "Natalia Aguilar (Subsecretaria MINVU)",
    "subsecretaria aguilar": "Natalia Aguilar (Subsecretaria MINVU)",
    "subsecretaria natalia aguilar": "Natalia Aguilar (Subsecretaria MINVU)",
    "rodrigo uribe": "Rodrigo Uribe (SERVIU)",
    "ditec": "DITEC MINVU",
    "ddu": "División de Desarrollo Urbano (DDU)",
    "dph": "División de Política Habitacional (DPH)",
    "parquemet": "Parquemet (Parque Metropolitano)",
    "parque metropolitano": "Parquemet (Parque Metropolitano)",
    
    # 2. Institucionalidad Ministerial y Regional
    "minvu": "MINVU (Central)",
    "ministerio de vivienda": "MINVU (Central)",
    "ministerio de vivienda y urbanismo": "MINVU (Central)",
    "subsecretaría de vivienda": "Subsecretaría de Vivienda",
    "subsecretaria de vivienda": "Subsecretaría de Vivienda",
    "seremi de vivienda": "SEREMI MINVU",
    "seremi minvu": "SEREMI MINVU",
    "seremis de vivienda": "SEREMI MINVU",
    "serviu": "SERVIU",
    "servius": "SERVIU",
    "serviu metropolitano": "SERVIU Metropolitano",
    "serviu valparaiso": "SERVIU Valparaíso",
    "serviu valparaíso": "SERVIU Valparaíso",
    "serviu biobio": "SERVIU Biobío",
    "serviu biobío": "SERVIU Biobío",
    "serviu araucania": "SERVIU Araucanía",
    "serviu araucanía": "SERVIU Araucanía",
    "serviu antofagasta": "SERVIU Antofagasta",
    "serviu tarapaca": "SERVIU Tarapacá",
    "serviu tarapacá": "SERVIU Tarapacá",
    "serviu atacama": "SERVIU Atacama",
    "serviu coquimbo": "SERVIU Coquimbo",
    "serviu o'higgins": "SERVIU O'Higgins",
    "serviu maule": "SERVIU Maule",
    "serviu nuble": "SERVIU Ñuble",
    "serviu ñuble": "SERVIU Ñuble",
    "serviu los rios": "SERVIU Los Ríos",
    "serviu los ríos": "SERVIU Los Ríos",
    "serviu los lagos": "SERVIU Los Lagos",
    "serviu aysen": "SERVIU Aysén",
    "serviu aysén": "SERVIU Aysén",
    "serviu magallanes": "SERVIU Magallanes",
    "serviu arica": "SERVIU Arica y Parinacota",
    "serviu arica y parinacota": "SERVIU Arica y Parinacota",

    # 3. Gremios, Sociedad Civil y Movimientos de Vivienda
    "cchc": "CChC (Cámara Chilena de la Construcción)",
    "cámara chilena de la construcción": "CChC (Cámara Chilena de la Construcción)",
    "camara chilena de la construccion": "CChC (Cámara Chilena de la Construcción)",
    "techo": "TECHO-Chile",
    "techo chile": "TECHO-Chile",
    "techo-chile": "TECHO-Chile",
    "deficit cero": "Fundación Déficit Cero",
    "déficit cero": "Fundación Déficit Cero",
    "fundación déficit cero": "Fundación Déficit Cero",
    "ukamau": "Movimiento Ukamau",
    "comité de vivienda": "Comités de Vivienda",
    "comités de vivienda": "Comités de Vivienda",
    "comité de allegados": "Comités de Allegados",
    "comités de allegados": "Comités de Allegados",
    "andha chile": "ANDHA Chile",
    
    # 4. Autoridades Políticas, Presidencia y Parlamentarios
    "jose antonio kast": "José Antonio Kast (Presidente)",
    "josé antonio kast": "José Antonio Kast (Presidente)",
    "presidente kast": "José Antonio Kast (Presidente)",
    "kast": "José Antonio Kast (Presidente)",
    "gabriel boric": "Gabriel Boric",
    "boric": "Gabriel Boric",
    "carlos montes": "Carlos Montes (Ex Ministro MINVU)",
    "montes": "Carlos Montes (Ex Ministro MINVU)",
    "gabriela elgueta": "Gabriela Elgueta (Ex Subsecretaria MINVU)",
    "tatiana rojas": "Tatiana Rojas (Ex Subsecretaria MINVU)",
    "fidel espinoza": "Fidel Espinoza (Senador)",
    "comision de vivienda": "Comisión de Vivienda (Congreso)",
    "comisión de vivienda": "Comisión de Vivienda (Congreso)",
    "claudio orrego": "Claudio Orrego (Gobernador RM)",
    "orrego": "Claudio Orrego (Gobernador RM)",
    "tomas vodanovic": "Tomás Vodanovic (Alcalde Maipú)",
    "tomás vodanovic": "Tomás Vodanovic (Alcalde Maipú)",
    "vodanovic": "Tomás Vodanovic (Alcalde Maipú)",
    "macarena ripamonti": "Macarena Ripamonti (Alcaldesa Viña del Mar)",
    "ripamonti": "Macarena Ripamonti (Alcaldesa Viña del Mar)",
    "camila nieto": "Camila Nieto (Alcaldesa Valparaíso)",
    "mario desbordes": "Mario Desbordes (Alcalde Santiago)",
    "desbordes": "Mario Desbordes (Alcalde Santiago)",
    "evelyn matthei": "Evelyn Matthei",
    "matthei": "Evelyn Matthei",
    
    # 5. Caso Convenios y Judicialización
    "daniel andrade": "Daniel Andrade (Caso Convenios)",
    "andrade": "Daniel Andrade (Caso Convenios)",
    "carlos contreras": "Carlos Contreras (Ex Seremi)",
    "democracia viva": "Democracia Viva",
    "procultura": "ProCultura",
    "urbanismo social": "Urbanismo Social",
    
    # 6. Instituciones de Control del Estado
    "contraloria": "Contraloría General",
    "contraloría": "Contraloría General",
    "contraloria general": "Contraloría General",
    "fiscalia": "Fiscalía Nacional",
    "fiscalía": "Fiscalía Nacional",
    "cde": "Consejo de Defensa del Estado (CDE)",
    "senapred": "SENAPRED"
}

def limpiar(txt):
    if not txt:
        return ""
    t = re.sub(r'<[^>]+>', ' ', str(txt))
    t = html.unescape(t)
    return re.sub(r'\s+', ' ', t).strip()

def extraer():
    print("[*] Iniciando indexación de vocerías y actores con WHITELIST ESTRICTA MINVU...")
    try:
        nlp = spacy.load("es_core_news_md")
    except Exception:
        print("  [!] Modelo 'es_core_news_md' no disponible, intentando 'es_core_news_sm'...")
        nlp = spacy.load("es_core_news_sm")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS entidades")
    cursor.execute("""
        CREATE TABLE entidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            articulo_id TEXT NOT NULL,
            entidad TEXT NOT NULL,
            tipo TEXT NOT NULL,
            medio TEXT NOT NULL,
            fecha TEXT
        )
    """)
    cursor.execute("CREATE INDEX idx_ent_minvu ON entidades(entidad, tipo)")
    cursor.execute("CREATE INDEX idx_ent_art_minvu ON entidades(articulo_id)")
    conn.commit()

    # ÚNICAMENTE extraer de publicaciones válidas del MINVU (es_minvu == 1)
    cursor.execute("SELECT id, medio, titulo, bajada, fecha_publicacion FROM articulos WHERE es_minvu = 1")
    articulos = cursor.fetchall()
    total = len(articulos)

    print(f"[*] Analizando menciones de actores en {total} artículos MINVU...")

    guardados = 0
    for idx, (art_id, medio, titulo, bajada, fecha) in enumerate(articulos, 1):
        texto = f"{limpiar(titulo)}. {limpiar(bajada)}"
        if not texto.strip():
            continue

        doc = nlp(texto)
        vistos = set()

        for ent in doc.ents:
            tipo = ent.label_
            if tipo in ["PER", "ORG"]:
                raw = ent.text.strip().strip(". ,:;\"'")
                low = raw.lower()

                # REGLA INVIOLABLE: SOLO admitir si está en la whitelist de actores de vivienda
                if low in WHITELIST_ACTORES_MINVU:
                    nombre_final = WHITELIST_ACTORES_MINVU[low]
                    if nombre_final not in vistos:
                        vistos.add(nombre_final)
                        cursor.execute("""
                            INSERT INTO entidades (articulo_id, entidad, tipo, medio, fecha)
                            VALUES (?, ?, ?, ?, ?)
                        """, (art_id, nombre_final, tipo, medio, fecha))
                        guardados += 1

        # Análisis por coincidencia directa de patrones (por si spaCy no detectó la entidad)
        t_low = texto.lower()
        for alias, nombre_can in WHITELIST_ACTORES_MINVU.items():
            if len(alias) >= 4 and nombre_can not in vistos:
                if re.search(r'\b' + re.escape(alias) + r'\b', t_low):
                    vistos.add(nombre_can)
                    cursor.execute("""
                        INSERT INTO entidades (articulo_id, entidad, tipo, medio, fecha)
                        VALUES (?, ?, ?, ?, ?)
                    """, (art_id, nombre_can, "PER" if "Ministro" in nombre_can or "Alcalde" in nombre_can else "ORG", medio, fecha))
                    guardados += 1

        if idx % 150 == 0 or idx == total:
            conn.commit()
            print(f"  -> {idx}/{total} analizados...")

    conn.commit()
    conn.close()
    print(f"\n[OK] Actores e instituciones purificadas indexadas: {guardados}")

if __name__ == "__main__":
    extraer()
