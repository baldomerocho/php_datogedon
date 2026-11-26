# Automatización editorial

El código del ejecutor vive en `editorial/`; la cola, las fichas, los manifiestos,
las credenciales y los logs permanecen en una carpeta privada externa al repositorio.
La fuente activa es Claude local. Una fuente retirada puede conservar su archivo
histórico en `archived_sources`, sin conexión de red ni fingir actividad reciente.

## Ciclos experimentales en la Mac

Desde v1.6 el planificador es `editorial/cycles.py`. Noticias: 06:00, 09:00 y
11:00; experiencias: 13:00, 15:00 y 18:00, America/Guatemala. Cada ventana produce
como máximo una entrada, tras verificar borrador, miniatura, enlaces y estado
remoto. Publica al terminar el mismo ciclo/día; no reserva nuevos días futuros.
Se conservan fechas y contenido de todas las entradas anteriores.

La Mac debe estar despierta y conectada. RunAtLoad recupera solo la ventana reciente
(75 min noticias, 120 min experiencias), nunca una ráfaga de ventanas perdidas.
La generación no corre en el servidor; WP-Cron sigue publicando la cola anterior.
Al acabar experiencias históricas viables, `catch_up=false` conserva solo 13:00.

`private/cycles.json` registra un intento durable por ventana antes de escribir.
Un bloqueo global evita solapamientos entre líneas. Un ciclo fallido/incierto no
se repite automáticamente: revisar borradores e IDs antes de recuperación manual.
El estado de éxito es por ciclo, no por día. El redactor tiene plazo de 45 minutos.
Salud a las 07/10/12/14/16/19 con aviso local; no envía mensajes ni emails.

Noticias usa estado separado en `news/`, búsqueda web en vivo y autor 135 Juan Pax;
no recolecta sesiones privadas. Se exige contrastar fuentes originales e
independientes, enlazarlas y guardar su revisión privada. Dos dominios distintos
no equivalen a independencia: el redactor debe comprobarla. Temas inciertos,
acusaciones y política controvertida quedan para revisión humana. Puede terminar
sin noticia; una herramienta averiada nunca se registra como falta de noticias.
Las experiencias conservan la anonimización y evidencia del trabajo humano/IA.

## Enlaces internos

`datogedon/find-related-posts` busca candidatos publicados, sin contraseña,
indexables y con canonical propio. Devuelve título, URL, extracto y coincidencias.
El mismo redactor lee el contenido completo antes de enlazar: coincidencias de
palabras no bastan. Entre cero y tres enlaces descriptivos por entrada; no hay
mínimo. No se modifican artículos anteriores para añadir enlaces inversos.

`editorial/internal_links.py --post-id ID` comprueba destinos publicados, anclas,
autorreferencias y duplicados sin reescribir HTML. El guardado MCP valida de nuevo
indexabilidad al publicar. Relevancia semántica sigue siendo revisión editorial.

## Publicación y autoría

`datogedon/save-post` permite `draft`, `future` y publicar un borrador preparado.
Noticias debe usar `kind=news`, `author=135` y `source_urls` citadas en el cuerpo.
El servidor exige permisos, dos dominios fuente, miniatura WebP 1200x630 con alt
<=180KB, extracto y categoría. No convierte un alta directa en publicación ni
sobrescribe publicados: un reintento devuelve su ID inmutable. No se cambian roles,
contraseñas ni slugs de autores. La biografía de Juan Pax identifica la firma
editorial asistida por IA; no afirma una revisión humana que no haya ocurrido.

El código se instala después de CI verde con:

```sh
python3 editorial/install-mac.py --state-dir /ruta/privada --sha SHA_VERIFICADO
python3 editorial/cycles.py --state-dir /ruta/privada --mode news
python3 editorial/cycles.py --state-dir /ruta/privada --health
```

Instalación guarda copia privada de configuración, plists y release anterior.
Estado, colas, fuentes y credenciales permanecen fuera de Git. El transporte MCP
solo usa la credencial local existente. Las imágenes usan herramientas disponibles
sin contratar APIs; un diagrama original es alternativa al generador. No presentar
ilustraciones generadas como fotografías documentales.

## Publicación en el servidor

`ops/datogedon-wp-cron.service` ejecuta el WP-Cron nativo como el usuario de la
aplicación. Su timer se comprueba cada cinco minutos, es persistente tras reiniciar
y tiene un límite de cuatro minutos por ejecución. No reinicia WordPress ni otras
aplicaciones. En reposo, la comprobación medida usó aproximadamente 0,5 s de CPU.
No recorre empresas ni añade un worker propio por tarea.

En la instalación inicial se guardó una copia privada de `wp-config.php` y se fijó
`DISABLE_WP_CRON=true` solo en esta aplicación, tras comprobar el ejecutor nativo.
Así se sustituye el disparo dependiente de visitas. Los templates del timer viajan
en el paquete por SHA: CI valida las unidades y el instalador compara su procedencia,
comprueba que apunten al sitio correcto y conserva las anteriores para recuperación.

```sh
systemctl status datogedon-wp-cron.timer
systemctl show datogedon-wp-cron.service -p Result -p ExecMainStatus
journalctl -u datogedon-wp-cron.service
```

