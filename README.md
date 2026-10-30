# Código Secreto

Juego educativo de **Hacktoberfest × IEEE HKN Nu Zeta, ESPOL**, para cinco equipos. Combina diez retos con sobres, fichas impresas, pistas físicas y una plataforma web con estética medieval, música y clasificación final.

**Juego publicado:** https://codigo-secreto-hacktoberfest.onrender.com/

## Qué incluye

- Nombre de gremio y número de equipo asignado del 1 al 5.
- Diez retos consecutivos, con confirmación de respuestas y avance controlado por el servidor.
- Cronómetro que empieza al confirmar el paso al segundo reto.
- Progreso guardado en la base de datos y recuperación mediante «Continuar misión».
- Transiciones con la tortuga del evento e interfaz adaptada a celulares.
- Controles de volumen y silencio en el parlante de la esquina superior.
- Un leaderboard protegido, con comparación entre respuestas enviadas y respuestas esperadas.

## Recorrido del juego

1. **Cuenta bien, lee mejor:** extraer la palabra x de cada una de las cinco instrucciones del club y escribir el código de cinco palabras. Es necesario acertar; se toleran hasta dos caracteres de diferencia tras normalizar. El comprobante «Mensaje descifrado» muestra el código correcto y pide susurrárselo al oído a Gabriel Vallejo. «Ya recibimos el sobre · Comenzar reto 2» inicia el tiempo.
2. **La contraseña imposible:** introducir el dígito central de la contraseña. «Ver código validado» vuelve a mostrar la indicación de Gabriel Vallejo y el código del primer reto, sin reiniciar el tiempo.
3. **El algoritmo corrompido:** obtener el resultado de un programa reconstruido.
4. **Compuertas en serie:** calcular la salida decimal del circuito del equipo.
5. **Dilo con emojis:** interpretar el refrán de la pantalla asignada al equipo y escribirlo completo. Al enviarlo, esté bien o mal, se pasa directamente al reto 6, sin confirmación emergente ni aviso de entrega presencial.
6. **Encuentra las diferencias:** responder usando el material físico.
7. **La transmisión interceptada:** resolver el protocolo NEXO con la grabación y el material físico.
8. **Transmisión de doble cifrado:** recuperar el mensaje de audio y responder con el dígito solicitado.
9. **Señales intermitentes:** interpretar tres cifras Morse. El foco reproduce la secuencia una sola vez por clic; después queda apagado y aparece «Volver a repetir». Hay una tabla de conversión consultable.
10. **Mensaje final:** combinar respuestas anteriores con el banco de palabras del equipo. Es necesario acertar para finalizar.

Las grabaciones y los materiales físicos de los retos se consultan según las fichas y sus QR; los MP3 de `static/audio/` son la música de ambiente de la plataforma.

## Reglas de respuestas y puntuación

- El primer reto y el mensaje final requieren una respuesta correcta.
- Para esas frases se ignoran mayúsculas, tildes y puntuación y se normalizan los espacios. El código del primer reto admite hasta dos caracteres de diferencia; el mensaje final conserva su validación anterior.
- Los retos numéricos permiten continuar con una respuesta incorrecta, pero exigen el formato indicado: un dígito, salvo Morse, que requiere tres cifras.
- No se pueden volver a responder retos anteriores ni saltarse etapas.
- Los campos de texto convierten la entrada a mayúsculas sin tildes; los numéricos filtran caracteres y longitud.
- Al finalizar, el servidor calcula los aciertos con las claves correspondientes al equipo. En el reto 5 se ignoran tildes, puntuación, mayúsculas y espacios repetidos. Se aceptan variantes previstas, como «Dios le ayuda» y «Dios lo ayuda», o «cien» y «ciento volando». No se usa coincidencia aproximada indiscriminada.
- La clasificación ordena por más aciertos y, en empate, por menor tiempo.

## Tiempo, recarga y conexión

El primer reto no consume tiempo. El inicio queda guardado en el servidor al pulsar «Ya recibimos el sobre · Comenzar reto 2» y no se reinicia al recargar. Una vez iniciado, el tiempo continúa aunque se vuelva a la portada o se pierda la conexión.

Cada respuesta aceptada y el avance se guardan en la base de datos. Al recargar con conexión, la portada ofrece «Continuar misión». La recuperación requiere el mismo navegador y conservar su cookie de sesión; no hay un código para transferir la misión a otro dispositivo.

Si una petición se interrumpe, recargar al recuperar internet permite consultar el último estado guardado. Una respuesta que no llegó al servidor no está confirmada. No existe funcionamiento sin conexión ni reconexión automática durante la carga inicial. El borrador de la respuesta actual puede conservarse en la misma pestaña al salir normalmente, pero no sustituye el guardado del servidor.

