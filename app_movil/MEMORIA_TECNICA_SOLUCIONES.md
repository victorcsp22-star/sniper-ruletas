# Registro de Memoria Técnica: Errores Críticos y Soluciones de Despliegue en Android Termux
# Fecha: 03-Noviembre-2026
# Sistema: Bot Sniper Multiruleta PWA Autónomo (server_zero_dep.py)

---

## 1. Problema de Conexión en Android Termux: "unknown url type: https" / Fallas de OpenSSL
- **Síntoma:** Al arrancar el bot en Termux, arroja `[-] urllib falló (<urlopen error unknown url type: https>)` y `No se pudo obtener el HTML de TuAzar`.
- **Causa Raíz:** En Android Termux, el intérprete Python nativo muchas veces carece del módulo C `_ssl.so` compilado o la librería del sistema `libcurl.so` tiene conflictos de símbolos (`SSL_set_quic_tls_early_data_enabled`). Esto impide abrir conexiones HTTPS directas desde Python.
- **Solución Definitiva (Sextupla Redundancia):**
  1. **Bridge PC Local:** Consultar primero al endpoint HTTP puro de la PC local en la LAN: `http://192.168.1.2:5000/api/tuazar_bridge`. Al ser HTTP plano, Python en Android lo lee al 100% sin requerir SSL.
  2. **Binario Musl `curl_static` Autónomo:** Se empaqueta en la raíz un binario ELF aarch64 compilado estáticamente con Musl libc y mbedTLS/WolfSSL embebido (10,061,488 bytes). Este ejecutable no depende de las librerías dinámicas de Android ni de Termux y descarga HTTPS perfectamente con `chmod +x curl_static`.
  3. **Wget Nativo:** Fallback con `wget --no-check-certificate -qO- --user-agent=Mozilla/5.0`.
  4. **Curl Nativo del Sistema:** `curl -k -s -L -A ...`.
  5. **Urllib con contexto permisivo:** `ssl.CERT_NONE`.

---

## 2. Contaminación del Paquete de Entrega (`sniper_ruletas.zip`)
- **Síntoma:** El usuario descargaba el zip en Termux pero seguían apareciendo las 9 ruletas viejas, saldos desactualizados o errores ya corregidos en la PC.
- **Causa Raíz:** Existían múltiples copias de `sniper_ruletas.zip` en rutas anidadas (`app_movil/static/sniper_ruletas.zip` y `app_movil/static/static/sniper_ruletas.zip`). El servidor web HTTP servía el archivo de la ruta anidada vieja de menor tamaño (378 KB) en lugar del paquete actualizado (10.2 MB).
- **Solución Definitiva:**
  1. Unificar y sincronizar siempre todas las copias en `app_movil/static/sniper_ruletas.zip` y `app_movil/static/static/sniper_ruletas.zip`.
  2. Incluir el binario `curl_static` en la raíz exacta del zip para que `chmod +x curl_static` funcione inmediatamente tras descomprimir.
  3. En Termux, usar comando de instalación limpia borrando la carpeta anterior:
     `cd ~ && rm -rf sniper && mkdir sniper && cd sniper && python -c "..." && chmod +x curl_static && python server_zero_dep.py`.

---

## 3. Política de Limpieza Diaria del Registro de Jugadas
- **Regla:** El registro de jugadas en pantalla (`Registro de Jugadas de Hoy`) debe filtrarse **exclusivamente por la fecha actual (`date_str = datetime.date.today().strftime('%Y-%m-%d')`)**.
- **Prohibición:** Queda terminantemente prohibido incluir fechas históricas previas (`2026-11-01`, `2026-11-02`) en la vista diaria. Cada medianoche el registro de jugadas se reinicia automáticamente en blanco (`Hoy: Bs 0.00 (0/0)`) para comenzar la jornada sin arrastrar disparos pasados.
