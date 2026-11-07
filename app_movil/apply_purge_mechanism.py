import sys, json, os

with open(r'C:/Users/victo/nuevas_ruletas/app_movil/build_final_v4.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Purgador automático de memorias anteriores en inicializarStorage
old_init = """    function inicializarStorage() {
      if (!localStorage.getItem('sniper_master_v8')) {
        const initialMap = {};
        for (const [rName, rData] of Object.entries(MASTER_SEED)) {
          const hist = rData.history || [];
          const last = hist.length > 0 ? hist[hist.length - 1] : null;
          const lastStr = last ? ('#' + last.numero + ' ' + (ANIMALES[last.numero] || last.animal) + ' (' + last.hora + ')') : 'Sin datos';
          initialMap[rName] = {
            racha: 0,
            misses: 0,
            is_active: false,
            candidatos: [],
            ultimo_str: lastStr,
            emoji: rData.emoji,
            payout: rData.payout,
            target_streaks: rData.target_streaks
          };
        }
        localStorage.setItem('sniper_master_v8', JSON.stringify(initialMap));
      }
      if (!localStorage.getItem('wallet_state_v8')) {
        const defaultWallet = {
          bankroll: 23200.0,
          pnl_today: -1200.0,
          ops_today: 2,
          wins_today: 0,
          inv_today: 1200.0,
          cob_today: 0.0,
          ledger: []
        };
        localStorage.setItem('wallet_state_v8', JSON.stringify(defaultWallet));
      }
    }"""

# Versión con auto-purga estricta: limpia cualquier versión previa (v1..v8, ruletas_db, state, etc.)
purge_code = """    // MECANISMO DE AUTO-PURGA ESTRICTA CONTRA CONTAMINACION DE MEMORIA
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
          bankroll: 22900.0,
          pnl_today: -1200.0,
          ops_today: 2,
          wins_today: 0,
          inv_today: 1200.0,
          cob_today: 0.0,
          ledger: []
        }};
        localStorage.setItem('wallet_state_v9', JSON.stringify(defaultWallet));
      }}
    }}"""

# Sustituir claves en todo el texto
text = text.replace('sniper_master_v8', 'sniper_master_v9')
text = text.replace('wallet_state_v8', 'wallet_state_v9')

# Localizar la funcion inicializarStorage y sustituirla
import re
text = re.sub(r'function inicializarStorage\(\) \{.*?\n    \}', purge_code, text, flags=re.DOTALL)

with open(r'C:/Users/victo/nuevas_ruletas/app_movil/build_final_v4.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("build_final_v4.py actualizado con purga estricta V9.")
