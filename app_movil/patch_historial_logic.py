import sys, os

with open(r'C:/Users/victo/nuevas_ruletas/app_movil/build_final_v4.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Buscamos la función sincronizarTuAzarAutomatico para que además descargue today_ledger.json
old_sync = """        const resp = await fetch('/live_radar.json?t=' + Date.now());
        if (!resp.ok) throw new Error('No se pudo descargar live_radar.json');
        const liveData = await resp.json();"""

new_sync = """        const resp = await fetch('/live_radar.json?t=' + Date.now());
        if (!resp.ok) throw new Error('No se pudo descargar live_radar.json');
        const liveData = await resp.json();

        // Descargar historial de disparos de hoy
        try {{
          const respLedger = await fetch('/today_ledger.json?t=' + Date.now());
          if (respLedger.ok) {{
            const ledgerData = await respLedger.json();
            const w = JSON.parse(localStorage.getItem('wallet_state_v8')) || {{}};
            w.ledger = ledgerData;
            w.ops_today = ledgerData.length;
            let hits = 0;
            let totInv = 0;
            let totCob = 0;
            let totPnl = 0;
            for (let op of ledgerData) {{
              if (op.condicion && op.condicion.includes('GANADA')) hits++;
              totInv += (op.total_bet || 0);
              totCob += (op.cobrado || 0);
              totPnl += (op.pnl || 0);
            }}
            w.wins_today = hits;
            w.inv_today = totInv;
            w.cob_today = totCob;
            w.pnl_today = totPnl;
            if (ledgerData.length > 0 && ledgerData[ledgerData.length - 1].saldo) {{
              w.bankroll = ledgerData[ledgerData.length - 1].saldo;
            }}
            localStorage.setItem('wallet_state_v8', JSON.stringify(w));
          }}
        }} catch (_eLed) {{
          console.warn('Error cargando today_ledger:', _eLed);
        }}"""

# Y en renderPantalla agregamos el pintado de historial
old_render = """      if (window.lucide) lucide.createIcons();
    }"""

new_render = """      // Renderizar historial de disparos
      const histContainer = document.getElementById('historial-container');
      if (histContainer) {{
        histContainer.innerHTML = '';
        const jugadas = w.ledger || [];
        const countBadge = document.getElementById('txt-historial-count');
        if (countBadge) countBadge.innerText = jugadas.length + (jugadas.length === 1 ? ' Jugada' : ' Jugadas');

        if (jugadas.length === 0) {{
          histContainer.innerHTML = `
            <div class="glass-card rounded-xl p-4 text-center text-slate-500 text-xs">
              Aún no hay disparos ejecutados en la jornada de hoy.
            </div>
          `;
        }} else {{
          jugadas.forEach(j => {{
            const esGanada = j.condicion && j.condicion.includes('GANADA');
            const bgClass = esGanada ? 'border-emerald-500/40 bg-emerald-950/20' : 'border-rose-900/30 bg-rose-950/10';
            const badgeClass = esGanada ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20';
            const pnlStr = (j.pnl >= 0 ? '+' : '') + 'Bs ' + (j.pnl || 0).toLocaleString('es-VE', {{minimumFractionDigits: 2}});

            histContainer.innerHTML += `
              <div class="glass-card rounded-xl p-3 border ${{bgClass}}">
                <div class="flex justify-between items-start mb-1.5">
                  <div class="flex items-center space-x-2">
                    <span class="text-xs font-black text-white">${{j.ruleta}}</span>
                    <span class="text-[10px] text-slate-400 font-mono">${{j.hora}}</span>
                  </div>
                  <span class="px-2 py-0.5 rounded text-[10px] font-black ${{badgeClass}}">${{pnlStr}}</span>
                </div>
                <div class="text-[11px] text-slate-300 mb-1 flex justify-between">
                  <span>Resultado: <b class="text-amber-400">${{j.resultado}}</b></span>
                  <span class="text-slate-500">Inversión: Bs ${{j.total_bet}}</span>
                </div>
                <div class="text-[10px] text-slate-500 truncate">
                  Candidatos: ${{j.candidatos}}
                </div>
              </div>
            `;
          }});
        }}
      }}

      if (window.lucide) lucide.createIcons();
    }}"""

if old_sync in text and old_render in text:
    text = text.replace(old_sync, new_sync)
    text = text.replace(old_render, new_render)
    print("Sincronizacion y renderizado de historial inyectados con exito.")
else:
    print("Fallo coincidencia de bloques:", old_sync in text, old_render in text)

with open(r'C:/Users/victo/nuevas_ruletas/app_movil/build_final_v4.py', 'w', encoding='utf-8') as f:
    f.write(text)
