import requests
import lxml.html
import re
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

def fetch_date(date_str):
    url = f"https://lotoven.com/animalito/lottoactivordint/resultados/{date_str}"
    retries = 3
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=12)
            if r.status_code == 200:
                doc = lxml.html.fromstring(r.text)
                txt = " ".join(doc.text_content().split())
                # Captura numero, animal, hora
                matches = re.findall(r"(\d{1,2}|00)\s+([A-Za-zÁÉÍÓÚáéíóúñÑ]+)\s+Lotto Activo RD Int\s+(\d{1,2}:\d{2}\s+[AP]M)", txt)
                if matches:
                    results = []
                    for num, anim, hora in matches:
                        results.append({
                            "fecha": date_str,
                            "hora": hora,
                            "numero": num,
                            "animal": anim,
                            "loteria": "Lotto Activo RD Internacional"
                        })
                    return date_str, results
                return date_str, []
        except Exception:
            time.sleep(1)
    return date_str, []

def main():
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2026, 10, 17)
    
    dates = []
    curr = start_date
    while curr <= end_date:
        dates.append(curr.strftime("%Y-%m-%d"))
        curr += timedelta(days=1)
        
    print(f"Total fechas a consultar: {len(dates)} (desde {dates[0]} hasta {dates[-1]})")
    
    all_draws = []
    completed = 0
    t0 = time.time()
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(fetch_date, d): d for d in dates}
        for future in as_completed(futures):
            d_str, res = future.result()
            completed += 1
            if res:
                all_draws.extend(res)
            if completed % 150 == 0 or completed == len(dates):
                elapsed = time.time() - t0
                print(f"Progreso: {completed}/{len(dates)} fechas ({completed/len(dates)*100:.1f}%) | Sorteos capturados: {len(all_draws)} | Tiempo: {elapsed:.1f}s")
                
    print(f"Descarga completada en {time.time() - t0:.1f}s. Total sorteos: {len(all_draws)}")
    
    if all_draws:
        df = pd.DataFrame(all_draws)
        
        # Mapeo de días de la semana en español
        dias_es = {
            0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves",
            4: "Viernes", 5: "Sábado", 6: "Domingo"
        }
        df["dt"] = pd.to_datetime(df["fecha"])
        df["dia"] = df["dt"].dt.dayofweek.map(dias_es)
        
        # Orden cronológico estricto: por fecha y hora
        hora_order = {
            "08:30 AM": 1, "09:30 AM": 2, "10:30 AM": 3, "11:30 AM": 4,
            "12:30 PM": 5, "01:30 PM": 6, "02:30 PM": 7, "03:30 PM": 8,
            "04:30 PM": 9, "05:30 PM": 10, "06:30 PM": 11, "07:30 PM": 12
        }
        df["hora_rank"] = df["hora"].map(hora_order).fillna(99)
        df = df.sort_values(by=["dt", "hora_rank"]).reset_index(drop=True)
        
        # Normalizar nombres de animales en mayúsculas sin acentos inconsistentes
        df["animal"] = df["animal"].str.upper()
        
        # Limpiar columnas
        df = df[["fecha", "dia", "hora", "numero", "animal", "loteria"]]
        
        out_csv = "C:/Users/victo/nuevas_ruletas/lotto_activo_rd_lotoven_completo.csv"
        df.to_csv(out_csv, index=False, encoding="utf-8-sig")
        print(f"Guardado exitoso en {out_csv} con {len(df)} registros.")
        print("Rango temporal capturado:", df["fecha"].min(), "a", df["fecha"].max())
        print("Muestra:")
        print(df.head(5))
        print(df.tail(5))

if __name__ == "__main__":
    main()
