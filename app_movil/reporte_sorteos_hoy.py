import glob, os, pandas as pd

csv_files = glob.glob(r'C:\Users\victo\nuevas_ruletas\*.csv')
print("REPORTE DE RESULTADOS DE HOY (2026-11-02) EN PC:")
for cf in sorted(csv_files):
    if 'ledger' in cf:
        continue
    rname = os.path.basename(cf).replace('.csv', '')
    try:
        df = pd.read_csv(cf)
        hoy = df[df['fecha'] == '2026-11-02']
        print(f"\n--- {rname} ({len(hoy)} sorteos) ---")
        for _, r in hoy.iterrows():
            print(f"  {r['hora']}: #{r['numero']} {r['animal']}")
    except Exception as e:
        print(f"Error {rname}: {e}")
