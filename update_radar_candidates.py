import os

path = "C:/Users/victo/nuevas_ruletas/app_movil/static/index.html"
with open(path, "r", encoding="utf-8") as f:
    c = f.read()

# Replace confusing header text
c = c.replace('<span class="text-[10px] text-slate-500 font-mono">Apuesta: Bs 100.00 fijo</span>',
              '<span class="text-[10px] text-emerald-400 font-mono font-bold">Burbujas: 🟢 $1.50 | 🟡 $1.00 | 🔴 $0.50</span>')

# In radar item rendering, add candidates display when urgencia === 1
old_radar_render = """                <p class="text-[11px] text-slate-400">${item.conteo_str}</p>
                <p class="text-[10px] text-slate-500 font-mono">Último: ${item.ultimo_salido}</p>
              </div>
            </div>
            <div class="text-right">
              <span class="text-[11px] font-mono font-bold text-slate-300">${item.payout}x</span>
            </div>"""

new_radar_render = """                <p class="text-[11px] text-slate-400">${item.conteo_str}</p>
                <p class="text-[10px] text-slate-500 font-mono">Último: ${item.ultimo_salido}</p>
                ${(item.urgencia === 1 && item.candidatos_str) ? `
                  <div class="mt-2 pt-2 border-t border-emerald-500/30">
                    <p class="text-[10px] font-bold text-emerald-300 mb-1">🎯 ANIMALES A COMPRAR ($${item.burbuja ? item.burbuja.stake.toFixed(2) : '1.00'} c/u):</p>
                    <div class="flex flex-wrap gap-1">${renderCandidatos(item.candidatos_str, false)}</div>
                  </div>
                ` : ''}
              </div>
            </div>
            <div class="text-right">
              <span class="text-[11px] font-mono font-bold text-slate-300">${item.payout}x</span>
            </div>"""

c_norm = c.replace("\r\n", "\n")
o_norm = old_radar_render.replace("\r\n", "\n")
n_norm = new_radar_render.replace("\r\n", "\n")

if o_norm in c_norm:
    c_norm = c_norm.replace(o_norm, n_norm, 1)
    print("Replaced radar render successfully.")
else:
    print("Could not find old_radar_render.")

with open(path, "w", encoding="utf-8") as f:
    f.write(c_norm)

print("Saved index.html.")
