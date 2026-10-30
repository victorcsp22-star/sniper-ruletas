"""
Herramienta de Análisis y Pruebas Estadísticas para Loterías de Animalitos
Permite evaluar frecuencias, números calientes/fríos, demoras (atrasos),
comportamiento por horario y rachas repetidas en base al archivo CSV generado.
"""

import argparse
import os
import pandas as pd


def analyze_lottery_data(csv_file: str, top_n: int = 10):
    if not os.path.exists(csv_file):
        print(f"[!] Error: El archivo '{csv_file}' no existe. Ejecuta primero lotto_bot.py.")
        return

    df = pd.read_csv(csv_file, encoding="utf-8-sig")
    total_draws = len(df)
    if total_draws == 0:
        print("[!] El archivo CSV está vacío.")
        return

    print("==================================================")
    print(" INFORME DE ANÁLISIS ESTADÍSTICO - LOTTO ACTIVO")
    print(f" Archivo: {csv_file}")
    print(f" Total de sorteos analizados: {total_draws:,}")
    print(f" Rango de fechas: {df['fecha'].min()} hasta {df['fecha'].max()}")
    print("==================================================\n")

    # 1. Animales más frecuentes (Calientes)
    print(f"--- TOP {top_n} ANIMALITOS MÁS FRECUENTES (CALIENTES) ---")
    freq = df.groupby(["numero", "animal"]).size().reset_index(name="apariciones")
    freq["porcentaje"] = (freq["apariciones"] / total_draws) * 100
    freq_sorted = freq.sort_values(by="apariciones", ascending=False).reset_index(drop=True)

    for i, row in freq_sorted.head(top_n).iterrows():
        print(f" {i+1:2d}. Nº {row['numero']:>2} - {row['animal']:<12} | {row['apariciones']:5d} veces ({row['porcentaje']:.2f}%)")

    # 2. Animales menos frecuentes (Fríos)
    print(f"\n--- TOP {top_n} ANIMALITOS MENOS FRECUENTES (FRÍOS) ---")
    for i, row in freq_sorted.tail(top_n).iloc[::-1].reset_index(drop=True).iterrows():
        print(f" {i+1:2d}. Nº {row['numero']:>2} - {row['animal']:<12} | {row['apariciones']:5d} veces ({row['porcentaje']:.2f}%)")

    # 3. Animalitos más salidores por Horario
    print("\n--- ANIMALITO LÍDER POR HORARIO ---")
    if "hora" in df.columns:
        hours = df["hora"].unique()
        # Ordenar horas si es posible
        try:
            sorted_hours = sorted(hours, key=lambda h: pd.to_datetime(h, format="%I:%M %p"))
        except Exception:
            sorted_hours = sorted(hours)

        for h in sorted_hours:
            df_hour = df[df["hora"] == h]
            if not df_hour.empty:
                top_hour = df_hour.groupby(["numero", "animal"]).size().reset_index(name="cuenta")
                top_hour = top_hour.sort_values(by="cuenta", ascending=False).iloc[0]
                pct = (top_hour['cuenta'] / len(df_hour)) * 100
                print(f"  {h:>8} -> Nº {top_hour['numero']:>2} {top_hour['animal']:<10} ({top_hour['cuenta']} veces, {pct:.1f}%)")

    # 4. Animalitos más salidores por Día de la semana
    print("\n--- ANIMALITO LÍDER POR DÍA DE LA SEMANA ---")
    if "dia" in df.columns:
        dias_orden = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        for d in dias_orden:
            df_dia = df[df["dia"] == d]
            if not df_dia.empty:
                top_dia = df_dia.groupby(["numero", "animal"]).size().reset_index(name="cuenta")
                top_dia = top_dia.sort_values(by="cuenta", ascending=False).iloc[0]
                pct = (top_dia['cuenta'] / len(df_dia)) * 100
                print(f"  {d:<10} -> Nº {top_dia['numero']:>2} {top_dia['animal']:<10} ({top_dia['cuenta']} veces, {pct:.1f}%)")

    # 5. Atrasos actuales (Días desde la última aparición de cada animal)
    print(f"\n--- TOP {top_n} ANIMALITOS MÁS ATRASADOS (Última vez vistos) ---")
    latest_date = pd.to_datetime(df["fecha"].max())
    df["_fecha_dt"] = pd.to_datetime(df["fecha"])
    last_seen = df.groupby(["numero", "animal"])["_fecha_dt"].max().reset_index()
    last_seen["dias_sin_salir"] = (latest_date - last_seen["_fecha_dt"]).dt.days
    last_seen_sorted = last_seen.sort_values(by="dias_sin_salir", ascending=False).reset_index(drop=True)

    for i, row in last_seen_sorted.head(top_n).iterrows():
        fecha_str = row['_fecha_dt'].strftime('%Y-%m-%d')
        print(f" {i+1:2d}. Nº {row['numero']:>2} - {row['animal']:<12} | {row['dias_sin_salir']:3d} días sin salir (último: {fecha_str})")

    print("\n==================================================")
    print(" Análisis completado. Puedes abrir el archivo CSV en Excel")
    print(" para aplicar filtros, tablas dinámicas y gráficos.")
    print("==================================================")


def main():
    parser = argparse.ArgumentParser(description="Análisis estadístico de números de lotería.")
    parser.add_argument("--csv", type=str, default="lotto_activo_2anios.csv", help="Ruta del archivo CSV a analizar")
    parser.add_argument("--top", type=int, default=10, help="Cantidad de elementos en los rankings (por defecto: 10)")
    args = parser.parse_args()

    analyze_lottery_data(args.csv, args.top)


if __name__ == "__main__":
    main()
