# Automatización editorial

El código del ejecutor vive en `editorial/`; la cola, las fichas, los manifiestos,
las credenciales y los logs permanecen en una carpeta privada externa al repositorio.
La fuente activa es Claude local. Una fuente retirada puede conservar su archivo
histórico en `archived_sources`, sin conexión de red ni fingir actividad reciente.

## Ejecución en la Mac

El LaunchAgent `com.datogedon.editorial-daily` llama a `editorial/runtime.py` a las
13:00, America/Guatemala. `RunAtLoad` permite recuperar una ejecución al iniciar
sesión después de esa hora. Antes de las 13:00 no genera contenido. Un registro
privado de éxito diario impide repetir el trabajo si se vuelve a lanzar el proceso.
La Mac debe estar disponible para recolectar y redactar; no hay un agente en la nube
con acceso a sus conversaciones. Las entradas ya programadas dependen del servidor.

```sh
python3 editorial/runtime.py --state-dir /ruta/privada/editorial
python3 editorial/runtime.py --state-dir /ruta/privada/editorial --health
```

El estado necesita `editorial-config.json`, `queue.json`, `DAILY-TASK.txt` basado
en `editorial/task.txt` y el transporte MCP ya autorizado. Las credenciales locales
existentes se leen de `~/.local/share/datogedon-mcp/credentials.json`; nunca se copian
a Git ni se imprimen. Los logs se guardan con permisos 600 y la carpeta privada 700.

El flujo conserva las fases existentes de redacción y escritura MCP:

1. Recolecta muestras acotadas, sin inputs/resultados de herramientas ni razonamiento
   interno. Redacta URLs, rutas, IPs y credenciales en la evidencia privada.
2. Fusiona continuaciones por identidad, prefiriendo actividad reciente antes que
   longitud de la muestra. Mantiene la procedencia y distingue el archivo retirado.
3. Concilia la cola con WordPress por lectura REST, porque `ai/get-post-details`
   no expone estado, fecha o miniatura. No cambia fechas ni textos remotos.
4. Consulta todas las entradas futuras y las publicadas hoy. Reserva los primeros
   horarios libres con margen de 30 minutos, sin superar dos entradas diarias.
5. Codex usa el guion editorial, la evidencia y MCP para preparar borradores,
   imágenes originales y programación. La revisión mantiene los títulos concretos,
   la atribución de herramientas/modelos y la distinción de decisiones humanas/IA.
6. `check-post.py` verifica borrador y programación. El padre vuelve a comprobar
   estado, fecha, imágenes y calidad; salir con código cero no equivale a éxito.

El modo de recuperación prepara hasta dos historias por ejecución. Al volver al
ritmo de una diaria no se mueven las entradas que ya estuvieran programadas. Los
horarios son de publicación (08:00/16:00), diferentes de la recolección a las 13:00.
Las muestras sin evidencia suficiente quedan pendientes, sin inventar una historia.
Los controles automáticos de forma no sustituyen la revisión narrativa y de privacidad.

Una ejecución fallida conserva el progreso. El lock evita redactores simultáneos;
el límite de 45 minutos termina también sus procesos hijos. No hay reintentos ciegos
de publicación. `--force` se reserva a una ejecución manual deliberada; no se usa
para repetir automáticamente un resultado incierto. El editorial_id estable evita
crear otra entrada al reintentar la misma historia mediante MCP.

## Comprobación y avisos

`com.datogedon.editorial-health` ejecuta `--health` a las 14:00. Comprueba ejecución
verificada del día, cola futura, fechas vencidas, miniaturas y metadatos. Un fallo
solicita una notificación local, como máximo una por tipo y día. No envía emails ni
mensajes externos. La presentación del aviso depende de los permisos de macOS.

Consultar `daily-status.json`, `editorial-health.json`, `private/last-success.json`
y `private/editorial-calendar.json` en el estado privado. Los registros publicados
se marcan como tales localmente: una fecha antigua no queda eternamente «programada».

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

`python3 tests/editorial.py` usa únicamente datos sintéticos. Cubre privacidad,
frescura, archivo retirado, horarios, transición de cadencia, estado atómico,
calidad, límite diario, idempotencia y salida cero con programación incorrecta.
Las pruebas de orquestación simulan el redactor; la ejecución desatendida real del
24 de noviembre se verificó por sus borradores, imágenes y estados futuros remotos.
