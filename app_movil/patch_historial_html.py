import sys, os

with open(r'C:/Users/victo/nuevas_ruletas/app_movil/build_final_v4.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = """      <div id="radar-container" class="space-y-2.5">
        <!-- Renderizado dinámico -->
      </div>
    </div>
  </main>"""

replacement = """      <div id="radar-container" class="space-y-2.5">
        <!-- Renderizado dinámico -->
      </div>
    </div>

    <!-- SECCION HISTORIAL DE DISPAROS DE HOY -->
    <div class="pt-4">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-xs font-black uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
          <i data-lucide="history" class="w-4 h-4 text-emerald-400"></i>
          <span>Disparos Ejecutados Hoy (Historial)</span>
        </h2>
        <span class="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full font-bold" id="txt-historial-count">0 Jugadas</span>
      </div>
      
      <div id="historial-container" class="space-y-2">
        <!-- Renderizado dinámico de jugadas -->
      </div>
    </div>
  </main>"""

if target in text:
    text = text.replace(target, replacement)
    print("Seccion HTML de historial reemplazada con exito.")
else:
    print("No se encontro target.")

with open(r'C:/Users/victo/nuevas_ruletas/app_movil/build_final_v4.py', 'w', encoding='utf-8') as f:
    f.write(text)
