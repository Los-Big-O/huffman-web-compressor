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
4. Compara los endpoints de `app.py` con `docs/api.md` (contrato del frontend) y con
   `API.md` (documentación del backend del equipo). `tests/test_contrato_api.py` lo revisa.
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
simples. El backend (`huffman/formato.py` y los endpoints) lo subió un compañero a `main`;
mi frontend se conecta a él a través de `huffman/adaptador.py`.

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
app.py                  # Flask (equipo): sirve public/, endpoints /api/... y Gutenberg; 413 si > 4 MB
huffman/frecuencias.py  # calcular_frecuencias(bytes), describir_simbolo(byte)
huffman/arbol.py        # Nodo, construir_arbol(frecuencias)
huffman/codigos.py      # generar_codigos(raiz)
huffman/bits.py         # codificar, empaquetar, desempaquetar, decodificar (equipo)
huffman/formato.py      # (equipo) empaquetar_bigo, inspeccionar_bigo, descomprimir_bigo
huffman/adaptador.py    # (mío) agrega a las respuestas del equipo los campos de docs/api.md
public/                 # index.html, estilos.css y un .js por tarea (incluye gutenberg.js)
API.md                  # documentación del backend del equipo (todos sus campos)
docs/api.md             # contrato que usa el frontend
tests/                  # pruebas (test_adaptador, test_contrato_api, test_integridad, test_gutenberg son mías)
```

No hay `cli.py` en `main`. Revisa `main` por si el equipo cambia la estructura.

## Decisiones de diseño

- Huffman sobre BYTES (0–255), no caracteres: UTF-8 (acentos, ñ) se recupera idéntico.
- Desempate fijo en el heap: `(peso, orden_de_creacion, nodo)`; las hojas se crean en
  orden de byte. Así compresor y descompresor construyen el mismo árbol.
- Un solo símbolo distinto: raíz con la hoja a la izquierda, código "0". Texto vacío: sin errores.
- Se guarda la tabla de frecuencias (no el árbol); el árbol se reconstruye al leer.
- Métricas con el tamaño del `.bigo` completo (encabezado incluido).
- Ejemplo de referencia, verificado a mano: "ABRACADABRA" → A=0, C=100, D=101, B=110,
  R=111; 23 bits; 1 bit de relleno; bytes 6E 8A DC.

## Formato .bigo (versión 1 del equipo, `huffman/formato.py`, enteros big-endian)

| Campo | Tamaño | Contenido |
|---|---|---|
| Firma | 4 bytes | `BIGO` |
| Versión | 1 byte | 1 |
| Tamaño original | 8 bytes | bytes del texto original |
| Total de bits | 8 bytes | bits codificados válidos (el relleno se calcula: `(8 - total % 8) % 8`) |
| Hash SHA-256 | 32 bytes | del texto original (empieza en el byte 21) |
| Número de símbolos | 2 bytes | 0 a 256 |
| Tabla de frecuencias | 9 bytes × símbolo | 1 byte símbolo + 8 bytes frecuencia, ordenada por byte |
| Datos comprimidos | variable | bits empaquetados |

Encabezado fijo: 55 bytes. **Aún no guarda nombre original ni fecha**: se lo pedí al
equipo; mientras tanto el inspector los recibe en `null` y los oculta. Si el equipo cambia
`CABECERA_FIJA`, falla una prueba de `test_adaptador.py` que avisa actualizar el adaptador.

## Contrato de la API (detalle completo en docs/api.md)

Todos reciben `multipart/form-data` con el campo `archivo` y responden JSON; error →
400/413 con `{"error": "..."}`. Las respuestas traen los campos del equipo (ver `API.md`)
MÁS los del contrato, que agrega `huffman/adaptador.py`; no se quitan los del equipo.

Los campos grandes van una sola vez y con el nombre del equipo (`archivo_bigo_b64`,
`archivo_txt_b64`): así un libro de 3 MB cabe en los 4.5 MB de Vercel (lo prueba
`test_contrato_api.py`). Por la misma razón `/api/descomprimir` ya no manda `texto_recuperado`.

- `POST /api/comprimir` (.txt) → `nombre_original`, `nombre_bigo`, `metricas`, `tabla`,
  `arbol`, `bits_muestra`, `archivo_bigo_b64`.
- `POST /api/inspeccionar` (.bigo) → `archivo{nombre,extension,bytes}`, `formato{firma,version}`,
  `nombre_original` (null), `fecha` (null), `sha256`, `metricas`,
  `estructura[{campo,inicio,bytes}]`, `tabla`, `arbol`, `bits_muestra`, `hex_muestra`.
- `POST /api/descomprimir` (.bigo) → `nombre_original` (deducido del nombre del .bigo),
  `bytes`, `integro` (false con 200 si el hash no coincide; 400 si no se puede decodificar),
  `sha256_guardado`, `sha256_recuperado`, `archivo_txt_b64`.
- `metricas`: `original_bytes`, `comprimido_bytes`, `ahorro_bytes`, `reduccion_porcentaje`,
  `razon_compresion`, `simbolos_distintos`, `total_bits`, `bits_relleno`, `encabezado_bytes`.
- `tabla[]`: `byte`, `simbolo`, `frecuencia`, `porcentaje`, `codigo`, `longitud`, `bits_totales`.
- `arbol`: nodo interno `{peso, izquierdo, derecho}`; hoja `{peso, byte, simbolo}`.

Si el equipo cambia nombres o campos, se ajusta `huffman/adaptador.py`, no el frontend.

## Frontend (estilo "libro antiguo")

Papel crema, tinta café, acento vino (#7A1F2B); EB Garamond + Courier Prime. La página es
un libro con índice y 6 capítulos que siguen el flujo de la actividad:
I El texto (cargar) → II Las frecuencias → III El árbol → IV La compresión (métricas y
descarga) → V El códice (inspector) → VI La restitución (descomprimir y verificar).

Un archivo JS por tarea: `app.js` (estado compartido, utilidades, carga del .txt),
`gutenberg.js` (buscador de Project Gutenberg, también en el Capítulo I), `metricas.js`,
`tabla.js`, `arbol.js`, `inspector.js`, `descompresion.js`. `app.js` llama a cada módulo
solo si existe (`typeof fn === "function"`). Todo se construye con `textContent`, nunca
`innerHTML` con datos del usuario.

`gutenberg.js` usa `/api/gutenberg/buscar` y `/api/gutenberg/comprimir` (el servidor baja
el libro; máximo 3 MB y solo de `gutenberg.org` o sus subdominios). Como el navegador solo
recibe una vista previa, deja `estado.original = null` y el Capítulo VI verifica con
SHA-256 sin comparar byte a byte. Sus pruebas (`tests/test_gutenberg.py`) simulan la red.

## Material que ya existe fuera de `main`

- Rama `Damian` en GitHub: mi núcleo del algoritmo; ya se fusionó en `main` (PR #19).
- Rama `Damian-frontend`: adaptador, frontend e integridad (issues #2, #9–#13, #20).
- Zips en `d:\visual codes\`: `dia1-huffman.zip` y `frontend-huffman.zip` (ya copiado a
  `public/`). `dia2-huffman.zip` (respaldo del backend) no está ahí; ya no hace falta.

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
