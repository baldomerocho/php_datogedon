# Interfaz de comentarios

La conversación usa el walker nativo de WordPress con listas sin numeración.
Cada respuesta identifica a su comentario padre y conserva los anclajes
`comment-ID` y `div-comment-ID`, el orden, la paginación y la moderación.

Las tarjetas agrupan avatar, nombre y fecha con bordes suaves y jerarquía tipográfica.
La referencia al padre y el nivel aparecen como metadatos discretos bajo el nombre;
en escritorio, la fecha queda alineada a la derecha. Cada respuesta tiene un conector
que termina junto al avatar, identifica al comentario padre por su nombre y muestra
su nivel explícito (la primera respuesta es nivel 1). Cada nivel conserva su
sangría: 32 px en escritorio y 16 px en móvil, sin aplanar niveles profundos. Los listados numerados escritos dentro de un comentario
conservan su formato: solo se elimina la numeración del árbol de conversación.
Los enlaces y palabras largos se ajustan a la tarjeta.

El formulario tiene etiquetas visibles, campos de tamaño legible y un acceso
directo desde la cabecera. Se carga `comment-reply` cuando la conversación está
abierta y tiene respuestas habilitadas. «Responder» mueve el formulario debajo
del comentario seleccionado y «Cancelar respuesta» lo devuelve a su lugar.

Las insignias se basan en el ID de usuario registrado: «Autor» para quien figura
como autor de la entrada y «Equipo» para el propietario configurado del sitio.
No se infiere identidad por el nombre público o el correo del comentarista.

CI crea una conversación sintética de cinco niveles y comprueba anchos de
320/390/1440, textos largos, modo claro/oscuro, listas, accesibilidad del formulario,
foco, respuesta/cancelación y ocultación de comentarios pendientes. Las pruebas
no envían comentarios. La verificación pública conserva un resumen hash de IDs,
padres y textos para comprobar que el rediseño no modifica la conversación.

## Participación

El enlace junto al título anuncia la conversación con su cantidad real. La sección
va antes de artículos relacionados y el formulario antes del listado de comentarios.
La pregunta invita a compartir experiencia y disentir sin ocultar los hilos.

En **Editar entrada → Conversación del artículo** se puede escribir una pregunta
específica y elegir un comentario destacado de una lista con autor y extracto (los 100
aprobados más recientes, además de la selección actual). La pregunta vacía usa
una invitación según la categoría; «Sin destacado» quita la selección. La selección es editorial, no una votación.
Solo se publica un extracto de comentarios aprobados pertenecientes a esa entrada;
si se moderan, borran o pasan a spam dejan de aparecer. El enlace abre el comentario
original, incluso con comentarios paginados. No se altera su texto ni posición.

Matomo recibe eventos `Discussion`: `view`, `open`, `start`, `reply`,
`featured_open`, `submit` y `received`. Los nombres contienen solamente un ID de
entrada o una etiqueta fija. `start` se envía una vez por página, al escribir;
`submit` es un intento enviado por el navegador. `received` usa un recibo de 120
segundos creado tras insertar un comentario válido (aprobado o pendiente), que
se consume al volver a la página. No equivale a publicación ni registra texto,
nombre o correo. No se envían avisos por email ni se añaden votaciones.
