"""
========================================================================================
 LABORATORIO CUANTITATIVO INDEPENDIENTE (SANDBOX DE ANÁLISIS DE RULETAS EXTRA)
========================================================================================
Módulo 100% segregado y aislado del portafolio principal (sniper_bot.py).
Permite descargar, analizar rebote de lags, calcular Criterio de Kelly y simular
el rendimiento de dos ruletas adicionales sin interferir con las 5 principales.
========================================================================================
"""

import argparse
import datetime
import os
import sys
import time
from typing import Dict, List, Optional
import lxml.html
import numpy as np
import pandas as pd
import requests
from scipy import stats

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://www.tuazar.com/loteria/animalitos/resultados/"
ANTERIORES_URL = BASE_URL + "anteriores/{date}/"
SEMANA_URL = BASE_URL + "semana/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

DIAS_MAP = {
    0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves",
    4: "Viernes", 5: "Sábado", 6: "Domingo"
}

# Catálogo de Ruletas Candidatas Disponibles en TuAzar para Análisis
AVAILABLE_CATALOG = {
    "lottobrasil": {
        "name": "Lotto Brasil",
        "card_title": "Lotto Brasil",
        "csv_file": os.path.join(BASE_DIR, "lottobrasil_2anios.csv"),
        "k_universe": 38,
        "payout": 37.0,
        "emoji": "🇧🇷"
    },
    "lottobicho": {
        "name": "Lotto Bicho",
        "card_title": "Lotto Bicho",
        "csv_file": os.path.join(BASE_DIR, "lottobicho_2anios.csv"),
        "k_universe": 38,
        "payout": 35.0,
        "emoji": "🐆"
    },
    "guacharito": {
        "name": "El Guacharito Millonario",
        "card_title": "El Guacharito Millonario",
        "csv_file": os.path.join(BASE_DIR, "guacharito_millonario_2anios.csv"),
        "k_universe": 100,
        "payout": 70.0,
        "emoji": "🦜"
    },
    "lotto_rd": {
        "name": "Lotto Activo RD Internacional",
        "card_title": "Lotto Activo RD Internacional",
        "csv_file": os.path.join(BASE_DIR, "lotto_activo_rd_2anios.csv"),
        "k_universe": 38,
        "payout": 30.0,
        "emoji": "🇩🇴"
    },
    "loto_chaima": {
        "name": "Loto Chaima",
        "card_title": "Loto Chaima",
        "csv_file": os.path.join(BASE_DIR, "loto_chaima_2anios.csv"),
        "k_universe": 38,
        "payout": 30.0,
        "emoji": "🏹"
    },
    "granja_millonaria": {
        "name": "Granja Millonaria - Animalitos",
        "card_title": "Granja Millonaria - Animalitos",
        "csv_file": os.path.join(BASE_DIR, "granja_millonaria_2anios.csv"),
        "k_universe": 38,
        "payout": 30.0,
        "emoji": "🚜"
    },
    "monje_millonario": {
        "name": "Monje Millonario",
        "card_title": "Monje Millonario",
        "csv_file": os.path.join(BASE_DIR, "monje_millonario_2anios.csv"),
        "k_universe": 38,
        "payout": 30.0,
        "emoji": "🧘"
    },
    "triple_popular": {
        "name": "Triple Popular",
        "card_title": "Triple Popular",
        "csv_file": os.path.join(BASE_DIR, "triple_popular_2anios.csv"),
        "k_universe": 38,
        "payout": 30.0,
        "emoji": "⭐"
    }
}

def parse_date_dmy(dmy_str: str) -> Optional[datetime.date]:
    try:
        parts = dmy_str.strip().split('/')
        if len(parts) == 3:
            return datetime.date(int(parts[2]), int(parts[1]), int(parts[0]))
    except Exception:
        pass
    return None

