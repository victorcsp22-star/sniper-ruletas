import sys, json, os

with open(r'C:/Users/victo/nuevas_ruletas/app_movil/static/seed_master.json', encoding='utf-8') as f:
    seed_data = json.load(f)

ANIMALES = {
    '0': 'DELFIN', '00': 'BALLENA', '1': 'CARNERO', '2': 'TORO', '3': 'CIEMPIES', '4': 'ALACRAN',
    '5': 'LEON', '6': 'RANA', '7': 'PERICO', '8': 'RATON', '9': 'AGUILA', '10': 'TIGRE',
    '11': 'GATO', '12': 'CABALLO', '13': 'MONO', '14': 'PALOMA', '15': 'ZORRO', '16': 'OSO',
    '17': 'PAVO', '18': 'BURRO', '19': 'CHIVO', '20': 'COCHINO', '21': 'GALLO', '22': 'CAMELLO',
    '23': 'CEBRA', '24': 'IGUANA', '25': 'GALLINA', '26': 'VACA', '27': 'PERRO', '28': 'ZAMURO',
    '29': 'ELEFANTE', '30': 'CAIMAN', '31': 'LAPA', '32': 'ARDILLA', '33': 'PESCADO', '34': 'VENADO',
    '35': 'JIRAFA', '36': 'CULEBRA', '37': 'AVESTRUZ', '38': 'PANTERA', '39': 'COBRA', '40': 'PUMA',
    '41': 'COLIBRI', '42': 'BUFALO', '43': 'MARIPOSA', '44': 'CHIGUIRE', '45': 'TUCAN', '46': 'PUMA',
    '47': 'PATO', '48': 'FLAMINGO', '49': 'HALCON', '50': 'GAVIOTA', '51': 'PELICANO', '52': 'GARZA',
    '53': 'GAVILAN', '54': 'LECHUZA', '55': 'LOBINA', '56': 'TIBURON', '57': 'CANGREJO', '58': 'DELFIN',
    '59': 'PULPO', '60': 'LANGOSTA', '61': 'CAMARON', '62': 'CACHICAMO', '63': 'CAMELLO', '64': 'OSO HORMIGUERO',
    '65': 'CANGURO', '66': 'JAGUAR', '67': 'LOBO', '68': 'ZORRA', '69': 'CONEJO', '70': 'BISONTE',
    '71': 'GUACHARO', '72': 'GORILA', '73': 'LEOPARDO', '74': 'RINOCERONTE', '75': 'HIPOPOTAMO'
}

