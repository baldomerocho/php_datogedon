# Guion y visuales de Shorts — v3

La noticia parte de un actor y un hecho que despierta curiosidad, con contexto
humano documentado: circunstancias, intereses, demanda de comunidad o una
consecuencia inesperada. El gancho promete algo que el corto entrega. No atribuir
ataques, indignación general o motivos sin evidencia; una condición que cambia
la conclusión aparece pronto. La documentación verificada del artículo precede
al corto. El blog conserva el desarrollo y los antecedentes.

Las experiencias enseñan una situación, evidencia, mecanismo y resultado útil.
Preferencias personales (por ejemplo Docker o entorno local) aparecen en el corto
solo cuando cambian esa explicación. Objetivo de prueba 25–40 segundos, hasta 60
si hace falta; 40–130 palabras, sin acelerar ni rellenar. Cierre hacia un artículo
o guía ya públicos, después de cumplir la promesa.

## Recursos visuales

Cada brief v3 tiene una escena `evidence`: captura, imagen de la fuente o ejemplo
rotulado. El recurso se busca primero en fuentes verificadas y después en otras
fuentes citadas. Los archivos locales se usan si existen y son pertinentes;
no se buscan imágenes en sesiones privadas ni se captura el escritorio.

`capture-evidence.mjs` abre una instancia temporal sin sesión, con Playwright ya
instalado (ruta a node_modules en `video.evidence_node_modules`). Ejemplo:

```
node capture-evidence.mjs --modules-root /ruta/al/node_modules --url https://fuente.example/anuncio --selector main --credit Autor --output ~/claude-activity-audit/videos/evidence/ID-fuente.png
```

El helper captura un fragmento, registra origen, fecha y hash en `.png.json` y
rechaza destinos de red privados. Para una imagen autorizada, `--image-url`
conserva la imagen entera. Se registra crédito y fundamento de uso; la atribución
por sí sola no concede licencia. Un ejemplo dibujado desde documentación pública
se etiqueta como tal y no se presenta como ejecución real ni prueba fotografiada.
Los hashes y el directorio acotado se verifican antes de renderizar.

La portada publicada del artículo se recupera desde su medio destacado. Se adapta
a 1080×1920 conservando toda la imagen, con relleno en gris y titular legible en
la zona central. No se estira ni se recortan rostros. `cover.jpg` se aplica donde
la plataforma lo permite. YouTube puede limitar la selección de portada de Shorts
a su app; se registra esa limitación sin bloquear ni fingir una subida de miniatura.

## Evaluación temprana

El manifiesto identifica la tanda mediante `experiment`; no se regeneran videos
ya entregados. La primera tanda prueba el conjunto de mejoras, no un experimento
causal que permita atribuir el resultado a la música o al gancho por separado.

Cortes deseados a 1, 3, 6 y 24 horas desde confirmación pública; revisión a 48 horas.
El publicador puede registrar cifras ya visibles al realizar sus subidas, sin
abrir paneles extra ni sondear. `metrics.json` guarda edad real, URL y evidencia;
retención, compartidos u otros campos ausentes quedan en null. No se reconstruyen
mediciones pasadas ni se comparan vistas de edades distintas como equivalentes.
El calendario de publicación no se aumenta. La música sigue la política v2:
una confirmación de ajustes guardados, sin análisis de audio por rutina.
