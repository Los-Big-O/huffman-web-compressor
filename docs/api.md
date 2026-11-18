# API de Huffman Web Compressor

Contrato entre el servidor (`app.py`) y la interfaz (`public/`). Si trabajas en la
interfaz, solo necesitas este documento: no hace falta entender el algoritmo.

Aquí están solo los campos que usa la interfaz. El backend del equipo responde además
sus propios campos (ver `API.md` en la raíz); `huffman/adaptador.py` agrega los de este
contrato. Los dos campos grandes (`archivo_bigo_b64` y `archivo_txt_b64`) conservan el
nombre del equipo y van **una sola vez**, para que un libro de 3 MB quepa en el límite de
4.5 MB por respuesta de Vercel.

Todos los endpoints reciben el archivo con `multipart/form-data` en un campo llamado
**`archivo`** y responden JSON. Si algo sale mal, responden con código 400 (o 413 si
el archivo pasa de 4 MB) y `{"error": "mensaje para mostrar al usuario"}`.

Ejemplo desde JavaScript:

```js
const formulario = new FormData();
formulario.append("archivo", archivoElegido);   // un File de un <input type="file">
const respuesta = await fetch("/api/comprimir", { method: "POST", body: formulario });
const datos = await respuesta.json();
if (!respuesta.ok) alert(datos.error);
```

## Objetos que se repiten

**`metricas`**

| Campo | Tipo | Significado |
|---|---|---|
| `original_bytes` | entero | Tamaño del .txt original |
| `comprimido_bytes` | entero | Tamaño del .bigo completo (encabezado incluido) |
| `ahorro_bytes` | entero | `original - comprimido` (negativo si el .bigo quedó más grande) |
| `reduccion_porcentaje` | número | Porcentaje de reducción, con 2 decimales |
| `razon_compresion` | número | `original / comprimido` |
| `simbolos_distintos` | entero | Bytes distintos del texto |
| `total_bits` | entero | Bits codificados válidos |
| `bits_relleno` | entero | Bits de relleno del último byte (0–7) |
| `encabezado_bytes` | entero | Tamaño del encabezado del .bigo |

Convertir a KB o MB es tarea de la interfaz: `bytes / 1024` y `bytes / 1024 / 1024`.

**`tabla`**: una fila por símbolo, de mayor a menor frecuencia.

```json
{"byte": 65, "simbolo": "A", "frecuencia": 5, "porcentaje": 45.45,
 "codigo": "0", "longitud": 1, "bits_totales": 5}
```

`simbolo` ya viene legible: `"espacio"`, `"salto de línea"`, o `"0xC3"` para bytes que
no son ASCII (por ejemplo, cada mitad de una "ñ" en UTF-8).

**`arbol`**: nodos anidados. Un nodo interno tiene `peso`, `izquierdo` (rama "0") y
`derecho` (rama "1"); una hoja tiene `peso`, `byte` y `simbolo`. En un texto de un solo
símbolo, `derecho` es `null`.

```json
{"peso": 11,
 "izquierdo": {"peso": 5, "byte": 65, "simbolo": "A"},
 "derecho": {"peso": 6, "izquierdo": {...}, "derecho": {...}}}
```

## `POST /api/comprimir`

Recibe un `.txt`. Responde:

| Campo | Contenido |
|---|---|
| `nombre_original` | `"quijote.txt"` |
| `nombre_bigo` | `"quijote.bigo"` (nombre sugerido para descargar) |
| `metricas` | Ver arriba |
| `tabla` | Ver arriba |
| `arbol` | Ver arriba |
| `bits_muestra` | Primeros 256 bits **válidos** en grupos de 8: `"01101110 10001010 1101110"` (el último grupo puede tener menos de 8: el relleno no se muestra) |
| `archivo_bigo_b64` | El archivo .bigo completo, en base64 |

Para descargar el .bigo en el navegador:

```js
const bytes = Uint8Array.from(atob(datos.archivo_bigo_b64), c => c.charCodeAt(0));
const enlace = document.createElement("a");
enlace.href = URL.createObjectURL(new Blob([bytes]));
enlace.download = datos.nombre_bigo;
enlace.click();
```

## `POST /api/inspeccionar`

Recibe un `.bigo`. Lee su encabezado **sin descomprimir el texto**. Responde:

| Campo | Contenido |
|---|---|
| `archivo` | `{"nombre", "extension", "bytes"}` del archivo recibido |
| `formato` | `{"firma": "BIGO", "version": 1}` |
| `nombre_original` | Nombre del .txt que se comprimió, o `null` si el formato no lo guarda |
| `fecha` | Fecha de creación, ISO 8601 en UTC, o `null` si el formato no la guarda |
| `sha256` | Huella guardada del texto original (hexadecimal) |
| `metricas` | Ver arriba |
| `estructura` | Lista de secciones del archivo: `{"campo", "inicio", "bytes"}` |
| `tabla` | Tabla de frecuencias con los códigos **reconstruidos** |
| `arbol` | Árbol **reconstruido** desde la tabla de frecuencias |
| `bits_muestra` | Primeros 256 bits válidos (igual que en `/api/comprimir`) |
| `hex_muestra` | Primeros 32 bytes comprimidos en hexadecimal: `"6E 8A DC"` |

Por ahora el formato v1 del equipo no guarda nombre ni fecha, así que los dos llegan
como `null` y la interfaz oculta esas filas.

## `POST /api/descomprimir`

Recibe un `.bigo`. Responde:

| Campo | Contenido |
|---|---|
| `nombre_original` | Nombre para descargar el texto recuperado, deducido del nombre del `.bigo` (`libro.bigo` → `libro.txt`) |
| `bytes` | Tamaño del texto recuperado |
| `integro` | `true` si el SHA-256 del texto recuperado coincide con el guardado; `false` si no |
| `sha256_guardado` | Huella que venía en el archivo |
| `sha256_recuperado` | Huella calculada sobre el texto recuperado |
| `archivo_txt_b64` | Los bytes recuperados, en base64 |

Si las huellas no coinciden, la respuesta es `200` con `integro: false`, para que la
interfaz muestre las dos huellas. Si el archivo está tan dañado que no se puede
decodificar, la respuesta es `400` con el error.

Para mostrar el texto y descargarlo:

```js
const bytes = Uint8Array.from(atob(datos.archivo_txt_b64), c => c.charCodeAt(0));
const texto = new TextDecoder("utf-8").decode(bytes);   // para mostrarlo
const blob = new Blob([bytes], { type: "text/plain" });  // para descargarlo idéntico
```

## Probar sin interfaz

```
python -m pytest    # incluye tests/test_contrato_api.py, que revisa este contrato
```
