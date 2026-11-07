import os

src_path = "C:/Users/victo/nuevas_ruletas/app_movil/index.html"
dst_path = "C:/Users/victo/nuevas_ruletas/app_movil/static/index.html"

with open(src_path, "r", encoding="utf-8") as f:
    c = f.read()

# 1. Header Title
old_h1 = """          <h1 class="text-sm font-bold tracking-tight text-white flex items-center gap-1.5">
            SNIPER V2 OFFLINE
            <span class="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono font-semibold">LIVE</span>
          </h1>"""

new_h1 = """          <h1 class="text-sm font-bold tracking-tight text-white flex items-center gap-1.5">
            SNIPER V3 DINÁMICO
            <span class="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-mono font-bold">BURBUJAS 30D</span>
          </h1>"""

c = c.replace(old_h1, new_h1)

# 2. Section "Registro de Jugadas de Hoy" Header & List
old_sec = """    <!-- Registro de Jugadas de Hoy (Animalitos jugados y resultados) -->
    <section id="section-today-ops" class="bg-brand-card border border-slate-800 rounded-2xl p-3.5 shadow-lg space-y-3">
      <div class="flex items-center justify-between pb-2 border-b border-slate-800/80">
        <h3 class="text-xs font-bold text-white flex items-center gap-1.5">
          <i data-lucide="history" class="w-4 h-4 text-emerald-400"></i> Registro de Jugadas de Hoy
        </h3>
        <span id="stat-today" class="text-[11px] font-mono text-emerald-400 font-semibold px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
          PnL Hoy: Bs 0.00
        </span>
      </div>

      <div id="recent-ops-list" class="space-y-2.5">
        <!-- Tarjetas detalladas de operaciones inyectadas con JS -->
      </div>
    </section>"""

new_sec = """    <!-- Registro de Jugadas de Hoy (Animalitos jugados y resultados) -->
    <section id="section-today-ops" class="bg-brand-card border border-slate-800 rounded-2xl p-3.5 shadow-lg space-y-3">
      <div class="flex items-center justify-between pb-2 border-b border-slate-800/80">
        <h3 class="text-xs font-bold text-white flex items-center gap-1.5">
          <i data-lucide="history" class="w-4 h-4 text-emerald-400"></i> Registro de Jugadas de Hoy
        </h3>
        <div class="flex items-center space-x-2">
          <span id="stat-today" class="text-[11px] font-mono text-emerald-400 font-semibold px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
            PnL Hoy: Bs 0.00
          </span>
          <button onclick="limpiarRegistroDiario()" class="flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-rose-500/15 hover:bg-rose-500/30 active:bg-rose-500 text-rose-300 active:text-white border border-rose-500/40 text-[10px] font-bold shadow-sm transition">
            <i data-lucide="trash-2" class="w-3 h-3"></i>
            <span>Limpiar</span>
          </button>
        </div>
      </div>

      <div id="recent-ops-list" class="space-y-2.5 max-h-72 overflow-y-auto pr-1">
        <!-- Tarjetas detalladas de operaciones inyectadas con JS -->
      </div>
    </section>"""

c = c.replace(old_sec, new_sec)

# 3. Radar Subtitle text
c = c.replace('<span class="text-[10px] text-slate-500 font-mono">Apuesta: Bs 100.00 fijo</span>',
              '<span class="text-[10px] text-emerald-400 font-mono font-bold">Burbujas: 🟢 $1.50 | 🟡 $1.00 | 🔴 $0.50</span>')

# 4. Hero Card Bubbles and Currency
old_hero_pills = """                <div class="flex items-center space-x-1.5">
                  <span class="text-[10px] font-mono font-black px-2 py-0.5 rounded-full border ${pesoPillClass}">
                    P:${peso}/10
                  </span>
                  <span class="text-[11px] font-mono font-bold px-2 py-0.5 rounded border ${badgeClass}">
                    ${sig.tipo.replace(/\\[P:\\d+(\\/10)?\\]/g, '').trim()}
                  </span>
                </div>"""

