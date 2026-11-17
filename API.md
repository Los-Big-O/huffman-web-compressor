# Documentacion de la API Backend (Formato `.bigo`)

Todas las rutas responden en formato JSON. En caso de error (`400` o `502`), devuelven `{"error": "Mensaje descriptivo"}`

## 1. Comprimir archivo `.txt` o texto directo
- **Endpoint:** `POST /api/comprimir`
- **Entrada (opcion A - archivo):** `FormData` con campo `archivo` (`.txt`)
- **Entrada (opcion B - texto):** JSON `{"texto": "ABRACADABRA", "nombre_archivo": "muestra.txt"}`
- **Respuesta (`200 OK`):**
  - `nombre_original`, `nombre_salida` (`.bigo`), `version` (`"BIGO v1"`), `sha256`
  - `metricas`: `{tamano_original_bytes, tamano_original_legible, tamano_comprimido_bytes, tamano_comprimido_legible, ahorro_bytes, ahorro_legible, reduccion_porcentaje, razon_compresion, simbolos_unicos, total_bits, tamano_cabecera_bytes, tamano_datos_bytes, bits_relleno}`
  - `tabla`: lista de objetos `{byte, simbolo, frecuencia, porcentaje, codigo, longitud_bits}`
  - `arbol`: nodo raiz recursivo `{peso, simbolo, etiqueta, es_hoja, izquierdo, derecho}`
  - `archivo_bigo_b64`: contenido binario del `.bigo` codificado en Base64 para descarga

## 2. Buscar libros en Project Gutenberg
- **Endpoint:** `GET /api/gutenberg/buscar?q=termino`
- **Respuesta (`200 OK`):** `{"libros": [{"id", "titulo", "autores", "descargas", "url_txt"}]}`

## 3. Descargar y comprimir libro de Project Gutenberg
- **Endpoint:** `POST /api/gutenberg/comprimir`
- **Entrada:** JSON `{"url_txt": "...", "titulo": "..."}`
- **Respuesta (`200 OK`):** Misma estructura que `/api/comprimir` mas `"vista_previa_texto"`

## 4. Inspeccionar archivo `.bigo` (sin texto original)
- **Endpoint:** `POST /api/inspeccionar`
- **Entrada:** `FormData` con campo `archivo` (`.bigo`)
- **Respuesta (`200 OK`):**
  - `nombre_archivo`, `extension`, `version`, `sha256_original`
  - `metricas`, `tabla`, `arbol`
  - `vista_binaria`: cadena legible con los primeros 64 bytes empaquetados en binario

## 5. Descomprimir `.bigo` y verificar integridad
- **Endpoint:** `POST /api/descomprimir`
- **Entrada:** `FormData` con campo `archivo` (`.bigo`)
- **Respuesta (`200 OK`):**
  - `nombre_salida` (`*_recuperado.txt`), `integro` (`true`), `sha256_esperado`, `sha256_calculado`, `tamano_recuperado`
  - `texto_recuperado`: texto plano recuperado
  - `archivo_txt_b64`: archivo `.txt` en Base64 para descarga directa