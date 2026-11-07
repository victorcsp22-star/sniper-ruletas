import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(r'C:\Users\victo\nuevas_ruletas\app_movil')
import server_zero_dep

print('server_zero_dep imported successfully')
b = server_zero_dep.get_30d_color_bubbles(30)
for k, v in b.items():
    print(f"{k:<30} {v['emoji']} {v['color']:<8} stake: ${v['stake']:.2f} pnl: ${v['pnl_30d']:+.2f}")