new_hero_pills = """                <div class="flex items-center space-x-1.5">
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

c = c.replace("Animales a Comprar (Bs ${sig.stake_unit", "Animales a Comprar ($ ${sig.stake_unit")
c = c.replace("💰 Bs ${sig.costo.toFixed(2)}", "💰 $ ${sig.costo.toFixed(2)}")
c = c.replace("🏆 Bs ${sig.premio_potencial.toFixed(2)}", "🏆 $ ${sig.premio_potencial.toFixed(2)}")

# 5. Radar item bubble and inminent candidates
old_radar_badge = """                  <span class="text-[9px] font-mono px-1 py-0.2 rounded border ${badgeColor}">
                    ${item.badge}
                  </span>
                  ${item.peso_label ? `<span class="text-[9px] font-mono px-1 py-0.2 rounded border ${item.peso_agente >= 7 ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' : (item.peso_agente >= 5 ? 'bg-amber-500/20 text-amber-300 border-amber-500/30' : 'bg-slate-800 text-slate-400 border-slate-700')}">${item.peso_label}</span>` : ''}
                </div>
                <p class="text-[11px] text-slate-400">${item.conteo_str}</p>
                <p class="text-[10px] text-slate-500 font-mono">Último: ${item.ultimo_salido}</p>"""

new_radar_badge = """                  <span class="text-[9px] font-mono px-1 py-0.2 rounded border ${badgeColor}">
                    ${item.badge}
                  </span>
                  ${item.burbuja ? `
                    <span class="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-full border shadow-sm flex items-center space-x-1" 
                          style="background: ${item.burbuja.color_hex}22; color: ${item.burbuja.color_hex}; border-color: ${item.burbuja.color_hex}55;">
                      <span>${item.burbuja.emoji}</span>
                      <span>$${item.burbuja.stake.toFixed(2)}</span>
                    </span>` : ''}
                  ${item.peso_label ? `<span class="text-[9px] font-mono px-1 py-0.2 rounded border ${item.peso_agente >= 7 ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' : (item.peso_agente >= 5 ? 'bg-amber-500/20 text-amber-300 border-amber-500/30' : 'bg-slate-800 text-slate-400 border-slate-700')}">${item.peso_label}</span>` : ''}
                </div>
                <p class="text-[11px] text-slate-400">${item.conteo_str}</p>
                <p class="text-[10px] text-slate-500 font-mono">Último: ${item.ultimo_salido}</p>
                ${(item.urgencia === 1 && item.candidatos_str) ? `
                  <div class="mt-2 pt-2 border-t border-emerald-500/30">
                    <p class="text-[10px] font-bold text-emerald-300 mb-1">🎯 ANIMALES A COMPRAR ($${item.burbuja ? item.burbuja.stake.toFixed(2) : '1.00'} c/u):</p>
                    <div class="flex flex-wrap gap-1">${renderCandidatos(item.candidatos_str, false)}</div>
                  </div>
                ` : ''}"""

c = c.replace(old_radar_badge, new_radar_badge)

# 6. Add limpiarRegistroDiario JS function right before </script> at the bottom
clean_func = """
    async function limpiarRegistroDiario() {
      if (!confirm('🗑️ ¿Deseas eliminar y vaciar el registro de jugadas de hoy para despejar la pantalla?\\n\\nLas jugadas quedarán respaldadas de forma segura en el archivo histórico institucional.')) {
        return;
      }
      try {
        const res = await fetch('/api/clear_today_ledger', { method: 'POST' });
        const data = await res.json();
        if (data.status === 'ok') {
          await loadTacticalStatus();
        } else {
          alert('Error: ' + data.message);
        }
      } catch (err) {
        alert('Error al conectar con el servidor: ' + err);
      }
    }
  </script>
</body>"""

c = c.replace("  </script>\n</body>", clean_func)

with open(dst_path, "w", encoding="utf-8") as f:
    f.write(c)

print("Generated clean app_movil/static/index.html successfully.")
