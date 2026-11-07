import glob, os

archivos = glob.glob(r'C:\Users\victo\nuevas_ruletas\**\*.csv', recursive=True)
for a in archivos:
    if 'ledger' in a.lower():
        print(f"ENCONTRADO: {a} (tamano: {os.path.getsize(a)} bytes)")
