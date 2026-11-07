import re

index_path = r"C:\Users\victo\nuevas_ruletas\app_movil\static\index.html"
with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

# Insertar el boton de Entrada Rapida junto al de Sincronizar en el header
header_buttons_old = '''      <!-- Botn de Sincronizacin Inmediata -->
      <button id="btn-sync" onclick="syncTuAzar()" class="flex items-center space-x-1.5 bg-brand-cardLight active:bg-emerald-600 text-slate-200 active:text-white px-3 py-1.5 rounded-lg border border-slate-700 text-xs font-semibold shadow-sm transition-all">
        <i id="sync-icon" data-lucide="refresh-cw" class="w-3.5 h-3.5"></i>
        <span id="sync-text">Sincronizar</span>
      </button>'''

header_buttons_new = '''      <div class="flex items-center space-x-1.5">
        <!-- Botón Entrada Rápida Offline (Cero Dependencia de Internet) -->
        <button onclick="toggleModalManual()" class="flex items-center space-x-1 bg-amber-500/20 active:bg-amber-500 text-amber-300 active:text-slate-950 px-2.5 py-1.5 rounded-lg border border-amber-500/40 text-xs font-bold shadow-sm transition">
          <i data-lucide="plus-circle" class="w-3.5 h-3.5"></i>
          <span>Entrada Offline</span>
        </button>

        <!-- Botón de Sincronización Inmediata -->
        <button id="btn-sync" onclick="syncTuAzar()" class="flex items-center space-x-1.5 bg-brand-cardLight active:bg-emerald-600 text-slate-200 active:text-white px-2.5 py-1.5 rounded-lg border border-slate-700 text-xs font-semibold shadow-sm transition-all">
          <i id="sync-icon" data-lucide="refresh-cw" class="w-3.5 h-3.5"></i>
          <span id="sync-text">TuAzar</span>
        </button>
      </div>'''

# Reemplazar con regex flexible para evitar problemas de encoding
pattern_header = r'<button id="btn-sync".*?</button>'
html = re.sub(pattern_header, header_buttons_new, html, flags=re.DOTALL)

# Insertar Modal de Entrada Offline antes de </body>
modal_offline = '''
  <!-- Modal de Entrada Rápida Offline (Ingreso manual sin internet) -->
  <div id="modal-manual" class="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm hidden flex items-center justify-center p-4">
    <div class="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-sm p-5 space-y-4 shadow-2xl">
      <div class="flex items-center justify-between border-b border-slate-800 pb-3">
        <div class="flex items-center space-x-2">
          <span class="text-amber-400 font-bold text-sm">⚡ Entrada Rápida Offline</span>
        </div>
        <button onclick="toggleModalManual()" class="text-slate-400 hover:text-white text-lg font-bold">✕</button>
      </div>

      <div class="space-y-3">
        <div>
          <label class="text-[11px] text-slate-400 block mb-1 font-semibold uppercase">1. Selecciona la Ruleta:</label>
          <select id="manual-ruleta" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-400">
            <option value="Lotto Gato">🐱 Lotto Gato</option>
            <option value="Loto Chaima">🏹 Loto Chaima</option>
            <option value="Guacharo Activo">🦇 Guacharo Activo</option>
            <option value="Lotto Activo">🦁 Lotto Activo</option>
            <option value="Ruleta Royal">👑 Ruleta Royal</option>
            <option value="Mega Animal 40">🦏 Mega Animal 40</option>
            <option value="Gatazo">🐯 Gatazo</option>
            <option value="Monje Millonario">🧘‍♂️ Monje Millonario</option>
            <option value="Granja Millonaria - Granjazo">🚜 Granja Millonaria - Granjazo</option>
          </select>
        </div>

        <div>
          <label class="text-[11px] text-slate-400 block mb-1 font-semibold uppercase">2. Número Salido:</label>
          <input type="text" id="manual-num" placeholder="Ej: 75, 08, 4" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-400 font-mono font-bold">
        </div>

        <div>
          <label class="text-[11px] text-slate-400 block mb-1 font-semibold uppercase">3. Nombre del Animal (Opcional):</label>
          <input type="text" id="manual-anim" placeholder="Ej: CODORNIZ, CABALLO..." class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-400 uppercase">
        </div>
      </div>

      <div class="pt-2">
        <button onclick="submitManualDraw()" class="w-full bg-emerald-500 hover:bg-emerald-400 active:bg-emerald-600 text-slate-950 font-bold py-2.5 rounded-xl text-xs transition shadow-lg">
          ⚡ Calcular Disparo Instantáneo (0.001s)
        </button>
      </div>
    </div>
  </div>

  <script>
    function toggleModalManual() {
      const m = document.getElementById('modal-manual');
      m.classList.toggle('hidden');
    }

    async function submitManualDraw() {
      const rul = document.getElementById('manual-ruleta').value;
      const num = document.getElementById('manual-num').value.trim();
      const anim = document.getElementById('manual-anim').value.trim();

      if (!num) {
        alert('Por favor escribe el número que salió.');
        return;
      }

      try {
        const resp = await fetch('/api/ingresar_sorteo', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ ruleta: rul, numero: num, animal: anim })
        });
        const res = await resp.json();
        if (res.status === 'ok') {
          toggleModalManual();
          document.getElementById('manual-num').value = '';
          document.getElementById('manual-anim').value = '';
          loadTacticalStatus();
        } else {
          alert('Error: ' + res.message);
        }
      } catch (err) {
        alert('Error al registrar sorteo offline: ' + err);
      }
    }
  </script>
'''

html = html.replace('</body>', modal_offline + '\n</body>')

with open(index_path, "w", encoding="utf-8") as f:
    f.write(html)

print("index.html actualizado exitosamente con Entrada Offline.")
