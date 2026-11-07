p = r"C:\Users\victo\nuevas_ruletas\app_movil\server_zero_dep.py"
with open(p, 'r', encoding='utf-8') as f:
    code = f.read()

func_def = '''def read_csv_series(fpath):
    """Lee un CSV de ruleta devolviendo una lista de diccionarios con fecha, hora, numero y animal."""
    rows = []
    if not os.path.exists(fpath):
        return rows
    try:
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                return rows
            h_map = {col.strip().lower(): idx for idx, col in enumerate(header)}
            f_idx = h_map.get("fecha", 0)
            h_idx = h_map.get("hora", 1)
            n_idx = h_map.get("numero", 2)
            a_idx = h_map.get("animal", 3)
            
            for r in reader:
                if len(r) > max(f_idx, h_idx, n_idx):
                    num = str(r[n_idx]).strip().lstrip("0") or "0"
                    anim = str(r[a_idx]).strip() if len(r) > a_idx else ""
                    rows.append({
                        "fecha": str(r[f_idx]).strip(),
                        "hora": str(r[h_idx]).strip(),
                        "numero": num,
                        "animal": anim
                    })
    except Exception as e:
        print(f"Error leyendo {fpath}: {e}")
    return rows
'''

idx = code.find('def get_ruleta_filepath(r_name):')
code = code[:idx] + func_def + '\n\n' + code[idx:]

with open(p, 'w', encoding='utf-8') as f:
    f.write(code)

print("read_csv_series insertado exitosamente.")