## Ejecutar localmente

Requisitos: **Python 3.12 o posterior** y acceso a internet para instalar las dependencias iniciales.

En Windows, abrir `INICIAR_LOCAL.cmd`. El lanzador crea un entorno virtual, instala `requirements.txt` y ejecuta la aplicación. Para configurar una instalación nueva, copiar primero `.env.example` a `.env` y revisar sus valores.

Alternativa en PowerShell, desde la carpeta del proyecto:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
.venv\Scripts\python app.py
```

Abrir **http://localhost:5001/**. No sobrescribir un `.env` existente al actualizar.

### Configuración

- `SECRET_KEY`: secreto aleatorio y estable para firmar las sesiones. Mantenerlo entre reinicios para no invalidar las sesiones existentes.
- `ADMIN_PASSWORD_HASH`: hash de la contraseña de organización, si se configura.
- `ADMIN_PASSWORD`: alternativa de contraseña en texto dentro del entorno; el hash tiene prioridad.
- `DATABASE_URL`: conexión PostgreSQL. Si no se define, se utiliza SQLite local.
- `DB_PATH`: ruta SQLite alternativa; por defecto, `instance/game.sqlite3`.
- `PORT`: puerto local; por defecto, `5001`.
- `RENDER=true`: activa cookies seguras para HTTPS en Render.

`.env`, la configuración real de las fotos y las bases SQLite están excluidos de Git. Las credenciales de producción se mantienen en las variables del servicio, no en el README.

## Códigos del primer reto

Cada club tiene cinco instrucciones sin palabras destacadas. La web muestra su valor x y sus cinco líneas. El código se reconstruye tomando la palabra x de cada línea, en orden:

- Club 1, x = 4: HALCÓN NOCTURNO VIGILA TRES FAROS.
- Club 2, x = 5: SIETE LUCIÉRNAGAS ILUMINAN PUENTE ROJO.
- Club 3, x = 3: LUNA PLATEADA CRUZA RÍO PROFUNDO.
- Club 4, x = 6: ZORRO VELOZ GUARDA NUEVE LLAVES.
- Club 5, x = 2: ÁRBOL ANTIGUO ESCONDE CUATRO ESTRELLAS.

No depende de ubicaciones del recinto. Tras acertar se muestra un comprobante con el código canónico para que el staff lo verifique. La pantalla pide acercarse a Gabriel Vallejo y susurrar el código al oído. El equipo debe confirmar el inicio solo después de recibir su sobre; esta confirmación la realiza el equipo, no es una autorización remota del staff. Hasta ese momento el tiempo permanece en cero. En el reto 2 se puede reabrir el comprobante. Las misiones de versiones anteriores que ya resolvieron su primer reto conservan su avance y su referencia original.

## Pantallas del reto 5

La pantalla se asigna según la salida de circuito correspondiente al equipo, igual que en la modalidad anterior:

- Equipo 1 → Pantalla 0: 🐴 🎁 🚫 👀 🦷
- Equipo 2 → Pantalla 3: 🏞️ 🔊 🪨
- Equipo 3 → Pantalla 2: 🐓 🌅 🙏 🤝
- Equipo 4 → Pantalla 5: 🐦 ✋ ⚖️ 💯 🐦 ☁️
- Equipo 5 → Pantalla 4: 🐕 📢 🚫 🦷

El participante escribe un refrán completo y pasa directamente al reto 6. No se muestra la solución ni hay avisos emergentes en este paso. La respuesta se evalúa para el puntaje y puede revisarse por organización al finalizar.

La modalidad actual ya no utiliza fotografías, claves de aula ni aulas provisionales. `event_config.example.json` se conserva como referencia de la versión anterior; no configura este reto.

## Leaderboard y organización

La ruta es **`/leaderboard`**; `/admin` redirige allí. También se accede mediante el escudo discreto de la esquina inferior izquierda.

- Cada entrada o recarga del leaderboard exige iniciar sesión de nuevo.
- Se muestra una sola clasificación con el nombre, equipo, aciertos, tiempo y detalle de cada reto.
- «Comparar respuestas» muestra lo enviado frente a la clave usada al finalizar. En cada respuesta incorrecta aparece «Validar como correcta». La organización confirma la revisión, se suma un acierto y se actualiza la clasificación sin sustituir la respuesta original.
- Las revisiones se guardan en PostgreSQL con su fecha y se distinguen como «Validada por organización». «Deshacer validación» retira el acierto añadido. Repetir la misma petición no duplica puntos; se mantienen los controles de sesión administrativa y CSRF.
- La versión móvil presenta los mismos registros en tarjetas.
- Los resultados se actualizan automáticamente cada tres segundos, salvo mientras se consulta una comparación o un diálogo.
- Borrar un registro exige volver a escribir la contraseña.
- «Exportar resultados» descarga una copia JSON y «Cerrar acceso» cierra la sesión administrativa.

La base conserva misiones y resultados por separado. Borrar un resultado del leaderboard no elimina automáticamente la misión asociada.

`legacy-results.json` conserva los registros históricos de la versión inicial. Se importan una sola vez al inicializar una base sin la marca `legacy-imported`; no se reinsertan al reiniciar una base existente después de borrarlos. Las muestras actuales y los resultados del evento viven en la base de datos, no en el repositorio.

## Música e identidad visual

El parlante superior permite ajustar el volumen o silenciar. La preferencia se conserva en el navegador. La música está habilitada inicialmente; si el navegador bloquea la reproducción automática, comienza con la primera interacción.

- La música de portada se reproduce una sola vez por carga de página.
- Los retos 7 y 8 mantienen la música en pausa para facilitar la escucha.
- La música vuelve al entrar en el reto 9 y continúa en el mensaje final.
- El cierre tiene su propia pista.

La interfaz utiliza los recursos gráficos del evento y una composición transparente de sus marcas. La tortuga y la piedra comparten un contenedor para conservar su posición relativa.

Los créditos y la procedencia de las pistas están en [MUSIC_CREDITS.md](MUSIC_CREDITS.md). Los recursos de terceros no adquieren una licencia libre por formar parte de este proyecto.

## Estructura del repositorio

```text
codigo-secreto-web/
├── app.py                       # Servidor, sesiones, validación y persistencia
├── templates/                   # Juego y panel de organización
├── static/
│   ├── game.js                  # Interfaz y recorrido
│   ├── admin.js                 # Leaderboard
│   ├── sound.js                 # Música y volumen
│   ├── game.css                 # Estilos base
│   ├── medieval.css             # Tema y adaptación de pantalla
│   ├── audio/                   # Música de ambiente
│   ├── event/                   # Identidad visual del evento
│   ├── sponsors/                # Marcas de la comunidad
│   └── challenges/              # Recursos gráficos de los retos
├── event_config.example.json    # Referencia de la modalidad anterior
├── legacy-results.json          # Importación histórica inicial
├── requirements.txt             # Dependencias del servidor
├── INICIAR_LOCAL.cmd            # Lanzador para Windows
├── .env.example                 # Modelo de variables de entorno
├── MUSIC_CREDITS.md              # Créditos musicales
└── README.md
```

En la copia local se conserva además `archivo-local/documentacion/`, con las guías, los imprimibles y los recursos originales entregados para el evento. Ese material está excluido del seguimiento local de Git y no se despliega. Los archivos temporales de revisión, fotogramas, capturas, bases de pruebas y scripts auxiliares se retiraron.

## Render y base de datos

El despliegue actual usa un servicio web de Render conectado a este repositorio privado, con PostgreSQL mediante su conexión interna. Los cambios enviados a `main` activan el despliegue automático del servicio existente.

**Construcción:**

```text
pip install -r requirements.txt
```

**Arranque:**

```sh
gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4
```

**Comprobación de salud:** `GET /healthz`. Ejecuta una consulta SQL y devuelve el estado y el tipo de almacenamiento.

Al iniciar, el servidor crea las tablas necesarias y añade las columnas de versiones anteriores sin borrar los resultados. Las tablas principales son `missions`, `submissions` y `app_metadata`. Los resultados nuevos identifican la modalidad de emojis y guardan la clave utilizada. La migración conserva los resultados de fotografía anteriores; las revisiones manuales se almacenan por reto en `manual_reviews`.

Para una instalación nueva en Render, configurar un `SECRET_KEY` estable, la contraseña de organización y `DATABASE_URL` con la conexión PostgreSQL apropiada. No usar SQLite en el almacenamiento efímero del servicio como sustituto de la base de producción. Consultar en el panel las condiciones y la fecha de vencimiento de la base gratuita y exportar los resultados antes de reemplazarla.

## Comprobaciones de mantenimiento

Sin modificar la base de producción:

```powershell
python -c "import ast; from pathlib import Path; ast.parse(Path('app.py').read_text(encoding='utf-8')); print('Sintaxis Python correcta')"
node --check static/game.js
node --check static/admin.js
node --check static/sound.js
```

Node.js solo se necesita para esas comprobaciones opcionales de JavaScript; no es una dependencia del servidor del juego.

Después de publicar, comprobar que el despliegue figure como activo, que `/healthz` responda correctamente y que el juego y `/leaderboard` carguen. Si se mantiene una pestaña abierta durante una actualización, recargar para obtener los archivos nuevos y usar «Continuar misión».
