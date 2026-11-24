# Interfaz de comentarios

La conversación usa el walker nativo de WordPress con listas sin numeración.
Cada respuesta identifica a su comentario padre y conserva los anclajes
`comment-ID` y `div-comment-ID`, el orden, la paginación y la moderación.

Las tarjetas agrupan avatar, nombre y fecha. Cada respuesta tiene un conector
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