Se probó una tarea temporal `datogedon_cron_probe` y se verificó su ejecución por el
servicio. Después se eliminaron el hook, la opción y el MU-plugin de prueba.
Para retirar el timer: habilitar primero el disparo por visitas eliminando la
constante `DISABLE_WP_CRON`, y después deshabilitar el timer. No restaurar toda la
base de datos para revertir esta configuración.

## Validación

`python3 tests/editorial.py` y `tests/editorial-abilities.php` usan datos sintéticos. Cubre privacidad,
frescura, archivo retirado, horarios, transición de cadencia, estado atómico,
calidad, límite diario, idempotencia y salida cero con programación incorrecta.
Las pruebas de orquestación simulan el redactor; la ejecución desatendida real del
24 de noviembre se verificó por sus borradores, imágenes y estados futuros remotos.


### Recuperación de verificadores y ciclos pendientes

El proceso Codex utiliza un perfil de permisos efímero `datogedon-editorial` que
extiende `:workspace` y habilita red para sus comandos. Se transmite por `-c` solo
a ese proceso; no modifica la configuración global ni elimina las protecciones
de escritura. `--search` habilita búsqueda, pero no concede por sí mismo red a
Python/los verificadores. Se comprobó DNS/HTTPS y un borrador real dentro del
sandbox con el mismo perfil (CLI 0.172.0).

El conteo compara todos los IDs anteriores, incluidos borradores pendientes de
otras ventanas. También reconoce un borrador ya existente que pasa a publicado
cuando pertenece a la ventana actual mediante `cycle_key`. Así una recuperación
no cuenta trabajo ajeno como una segunda publicación ni crea otra copia.

Un ciclo fallido requiere conciliación explícita: verificar WordPress, conservar
ID/editorial_id/miniatura, contrastar fuentes, validar el borrador y publicar el
mismo ID. Registrar el intento anterior y la recuperación en el libro de ciclos;
actualizar fechas remotas de la cola después de publicar y crear la constancia
`cycle-success` únicamente tras comprobar el resultado. No borrar intentos ni
relanzar publicaciones inciertas sin consultar su estado real.


### TikTok: México y música complementaria

Los nuevos briefs priorizan México; Colombia, Argentina y España sirven de
contraste. Español latino informal, sin perder rigor ni forzar regionalismos.
El gancho, intro de un segundo y outro aprobados se mantienen. La intro sustituye
un segundo de imagen del cuerpo: la narración y los subtítulos continúan, sin
silencio añadido. El maestro conserva la voz normalizada y, solo en noticias,
un identificador sonoro original de 480 ms. No incluye música de fondo; los sonidos
nativos de TikTok se añaden después cuando corresponde.

El redactor prepara `private/video-distribution-ID.json` junto al brief, con
candidatos musicales y evidencia fechada por país/período. En noticias consulta
las tendencias públicas mediante la búsqueda existente; sin evidencia registra
`needs_review`, sin bloquear publicación ni render. No se confunde popularidad
acumulada con crecimiento. No hay integración autenticada con Discovery API;
la selección y escucha final siguen siendo una revisión en TikTok.

Ganancia musical inicial entre -18 y -13 dB según densidad y escucha móvil;
no representa diferencia LUFS contra la voz. No se aplican cambios retroactivos
al video Rust aprobado ni a su borrador en TikTok. Las comparaciones registran
sonido/versión, nivel y resultados disponibles, sin inferir causalidad de una pieza.


### Publicación de videos y relación con artículos

Autorización editorial: noticias se publican al verificar el artículo público;
experiencias se programan a la fecha del artículo o después. Verificar el permalink
público y su estado, no solo la fecha planificada. Si el artículo aún es futuro,
la liberación del video queda pendiente de esa comprobación; programar dos sistemas
por reloj no asegura que WordPress esté disponible. La carga se hace en el Chrome
Datogedon autorizado, separada del redactor, y se verifica en Studio. Un intento
incierto requiere conciliación antes de otro envío.

La URL de TikTok confirmada se vincula en una sección del artículo original,
conservando título, slug y fecha de publicación. No se crea otro post ni una URL
vacía para el video programado. Por ahora la referencia es un enlace ligero:
no añade reproductores ni scripts de terceros al cargar la página. Una futura
biblioteca de videos podrá reutilizar estas relaciones sin duplicar artículos.


### Noticias y paleta de video

La habilidad editorial añade la etiqueta `Noticias` (`noticias`) a `kind=news`,
conservando las otras etiquetas y categorías. También se clasifica el archivo
previo de noticias, sin cambiar URLs ni fechas.

Renderer v6: fondos, paneles, texto e intro/outro neutros. El acento se limita a
la cifra o comparación central; la etiqueta de tema y el progreso son grises.
Se conserva el logo y el mastering. Los maestros ya aprobados no se reeditan.

Noticias usa una entrada rápida de logo/texto, cabecera y barrido horizontal,
con un identificador de dos notas sintetizado localmente. Se mezcla debajo de
la voz, con RMS máximo de un cuarto del de la narración durante ese intervalo,
antes de la normalización final a -16 LUFS. Experiencias conserva la entrada
tranquila, sin identificador sonoro. Ambas duran un segundo sobre voz existente.
Las revisiones se renderizan en otra carpeta; una actualización del renderer
no sobrescribe trabajos ya publicados, programados o en proceso de distribución.
