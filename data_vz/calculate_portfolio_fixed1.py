import sys
import pandas as pd
from live_production_tracker import PORTFOLIOS_CONFIG

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def analyze_portfolio(pkey, title, start_date=None):
    cfg = PORTFOLIOS_CONFIG[pkey]
    tot_opps = 0
    tot_draws_played = 0
    tot_animals_bet = 0
    tot_wins = 0
    tot_invested = 0.0
    tot_collected = 0.0
    
    ruleta_summaries = []
    
    for r_name, r_cfg in cfg["ruletas"].items():
        df = pd.read_csv(r_cfg["file"], dtype={"numero": str})
        df["numero"] = df["numero"].astype(str).str.strip()
        df["sort_dt"] = pd.to_datetime(df["fecha"] + " " + df["hora"], format="%Y-%m-%d %I:%M %p", errors="coerce")
        df = df.sort_values(by="sort_dt").reset_index(drop=True)
        
        lags = r_cfg["lags"]
        payout = r_cfg["payout"]
        nums = df["numero"].tolist()
        
        streak = 0
        r_opps = 0
        r_draws = 0
        r_animals = 0
        r_wins = 0
        
        for i in range(max(lags) + 6, len(nums)):
            fecha = df.iloc[i]["fecha"]
            if start_date and fecha < start_date:
                # Solo actualizar racha previa para continuidad exacta
                actual = nums[i]
                rec6 = set(nums[i-6:i])
                cands = list({nums[i-l] for l in lags} - rec6)
                if cands:
                    hit = (actual in cands)
                    if hit:
                        streak = 0
                    else:
                        streak += 1
                continue
                
            actual = nums[i]
            rec6 = set(nums[i-6:i])
            cands = list({nums[i-l] for l in lags} - rec6)
            if cands:
                cost = len(cands)
                hit = (actual in cands)
                r_opps += 1
                
                if streak == 1:
                    r_draws += 1
                    r_animals += cost
                    if hit:
                        r_wins += 1
                
                if hit:
                    streak = 0
                else:
                    streak += 1
                    
        r_loss = r_draws - r_wins
        r_wr = (r_wins / r_draws * 100.0) if r_draws > 0 else 0.0
        r_inv = r_animals * 1.0 # $1 por animal
        r_cob = r_wins * payout * 1.0
        r_pnl = r_cob - r_inv
        r_roi = (r_pnl / r_inv * 100.0) if r_inv > 0 else 0.0
        
        tot_opps += r_opps
        tot_draws_played += r_draws
        tot_animals_bet += r_animals
        tot_wins += r_wins
        tot_invested += r_inv
        tot_collected += r_cob
        
        ruleta_summaries.append({
            "Ruleta": f"{r_cfg['emoji']} {r_name}",
            "Payout": f"{payout:.0f}x",
            "Sorteos Jugados": r_draws,
            "Animales Apostados": r_animals,
            "Prom. Animales/Sorteo": f"{r_animals/r_draws:.2f}" if r_draws > 0 else "0",
            "Ganadas": r_wins,
            "Perdidas": r_loss,
            "Win Rate": f"{r_wr:.2f}%",
            "Total Invertido": f"${r_inv:,.2f}",
            "Total Cobrado": f"${r_cob:,.2f}",
            "PnL Neto": f"{'+' if r_pnl>=0 else ''}${r_pnl:,.2f}",
            "ROI": f"{r_roi:+.1f}%"
        })
        
    df_s = pd.DataFrame(ruleta_summaries)
    
    tot_loss = tot_draws_played - tot_wins
    tot_wr = (tot_wins / tot_draws_played * 100.0) if tot_draws_played > 0 else 0.0
    tot_pnl = tot_collected - tot_invested
    tot_roi = (tot_pnl / tot_invested * 100.0) if tot_invested > 0 else 0.0
    
    print("=" * 95)
    print(f" {title}")
    print("=" * 95)
    print(df_s.to_string(index=False))
    print("-" * 95)
    print(f" TOTALES CONSOLIDADOS:")
    print(f"  - Sorteos Jugados (Oportunidades donde invirtió): {tot_draws_played:,} sorteos")
    print(f"  - Total Animales Apostados ($1.00 USD c/u):        {tot_animals_bet:,} fichas (promedio {tot_animals_bet/tot_draws_played:.2f} por sorteo)")
    print(f"  - 🟢 Sorteos Ganados:                              {tot_wins:,} aciertos ({tot_wr:.2f}% Win Rate)")
    print(f"  - 🔴 Sorteos Perdidos:                             {tot_loss:,} fallos ({100 - tot_wr:.2f}%)")
    print(f"  - Total Invertido (Stakes de $1):                  ${tot_invested:,.2f} USD")
    print(f"  - Total Pagado / Cobrado:                          ${tot_collected:,.2f} USD")
    print(f"  - Beneficio Neto (PnL):                            {'+' if tot_pnl>=0 else ''}${tot_pnl:,.2f} USD")
    print(f"  - Rentabilidad Neta (ROI):                         {'+' if tot_roi>=0 else ''}{tot_roi:.2f}%")
    print("=" * 95 + "\n")
    
    return {
        "draws": tot_draws_played,
        "animals": tot_animals_bet,
        "wins": tot_wins,
        "loss": tot_loss,
        "invested": tot_invested,
        "collected": tot_collected,
        "pnl": tot_pnl
    }

