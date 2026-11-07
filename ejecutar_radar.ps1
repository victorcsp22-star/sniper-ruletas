# Script de ejecución continua del Radar Sniper en PowerShell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$host.UI.RawUI.WindowTitle = "🎯 BOT SNIPER 7 RULETAS | BACKTEST EN VIVO REAL (0.75x KELLY OPTIMIZADO)"

Write-Host "==========================================================================================" -ForegroundColor Cyan
Write-Host " 🎯 INICIANDO BOT SNIPER EN VIVO (7 RULETAS) | MODELO OPTIMIZADO CON CONTROL DE DRAWDOWN" -ForegroundColor Green
Write-Host "    Capital Base: `$200.00 USD | Reinicio Semanal 7 Días | Motor de Catch-Up Activo" -ForegroundColor Yellow
Write-Host "==========================================================================================" -ForegroundColor Cyan

while ($true) {
    try {
        python C:\Users\victo\nuevas_ruletas\bot_nuevas_ruletas.py --loop 60
    } catch {
        Write-Host "⚠️ Error detectado: $_. Reiniciando bucle en 15 segundos..." -ForegroundColor Red
        Start-Sleep -Seconds 15
    }
}
