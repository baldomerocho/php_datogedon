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
