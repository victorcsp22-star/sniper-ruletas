# AGY-QUANT HARNESS: SPECIFICATION & AUDIT FRAMEWORK
# Basado en el estándar AgenKit (agenkit.xyz) y los Principios de Rigor Cuantitativo Institucional

Este documento define el marco formal obligatorio para la conceptualización, validación, dimensionamiento, ejecución y gobernanza de sistemas autónomos de trading cuantitativo en nuestro laboratorio.

---

## 1. COMPUERTA 1: ESPECIFICACIÓN DE MERCADO Y VENTAJA MATEMÁTICA (EDGE)
Cada sistema o módulo debe completar obligatoriamente este bloque antes de escribir código:

* **Venue & Plomería:**
  - Clase de Activo / Instrumento:
  - Broker / Exchange / Banca:
  - Horarios y Régimen de Sesión:
  - Estructura de Costos (Comisiones maker/taker, spread, impuestos, arrastre de cuota):
  - Límites de API, latencia esperada y tamaño mínimo de orden (*tick/lot size*):
* **El Alfa / Edge (1 oración matemática):**
* **La Contraparte:** ¿Quién está del otro lado perdiendo dinero y cuál es su incentivo/restricción estructural para hacerlo?
* **Razón Económica de Persistencia:** ¿Por qué la ineficiencia no ha sido arbitrada?

---

## 2. COMPUERTA 2: RIGOR DE DATOS Y PROTOCOLO DE VALIDACIÓN
* **Higiene Temporal:** Prohibición absoluta de *look-ahead bias*. Timestamps sincronizados al cierre del tick/vela anterior.
* **Protocolo de Validación:**
  - Partición cronológica estricta (Entrenamiento, Validación, Fuera de Muestra / *Out-of-Sample*).
  - Embargos y Purga (*Purged Cross-Validation*) para evitar autocorrelación serial.
  - Walk-Forward Analysis Dinámico.
* **Meseta de Parámetros (*Parameter Stability Surface*):**
  - Barrido de parámetros adyacentes ($N \pm 1, N \pm 2$).
  - Rechazo automático de estrategias frágiles (*needle in a haystack*).
* **Conteo de Ensayos:** Reportar cada variante probada ($K$ ensayos) para calcular el *Deflated Sharpe Ratio* o ajuste de White/Bonferroni.

---

## 3. COMPUERTA 3: GOBERNANZA DE RIESGO Y MOTOR DE EJECUCIÓN
* **Soberanía del Módulo de Riesgo:** El motor de riesgo tiene prioridad por código duro sobre el generador de señales.
* **Dimensionamiento:**
  - Fractional Kelly ($\le 0.25 \times \text{Full Kelly}$) o Volatility Targeting. Prohibido Full Kelly y martingalas lineales.
  - Amortiguador de Drawdown (*Cushion Scaling*).
* **Protecciones Activas:**
  - Límite de pérdida diaria y semanal (*Circuit Breaker*).
  - Límite de posición máxima por activo y por cartera.
  - Chequeo de datos estancados (*Stale Data Timeout*).
  - Desconexión segura y reconciliación de órdenes (*In-flight orders reconciliation*).

---

## 4. COMPUERTA 4: AUDITORÍA ANTAGONISTA (BEAR CASE & PRE-MORTEM)
* **¿Cómo fallará este sistema en vivo?**
* **Criterios de Invalidación Empírica:** Métrica cuantitativa exacta que, de ser alcanzada en producción, detiene el sistema permanentemente.
* **Sensibilidad Extrema a Costos:** ¿Sobrevive al duplicar comisiones y triplicar el deslizamiento (*slippage*)?
