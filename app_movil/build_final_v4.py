import sys, json, os
sys.path.append(r'C:/Users/victo/nuevas_ruletas')
import pandas as pd
from app_movil.server_zero_dep import RULETAS, read_csv_series

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

master_database = {}
for r_name, cfg in RULETAS.items():
    rows = read_csv_series(cfg['file'])[-200:]
    master_database[r_name] = {
        'title': cfg['title'],
        'emoji': cfg['emoji'],
        'payout': cfg['payout'],
        'target_streaks': cfg.get('target_streaks', [1]),
        'lags': cfg['lags'],
        'rec_w': cfg['rec_w'],
        'anti_clustering': cfg['anti_clustering'],
        'blacklist': cfg['blacklist'],
        'history': rows
    }

html_code = f"""<!DOCTYPE html>
<html lang="es" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <title>Sniper Ruletas | Cartera Táctica</title>
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
      
      <!-- BOTONES ACCION -->
      <div class="flex items-center space-x-2">
        <button id="btn-sync" onclick="sincronizarTuAzarAutomatico()" title="Sincronizar TuAzar en Vivo" class="p-2 bg-slate-800 hover:bg-slate-700 text-emerald-400 rounded-xl text-xs border border-slate-700 flex items-center space-x-1">
          <i data-lucide="refresh-cw" class="w-4 h-4"></i>
        </button>
        <button onclick="abrirModalEntrada()" class="flex items-center space-x-1.5 bg-amber-500 hover:bg-amber-600 text-slate-950 font-black px-3 py-2 rounded-xl text-xs shadow-lg shadow-amber-500/20 active:scale-95 transition-all">
          <i data-lucide="plus-circle" class="w-4 h-4"></i>
          <span>Anotar Sorteo</span>
        </button>
      </div>
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
      <span class="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full font-bold" id="txt-cant-ordenes">1 Activa</span>
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

  <!-- SCRIPT INSTITUCIONAL -->
  <script>
    const ANIMALES = {json.dumps(ANIMALES, ensure_ascii=False)};
    const MASTER_SEED = {json.dumps(master_database, ensure_ascii=False)};

        // MECANISMO DE AUTO-PURGA ESTRICTA CONTRA CONTAMINACION DE MEMORIA
    function purgarMemoriasAntiguas() {{
      const clavesValidas = ['sniper_master_v9', 'wallet_state_v9'];
      for (let i = localStorage.length - 1; i >= 0; i--) {{
        const key = localStorage.key(i);
        if (!clavesValidas.includes(key)) {{
          console.warn('Purgando memoria contaminada:', key);
          localStorage.removeItem(key);
        }}
      }}
    }}

    function inicializarStorage() {{
      purgarMemoriasAntiguas();

      if (!localStorage.getItem('sniper_master_v9')) {{
        const initialMap = {{}};
        for (const [rName, rData] of Object.entries(MASTER_SEED)) {{
          const hist = rData.history || [];
          const last = hist.length > 0 ? hist[hist.length - 1] : null;
          const lastStr = last ? ('#' + last.numero + ' ' + (ANIMALES[last.numero] || last.animal) + ' (' + last.hora + ')') : 'Sin datos';
          initialMap[rName] = {{
            racha: 0,
            misses: 0,
            is_active: false,
            candidatos: [],
            ultimo_str: lastStr,
            emoji: rData.emoji,
            payout: rData.payout,
            target_streaks: rData.target_streaks
          }};
        }}
        localStorage.setItem('sniper_master_v9', JSON.stringify(initialMap));
      }}
      if (!localStorage.getItem('wallet_state_v9')) {{
        const defaultWallet = {{
          bankroll: 22100.0,
          pnl_today: -2000.0,
          ops_today: 3,
          wins_today: 0,
          inv_today: 2000.0,
          cob_today: 0.0,
          ledger: []
        }};
        localStorage.setItem('wallet_state_v9', JSON.stringify(defaultWallet));
      }}
    }}

        async function sincronizarTuAzarAutomatico() {{
      const btnSync = document.getElementById('btn-sync');
      if (btnSync) btnSync.classList.add('animate-spin');
      
      try {{
        const resp = await fetch('/live_radar.json?t=' + Date.now());
        if (!resp.ok) throw new Error('No se pudo descargar live_radar.json');
        const liveData = await resp.json();

        // Descargar historial de disparos de hoy
        try {{
          const respLedger = await fetch('/today_ledger.json?t=' + Date.now());
          if (respLedger.ok) {{
            const ledgerData = await respLedger.json();
            const w = JSON.parse(localStorage.getItem('wallet_state_v9')) || {{}};
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
            localStorage.setItem('wallet_state_v9', JSON.stringify(w));
          }}
        }} catch (_eLed) {{
          console.warn('Error cargando today_ledger:', _eLed);
        }}

        const db = JSON.parse(localStorage.getItem('sniper_master_v9')) || {{}};
        for (const [rName, rInfo] of Object.entries(liveData)) {{
          if (!db[rName]) db[rName] = {{}};
          db[rName].racha = rInfo.racha;
          db[rName].misses = rInfo.misses;
          db[rName].is_active = rInfo.is_active;
          db[rName].candidatos = rInfo.candidatos.map(c => c.numero);
          db[rName].ultimo_str = rInfo.ultimo_str;
          db[rName].emoji = rInfo.emoji;
          db[rName].payout = rInfo.payout;
          db[rName].target_streaks = rInfo.target_streaks;
        }}

        localStorage.setItem('sniper_master_v9', JSON.stringify(db));
        evaluarYRenderizar();
      }} catch (err) {{
        console.warn('Error en auto-sync:', err);
      }} finally {{
        if (btnSync) btnSync.classList.remove('animate-spin');
      }}
    }}

    function reiniciarEstadoOficial() {{
      sincronizarTuAzarAutomatico();
    }}

    // MOTOR EXACTO DE PYTHON REPRODUCIDO EN JAVASCRIPT
    function calcularRachaYCandidatosInstitucional(rows, cfg) {{
      if (!rows || rows.length < 40) return {{ racha: 0, misses: 0, candidatos: [], ultimo_str: 'Sin datos', is_anti_blocked: false }};
      
      const nums = rows.map(r => String(r.numero).trim());
      const dates = rows.map(r => String(r.fecha).trim());
      const lags = cfg.lags;
      const rec_w = cfg.rec_w;
      const use_anti = Boolean(cfg.anti_clustering);
      const blacklist = new Set(cfg.blacklist || []);
      const target_streaks = cfg.target_streaks || [1];

      let streak = 0;
      let trigger_misses = 0;
      let cur_d = null;
      let seen_today = new Set();
      let prev_was_repeat = false;

      const max_l = Math.max(...lags);
      const min_k = Math.max(max_l, rec_w) + 1;

      for (let i = min_k; i < nums.length; i++) {{
        const actual = nums[i];
        const d = dates[i];

        if (d !== cur_d) {{
          cur_d = d;
          seen_today = new Set();
          prev_was_repeat = false;
        }}

        const rec_set = new Set(nums.slice(i - rec_w, i));
        const raw_cands = [];
        for (let l of lags) {{
          if (i - l >= 0) raw_cands.push(nums[i - l]);
        }}

        // Filtrar recencia y blacklist
        const cands_set = new Set();
        for (let c of raw_cands) {{
          if (!rec_set.has(c) && !blacklist.has(c)) {{
            cands_set.add(c);
          }}
        }}

        const skip_anti = (use_anti && prev_was_repeat);
        const has_cands = (cands_set.size > 0);

        if (has_cands && !skip_anti) {{
          const hit = cands_set.has(actual);
          if (target_streaks.includes(streak)) {{
            trigger_misses = hit ? 0 : (trigger_misses + 1);
          }}
          streak = hit ? 0 : (streak + 1);
        }} else if (has_cands && skip_anti) {{
          const hit = cands_set.has(actual);
          streak = hit ? 0 : (streak + 1);
          if (target_streaks.includes(streak)) {{
            trigger_misses += 1;
          }}
        }}

        const is_rep = seen_today.has(actual);
        seen_today.add(actual);
        prev_was_repeat = is_rep;
      }}

      // Determinar candidatos para el PRÓXIMO sorteo
      const rec_set_now = new Set(nums.slice(nums.length - rec_w));
      const raw_now = [];
      for (let l of lags) {{
        if (nums.length >= l) raw_now.push(nums[nums.length - l]);
      }}

      const proximo_cands_set = new Set();
      for (let c of raw_now) {{
        if (!rec_set_now.has(c) && !blacklist.has(c)) {{
          proximo_cands_set.add(c);
        }}
      }}

      // Comprobar AntiCluster hoy
      const last_date = dates[dates.length - 1] || '';
      const day_nums = [];
      for (let j = 0; j < nums.length; j++) {{
        if (dates[j] === last_date) day_nums.push(nums[j]);
      }}
      const is_anti_blocked = Boolean(use_anti && day_nums.length >= 2 && day_nums.slice(0, -1).includes(day_nums[day_nums.length - 1]));

      let final_cands = Array.from(proximo_cands_set).sort((a,b) => parseInt(a) - parseInt(b));
      if (is_anti_blocked) final_cands = [];

      const last_row = rows[rows.length - 1];
      const last_str = '#' + last_row.numero + ' ' + (ANIMALES[last_row.numero] || last_row.animal || 'ANIMAL') + ' (' + last_row.hora + ')';

      return {{
        racha: streak,
        misses: trigger_misses,
        candidatos: final_cands,
        ultimo_str: last_str,
        is_anti_blocked: is_anti_blocked
      }};
    }}

    function evaluarYRenderizar() {{
      const masterDb = JSON.parse(localStorage.getItem('sniper_master_v9')) || {{}};
      const activeSignals = [];
      const radarItems = [];

      for (const [rName, rData] of Object.entries(masterDb)) {{
        const racha = rData.racha !== undefined ? rData.racha : 0;
        const misses = rData.misses !== undefined ? rData.misses : 0;
        const enObjetivo = Boolean(rData.is_active);
        const cands = rData.candidatos || [];
        const ultimoStr = rData.ultimo_str || 'Sin datos';

        let conteoStr = '';
        let urgencia = 3;
        let badge = 'Racha ' + racha;

        if (enObjetivo && cands.length > 0) {{
          conteoStr = '🚨 ¡DISPARAR AHORA! (' + misses + ')';
          urgencia = 1;
          badge = '🔥 Racha ' + racha + ' (Objetivo)';

          activeSignals.push({{
            ruleta: rName,
            emoji: rData.emoji || '🎯',
            payout: rData.payout || 60.0,
            candidatos: cands,
            ultimo_str: ultimoStr,
            fichas: cands.length,
            costo: cands.length * 100.0,
            premio: (rData.payout || 60.0) * 100.0
          }});
        }} else if (racha === 0) {{
          conteoStr = '⚠️ Falta 1 fallo';
          urgencia = 2;
          badge = '🟢 Racha 0';
        }} else {{
          conteoStr = '💤 Espera reinicio (' + racha + ')';
          urgencia = 3;
          badge = '🟡 Racha ' + racha;
        }}

        radarItems.push({{
          ruleta: rName,
          emoji: rData.emoji || '🎯',
          payout: rData.payout || 60.0,
          badge: badge,
          conteoStr: conteoStr,
          urgencia: urgencia,
          ultimo_str: ultimoStr
        }});
      }}

      radarItems.sort((a,b) => a.urgencia - b.urgencia);
      renderPantalla(activeSignals, radarItems);
    }}

    function renderPantalla(activeSignals, radarItems) {{
      const w = JSON.parse(localStorage.getItem('wallet_state_v9'));
      document.getElementById('txt-saldo').innerText = 'Bs ' + w.bankroll.toLocaleString('es-VE', {{minimumFractionDigits: 2}});
      document.getElementById('txt-pnl').innerText = (w.pnl_today >= 0 ? '+' : '') + 'Bs ' + w.pnl_today.toLocaleString('es-VE', {{minimumFractionDigits: 2}});
      document.getElementById('txt-ops').innerText = w.ops_today + ' (' + w.wins_today + ' Hits)';
      document.getElementById('txt-inv').innerText = 'Bs ' + w.inv_today.toLocaleString('es-VE');
      document.getElementById('txt-cob').innerText = 'Bs ' + w.cob_today.toLocaleString('es-VE');

      const sigContainer = document.getElementById('hero-signals-container');
      sigContainer.innerHTML = '';
      document.getElementById('txt-cant-ordenes').innerText = activeSignals.length + (activeSignals.length === 1 ? ' Activa' : ' Activas');

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

      // Renderizar historial de disparos
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
    }}

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

      const db = JSON.parse(localStorage.getItem('sniper_master_v9'));
      if (!db[rName]) return;

      const cfg = db[rName];
      const prevCalc = calcularRachaYCandidatosInstitucional(cfg.history, cfg);
      const w = JSON.parse(localStorage.getItem('wallet_state_v9'));

      // Si habia disparo activo en esta ruleta, liquidar apuesta
      if (cfg.target_streaks.includes(prevCalc.racha) && !prevCalc.is_anti_blocked && prevCalc.candidatos.length > 0) {{
        const betCost = prevCalc.candidatos.length * 100.0;
        const hit = prevCalc.candidatos.includes(num);
        const winAmount = hit ? (cfg.payout * 100.0) : 0.0;
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
          cands: prevCalc.candidatos,
          numero: num,
          animal: ANIMALES[num] || 'ANIMAL',
          hit: hit,
          netPnl: netPnl
        }});
        localStorage.setItem('wallet_state_v9', JSON.stringify(w));
      }}

      // Insertar nuevo sorteo en el historial local
      const todayStr = new Date().toISOString().split('T')[0];
      cfg.history.push({{
        fecha: todayStr,
        hora: hora,
        numero: num,
        animal: ANIMALES[num] || 'ANIMAL'
      }});
      localStorage.setItem('sniper_master_v9', JSON.stringify(db));

      cerrarModalEntrada();
      document.getElementById('in-numero').value = '';
      evaluarYRenderizar();
    }}

    function actualizarReloj() {{
      const ahora = new Date();
      document.getElementById('reloj-header').innerText = ahora.toLocaleTimeString('es-VE', {{hour: '2-digit', minute:'2-digit', second:'2-digit', hour12: true}});
    }}

    window.addEventListener('DOMContentLoaded', () => {{
      inicializarStorage();
      evaluarYRenderizar();
      actualizarReloj();
      setInterval(actualizarReloj, 1000);
      // Auto-sincronizar con TuAzar al abrir la app y cada 60 segundos
      sincronizarTuAzarAutomatico();
      setInterval(sincronizarTuAzarAutomatico, 60000);
    }});
  </script>
</body>
</html>
"""

with open(r'C:/Users/victo/nuevas_ruletas/app_movil/static/index.html', 'w', encoding='utf-8') as f:
    f.write(html_code)

print('static/index.html generado exitosamente con el motor de réplica exacta.')
