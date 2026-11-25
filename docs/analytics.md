# Medición de Datogedon

El plugin Matomo existente gestiona visitas, búsqueda interna, descargas y enlaces
salientes del sitio ID 1. El tema añade eventos mediante la misma cola `_paq`:
no inicia otro tracker ni duplica `trackPageView` o `trackSiteSearch`.

| Categoría / acción | Qué representa | Etiqueta / valor |
| --- | --- | --- |
| `Navigation/article_open` | Abrir una tarjeta de artículo | `post:ID` del destino |
| `Navigation/related_open` | Abrir un relacionado | `post:ID` del destino |
| `Navigation/section_open` | Abrir una sección desde menú o portada | sección fija |
| `Navigation/open` | Abrir menú móvil | `mobile_menu` |
| `Search/open` | Abrir el buscador de cabecera | `header` |
| `Search/submit` | Enviar una búsqueda | `header`, `hero` o `results` |
| `Search/autocomplete_select` | Elegir una sugerencia | `post:ID` del destino |
| `Search/results` | Mostrar resultados de búsqueda | `found` / `empty`, cantidad |
| `Interface/theme_change` | Cambiar tema claro/oscuro | `light` / `dark` |
| `Reading/progress_50` | Alcanzar el 50 % del cuerpo con al menos 10 s en primer plano | `post:ID`, 50 |
| `Reading/progress_90` | Alcanzar el 90 % del cuerpo con al menos 30 s en primer plano | `post:ID`, 90 |
| `Collaboration/open` | Abrir Colabora | ubicación del enlace |
| `Collaboration/contact_open` | Abrir Contacto | ubicación del enlace |

Los hitos se emiten una vez por carga de artículo. Se mide el cuerpo, sin contar
cabecera, relacionados, comentarios ni pie. El tiempo de pestaña oculta o sin foco
no cuenta. Estos hitos indican exposición al contenido; no demuestran comprensión.
Los eventos de colaboración indican intención, no un formulario enviado con éxito.

Las etiquetas de los eventos nuevos no incluyen texto escrito, emails, títulos,
URLs con parámetros, identificadores personales ni contenido de formularios.
Matomo conserva el contexto habitual de la página, incluida su URL. Las palabras
buscadas siguen el seguimiento nativo ya configurado en Matomo. Los eventos pasan por ese tracker y
sus decisiones de consentimiento/exclusión; no hay un envío alternativo ni cookies
adicionales. Si Matomo está bloqueado o ausente, la navegación sigue funcionando.

## Validación

CI usa contenido sintético y una cola de Matomo interceptada. Comprueba interacciones,
ausencia de duplicados, lectura en primer plano, respuestas de autocompletado fuera
de orden y navegación por teclado, sin enviar datos de CI a Matomo.

Tras desplegar se comprueban solicitudes reales y su almacenamiento mediante la
API de informes. Las pruebas públicas generan tráfico y eventos de prueba; no se
borran registros de visitantes. Los informes agregados pueden actualizarse después
del registro en vivo: comprobar `live_site_events` para una prueba reciente.

```sh
chmod 600 /ruta/privada/matomo.env
python3 scripts/matomo-audit.py --env /ruta/privada/matomo.env
```

El archivo contiene `APIKEY=...`; nunca se añade a Git. Basta acceso de lectura al
sitio 1. El token viaja por POST HTTPS y no se instala en WordPress, JavaScript ni
GitHub Actions. La salida omite IPs, IDs de visitantes y términos de búsqueda.

Para consultar el rendimiento, filtrar por categoría en Comportamiento → Eventos.
Los IDs `post:ID` corresponden al ID de la entrada en WordPress. Separar aperturas,
progreso de lectura e intención de colaboración al interpretar los resultados.

## Conversaciones

`Discussion/view` registra ver la cabecera; `open`, el acceso a participar;
`start`, comenzar a escribir una vez por página; `reply`, elegir responder;
`featured_open`, abrir el comentario destacado. Usan solamente `post:ID`.
`submit` registra el intento de envío; `received`, un recibo de inserción aceptada
(aprobada o pendiente), consumido una vez mediante cookie de 120 segundos con
valor fijo. No indica aprobación, no mide todo envío si el navegador bloquea
analítica y no incluye contenido, nombres ni correo. No se inicializa otro tracker.
