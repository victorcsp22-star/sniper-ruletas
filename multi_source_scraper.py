"""
multi_source_scraper.py
-----------------------
Módulo autónomo de ingestión de resultados en vivo para las 6 ruletas activas:
1. Lotto Gato -> triplegato.com API (res-gato)
2. Gatazo -> triplegato.com API (res-gatazo)
3. Loto Chaima -> resultadosvenezuela.com (/lottery/loto-chaima)
4. Monje Millonario -> resultadosvenezuela.com (/lottery/monje-millonario)
5. Guacharo Activo -> resultadosvenezuela.com (/lottery/guacharo-activo) [Fallback: lottoresultados.com]
6. Granja Millonaria - Granjazo -> resultadosvenezuela.com (/lottery/granjazo) [Fallback: lottoresultados.com]
"""

import urllib.request
import json
import re
import ssl
import datetime

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8'
}

MESES_ES = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
    'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
}

def normalize_hora(h_str):
    if not h_str:
        return ""
    h_str = h_str.strip().upper()
    m = re.match(r'^0?(\d{1,2}):(\d{2})\s*(AM|PM)?$', h_str)
    if m:
        hh, mm, ampm = m.groups()
        if ampm:
            return f"{int(hh)}:{mm} {ampm}"
        return f"{int(hh)}:{mm}"
    return h_str

def normalize_num(raw_n):
    if raw_n is None:
        return None
    s = str(raw_n).strip()
    if s.lower() in ["none", "null", "", "-", "--"]:
        return None
    if s in ["00", "0"]:
        return s
    clean = s.lstrip("0") or "0"
    return clean

