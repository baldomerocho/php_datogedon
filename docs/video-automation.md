# Videos informativos locales

La producción corre en esta Mac, separada de la publicación en TikTok. Genera
borradores verticales 1080×1920, H.264/AAC, 30 fps, voz genérica es_MX, gráficos
originales y subtítulos medidos por la duración de cada fragmento de narración.
No hay música, avatar ni clonación de voz. La información procede del artículo
público, con fecha real y créditos. Cada cifra lleva su alcance en pantalla.

Requiere FFmpeg con libass, una fuente Arial instalada en macOS y el entorno
Python aislado descrito por `editorial/video-requirements.txt`. La voz Piper
`es_MX-ald-medium` tiene tarjeta de modelo con dataset Unlicense y modelo base
CC0; conservar su MODEL_CARD junto al modelo fuera de Git. No se usan las voces
del sistema de Apple para contenido público ni se contratan APIs.

Configuración privada `video`: enabled, python, model, output_dir, state_dir,
account. Noticias hereda solo esta configuración técnica desde el estado principal.
Tras publicar, el redactor prepara `private/video-brief-ID.json` y el padre
registra un trabajo por artículo. Los resultados quedan `ready_for_review`, nunca
publicados. Si falta el guion o falla el montaje, el artículo sigue publicado y
el trabajo queda pendiente/fallido; no se repite la publicación del artículo.
No hay sondeo constante ni un servicio nuevo por video.

```sh
/path/to/video-venv/bin/python editorial/video.py \
  --brief /private/video-brief-ID.json \
  --output /local/video-ID \
  --model /local/es_MX-ald-medium.onnx
```

Salida: video.mp4, cover.jpg, subtitles.srt, caption.txt y manifest.json (fuentes,
modelo, duración, hash y estado). Los WAV y guiones quedan locales. No guardar
conversaciones, credenciales, modelos ni renderizados en el repositorio público.

La cuenta solicitada es @datogedon. Metricool MCP es una opción por conectar;
no se ha autorizado una sesión ni publicado contenido en TikTok. Su documentación
indica MCP en Free y publicación TikTok, sujetos al límite del plan. Un usuario
público de TikTok no sustituye OAuth. Verificar cuenta, límites, metadatos y
requisitos de publicación al conectar; no crear un bot privado que eluda la
revisión de TikTok Direct Post. No habilitar publicación automática desde este
renderizador: solo produce material local para revisión.
