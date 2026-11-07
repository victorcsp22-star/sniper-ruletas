import os

path_html = r"C:\Users\victo\nuevas_ruletas\app_movil\static\index.html"
with open(path_html, "r", encoding="utf-8") as f:
    text = f.read()

# Restaurar ${ en los templates literales
text = text.replace("Bs {", "${")
text = text.replace("Bs Bs ${", "Bs ${")
text = text.replace("Bs ${cleanText}", "${cleanText}")
text = text.replace("P:Bs ${peso}", "P:${peso}")
text = text.replace("border Bs ${colorClass}", "border ${colorClass}")
text = text.replace("border Bs ${badgeClass}", "border ${badgeClass}")
text = text.replace("border Bs ${pesoPillClass}", "border ${pesoPillClass}")
text = text.replace("border-2 Bs ${borderClass}", "border-2 ${borderClass}")
text = text.replace("from-emerald-950 via-slate-900 to-emerald-950", "from-emerald-950 via-slate-900 to-emerald-950")

with open(path_html, "w", encoding="utf-8") as f:
    f.write(text)

with open(r"C:\Users\victo\nuevas_ruletas\app_movil\index.html", "w", encoding="utf-8") as f:
    f.write(text)

print("Plantillas HTML y JS restauradas limpiamente!")
