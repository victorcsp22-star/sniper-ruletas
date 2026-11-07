import sys
sys.path.append(r'C:\Users\victo\nuevas_ruletas\app_movil')
from server_zero_dep import get_current_streaks, parse_tuazar_results_pure, RULETAS

print("=== TEST ZERO DEP STREAKS ===")
for r in RULETAS:
    stk, miss, info = get_current_streaks(r)
    m = info.get("is_markov")
    c = len(info.get("cands"))
    print(f" {r:<16}: streak={stk}, misses={miss}, markov={m}, cands={c}")

print("\n=== TEST PURE TUAZAR SCRAPER ===")
res = parse_tuazar_results_pure()
for r, items in res.items():
    print(f" {r:<16}: {len(items)} draws scraped")
