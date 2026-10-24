# Código Secreto · Hacktoberfest × IEEE HKN Nu Zeta

Juego educativo para cinco equipos de ESPOL. Diez etapas conectan pistas físicas con validación web. Interfaz en español y adaptación móvil.

## Ejecutar

Python 3.12 o posterior:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
.venv\Scripts\python app.py
```

Abrir http://localhost:5001. Configurar SECRET_KEY con un valor aleatorio estable. La administración usa ADMIN_PASSWORD o ADMIN_PASSWORD_HASH; solicita otra vez la contraseña al borrar cada registro. Para Render se configura la contraseña solicitada por el organizador mediante variables de entorno.

Sin DATABASE_URL se usa SQLite en instance/game.sqlite3. Con DATABASE_URL se usa PostgreSQL; Render conecta mediante su URL interna en la misma región (Ohio). Las credenciales nunca se incluyen en Git.

## Preparar aulas

Copiar event_config.example.json a event_config.json. Para cada foto completar url (p. ej. /static/challenges/foto-0.jpg), answer (cadena que conserva ceros iniciales) y destination (ubicación real autorizada). Correspondencia equipos 1–5 → fotos 0, 3, 2, 5, 4. No incluir las claves en archivos de static.

Mientras no existan fotos reales, la interfaz muestra una ilustración genérica de aula. Solo el monitor puede habilitar esa etapa con contraseña. Se registra PENDIENTE y no suma acierto: una misión provisional termina con 9/10. Con fotos completas se valida su código y se muestra la ubicación real.

## Reglas y clasificación

Orden: lectura, contraseña, Python, circuito, fotografía, diferencias, NEXO, doble cifrado, Morse, mensaje final. Validación en servidor; normalización de tildes y puntuación en las frases. Las respuestas numéricas conservan orden y longitud. No se permite avanzar enviando directamente una etapa futura. Los errores permiten reintentar sin penalización, como indica la ficha física; el reloj continúa. Las transiciones también forman parte del tiempo total.

Se mantiene el criterio del leaderboard: más aciertos primero y menor tiempo en empate. Cada misión finalizada se registra una sola vez. El servidor mide el tiempo; recargar la página recupera el progreso mediante la sesión. /admin exige contraseña; también protege las respuestas correctas. Exportar resultados descarga JSON para conservar los datos antes del vencimiento de PostgreSQL gratuito.

## Recursos

Las fichas originales se extrajeron sin regenerar de imprimir_reto_2_3_6_7_8.pdf. Conservan los QR y las imágenes de diferencias. Los audios de NEXO y doble cifrado se consultan mediante sus QR originales. Las pistas impresas siguen siendo parte necesaria de la experiencia.

Música: cinco pistas de la playlist Dark Ages de Plants vs. Zombies 2, descargadas directamente y convertidas a MP3 tras la declaración de autorización del organizador. Ver MUSIC_CREDITS.md. El usuario activa la reproducción; hay volumen y silencio. Se pausa durante NEXO, doble cifrado y Morse. No se redistribuyen como contenido de licencia abierta.

Branding: fuentes PNG originales conservadas. El archivo SVG del lockup contiene exactamente los tres originales embebidos; el PNG es una exportación transparente de 4202 × 320. No se inventan detalles adicionales en el logo blanco cuya fuente mide 783 × 96. compose-brand.cjs regenera ambos usando Sharp. La interfaz usa el SVG para conservar los originales. La tortuga y la base se muestran como archivos originales.

## Validación

```powershell
python -m unittest test_game -v
node --check static/game.js
node --check static/admin.js
```

Las pruebas usan una base SQLite aislada: recorren los cinco equipos, rechazos de respuestas, habilitación provisional, normalización, correspondencia circuito/Morse/bancos, protección CSRF y eliminación con nueva contraseña. No modifican PostgreSQL de producción.

## Render

Servicio web gratuito: pip install -r requirements.txt; gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4. DATABASE_URL usa la conexión interna del PostgreSQL existente; SECRET_KEY y ADMIN_PASSWORD_HASH se configuran como secretos. /healthz comprueba la conexión SQL. PostgreSQL gratuito vence el 23 de noviembre de 2026; exportar los resultados antes. No hay conversión automática a un plan pagado.

## Diferencias entre guías resueltas

La numeración de etapas 1–10 de la guía de programadores y las fichas finales se usa como referencia visible; no se usa el orden histórico de la portada. La foto depende de la etapa 4 (circuito), no del conteo de diferencias. Doble cifrado valida 8; NEXO valida 5. A=2 y B=3 son constantes de cuatro bits; el equipo 1 puede obtener cero. Los bancos finales concuerdan con Morse 251, 372, 583, 916 y 635.

Los registros de database.json anteriores se conservan en legacy-results.json y se importan una sola vez, manteniendo puntajes y tiempos originales. Borrarlos desde el panel no los vuelve a importar. Sus casillas se comparan con la clave histórica del juego anterior.