def scrape_lottery_history(target_key: str, weeks_back: int = 104) -> pd.DataFrame:
    """Descarga el historial de una ruleta específica si su CSV no existe."""
    info = AVAILABLE_CATALOG[target_key]
    csv_path = info["csv_file"]
    
    if os.path.exists(csv_path):
        df_existing = pd.read_csv(csv_path)
        if len(df_existing) > 300:
            print(f"[✓] {info['name']}: Historial ya disponible ({len(df_existing):,} sorteos en {os.path.basename(csv_path)}).")
            return df_existing

    print(f"[+] Descargando historial de {info['name']} desde TuAzar ({weeks_back} semanas)...")
    session = requests.Session()
    session.headers.update(HEADERS)
    
    today = datetime.date.today()
    curr = today
    while curr.weekday() != 6:
        curr -= datetime.timedelta(days=1)
    sundays = []
    for _ in range(weeks_back):
        sundays.append(curr)
        curr -= datetime.timedelta(days=7)

    records = []
    seen = set()

    for idx, sunday in enumerate(sundays, 1):
        sunday_str = sunday.strftime("%Y-%m-%d")
        url = ANTERIORES_URL.format(date=sunday_str) if idx > 1 else SEMANA_URL
        try:
            r = session.get(url, timeout=10)
            if r.status_code == 200:
                doc = lxml.html.fromstring(r.text)
                for card in doc.xpath('//div[contains(@class, "lw-card")]'):
                    t = card.xpath('.//h3[contains(@class, "lw-title")]')
                    if t and t[0].text_content().strip() == info["card_title"]:
                        table = card.xpath('.//table[contains(@class, "lw-table")]')
                        if not table:
                            continue
                        day_headers = table[0].xpath('.//thead//th[contains(@class, "lw-day")]')
                        dates = [parse_date_dmy(th.xpath('.//span[contains(@class, "lw-day-num")]')[0].text_content())
                                 if th.xpath('.//span[contains(@class, "lw-day-num")]') else None for th in day_headers]
                        
                        for row in table[0].xpath('.//tbody/tr'):
                            time_el = row.xpath('.//th[contains(@class, "lw-time")]')
                            draw_time = time_el[0].text_content().strip() if time_el else ""
                            for dt, cell in zip(dates, row.xpath('.//td')):
                                if dt is None:
                                    continue
                                num_el = cell.xpath('.//span[@class="lw-animal-num"]')
                                anim_el = cell.xpath('.//span[@class="lw-animal"]')
                                if num_el and anim_el:
                                    num = num_el[0].text_content().strip()
                                    anim = anim_el[0].text_content().strip()
                                    if num and anim and num != "-":
                                        k = (dt.strftime("%Y-%m-%d"), draw_time)
                                        if k not in seen:
                                            seen.add(k)
                                            records.append({
                                                "fecha": dt.strftime("%Y-%m-%d"),
                                                "dia": DIAS_MAP.get(dt.weekday(), ""),
                                                "hora": draw_time,
                                                "numero": str(num),
                                                "animal": str(anim),
                                                "loteria": info["name"]
                                            })
        except Exception:
            pass
        
        pct = (idx / len(sundays)) * 100
        print(f"\r  Progreso descarga: {idx}/{len(sundays)} ({pct:.1f}%) | {len(records)} sorteos", end="", flush=True)
        time.sleep(0.08)

    print()
    df = pd.DataFrame(records)
    if not df.empty:
        try:
            df["_h"] = pd.to_datetime(df["hora"], format="%I:%M %p", errors="coerce").dt.time
            df = df.sort_values(by=["fecha", "_h"]).drop(columns=["_h"]).reset_index(drop=True)
        except Exception:
            df = df.sort_values(by=["fecha", "hora"]).reset_index(drop=True)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"[✓] Guardado en {csv_path}: {len(df):,} sorteos.")
    else:
        print(f"[!] No se pudieron extraer sorteos para {info['name']}.")
    return df

