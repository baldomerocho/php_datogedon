# Datogedon

Código propio del blog [datogedon.com](https://datogedon.com): tema WordPress,
estructura editorial, SEO y capacidades de publicación MCP.

## Contenido

- `theme/datogedon-reader`: tema de lectura, navegación, perfiles y relacionados.
- `mu-plugins/datogedon-site.php`: identidad, schema, categorías y estructura editorial.
- `plugins/datogedon-editorial-mcp`: borradores, programación y medios por MCP.
- `tests`: comprobaciones de estructura HTTP y comportamiento en navegador.
- `scripts`: inventario de rutas, comparación y despliegue con recuperación.

No contiene WordPress core, credenciales, datos de usuarios, base de datos,
conversaciones de asistentes ni el archivo de publicaciones. El sitio y su contenido
se administran separadamente. La licencia del código no concede derechos sobre las
publicaciones, fotografías o marcas del sitio.

## Instalación y configuración

Requiere WordPress 6.9+, PHP 8.3+, Rank Math y el generador XML de sitemaps
existente. Copiar el tema a `wp-content/themes`, el MU-plugin a `wp-content/mu-plugins`
y la integración editorial a `wp-content/plugins`. No sustituir `wp-config.php`.

Activar el tema y ejecutar explícitamente `wp datogedon configure --owner=ID` con
un autor humano existente. Este comando configura las páginas y el menú editoriales;
sus textos se mantienen en el código. No cambia categorías ni la estructura de
permalinks de los artículos. Las rutas históricas de categorías sin `/category/`
redirigen a la versión canónica.

La configuración editorial no se ejecuta en cada petición. Los perfiles humanos
conservan sus logins; el nombre público y la biografía se configuran en WordPress.
El sitemap público se conserva en `/sitemap.xml`; Rank Math emite el JSON-LD y
el MU-plugin normaliza la identidad y las migas estructuradas.

## Comprobación

```sh
find theme mu-plugins plugins tests scripts -name '*.php' -print0 | xargs -0 -n1 php -l
python3 scripts/check-public-source.py
wp eval-file scripts/route-inventory.php > /ruta/privada/routes.json
python3 tests/seo.py https://tu-sitio.example /ruta/privada/routes.json
npm ci
npx playwright install chromium
SITE_URL=https://tu-sitio.example npm run test:browser
```

Los tests HTTP no certifican indexación ni resultados enriquecidos de Google.
Las métricas de laboratorio no sustituyen datos de campo Core Web Vitals.

## CI/CD

GitHub Actions valida PHP, instala WordPress con datos sintéticos en una base
efímera, compara rutas, comprueba SEO y prueba escritorio/móvil. El paquete generado
por el runner hospedado es inmutable por SHA de commit y tiene SHA-256.

Solo los pushes a `main` o ejecuciones manuales autorizadas de `main` llegan al
runner dedicado de despliegue. PRs y forks se ejecutan en runners hospedados y
no reciben acceso al host. El runner de producción descarga el paquete, valida
su digest y aplica únicamente el tema y extensiones de esta aplicación.

Los runners existentes están registrados en otros repositorios. Su ámbito de
GitHub no permite compartirlos con este repositorio personal; no se trasladó
ningún proyecto ni se modificaron runners ajenos.

Cada versión del tema queda en una carpeta nueva. Se conserva el tema anterior,
se registra una copia privada de las opciones afectadas y se comprueban las rutas
publicadas y la salud pública. Un fallo restaura código y configuración. El servidor
no compila imágenes ni reconstruye WordPress, y no reinicia otras aplicaciones.

El instalador privilegiado requiere `/etc/datogedon-deploy.json`, fuera de Git,
con `site_root`, `public_url`, `private_root`, `site_user`, `owner_id`, `owner_name`
y `owner_description`. El usuario del runner solo puede invocar el comando de
despliegue restringido. Los diarios y las copias de opciones nunca son artefactos públicos.

`workflow_dispatch` permite `exercise_rollback`: despliega el paquete y provoca
un fallo de comprobación para verificar la restauración. `[skip deploy]` en un
commit mantiene CI sin desplegar; no omite las validaciones.

## Autores

El registro público permanece desactivado. Las propuestas llegan por Contacto,
se preparan como borradores y se revisan antes de programarlas. Un colaborador
no tiene permiso de publicación; un editor gestiona la revisión y los medios.

## Licencia

GPL-2.0-or-later para el código propio. El tema parte del tema personalizado
Datogedon Reader existente; se mantienen sus créditos. WordPress y los plugins
de terceros conservan sus respectivas licencias y no se incluyen aquí.

## Analítica

La integración amplía el Matomo existente con navegación, búsquedas, progreso de
lectura y colaboración. Consulta [el catálogo de eventos y su validación](docs/analytics.md).
La API de informes se consulta con `scripts/matomo-audit.py`, usando un archivo
privado local; ningún token forma parte del sitio ni del repositorio.
