import pandas as pd

datasets = {
    "Lotto Activo": ("lotto_activo_2anios.csv", 38, 30),
    "La Granjita": ("la_granjita_2anios.csv", 38, 30),
    "Ruleta Royal": ("ruleta_royal_2anios.csv", 37, 30),
    "Guacharo Activo": ("guacharo_activo_2anios.csv", 77, 60),
    "El Guacharito Millonario": ("guacharito_millonario_2anios.csv", 100, 70),
    "Selva Plus": ("selva_plus_2anios.csv", 100, 80),
    "Lotto Activo RD": ("lotto_activo_rd_2anios.csv", 38, 30)
}

print(f"{'Loteria':26s} | {'Sorteos':8s} | {'Desde':10s} | {'Hasta':10s} | {'Núm':4s} | {'Pago':4s}")
print("-" * 75)
for name, (fname, nums, payout) in datasets.items():
    try:
        df = pd.read_csv(fname)
        print(f"{name:26s} | {len(df):8,d} | {df['fecha'].min():10s} | {df['fecha'].max():10s} | {nums:4d} | {payout:4d}x")
    except Exception as e:
        print(f"{name:26s} | Error: {e}")