def fetch_url(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return r.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return ""

def fetch_triplegato_api(dates=None):
    if not dates:
        today_iso = datetime.date.today().strftime("%Y-%m-%d")
        yest_iso = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        dates = [yest_iso, today_iso]
        
    results = {"Lotto Gato": [], "Gatazo": []}
    mapping = [
        ("res-gato", "Lotto Gato"),
        ("res-gatazo", "Gatazo")
    ]
    
    for endpoint, ruleta_name in mapping:
        for d_str in dates:
            url = f"https://triplegato.com/api/{endpoint}?fecha={d_str}"
            body = fetch_url(url, timeout=8)
            if not body:
                continue
            try:
                data = json.loads(body)
                if isinstance(data, list):
                    for item in data:
                        num = normalize_num(item.get("numero"))
                        if num is None:
                            continue
                        hora = normalize_hora(item.get("hora", ""))
                        anim = str(item.get("animal", "")).strip()
                        f_raw = str(item.get("fecha", "")).strip()
                        f_iso = d_str
                        if "/" in f_raw:
                            pts = f_raw.split("/")
                            if len(pts) == 3:
                                d, m, y = pts
                                f_iso = f"{y}-{int(m):02d}-{int(d):02d}"
                        results[ruleta_name].append({
                            "fecha": f_iso,
                            "hora": hora,
                            "numero": num,
                            "animal": anim,
                            "loteria": ruleta_name
                        })
            except Exception:
                pass
    return results

def fetch_resultados_venezuela():
    results = {
        "Loto Chaima": [],
        "Monje Millonario": [],
        "Guacharo Activo": [],
        "Granja Millonaria - Granjazo": []
    }
    today_iso = datetime.date.today().strftime("%Y-%m-%d")
    mapping = [
        ("loto-chaima", "Loto Chaima"),
        ("monje-millonario", "Monje Millonario"),
        ("guacharo-activo", "Guacharo Activo"),
        ("granjazo", "Granja Millonaria - Granjazo")
    ]
    
    card_pat = re.compile(
        r'card-time">\s*(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))\s*</div>.*?<div[^>]*>\s*(\d{1,2}|00)\s*</div>.*?<div[^>]*>\s*([A-Za-zÁÉÍÓÚáéíóúñÑ\s]+?)\s*</div>',
        re.DOTALL | re.IGNORECASE
    )
    
    for slug, ruleta_name in mapping:
        url = f"https://resultadosvenezuela.com/lottery/{slug}"
        html = fetch_url(url, timeout=10)
        if not html:
            continue
        
        date_iso = today_iso
        m_d = re.search(r"(\d{1,2})\s+de\s+([A-Za-z]+)\s+de\s+(\d{4})", html, re.IGNORECASE)
        if m_d:
            d_num = int(m_d.group(1))
            m_name = m_d.group(2).lower()
            y_num = int(m_d.group(3))
            m_idx = MESES_ES.get(m_name, datetime.date.today().month)
            date_iso = f"{y_num}-{m_idx:02d}-{d_num:02d}"
        
        matches = card_pat.findall(html)
        for h_str, num_str, anim_str in matches:
            num = normalize_num(num_str)
            if num is None:
                continue
            hora = normalize_hora(h_str)
            anim = anim_str.strip()
            results[ruleta_name].append({
                "fecha": date_iso,
                "hora": hora,
                "numero": num,
                "animal": anim,
                "loteria": ruleta_name
            })
    return results

def fetch_lottoresultados_fallback():
    fallback_results = {"Guacharo Activo": [], "Granja Millonaria - Granjazo": []}
    today_iso = datetime.date.today().strftime("%Y-%m-%d")
    mapping = [
        ("guacharo-activo", "Guacharo Activo"),
        ("el-granjazo-granja-millonaria", "Granja Millonaria - Granjazo")
    ]
    pat = re.compile(
        r'result-item-time[^>]*>\s*(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))\s*</div>.*?<div[^>]*font-bold[^>]*>\s*(\d{1,2}|00)\s*</div>.*?<div[^>]*uppercase[^>]*>\s*([A-Za-zÁÉÍÓÚáéíóúñÑ\s]+?)\s*</div>',
        re.DOTALL | re.IGNORECASE
    )
    for slug, ruleta_name in mapping:
        url = f"https://www.lottoresultados.com/resultados/animalitos/{slug}"
        html = fetch_url(url, timeout=10)
        if not html:
            continue
        matches = pat.findall(html)
        for h_str, num_str, anim_str in matches:
            num = normalize_num(num_str)
            if num is None:
                continue
            fallback_results[ruleta_name].append({
                "fecha": today_iso,
                "hora": normalize_hora(h_str),
                "numero": num,
                "animal": anim_str.strip(),
                "loteria": ruleta_name
            })
    return fallback_results

def fetch_all_live_sources():
    all_draws = {
        "Lotto Gato": [],
        "Gatazo": [],
        "Loto Chaima": [],
        "Monje Millonario": [],
        "Guacharo Activo": [],
        "Granja Millonaria - Granjazo": []
    }
    
    # 1. TripleGato API (Gato y Gatazo)
    tg_data = fetch_triplegato_api()
    for k, v in tg_data.items():
        all_draws[k].extend(v)
        
    # 2. ResultadosVenezuela (Chaima, Monje, Guacharo, Granjazo)
    rv_data = fetch_resultados_venezuela()
    for k, v in rv_data.items():
        all_draws[k].extend(v)
        
    # 3. Fallback a lottoresultados si Guacharo o Granjazo vienen vacíos
    if not all_draws["Guacharo Activo"] or not all_draws["Granja Millonaria - Granjazo"]:
        lr_data = fetch_lottoresultados_fallback()
        if not all_draws["Guacharo Activo"] and lr_data.get("Guacharo Activo"):
            all_draws["Guacharo Activo"].extend(lr_data["Guacharo Activo"])
        if not all_draws["Granja Millonaria - Granjazo"] and lr_data.get("Granja Millonaria - Granjazo"):
            all_draws["Granja Millonaria - Granjazo"].extend(lr_data["Granja Millonaria - Granjazo"])
            
    return all_draws
