# Huffman Web Compressor — contexto del proyecto

Aplicación web que comprime y descomprime archivos de texto con el algoritmo de Huffman
(técnica voraz) y un formato de archivo propio `.bigo`. Actividad integradora de
Análisis de Algoritmos (2026B). Equipo **Los Big-O**. Trabajo con Damián (rama personal).

## Al iniciar cada sesión (hazlo antes de proponer cambios)

Mis compañeros suben código a `main` sin avisar, a veces directo y sin pull request.
El plan original de 4 días ya no aplica: me adapto a lo que ellos van subiendo.

1. `git fetch` y `git status`: en qué rama estoy y si hay cambios sin commit.
2. `git log --oneline origin/main -15`: qué subió el equipo desde la última vez.
3. Revisa esos cambios y córrelos: `python -m pytest`.
4. Compara los endpoints de `app.py` con `docs/api.md` (si existe). El frontend depende de ese contrato.
5. Dime en pocas líneas qué cambió, si algo se rompió y qué conviene hacer después.

La fuente de verdad es el código actual de `main`, no este archivo. Si algo aquí ya no
coincide con el código, avísame y propón actualizar este archivo.

## Lo que pide la actividad (resumen)

- Entrada: subir un `.txt` local. Búsqueda en Project Gutenberg: **opcional** (el profesor
  dijo que no es primordial; si se hace, usar la API pública Gutendex desde el backend).
- Huffman implementado por el equipo: frecuencias → cola de prioridad → árbol voraz →
  códigos → codificar → archivo comprimido real → descomprimir sin el `.txt` original.
- Formato propio `.bigo`, documentado, con versión, info para reconstruir el árbol,
  datos comprimidos, bits válidos del último byte, tamaño original y metadatos.
- Métricas en la interfaz: tamaño original y comprimido (bytes y KB/MB), ahorro,
  % de reducción, razón de compresión, número de símbolos.
- Visualización: tabla de frecuencias, código de cada símbolo y árbol de Huffman.
- Inspector: con solo el `.bigo`, mostrar nombre/extensión, versión, tamaños, ahorro, %,
  símbolos, tabla, códigos, árbol reconstruido, total de bits y bits parciales; después,
  botón explícito para DESCOMPRIMIR, ver el texto y descargarlo como `.txt`.
- Integridad: recuperado idéntico al original (usamos SHA-256 + comparación byte a byte).
- Pruebas mínimas documentadas: texto pequeño, libro de Gutenberg, integridad, archivo nuevo.
- GitHub: README completo, documentación del formato, evidencias, URL del deploy,
  uso de IA, limitaciones. GitHub Projects con Backlog → Por hacer → En progreso →
  En revisión → Terminado. Deploy público gratuito (Vercel).
- En la revisión me pueden preguntar por cualquier línea: "la IA lo generó" no cuenta.

Reparto acordado con el profesor: yo hago lo primordial (carga del `.txt`, frecuencias,
cola de prioridad y árbol, visualización, frontend); mis compañeros eligen issues más
simples. Un compañero dijo que haría el backend; su entrega es incierta, así que tengo
un respaldo listo (ver abajo).

## Reglas obligatorias

- Huffman a mano. PROHIBIDO usar zlib, gzip, zipfile, bz2, lzma o cualquier biblioteca de
  compresión. Permitido: `heapq` (solo como cola de prioridad), `hashlib`, `struct`.
- Nunca guardar el texto original dentro del `.bigo`.
- Nada de servicios de pago.
- Código simple y legible, con comentarios en español que expliquen el porqué.
- Antes de algo grande, explícame el plan y espera mi confirmación.
- Si el código de un compañero rompe algo o no sigue el contrato, dímelo antes de "arreglarlo".

## Tecnología y estructura

- Python 3 + Flask. Vercel detecta la app en `app.py` (variable `app`) y sirve `public/`
  desde su CDN. Límite de Vercel: 4.5 MB por petición y respuesta.
- Frontend: HTML/CSS/JavaScript sin frameworks; el árbol se dibuja con SVG propio.
- Pruebas: pytest (`pytest.ini` con `pythonpath = .`).

```
app.py                  # Flask: sirve public/ y los endpoints /api/...
cli.py                  # python cli.py comprimir libro.txt / descomprimir libro.bigo
huffman/frecuencias.py  # calcular_frecuencias(bytes), describir_simbolo(byte)
huffman/arbol.py        # Nodo, construir_arbol(frecuencias)
huffman/codigos.py      # generar_codigos(raiz)
huffman/bits.py         # codificar, empaquetar, desempaquetar, decodificar
huffman/formato_bigo.py # escribir_bigo(...), leer_bigo(bytes)
huffman/compresor.py    # comprimir(datos, nombre), descomprimir(archivo)
huffman/vista.py        # tabla_simbolos, arbol_a_dict, calcular_metricas (para JSON)
public/                 # index.html, estilos.css y un .js por capítulo
docs/api.md             # contrato entre backend y frontend
tests/                  # pruebas
```

Esta es la estructura que yo preparé; la del equipo puede ser distinta. Revisa `main`.

## Decisiones de diseño

- Huffman sobre BYTES (0–255), no caracteres: UTF-8 (acentos, ñ) se recupera idéntico.
- Desempate fijo en el heap: `(peso, orden_de_creacion, nodo)`; las hojas se crean en
  orden de byte. Así compresor y descompresor construyen el mismo árbol.