# 1. Backtest Histórico Completo 2 Años - Venezuela
vz_2y = analyze_portfolio("venezuela", "🇻🇪 CARTERA VENEZUELA (5 RULETAS) - HISTÓRICO COMPLETO 2 AÑOS (2024-2026)")

# 2. Último Mes Auditado - Venezuela
vz_1m = analyze_portfolio("venezuela", "🇻🇪 CARTERA VENEZUELA (5 RULETAS) - ÚLTIMO MES AUDITADO (14-SEP AL 15-OCT-2026)", start_date="2026-09-14")

# 3. Backtest Histórico Completo 2 Años - Brasil
br_2y = analyze_portfolio("brasil", "🇧🇷 CARTERA BRASIL (2 RULETAS) - HISTÓRICO COMPLETO 2 AÑOS (2024-2026)")

# 4. Último Mes Auditado - Brasil
br_1m = analyze_portfolio("brasil", "🇧🇷 CARTERA BRASIL (2 RULETAS) - ÚLTIMO MES AUDITADO (14-SEP AL 15-OCT-2026)", start_date="2026-09-14")

# 5. Global 2 Años
tot_draws_2y = vz_2y["draws"] + br_2y["draws"]
tot_anim_2y = vz_2y["animals"] + br_2y["animals"]
tot_wins_2y = vz_2y["wins"] + br_2y["wins"]
tot_loss_2y = vz_2y["loss"] + br_2y["loss"]
tot_inv_2y = vz_2y["invested"] + br_2y["invested"]
tot_cob_2y = vz_2y["collected"] + br_2y["collected"]
tot_pnl_2y = tot_cob_2y - tot_inv_2y

print("=" * 95)
print(" 🌐 GRAN TOTAL CONSOLIDADO AMBOS PORTAFOLIOS (7 RULETAS EN PARALELO - 2 AÑOS A $1 FIJO)")
print("=" * 95)
print(f" Sorteos Totales Jugados:   {tot_draws_2y:,} sorteos")
print(f" Animalitos Apostados:      {tot_anim_2y:,} fichas ($1.00 USD c/u)")
print(f" Ganadas (Aciertos):        {tot_wins_2y:,} ({tot_wins_2y/tot_draws_2y*100:.2f}% Win Rate)")
print(f" Perdidas (Fallos):         {tot_loss_2y:,}")
print(f" Total Invertido:           ${tot_inv_2y:,.2f} USD")
print(f" Total Pagado / Cobrado:    ${tot_cob_2y:,.2f} USD")
print(f" Beneficio Neto (PnL):      +${tot_pnl_2y:,.2f} USD")
print(f" Retorno Neto (ROI):        +{tot_pnl_2y/tot_inv_2y*100:.2f}%")
print("=" * 95)