html_code = f"""<!DOCTYPE html>
<html lang="es" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <title>Sniper Ruletas | Motor Cuantitativo Autónomo</title>
  <meta name="theme-color" content="#10b981">
  <meta name="mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/lucide@latest"></script>
  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          colors: {{
            brand: {{
              dark: '#070b14',
              card: '#0f172a',
              cardLight: '#1e293b',
              accent: '#10b981',
              accentHover: '#059669',
              warning: '#f59e0b',
              danger: '#ef4444'
            }}
          }}
        }}
      }}
    }}
  </script>
  <style>
    body {{ background-color: #070b14; color: #f8fafc; font-family: system-ui, -apple-system, sans-serif; -webkit-tap-highlight-color: transparent; }}
    .glass-card {{ background: rgba(15, 23, 42, 0.75); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }}
    .pulse-green {{ animation: pulse 2s infinite; }}
    @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.4; }} }}
  </style>
</head>
<body class="min-h-screen flex flex-col pb-24">

  <!-- HEADER -->
  <header class="sticky top-0 z-40 bg-brand-dark/95 backdrop-blur border-b border-slate-800 px-4 py-3">
    <div class="max-w-md mx-auto flex items-center justify-between">
      <div class="flex items-center space-x-2.5">
        <div class="p-2 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
          <i data-lucide="crosshair" class="w-5 h-5 text-emerald-400"></i>
        </div>
        <div>
          <div class="flex items-center space-x-2">
            <h1 class="font-black text-sm tracking-wide text-white uppercase">SNIPER V3 PWA</h1>
            <span class="px-1.5 py-0.5 text-[9px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded">AUTÓNOMO</span>
          </div>
          <p id="reloj-header" class="text-xs text-slate-400 font-mono">--:-- --</p>
        </div>
      </div>
      
      <!-- BOTON ENTRADA RAPIDA -->
      <button onclick="abrirModalEntrada()" class="flex items-center space-x-1.5 bg-amber-500 hover:bg-amber-600 text-slate-950 font-black px-3 py-2 rounded-xl text-xs shadow-lg shadow-amber-500/20 active:scale-95 transition-all">
        <i data-lucide="plus-circle" class="w-4 h-4"></i>
        <span>Anotar Sorteo</span>
      </button>
    </div>
  </header>

  <!-- BANNER CAPITAL Y ESTADISTICAS -->
  <div class="max-w-md mx-auto w-full px-4 pt-4">
    <div class="glass-card rounded-2xl p-4 shadow-xl relative overflow-hidden">
      <div class="flex justify-between items-start mb-2">
        <div>
          <span class="text-[10px] font-bold tracking-wider text-slate-400 uppercase">Saldo en Mesa</span>
          <div class="flex items-baseline space-x-1">
            <span class="text-2xl font-black text-emerald-400" id="txt-saldo">Bs 24,100.00</span>
          </div>
        </div>
        <div class="text-right">
          <span class="text-[10px] font-bold tracking-wider text-slate-400 uppercase">PnL Hoy</span>
          <p class="text-sm font-bold text-emerald-400" id="txt-pnl">+Bs 6,700.00</p>
        </div>
      </div>
      <div class="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800 text-center text-xs">
        <div>
          <span class="text-slate-500 text-[10px] block">Operaciones</span>
          <span class="font-bold text-slate-200" id="txt-ops">14 (3 Hits)</span>
        </div>
        <div>
          <span class="text-slate-500 text-[10px] block">Invertido</span>
          <span class="font-bold text-slate-200" id="txt-inv">Bs 8,300</span>
        </div>
        <div>
          <span class="text-slate-500 text-[10px] block">Cobrado</span>
          <span class="font-bold text-emerald-400" id="txt-cob">Bs 15,000</span>
        </div>
      </div>
    </div>
  </div>

  <!-- SECCION DE ORDENES ACTIVAS (HERO SIGNALS) -->
  <main class="max-w-md mx-auto w-full px-4 mt-4 space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-xs font-black uppercase tracking-wider text-slate-400 flex items-center space-x-2">
        <span class="w-2 h-2 rounded-full bg-emerald-500 pulse-green"></span>
        <span>Disparos Inminentes (Órdenes)</span>
      </h2>
      <span class="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full font-bold" id="txt-cant-ordenes">0 Activas</span>
    </div>

    <!-- CONTENEDOR HERO SEÑALES -->
    <div id="hero-signals-container" class="space-y-3">
      <!-- Renderizado dinámico -->
    </div>

    <!-- RADAR COMPLETO DE LAS 7 RULETAS -->
    <div class="pt-2">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-xs font-black uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
          <i data-lucide="radar" class="w-4 h-4 text-cyan-400"></i>
          <span>Radar de las 7 Ruletas</span>
        </h2>
        <span class="text-[10px] text-slate-500">Apuesta fija Bs 100/ficha</span>
      </div>
      
      <div id="radar-container" class="space-y-2.5">
        <!-- Renderizado dinámico -->
      </div>
    </div>
  </main>

  <!-- MODAL ENTRADA RAPIDA DE SORTEOS -->
  <div id="modal-entrada" class="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 hidden">
    <div class="glass-card w-full max-w-sm rounded-2xl p-5 border border-slate-700 shadow-2xl">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-sm font-black text-white flex items-center space-x-2">
          <i data-lucide="plus-circle" class="w-5 h-5 text-amber-400"></i>
          <span>Anotar Resultado de Sorteo</span>
        </h3>
        <button onclick="cerrarModalEntrada()" class="text-slate-400 hover:text-white p-1">
          <i data-lucide="x" class="w-5 h-5"></i>
        </button>
      </div>

      <div class="space-y-3.5">
        <div>
          <label class="text-[11px] font-bold text-slate-400 block mb-1 uppercase">Ruleta Oficial</label>
          <select id="sel-ruleta" class="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm font-bold text-white focus:outline-none focus:border-emerald-500">
            <option value="Lotto Gato">🐱 Lotto Gato (60x)</option>
            <option value="Loto Chaima">🦜 Loto Chaima (60x)</option>
            <option value="Guacharo Activo">🦇 Guacharo Activo (60x)</option>
            <option value="Ruleta Royal">👑 Ruleta Royal (30x)</option>
            <option value="Gatazo">🐯 Gatazo (60x)</option>
            <option value="Lotto Activo">🦁 Lotto Activo (30x)</option>
            <option value="Monje Millonario">🧘 Monje Millonario (60x)</option>
          </select>
        </div>

        <div>
          <label class="text-[11px] font-bold text-slate-400 block mb-1 uppercase">Hora del Sorteo</label>
          <input type="text" id="in-hora" placeholder="Ej: 9:10 AM" class="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500">
        </div>

        <div>
          <label class="text-[11px] font-bold text-slate-400 block mb-1 uppercase">Número que salió</label>
          <input type="text" id="in-numero" placeholder="Ej: 0, 12, 27" class="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-base font-black text-amber-400 focus:outline-none focus:border-emerald-500">
        </div>

        <button onclick="ejecutarEntradaSorteo()" class="w-full bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-black py-2.5 rounded-xl text-sm shadow-lg shadow-emerald-500/20 active:scale-95 transition-all mt-2">
          Guardar y Recalcular Radar
        </button>
      </div>
    </div>
  </div>

  <!-- SCRIPT CON LOGICA MATEMATICA COMPLETA Y SEED DATA -->
  <script>
    // 1. DICCIONARIO MAESTRO DE ANIMALES
    const ANIMALES = {json.dumps(ANIMALES, ensure_ascii=False)};

    // 2. SEED DATA COMPLETO DE LAS 7 RULETAS
    const SEED_DATA = {json.dumps(seed_data, ensure_ascii=False)};

    // 3. INICIALIZACION DEL STORAGE LOCAL
    function inicializarStorage() {{
      if (!localStorage.getItem('ruletas_db')) {{
        localStorage.setItem('ruletas_db', JSON.stringify(SEED_DATA));
      }}
      if (!localStorage.getItem('wallet_state')) {{
        const defaultWallet = {{
          bankroll: 24100.0,
          pnl_today: 6700.0,
          ops_today: 14,
          wins_today: 3,
          inv_today: 8300.0,
          cob_today: 15000.0,
          ledger: []
        }};
        localStorage.setItem('wallet_state', JSON.stringify(defaultWallet));
      }}
    }}

    // 4. MOTOR MATEMATICO EXACTO (CALCULO DE RACHAS Y CANDIDATOS)
    function calcularRachaYCandidatos(historia, cfg) {{
      if (!historia || historia.length < 20) {{
        return {{ racha: 0, misses: 0, candidatos: [], ultimo_salido: 'Sin datos' }};
      }}
      const lags = cfg.lags;
      const rec_w = cfg.rec_w || 6;
      const target_streaks = cfg.target_streaks || [1];
      const max_lag = Math.max(...lags);
      const min_idx = max_lag + rec_w;
      
      let streak = 0;
      let trigger_misses = 0;
      
      // Simular toda la serie para obtener racha y misses exactos
      for (let i = min_idx; i < historia.length; i++) {{
        const actual = String(historia[i].numero).trim();
        const rec_set = new Set();
        for (let r = 1; r <= rec_w; r++) {{
          rec_set.add(String(historia[i - r].numero).trim());
        }}
        
        const cands_set = new Set();
        for (let l of lags) {{
          const c = String(historia[i - l].numero).trim();
          if (!rec_set.has(c)) {{
            cands_set.add(c);
          }}
        }}
        
        const cands_list = Array.from(cands_set);
        if (cands_list.length > 0) {{
          const hit = cands_set.has(actual);
          if (hit) {{
            streak += 1;
            trigger_misses = 0;
          }} else {{
            streak = 0;
            trigger_misses += 1;
          }}
        }}
      }}
      
      // Candidatos para el PROXIMO disparo (i = historia.length)
      const last_rec_set = new Set();
      for (let r = 1; r <= rec_w; r++) {{
        last_rec_set.add(String(historia[historia.length - r].numero).trim());
      }}
      const proximo_cands = new Set();
      for (let l of lags) {{
        const c = String(historia[historia.length - l].numero).trim();
        if (!last_rec_set.has(c)) {{
          proximo_cands.add(c);
        }}
      }}
      
      const ultimo = historia[historia.length - 1];
      const ultimo_str = '#' + ultimo.numero + ' ' + (ANIMALES[ultimo.numero] || ultimo.animal) + ' (' + ultimo.hora + ')';
      
      return {{
        racha: streak,
        misses: trigger_misses,
        candidatos: Array.from(proximo_cands).sort((a,b) => parseInt(a)-parseInt(b)),
        ultimo_str: ultimo_str
      }};
    }}

    // 5. EVALUACION DEL RADAR Y ORDENES
    function evaluarRadarCompleto() {{
      const db = JSON.parse(localStorage.getItem('ruletas_db'));
      const activeSignals = [];
      const radarItems = [];
      
      for (const [rName, cfg] of Object.entries(db)) {{
        const res = calcularRachaYCandidatos(cfg.history, cfg);
        const enObjetivo = cfg.target_streaks.includes(res.racha);
        
        let conteoStr = '';
        let urgencia = 3;
        let badge = 'Racha ' + res.racha;
        
        if (enObjetivo) {{
          conteoStr = '🚨 ¡DISPARAR AHORA! (' + res.misses + ')';
          urgencia = 1;
          badge = '🔥 Racha ' + res.racha + ' (Objetivo)';
          
          activeSignals.push({{
            ruleta: rName,
            emoji: cfg.emoji,
            payout: cfg.payout,
            candidatos: res.candidatos,
            ultimo_str: res.ultimo_str,
            fichas: res.candidatos.length,
            costo: res.candidatos.length * 100.0,
            premio: cfg.payout * 100.0
          }});
        }} else if (res.racha === 0) {{
          conteoStr = '⚠️ Falta 1 fallo';
          urgencia = 2;
          badge = '🟢 Racha 0';
        }} else {{
          conteoStr = '💤 Espera reinicio (' + res.racha + ')';
          urgencia = 3;
          badge = '🟡 Racha ' + res.racha;
        }}
        
        radarItems.push({{
          ruleta: rName,
          emoji: cfg.emoji,
          payout: cfg.payout,
          badge: badge,
          conteoStr: conteoStr,
          urgencia: urgencia,
          ultimo_str: res.ultimo_str
        }});
      }}
      
      // Ordenar radar por urgencia
      radarItems.sort((a,b) => a.urgencia - b.urgencia);
      
      renderPantalla(activeSignals, radarItems);
    }}

    // 6. RENDERIZAR EN PANTALLA
    function renderPantalla(activeSignals, radarItems) {{
      // Wallet
      const w = JSON.parse(localStorage.getItem('wallet_state'));
      document.getElementById('txt-saldo').innerText = 'Bs ' + w.bankroll.toLocaleString('es-VE', {{minimumFractionDigits: 2}});
      document.getElementById('txt-pnl').innerText = (w.pnl_today >= 0 ? '+' : '') + 'Bs ' + w.pnl_today.toLocaleString('es-VE', {{minimumFractionDigits: 2}});
      document.getElementById('txt-ops').innerText = w.ops_today + ' (' + w.wins_today + ' Hits)';
      document.getElementById('txt-inv').innerText = 'Bs ' + w.inv_today.toLocaleString('es-VE');
      document.getElementById('txt-cob').innerText = 'Bs ' + w.cob_today.toLocaleString('es-VE');
      
      // Hero Signals
      const sigContainer = document.getElementById('hero-signals-container');
      sigContainer.innerHTML = '';
      document.getElementById('txt-cant-ordenes').innerText = activeSignals.length + ' Activas';
      
      if (activeSignals.length === 0) {{
        sigContainer.innerHTML = `
          <div class="glass-card rounded-2xl p-5 text-center text-slate-400">
            <i data-lucide="shield-check" class="w-8 h-8 mx-auto text-emerald-400 mb-2 opacity-60"></i>
            <p class="text-xs font-bold">Sin disparos inminentes en este momento.</p>
            <p class="text-[10px] text-slate-500 mt-0.5">El radar está monitoreando los próximos sorteos.</p>
          </div>
        `;
      }} else {{
        activeSignals.forEach(sig => {{
          const candsHtml = sig.candidatos.map(c => `
            <span class="px-2.5 py-1 bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 font-black rounded-lg text-xs">
              #${{c}} ${{ANIMALES[c] || ''}}
            </span>
          `).join('');
          
          sigContainer.innerHTML += `
            <div class="bg-gradient-to-br from-emerald-950/40 via-slate-900 to-slate-900 border-2 border-emerald-500/50 rounded-2xl p-4 shadow-xl shadow-emerald-950/30">
              <div class="flex justify-between items-start mb-2.5">
                <div class="flex items-center space-x-2">
                  <span class="text-2xl">${{sig.emoji}}</span>
                  <div>
                    <h3 class="font-black text-sm text-white">${{sig.ruleta}}</h3>
                    <span class="text-[10px] text-emerald-400 font-bold uppercase tracking-wider">🚨 ¡DISPARAR AHORA!</span>
                  </div>
                </div>
                <div class="text-right">
                  <span class="text-xs font-black text-emerald-400">${{sig.payout}}x Payout</span>
                  <p class="text-[10px] text-slate-400">Premio: Bs ${{sig.premio.toLocaleString()}}</p>
                </div>
              </div>
              
              <div class="mb-3">
                <span class="text-[10px] font-bold text-slate-400 block mb-1 uppercase">Candidatos Oficiales (${{sig.fichas}} fichas - Bs ${{sig.costo}}):</span>
                <div class="flex flex-wrap gap-1.5">
                  ${{candsHtml}}
                </div>
              </div>
              
              <div class="text-[10px] text-slate-400 border-t border-slate-800/80 pt-2 flex justify-between">
                <span>Último: ${{sig.ultimo_str}}</span>
                <span class="font-bold text-slate-300">Frecuencia P:10/10</span>
              </div>
            </div>
          `;
        }});
      }}
      
      // Radar items
      const radarContainer = document.getElementById('radar-container');
      radarContainer.innerHTML = '';
      radarItems.forEach(item => {{
        let statusClass = 'text-slate-400';
        if (item.urgencia === 1) statusClass = 'text-emerald-400 font-bold';
        else if (item.urgencia === 2) statusClass = 'text-amber-400 font-bold';
        
        radarContainer.innerHTML += `
          <div class="glass-card rounded-xl p-3 flex items-center justify-between border border-slate-800">
            <div class="flex items-center space-x-2.5">
              <span class="text-xl">${{item.emoji}}</span>
              <div>
                <h4 class="text-xs font-bold text-white">${{item.ruleta}}</h4>
                <p class="text-[10px] text-slate-400">${{item.ultimo_str}}</p>
              </div>
            </div>
            <div class="text-right">
              <span class="text-xs ${{statusClass}} block">${{item.conteoStr}}</span>
              <span class="text-[9px] text-slate-500 font-mono">${{item.payout}}x | ${{item.badge}}</span>
            </div>
          </div>
        `;
      }});
      
      if (window.lucide) lucide.createIcons();
    }}

    // 7. ENTRADA MANUAL DE RESULTADO
    function abrirModalEntrada() {{
      document.getElementById('modal-entrada').classList.remove('hidden');
    }}
    function cerrarModalEntrada() {{
      document.getElementById('modal-entrada').classList.add('hidden');
    }}
    
    function ejecutarEntradaSorteo() {{
      const rName = document.getElementById('sel-ruleta').value;
      const hora = document.getElementById('in-hora').value.trim() || 'Manual';
      const num = document.getElementById('in-numero').value.trim();
      
      if (!num) {{
        alert('Escribe el número que salió.');
        return;
      }}
      
      const db = JSON.parse(localStorage.getItem('ruletas_db'));
      if (!db[rName]) return;
      
      // Evaluar si habia disparo activo en esta ruleta para liquidar apuesta
      const resPrev = calcularRachaYCandidatos(db[rName].history, db[rName]);
      const w = JSON.parse(localStorage.getItem('wallet_state'));
      
      if (db[rName].target_streaks.includes(resPrev.racha)) {{
        const betCost = resPrev.candidatos.length * 100.0;
        const hit = resPrev.candidatos.includes(num);
        const winAmount = hit ? (db[rName].payout * 100.0) : 0.0;
        const netPnl = winAmount - betCost;
        
        w.bankroll += netPnl;
        w.pnl_today += netPnl;
        w.ops_today += 1;
        w.inv_today += betCost;
        w.cob_today += winAmount;
        if (hit) w.wins_today += 1;
        
        w.ledger.unshift({{
          hora: hora,
          ruleta: rName,
          cands: resPrev.candidatos,
          numero: num,
          animal: ANIMALES[num] || 'ANIMAL',
          hit: hit,
          netPnl: netPnl
        }});
        localStorage.setItem('wallet_state', JSON.stringify(w));
      }}
      
      // Anexar nuevo sorteo
      db[rName].history.push({{
        fecha: new Date().toISOString().split('T')[0],
        hora: hora,
        numero: num,
        animal: ANIMALES[num] || 'ANIMAL'
      }});
      localStorage.setItem('ruletas_db', JSON.stringify(db));
      
      cerrarModalEntrada();
      document.getElementById('in-numero').value = '';
      evaluarRadarCompleto();
    }}

    // 8. RELOJ Y ACTUALIZACION
    function actualizarReloj() {{
      const ahora = new Date();
      document.getElementById('reloj-header').innerText = ahora.toLocaleTimeString('es-VE', {{hour: '2-digit', minute:'2-digit', second:'2-digit', hour12: true}});
    }}

    // ARRANQUE
    window.addEventListener('DOMContentLoaded', () => {{
      inicializarStorage();
      evaluarRadarCompleto();
      actualizarReloj();
      setInterval(actualizarReloj, 1000);
    }});
  </script>
</body>
</html>
"""

with open(r'C:/Users/victo/nuevas_ruletas/app_movil/static/app_autonoma.html', 'w', encoding='utf-8') as f:
    f.write(html_code)

print('app_autonoma.html creado exitosamente con longitud:', len(html_code))
