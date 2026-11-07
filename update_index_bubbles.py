import os

path = "C:/Users/victo/nuevas_ruletas/app_movil/static/index.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

target = """                <div class="flex items-center space-x-1.5">
                  <span class="text-[10px] font-mono font-black px-2 py-0.5 rounded-full border ${pesoPillClass}">
                    P:${peso}/10
                  </span>
                  <span class="text-[11px] font-mono font-bold px-2 py-0.5 rounded border ${badgeClass}">
                    ${sig.tipo.replace(/\[P:\\d+(\\/10)?\\]/g, '').trim()}
                  </span>
                </div>"""

# Let's search without regex escape in python string:
old_block = """                <div class="flex items-center space-x-1.5">
                  <span class="text-[10px] font-mono font-black px-2 py-0.5 rounded-full border ${pesoPillClass}">
                    P:${peso}/10
                  </span>
                  <span class="text-[11px] font-mono font-bold px-2 py-0.5 rounded border ${badgeClass}">
                    ${sig.tipo.replace(/\\[P:\\d+(\\/10)?\\]/g, '').trim()}
                  </span>
                </div>"""

new_block = """                <div class="flex items-center space-x-1.5">
                  ${sig.burbuja ? `
                  <span class="text-[10px] font-bold px-2 py-0.5 rounded border inline-flex items-center gap-1 shadow-sm"
                        style="background: ${sig.burbuja.color_hex}25; color: ${sig.burbuja.color_hex}; border-color: ${sig.burbuja.color_hex}66;">
                    <span>${sig.burbuja.emoji}</span>
                    <span>$${sig.burbuja.stake.toFixed(2)}</span>
                  </span>` : ''}
                  <span class="text-[10px] font-mono font-black px-2 py-0.5 rounded-full border ${pesoPillClass}">
                    P:${peso}/10
                  </span>
                  <span class="text-[11px] font-mono font-bold px-2 py-0.5 rounded border ${badgeClass}">
                    ${sig.tipo.replace(/\\[P:\\d+(\\/10)?\\]/g, '').trim()}
                  </span>
                </div>"""

c_norm = content.replace('\r\n', '\n')
o_norm = old_block.replace('\r\n', '\n')
n_norm = new_block.replace('\r\n', '\n')

print("Found block:", o_norm in c_norm)
c_norm = c_norm.replace(o_norm, n_norm, 1)

# Also let's check Animales a Comprar (Bs -> $)
c_norm = c_norm.replace("Animales a Comprar (Bs ${sig.stake_unit", "Animales a Comprar ($ ${sig.stake_unit")
c_norm = c_norm.replace("💰 Bs ${sig.costo.toFixed(2)}", "💰 $ ${sig.costo.toFixed(2)}")
c_norm = c_norm.replace("🏆 Bs ${sig.premio_potencial.toFixed(2)}", "🏆 $ ${sig.premio_potencial.toFixed(2)}")

with open(path, "w", encoding="utf-8") as f:
    f.write(c_norm)

print("Updated index.html successfully.")
