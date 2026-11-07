import os

path = "C:/Users/victo/nuevas_ruletas/app_movil/static/index.html"
with open(path, "r", encoding="utf-8") as f:
    c = f.read()

# 1. Update Section Header and List Container
old_section = """    <!-- Registro de Jugadas de Hoy (Animalitos jugados y resultados) -->
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

new_section = """    <!-- Registro de Jugadas de Hoy (Animalitos jugados y resultados) -->
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

# 2. Add Javascript function
js_func = """    async function limpiarRegistroDiario() {
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
        alert('Error de conexión al limpiar: ' + err);
      }
    }
"""

c_norm = c.replace("\r\n", "\n")
o_norm = old_section.replace("\r\n", "\n")
n_norm = new_section.replace("\r\n", "\n")

if o_norm in c_norm:
    c_norm = c_norm.replace(o_norm, n_norm, 1)
    # Add JS function before </script>
    c_norm = c_norm.replace("</script>", js_func + "\n  </script>")
    with open(path, "w", encoding="utf-8") as f:
        f.write(c_norm)
    print("Updated index.html with clear button and function.")
else:
    print("Could not find old_section in index.html.")
