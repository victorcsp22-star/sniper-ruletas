import os

path = "C:/Users/victo/nuevas_ruletas/app_movil/static/index.html"
with open(path, "r", encoding="utf-8") as f:
    c = f.read()

old_h1 = """          <h1 class="text-sm font-bold tracking-tight text-white flex items-center gap-1.5">
            SNIPER V2 OFFLINE
            <span class="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono font-semibold">LIVE</span>
          </h1>"""

new_h1 = """          <h1 class="text-sm font-bold tracking-tight text-white flex items-center gap-1.5">
            SNIPER V3 DINÁMICO
            <span class="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-mono font-bold">BURBUJAS 30D</span>
          </h1>"""

c_norm = c.replace("\r\n", "\n")
o_norm = old_h1.replace("\r\n", "\n")
n_norm = new_h1.replace("\r\n", "\n")

if o_norm in c_norm:
    c_norm = c_norm.replace(o_norm, n_norm, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(c_norm)
    print("Updated index.html header successfully.")
else:
    print("Could not find old_h1.")