- Un solo símbolo distinto: raíz con la hoja a la izquierda, código "0". Texto vacío: sin errores.
- Se guarda la tabla de frecuencias (no el árbol); el árbol se reconstruye al leer.
- Métricas con el tamaño del `.bigo` completo (encabezado incluido).
- Ejemplo de referencia, verificado a mano: "ABRACADABRA" → A=0, C=100, D=101, B=110,
  R=111; 23 bits; 1 bit de relleno; bytes 6E 8A DC.

## Formato .bigo (versión 1, enteros big-endian)

| Campo | Tamaño | Contenido |
|---|---|---|
| Firma | 4 bytes | `BIGO` |
| Versión | 1 byte | 1 |
| Longitud del nombre | 2 bytes | bytes del nombre original |
| Nombre original | variable | UTF-8 |
| Fecha de creación | 8 bytes | marca de tiempo Unix |
| Tamaño original | 8 bytes | bytes del texto original |
| Hash SHA-256 | 32 bytes | del texto original |
| Número de símbolos | 2 bytes | 0 a 256 |
| Tabla de frecuencias | 5 bytes × símbolo | 1 byte símbolo + 4 bytes frecuencia, ordenada por byte |
| Bits de relleno | 1 byte | 0–7 |
| Total de bits | 8 bytes | bits codificados válidos |
| Datos comprimidos | variable | bits empaquetados |

## Contrato de la API (detalle completo en docs/api.md)

Todos reciben `multipart/form-data` con el campo `archivo` y responden JSON; error →
400/413 con `{"error": "..."}`.

- `POST /api/comprimir` (.txt) → `nombre_original`, `nombre_bigo`, `metricas`, `tabla`,
  `arbol`, `bits_muestra`, `archivo_bigo_base64`.
- `POST /api/inspeccionar` (.bigo) → `archivo{nombre,extension,bytes}`, `formato{firma,version}`,
  `nombre_original`, `fecha`, `sha256`, `metricas`, `estructura[{campo,inicio,bytes}]`,
  `tabla`, `arbol`, `bits_muestra`, `hex_muestra`.
- `POST /api/descomprimir` (.bigo) → `nombre_original`, `bytes`, `integro`,
  `sha256_guardado`, `sha256_recuperado`, `texto_base64`.
- `metricas`: `original_bytes`, `comprimido_bytes`, `ahorro_bytes`, `reduccion_porcentaje`,
  `razon_compresion`, `simbolos_distintos`, `total_bits`, `bits_relleno`, `encabezado_bytes`.
- `tabla[]`: `byte`, `simbolo`, `frecuencia`, `porcentaje`, `codigo`, `longitud`, `bits_totales`.
- `arbol`: nodo interno `{peso, izquierdo, derecho}`; hoja `{peso, byte, simbolo}`.

Si el backend del equipo usa otros nombres, lo más simple suele ser adaptar los
endpoints a este contrato (o una función adaptadora en el backend), no reescribir el frontend.

## Frontend (estilo "libro antiguo")

Papel crema, tinta café, acento vino (#7A1F2B); EB Garamond + Courier Prime. La página es
un libro con índice y 6 capítulos que siguen el flujo de la actividad:
I El texto (cargar) → II Las frecuencias → III El árbol → IV La compresión (métricas y
descarga) → V El códice (inspector) → VI La restitución (descomprimir y verificar).

Un archivo JS por capítulo: `app.js` (estado compartido, utilidades, carga del .txt),
`metricas.js`, `tabla.js`, `arbol.js`, `inspector.js`, `descompresion.js`. `app.js` llama
a cada módulo solo si existe (`typeof fn === "function"`). Todo se construye con
`textContent`, nunca `innerHTML` con datos del usuario.

## Material que ya existe fuera de `main`

- Rama `Damian` en GitHub: mi núcleo del algoritmo (5 commits del día 1, 23 pruebas).
  Nunca se fusionó en `main`; puede tener conflictos con lo que subió el equipo.
- `dia2-huffman.zip` (respaldo del backend): formato_bigo, compresor, vista, endpoints,
  cli.py, docs/api.md; 52 pruebas pasando. Úsalo solo si el backend del equipo no llega.
- `frontend-huffman.zip`: `public/` completo + `docs/api.md`, probado en navegador.
- Los zips están en mi computadora; si los necesitas, pídeme la ruta.

## Flujo de trabajo con Git

- Nunca hagas commit directo en `main`. Trabajo en una rama mía y abro pull request.
- Los commits son míos: antes de cada commit explícame qué contiene para que lo entienda.
- Commits pequeños, mensajes en español con el issue: `Muestra la tabla de frecuencias (#10)`.
- No hagas `git push` ni abras pull requests sin que yo lo pida.
- Nunca reescribas historia publicada (`push --force`, `rebase` de ramas compartidas).
- GitHub cuenta mis contribuciones cuando los commits llegan a `main`: recuérdame el merge.

## Comandos

- Instalar: `python -m pip install -r requirements.txt`
- Correr local: `python app.py` → http://127.0.0.1:5000
- Pruebas: `python -m pytest`

## Uso de IA (lo pide la actividad)

Registra en `docs/uso-de-ia.md` qué se le pidió a la IA en cada tarea y cómo se validó
(pruebas, conteo a mano, comparación de hashes). Al cerrar una tarea, hazme 3 preguntas
como si fueras el profesor para comprobar que entiendo el código.
