# Videos informativos locales

La producción corre en esta Mac, separada de la publicación en TikTok. Genera
borradores verticales 1080×1920, H.264/AAC, 30 fps, voz Gemini en español latino, gráficos
originales y subtítulos medidos por la duración de cada fragmento de narración.
No hay música, avatar ni clonación de voz. La información procede del artículo
público, con fecha real y créditos. Cada cifra lleva su alcance en pantalla.

Requiere FFmpeg con libass, una fuente Arial instalada en macOS y el entorno
Python aislado descrito por `editorial/video-requirements.txt` (solo Pillow).
La voz se genera con Gemini 3.8 Flash TTS, preset Algieba y estilo cálido de
narración tecnológica. El montaje y los subtítulos siguen en la Mac. Se retiraron
Piper y el modelo local rechazado por el usuario.

Las claves se leen únicamente de un dotenv privado con permisos 600, fuera de Git.
`PUBLIC_APIKEY` tiene prioridad; `APIKEY` es respaldo autorizado solo si la primera
responde HTTP 429. Un RetryInfo corto permite un reintento acotado de la primera;
si sigue agotada, se usa la segunda durante ese render. Errores de autenticación,
permisos, modelo, servidor o conexión NO cambian a la clave de pago. Un timeout
incierto no se repite automáticamente. El nombre de la variable no garantiza por
sí solo el estado de facturación del proyecto de Google.

Los audios se cachean por texto/modelo/voz/estilo. Reintentar un montaje aprovecha
las locuciones existentes. `tts-usage.json` registra el slot usado y contadores,
nunca las claves ni cuerpos de error del proveedor. Solo se envía el guion basado
en el artículo ya público. Los headers autenticados no se redirigen a otro host.

Configuración privada `video`: enabled, python, tts, output_dir, state_dir,
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
  --tts-config /private/gemini-voice-config.json
```

Salida: video.mp4, cover.jpg, subtitles.srt, caption.txt y manifest.json (fuentes,
modelo/voz, duración, hash y estado). Los WAV y guiones quedan locales. No guardar
conversaciones, credenciales, modelos ni renderizados en el repositorio público.

La cuenta solicitada es @datogedon. Metricool MCP es una opción por conectar;
no se ha autorizado una sesión ni publicado contenido en TikTok. Su documentación
indica MCP en Free y publicación TikTok, sujetos al límite del plan. Un usuario
público de TikTok no sustituye OAuth. Verificar cuenta, límites, metadatos y
requisitos de publicación al conectar; no crear un bot privado que eluda la
revisión de TikTok Direct Post. No habilitar publicación automática desde este
renderizador: solo produce material local para revisión.
