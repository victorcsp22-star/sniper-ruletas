import pandas as pd
import numpy as np

# Verificar cómo se extrajeron esas transiciones Markov y qué soporte real tienen
rutas = {
    "Guacharo Activo": (r"C:\Users\victo\nuevas_ruletas\data_vz\guacharo_activo_2anios.csv", {'21': '0', '8': '67', '29': '2'}),
    "Lotto Activo": (r"C:\Users\victo\nuevas_ruletas\data_vz\lotto_activo_2anios.csv", {'14': '0', '31': '0', '6': '0'}),
    "Ruleta Royal": (r"C:\Users\victo\nuevas_ruletas\data_vz\ruleta_royal_2anios.csv", {'25': '22', '8': '27'}),
    "Mega Animal 40": (r"C:\Users\victo\nuevas_ruletas\mega_animal_40.csv", {'30': '0', '11': '0', '32': '35'}),
    "Gatazo": (r"C:\Users\victo\nuevas_ruletas\gatazo.csv", {'30': '63', '48': '21', '23': '42'}),
    "Lotto Gato": (r"C:\Users\victo\nuevas_ruletas\lotto_gato.csv", {'14': '0', '27': '15', '3': '7'}),
    "Loto Chaima": (r"C:\Users\victo\nuevas_ruletas\loto_chaima.csv", {'48': '0', '55': '0', '12': '0'})
}

print("=== AUDITORIA DE RELEVANCIA ESTADISTICA DE PARES MARKOV ===")
for r_name, (fpath, m_dict) in rutas.items():
    df = pd.read_csv(fpath)
    nums = [str(x).strip().lstrip("0") or "0" for x in df['numero']]
    print(f"\n[{r_name}] Total sorteos: {len(nums)}")
    for origen, destino in m_dict.items():
        origen_norm = str(origen).strip().lstrip("0") or "0"
        destino_norm = str(destino).strip().lstrip("0") or "0"
        
        # Conteo de transiciones
        total_origen = 0
        hits_transicion = 0
        for i in range(len(nums) - 1):
            if nums[i] == origen_norm:
                total_origen += 1
                if nums[i+1] == destino_norm:
                    hits_transicion += 1
                    
        pct = (hits_transicion / total_origen * 100) if total_origen > 0 else 0
        print(f"  Transición #{origen_norm} -> #{destino_norm}: {hits_transicion} de {total_origen} veces ({pct:.2f}%)")
