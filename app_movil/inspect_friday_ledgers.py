import pandas as pd

ledgers = [
    r"C:\Users\victo\nuevas_ruletas\ledger_nuevas_ruletas.csv",
    r"C:\Users\victo\nuevas_ruletas\app_movil\ledger_nuevas_ruletas.csv",
    r"C:\Users\victo\nuevas_ruletas\data_vz\production_ledger_venezuela.csv"
]

for l in ledgers:
    print(f"\n=================== {l} ===================")
    try:
        df = pd.read_csv(l)
        print("Columnas:", list(df.columns))
        print("Total filas:", len(df))
        if 'fecha' in df.columns:
            print("Fechas unicas:", df['fecha'].unique())
            recientes = df[df['fecha'] >= '2026-10-30']
            print(f"Filas desde 2026-10-30 (Viernes): {len(recientes)}")
            for idx, r in recientes.iterrows():
                print(f"  [{r['fecha']} {r.get('hora', '')}] {r.get('ruleta', '')} | Cands: {r.get('candidatos', '')} | Salio: {r.get('resultado', '')} | Cond: {r.get('condicion', '')} | PnL: {r.get('pnl', '')}")
    except Exception as e:
        print(f"Error leyendo {l}: {e}")
