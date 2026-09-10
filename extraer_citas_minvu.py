import sqlite3
import re
import html

DB_NAME = "monitor_minvu.db"
PATRON_CITAS = re.compile(r'["«“]([^"»”\n]{25,450})["»”]')

def procesar():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

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
    cursor.execute("DROP TABLE IF EXISTS citas")
    cursor.execute("""
        CREATE TABLE citas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            articulo_id TEXT NOT NULL,
            cita TEXT NOT NULL,
            medio TEXT NOT NULL,
            eje_tematico TEXT,
            fecha TEXT
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_citas_art ON citas(articulo_id)")

    cursor.execute("SELECT id, medio, cuerpo, eje_tematico, fecha_publicacion FROM articulos WHERE cuerpo IS NOT NULL AND cuerpo != ''")
    articulos = cursor.fetchall()
    total = len(articulos)

    print(f"[*] Extrayendo declaraciones textuales en {total} artículos MINVU...")

    guardadas = 0
    for art_id, medio, cuerpo, eje, fecha in articulos:
        texto = html.unescape(cuerpo).replace("\r", " ")
        citas = PATRON_CITAS.findall(texto)
        vistas = set()

        for c in citas:
            c_str = c.strip()
            if any(term in c_str for term in ["http", "<", "=", "{", "function()", "window."]):
                continue
            if c_str not in vistas:
                vistas.add(c_str)
                cursor.execute("""
                    INSERT INTO citas (articulo_id, cita, medio, eje_tematico, fecha)
                    VALUES (?, ?, ?, ?, ?)
                """, (art_id, c_str, medio, eje or "General", fecha))
                guardadas += 1

    conn.commit()
    conn.close()
    print(f"[OK] Citas y verbatims MINVU indexados: {guardadas}")

if __name__ == "__main__":
    procesar()
