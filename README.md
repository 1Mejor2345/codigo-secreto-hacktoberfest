# Código Secreto · Hacktoberfest × IEEE HKN Nu Zeta

Juego educativo para cinco equipos de ESPOL. Diez etapas conectan pistas físicas y plataforma web. Interfaz medieval en español, con vistas para celular.

## Ejecutar localmente

Python 3.12 o posterior. Ejecutar INICIAR_LOCAL.cmd o:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
.venv\Scripts\python app.py
```

Abrir http://localhost:5001. SECRET_KEY debe ser aleatoria y estable. Sin DATABASE_URL se usa SQLite en instance/game.sqlite3. Con DATABASE_URL se usa PostgreSQL. Render utiliza la conexión interna de PostgreSQL en Ohio, sin acceso externo a la base. Credenciales excluidas de Git.

## Dinámica vigente

El participante introduce el nombre del club o gremio (2–60 caracteres) y el equipo asignado (1–5). Debe escribir y confirmar una respuesta para cada uno de los diez retos. Toda respuesta no vacía se guarda y permite avanzar, aunque sea incorrecta. No se exige acertar para pasar. Los aciertos se calculan en el servidor al finalizar. No se publica la solución durante el recorrido.

El orden es lectura, contraseña, Python, circuito, fotografía, diferencias, NEXO, doble cifrado, Morse y mensaje final. A=2 y B=3 son constantes de cuatro bits. Circuitos por equipo: 0, 3, 2, 5, 4. Morse: 251, 372, 583, 916, 635. NEXO: 5. Doble cifrado: 8. Las frases admiten cambios de tildes, mayúsculas y puntuación; las respuestas numéricas conservan ceros iniciales y orden.

Volver al inicio conserva la misión y el borrador local de la respuesta actual. El cronómetro continúa. «Continuar misión» retoma el reto pendiente. Solo las misiones finalizadas entran al ranking. Un nombre no sustituye el número asignado, que determina las claves de ese equipo.

## Aulas pendientes

Copiar event_config.example.json a event_config.json y completar url, answer y destination para cada foto. Equipos 1–5 reciben fotos 0, 3, 2, 5 y 4. Guardar los códigos como cadenas para conservar ceros iniciales. No guardar claves en static.

Sin foto real se muestra una ilustración genérica y se pide escribir «pendiente». Esa respuesta también permite continuar y queda visible en la comparación; sin una clave real la etapa no suma acierto y se marca pendiente. No se inventan aulas.

## Un solo leaderboard

El acceso está en el pequeño escudo discreto de la esquina inferior izquierda. La ruta única es /leaderboard (/admin redirige allí). Cada entrada o recarga exige de nuevo la contraseña de organización. / y /leaderboard revocan la sesión administrativa previa. Las respuestas correctas y el ranking están protegidos en servidor; las respuestas de la API y la página no se almacenan en caché.

Se ordena por más aciertos y menor tiempo en empate. Cada registro muestra nombre del club, equipo asignado, resultado por reto y comparación de **respuesta enviada** frente a **respuesta real**. No hay selector de versiones ni rankings separados. En celular, las mismas filas se convierten en tarjetas legibles. Los datos de referencia se devuelven por registro y se conserva una instantánea de la clave usada al finalizar.

Los siete registros originales se importan una sola vez desde legacy-results.json, preservando sus puntajes y tiempos. Se comparan con su clave histórica; no se vuelven a importar después de borrarlos. La migración agrega columnas sin borrar registros de versiones anteriores.

ADMIN_PASSWORD_HASH o ADMIN_PASSWORD configuran el acceso. Borrar cada registro exige volver a escribir la contraseña. «Cerrar acceso» revoca la sesión. El ranking se actualiza cada tres segundos cuando no se está consultando una comparación. Exportar resultados descarga JSON para conservarlos antes del vencimiento de la base gratuita.

## Música y recursos visuales

Cinco pistas MP3 de Dark Ages / Plants vs. Zombies 2 se descargaron y convirtieron localmente tras la declaración de autorización del organizador; ver MUSIC_CREDITS.md. Música habilitada por defecto; ante bloqueo del autoplay comienza con la primera interacción. El parlante superior despliega el volumen y el silencio. Se pausa durante NEXO, doble cifrado y Morse.

Tortuga y piedra mantienen su proporción dentro de un mismo contenedor, sin animación vertical independiente. Lockup del evento: SVG con los tres originales embebidos y exportación PNG transparente. Google for Developers usa el recurso oficial para fondo oscuro, exportado a PNG con alfa real, sin fondo blanco ni redibujado:
https://www.gstatic.com/devrel-devsite/prod/v5a0f9ff8b593048661361a49e11ab98a8b1ac025e19e60e6189f2b56796f8a43/developers/images/lockup-dark-theme-new.svg

Se retiró el emblema adicional de IEEE Eta Kappa Nu de la fila de aliados. Las fichas originales se extrajeron sin regenerar del PDF del evento y conservan los QR y las diferencias originales. Esas pistas físicas siguen siendo parte de la experiencia.

## Validación

```powershell
python -m unittest test_game -v
node --check static/game.js
node --check static/admin.js
node --check static/sound.js
```

Pruebas con bases SQLite aisladas: los cinco equipos, respuestas erróneas que avanzan, bloqueo de respuestas vacías y saltos, puntaje real, nombre, clave específica por equipo, instantáneas de referencia, migración de datos antiguos, contraseña en cada entrada, CSRF y nueva contraseña al borrar. La revisión de anchos de celular se realiza con iframes de 320–430 px en un servidor local de pruebas, sin modificar datos de Render.

## Render

Servicio gratuito con gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4. /healthz consulta SQL. PostgreSQL gratuito vence el 23 de noviembre de 2026; exportar los resultados antes. No se cambia automáticamente a un plan pagado.

Una misión en curso permite editar el nombre del gremio desde el inicio sin reiniciar el reloj, borrar respuestas ni cambiar el número asignado.
