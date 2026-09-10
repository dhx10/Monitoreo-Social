import time
import sys
from datetime import datetime

def ejecutar_ciclo_actualizacion():
    print("==================================================")
    print(f" ACTUALIZADOR SECTORIAL | MONITOR MINVU CHILE")
    print(f" Fecha y Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Autoridades vigentes: Ministro Iván Poduje | Subsecretaria Natalia Aguilar")
    print(f" Cadencia Operativa: Cada 15 Minutos (24/7)")
    print("==================================================\n")

    inicio = time.time()

    print(">>> 1. Ingesta Nacional (85+ Canales: Prensa, 16 Regiones, TV y Redes)...")
    import ingesta_minvu
    ingesta_minvu.procesar_feeds()

    print("\n>>> 2. Clasificación en 7 Ejes MINVU, Sentimiento y Drivers Emocionales...")
    import clasificar_minvu
    clasificar_minvu.procesar()

    print("\n>>> 3. Mapeo Canónico de Actores y Vocerías Institucionales...")
    import analizar_actores_minvu
    analizar_actores_minvu.extraer()

    print("\n>>> 4. Extracción de Verbatims y Declaraciones Textuales...")
    import extraer_citas_minvu
    extraer_citas_minvu.procesar()

    duracion = round(time.time() - inicio, 1)
    print(f"\n==================================================")
    print(f" [OK] Monitor MINVU actualizado exitosamente en {duracion} segundos.")
    print(f"==================================================")

if __name__ == "__main__":
    if "--loop" in sys.argv:
        # Modo servicio continuo cada 15 minutos
        minutos = 15
        try:
            idx = sys.argv.index("--loop")
            if idx + 1 < len(sys.argv) and sys.argv[idx + 1].isdigit():
                minutos = int(sys.argv[idx + 1])
        except Exception:
            pass

        print(f"[*] Iniciando Monitor MINVU en MODO CONTINUO (cada {minutos} minutos)...")
        while True:
            ejecutar_ciclo_actualizacion()
            print(f"\n[DORMIR] Próxima actualización en {minutos} minutos. Esperando...")
            for seg in range(minutos * 60, 0, -30):
                time.sleep(30)
    else:
        ejecutar_ciclo_actualizacion()
