import os

paths = [
    r"C:\Users\victo\nuevas_ruletas\app_movil\static\index.html",
    r"C:\Users\victo\nuevas_ruletas\app_movil\index.html"
]

for p in paths:
    if not os.path.exists(p):
        continue
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()

    # Ajustar intervalo de 15000 a 30000 ms
    html = html.replace("setInterval(loadTacticalStatus, 15000);", "setInterval(loadTacticalStatus, 30000);")

    # Mejorar la funcion syncTuAzar para dar feedback limpio
    old_sync = """    // Sincronizar en vivo con TuAzar
    async function syncTuAzar() {
      const btn = document.getElementById('btn-sync');
      const icon = document.getElementById('sync-icon');
      const txt = document.getElementById('sync-text');

      icon.classList.add('sync-spin');
      txt.textContent = 'Consultando...';
      btn.disabled = true;

      // Vibracin hǭptica en celulares compatibles
      if (navigator.vibrate) navigator.vibrate(30);

      try {
        const res = await fetch('/api/sync', { method: 'POST' });
        const data = await res.json();
        await loadTacticalStatus();
        if (data.status === 'ok') {
          alert(`Sincronizacin con TuAzar completada.\\nNuevos sorteos agregados: ${data.total_new_draws}\\nHora: ${data.synced_at}`);
        } else {
          alert('Aviso al sincronizar: ' + (data.message || 'Error'));
        }
      } catch (err) {
        alert('Error conectando con el servidor: ' + err);
      } finally {
        icon.classList.remove('sync-spin');
        txt.textContent = 'Sincronizar';
        btn.disabled = false;
      }
    }"""

    # Buscar la definicion de syncTuAzar de forma flexible
    if "async function syncTuAzar()" in html:
        # Reemplazar con una version mejorada
        start_idx = html.find("async function syncTuAzar()")
        end_idx = html.find("    // Alternar Modal de Reporte", start_idx)
        if end_idx != -1:
            new_func = """    // Sincronizar en vivo con TuAzar bajo demanda
    async function syncTuAzar() {
      const btn = document.getElementById('btn-sync');
      const icon = document.getElementById('sync-icon');
      const txt = document.getElementById('sync-text');

      if (icon) icon.classList.add('sync-spin');
      if (txt) txt.textContent = 'Consultando...';
      if (btn) btn.disabled = true;

      if (navigator.vibrate) navigator.vibrate(30);

      try {
        const res = await fetch('/api/sync', { method: 'POST' });
        const data = await res.json();
        await loadTacticalStatus();
        if (data.status === 'ok') {
          alert(`✅ Sincronización Completada\\nNuevos sorteos: ${data.total_new_draws}\\nHora: ${data.synced_at}`);
        } else {
          alert('⚠️ Aviso: ' + (data.message || 'Sin respuesta'));
        }
      } catch (err) {
        alert('❌ Error al conectar: ' + err);
      } finally {
        if (icon) icon.classList.remove('sync-spin');
        if (txt) txt.textContent = 'TuAzar';
        if (btn) btn.disabled = false;
      }
    }\n\n"""
            html = html[:start_idx] + new_func + html[end_idx:]

    with open(p, "w", encoding="utf-8") as f:
        f.write(html)

print("index.html actualizado.")
