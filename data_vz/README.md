# 🎯 Bot Sniper Cuantitativo Multi-Ruleta (Animalitos de Venezuela)

Sistema inteligente de arbitraje estadístico y monitoreo en tiempo real para las 4 principales loterías de animalitos de Venezuela:
1. **🦁 Lotto Activo** (38 animales, paga 30x)
2. **👑 Ruleta Royal** (37 animales, paga 30x)
3. **🐸 La Granjita** (38 animales, paga 30x)
4. **🦇 Guácharo Activo** (77 animales, paga 60x)

El sistema se conecta a **TuAzar**, actualiza los resultados en vivo, aplica el **reloj armónico de rebote** para cada ruleta, descarta los animales salidos en las últimas 6 horas y emite **señales de disparo únicamente cuando se activa el Gatillo Táctico Post-Fallo 1**.

---

## 🚀 Uso del Bot en Tiempo Real (`sniper_bot.py`)

### 1. Consulta Rápida del Estado Actual (One-Shot)
Ejecuta una consulta instantánea para ver si hay algún disparo activo en este momento:

```bash
python sniper_bot.py --bankroll 100 --risk 0.20
```

* `--bankroll`: Tu capital total disponible en USD (por defecto: `100.0`).
* `--risk`: Porcentaje del capital a apostar por cada animal (por defecto: `0.20%`).

### 2. Modo Monitor Continuo (Daemon / Loop)
Deja el bot corriendo en tu computadora. Se actualiza automáticamente cada 4 minutos y te avisa en pantalla cuando se enciende una señal de apuesta:

```bash
python sniper_bot.py --loop --bankroll 100 --risk 0.20
```

### 3. Alertas en Tiempo Real a tu Telegram (Smartphone)
El bot puede enviarte una notificación push a tu teléfono cada vez que una ruleta active una señal de apuesta:

```bash
python sniper_bot.py --loop --bankroll 100 --risk 0.20 --tg_token "TU_TOKEN_TELEGRAM" --tg_chat "TU_CHAT_ID"
```

---

## 🧠 Las Reglas Matemáticas Incorporadas

| Ruleta | Universo | Pago Oficial | Lags de Rebote Preferidos | Regla de Exclusión | Condición de Disparo |
| :--- | :---: | :---: | :---: | :---: | :---: |
| 🦁 **Lotto Activo** | 38 | 30x | **Lags [14, 15, 18, 20]** | Tacha los de las últimas 6h | Solo tras 1 fallo previo |
| 👑 **Ruleta Royal** | 37 | 30x | **Lags [16, 19, 21, 23]** | Tacha los de las últimas 6h | Solo tras 1 fallo previo |
| 🐸 **La Granjita** | 38 | 30x | **Lags [14, 15, 17]** | Tacha los de las últimas 6h | Solo tras 1 fallo previo |
| 🦇 **Guácharo Activo** | 77 | 60x | **Lags [25, 31, 41, 42]** | Tacha los de las últimas 6h | Solo tras 1 fallo previo |

---

## 📁 Archivos del Proyecto

- `sniper_bot.py`: **El bot operativo en tiempo real** (conecta a TuAzar, procesa los 4 juegos y genera las señales).
- `portfolio_multi_backtest.py`: Simulador del portafolio combinado de las 4 ruletas ($100 $\to$ $1.279 - $7.957 USD).
- `cross_lottery_comparison.py`: Comparativa estadística y de ROI entre las 4 loterías.
- `rebound_lags_analysis.py`: Escáner de lags del 1 al 50 para detectar picos armónicos.
- `multi_lottery_scraper.py`: Descargador masivo de historiales de 2 años desde TuAzar.
- `lotto_activo_2anios.csv`: Historial de 2 años de Lotto Activo (8.669 sorteos).
- `la_granjita_2anios.csv`: Historial de 2 años de La Granjita (8.630 sorteos).
- `ruleta_royal_2anios.csv`: Historial de 2 años de Ruleta Royal (6.998 sorteos).
- `guacharo_activo_2anios.csv`: Historial de 2 años de Guácharo Activo (8.786 sorteos).
