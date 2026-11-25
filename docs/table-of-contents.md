# Índice de artículos

Datogedon Reader genera el índice en PHP dentro de `the_content`, después de los
bloques y shortcodes. No modifica entradas, categorías, permalinks ni la base de
contenido. Se limita a la consulta principal de una entrada o página; se excluyen
extractos, archivos, feeds, administración y respuestas REST.

Un artículo de al menos 500 palabras y tres encabezados H2/H3 recibe un índice
contraído antes de su primera sección. El umbral evita ruido en noticias breves.
La lista agrupa los H3 bajo el H2 correspondiente; encabezados H1/H4–H6 conservan
anclas pero no se incluyen en la lista. `datogedon_reader_show_toc` permite ajustar
la política. Las anclas se generan también cuando no se muestra el índice.

El componente utiliza `details`, `summary`, `nav` y listas HTML. Funciona con teclado
y sin JavaScript; respeta modo oscuro, móvil y movimiento reducido. El JavaScript
existente mejora el foco al navegar, sin reemplazar fragmentos, historial ni enlaces.
No incorpora librerías ni recursos externos nuevos. No añade schema de FAQ ni
promete resultados enriquecidos por incluir un índice.

## Compatibilidad

Se conservan los IDs manuales y anclas internas existentes. La normalización de
fragmentos mantiene las opciones anteriores de TOC+ (`toc-options`): mayúsculas,
guiones bajos y sufijos. Si un encabezado ya tiene otro ID, se añade un alias del
fragmento compatible sin duplicar IDs. Se ignoran ejemplos literales y comentarios.

`[toc]` fuerza la ubicación del índice; soporta `label` y `start` (mínimo dos
secciones). `[no_toc]` lo oculta, conservando anclas. No se reproduce todo el panel
ni las opciones de TOC+. El inventario previo de producción encontró 103 entradas
/páginas, 16 IDs de sección y ningún shortcode o widget de TOC+ en uso.

`wp datogedon configure` desactiva exclusivamente TOC+ cuando el tema propio está
cargado. Antes comprueba dependencias de widgets y shortcodes de sitemap; si las
encuentra detiene la migración. El plugin y sus opciones se conservan. El diario
de despliegue registra su activación y posición en la lista; el rollback restaura
ese estado sin modificar la activación de otros plugins.

## Verificación y recuperación

CI instala la misma versión de TOC+ usada en producción (202609.1), compara
fragmentos contra su implementación real y prueba migración/restauración. El
navegador verifica escritorio/móvil, teclado, modo oscuro, funcionamiento sin JS,
jerarquía, anclas antiguas, visibilidad bajo la cabecera y exclusión de artículos
breves y REST. Los artículos de prueba solo se crean en bases sintéticas.

`scripts/toc-inventory.php`, mediante `wp eval-file`, produce un inventario de rutas,
fragmentos, shortcodes y widgets sin exportar el contenido de los artículos. Guardar
resultados en el directorio privado de operación y comparar los IDs antes/después.
El circuito existente de despliegue conserva el tema anterior, registra opciones y
comprueba todas las rutas publicadas. Una recuperación manual debe restaurar el
tema previo y el diario `options-before.json` de ese despliegue; reactivar TOC+ si
estaba activo. Purgar únicamente la caché HTML de esta aplicación. Nunca vaciar
la caché de objetos compartida ni borrar el plugin durante la migración.