def analyze_rebound_and_kelly(target_key: str, df: pd.DataFrame, max_lag: int = 40):
    info = AVAILABLE_CATALOG[target_key]
    nums = df["numero"].tolist()
    total = len(nums)
    k_univ = info["k_universe"]
    payout = info["payout"]
    p0 = 1.0 / k_univ
    be_rate = (1.0 / payout) * 100.0

    print("\n" + "=" * 90)
    print(f" {info['emoji']} ANÁLISIS DE REBOTE Y CRITERIO DE KELLY: {info['name'].upper()}")
    print(f"   Universo: {k_univ} números | Pago: {payout:.0f}x | Break-Even: {be_rate:.2f}% | Sorteos: {total:,}")
    print("=" * 90)

    lag_stats = []
    for lag in range(1, max_lag + 1):
        valid = total - lag
        if valid <= 0:
            continue
        matches = sum(1 for i in range(lag, total) if nums[i] == nums[i - lag])
        p_hat = matches / valid
        se = np.sqrt(p0 * (1.0 - p0) / valid) if valid > 0 else 0.001
        z = (p_hat - p0) / se

        # Filtrado de 6 horas
        matches_filt = 0
        trials_filt = 0
        for i in range(max(25, lag), total):
            cand = nums[i - lag]
            if cand not in set(nums[i-6:i]):
                trials_filt += 1
                if nums[i] == cand:
                    matches_filt += 1
        p_filt = (matches_filt / trials_filt * 100.0) if trials_filt > 0 else 0.0

        lag_stats.append({
            "lag": lag,
            "pct_bruto": p_hat * 100.0,
            "pct_filt": p_filt,
            "z_score": z
        })

    df_lags = pd.DataFrame(lag_stats)
    rebound = df_lags[df_lags["lag"] >= 7].sort_values(by="pct_filt", ascending=False).reset_index(drop=True)

    print("TOP 5 LAGS CON MAYOR EFECTO REBOTE (lag >= 7):")
    for idx, row in rebound.head(5).iterrows():
        supera = "SI (+EV)" if row["pct_filt"] > be_rate else "NO (-EV)"
        print(f"  #{idx+1}: Lag {int(row['lag']):2d} -> Prob Filtrada: {row['pct_filt']:5.2f}% | Z-Score: {row['z_score']:+5.2f} | Supera BE ({be_rate:.2f}%): {supera}")

    # Optimización de canasta
    top_lags = rebound["lag"].head(4).tolist()
    
    # Backtest individual bajo Gatillo Post-Fallo 1
    streak = 0
    signals = 0
    hits = 0
    flat_pnl = 0.0

    for i in range(max(top_lags) + 7, total):
        actual = nums[i]
        rec6 = set(nums[i-6:i])
        cands = list({nums[i-l] for l in top_lags} - rec6)
        cost = len(cands)
        hit = (actual in cands)

        if streak == 1 and cost > 0:
            signals += 1
            if hit:
                hits += 1
                flat_pnl += (payout - cost)
            else:
                flat_pnl -= cost

        if hit:
            streak = 0
        else:
            streak += 1

    win_rate = (hits / signals * 100.0) if signals > 0 else 0.0
    roi = (flat_pnl / (signals * len(top_lags)) * 100.0) if signals > 0 else 0.0

    # Criterio de Kelly
    b = (payout / len(top_lags)) - 1.0
    p = win_rate / 100.0
    q = 1.0 - p
    f_star = max(0.0, (b * p - q) / b) if b > 0 else 0.0
    f_unit = f_star / len(top_lags) if len(top_lags) > 0 else 0.0

    print(f"\n>> CANASTA ÓPTIMA PROPUESTA: Lags {top_lags}")
    print(f"   • Señales con Gatillo Post-Fallo 1: {signals:,} ensayos")
    print(f"   • Aciertos: {hits} ({win_rate:.2f}%) | Break-Even Requerido: {be_rate:.2f}%")
    print(f"   • Retorno Plano: {flat_pnl:+.0f} unidades | ROI: {roi:+.2f}%")
    print(f"   • Fracción Full Kelly Cesta: {f_star*100:.2f}% | Kelly Unitario por Animal: {f_unit*100:.3f}%")
    
    if win_rate > be_rate:
        print(f"   • Veredicto: 🟢 ESTRATEGIA CON VENTAJA (+EV) — Apta para consideración.")
    else:
        print(f"   • Veredicto: 🔴 ESTRATEGIA SIN VENTAJA (-EV) — Desaconsejada debido a margen de la banca.")

    return {
        "name": info["name"],
        "top_lags": top_lags,
        "win_rate": win_rate,
        "be_rate": be_rate,
        "f_unit": f_unit,
        "roi": roi,
        "is_positive_ev": win_rate > be_rate
    }

def main():
    parser = argparse.ArgumentParser(description="Laboratorio Sandbox de Análisis de Ruletas Extra")
    parser.add_argument("--ruleta1", type=str, default="lotto_rd", choices=list(AVAILABLE_CATALOG.keys()),
                        help="Primera ruleta adicional a analizar (por defecto: lotto_rd)")
    parser.add_argument("--ruleta2", type=str, default="loto_chaima", choices=list(AVAILABLE_CATALOG.keys()),
                        help="Segunda ruleta adicional a analizar (por defecto: loto_chaima)")
    args = parser.parse_args()

    print("\n" + "=" * 90)
    print(" 🧪 LABORATORIO CUANTITATIVO AISLADO: ANÁLISIS DE 2 RULETAS INDEPENDIENTES")
    print(f"    Ruleta 1: {AVAILABLE_CATALOG[args.ruleta1]['name']}")
    print(f"    Ruleta 2: {AVAILABLE_CATALOG[args.ruleta2]['name']}")
    print("=" * 90)

    for r_key in [args.ruleta1, args.ruleta2]:
        df = scrape_lottery_history(r_key)
        if not df.empty:
            analyze_rebound_and_kelly(r_key, df)

if __name__ == "__main__":
    main()
