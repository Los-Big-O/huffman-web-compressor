# Documentacion de la API Backend (Formato `.bigo`)

Todas las rutas responden en formato JSON. En caso de error (`400`, `413` o `502`), devuelven `{"error": "Mensaje descriptivo"}`

- `413`: la peticion pasa de 4 MB (Vercel acepta como maximo 4.5 MB por peticion y por respuesta).
- Ademas de sus campos, las respuestas incluyen los campos del contrato que usa el frontend
  (`docs/api.md`); los agrega `huffman/adaptador.py`. Abajo se marcan como *(contrato)*.
- Los campos grandes (el `.bigo` y el texto recuperado en Base64) van **una sola vez**, para que
  un libro de 3 MB quepa en el limite de Vercel.

## 1. Comprimir archivo `.txt` o texto directo
- **Endpoint:** `POST /api/comprimir`
- **Entrada (opcion A - archivo):** `FormData` con campo `archivo` (`.txt`)
- **Entrada (opcion B - texto):** JSON `{"texto": "ABRACADABRA", "nombre_archivo": "muestra.txt"}`
- **Respuesta (`200 OK`):**
  - `nombre_original`, `nombre_salida` (`.bigo`), `version` (`"BIGO v1"`), `sha256`
  - `nombre_bigo` *(contrato)*: igual a `nombre_salida`
  - `metricas`: `{tamano_original_bytes, tamano_original_legible, tamano_comprimido_bytes, tamano_comprimido_legible, ahorro_bytes, ahorro_legible, reduccion_porcentaje, razon_compresion, simbolos_unicos, total_bits, tamano_cabecera_bytes, tamano_datos_bytes, bits_relleno}`
    mas *(contrato)* `{original_bytes, comprimido_bytes, simbolos_distintos, encabezado_bytes}` con los mismos valores
  - `tabla`: lista de objetos `{byte, simbolo, frecuencia, porcentaje, codigo, longitud_bits}`
    mas *(contrato)* `longitud` (igual a `longitud_bits`) y `bits_totales` (`frecuencia × longitud`)
  - `arbol` *(contrato)*: nodo interno `{peso, izquierdo, derecho}`; hoja `{peso, byte, simbolo}` (sin `izquierdo`).
    Con un solo simbolo distinto, la raiz tiene `derecho: null`. Texto vacio: `null`
  - `bits_muestra` *(contrato)*: primeros 256 bits validos en grupos de 8 (`"01101110 10001010 1101110"`)
  - `archivo_bigo_b64`: contenido binario del `.bigo` codificado en Base64 para descarga

## 2. Buscar libros en Project Gutenberg
- **Endpoint:** `GET /api/gutenberg/buscar?q=termino`
- **Respuesta (`200 OK`):** `{"libros": [{"id", "titulo", "autores", "descargas", "url_txt"}]}`

## 3. Descargar y comprimir libro de Project Gutenberg
- **Endpoint:** `POST /api/gutenberg/comprimir`
- **Entrada:** JSON `{"url_txt": "...", "titulo": "..."}`
- **Respuesta (`200 OK`):** Misma estructura que `/api/comprimir` mas `"vista_previa_texto"`
- **Errores:**
  - `400` si el dominio de `url_txt` no es `gutenberg.org` o un subdominio suyo (se revisa el
    dominio, no basta con que el texto aparezca en la URL), si no es `http`/`https`, o si una
    redireccion lleva fuera de Project Gutenberg
  - `413` si el libro pesa mas de 3 MB (con mas, la respuesta pasaria el limite de 4.5 MB de Vercel)
  - `502` si no se pudo descargar el libro

## 4. Inspeccionar archivo `.bigo` (sin texto original)
- **Endpoint:** `POST /api/inspeccionar`
- **Entrada:** `FormData` con campo `archivo` (`.bigo`)
- **Respuesta (`200 OK`):**
  - `nombre_archivo`, `extension`, `version`, `sha256_original`
  - `metricas`, `tabla`, `arbol`: igual que en `/api/comprimir`, reconstruidos desde la tabla de frecuencias
  - `vista_binaria`: cadena legible con los primeros 64 bytes empaquetados en binario
  - *(contrato)* `archivo`: `{nombre, extension, bytes}` del `.bigo` recibido
  - *(contrato)* `formato`: `{firma: "BIGO", version: 1}`
  - *(contrato)* `nombre_original`, `fecha`: `null` por ahora (el formato v1 aun no los guarda)
  - *(contrato)* `sha256`: igual a `sha256_original`
  - *(contrato)* `estructura`: secciones del archivo `[{campo, inicio, bytes}]`
  - *(contrato)* `bits_muestra`: primeros 256 bits validos; `hex_muestra`: primeros 32 bytes en hexadecimal (`"6E 8A DC"`)

## 5. Descomprimir `.bigo` y verificar integridad
- **Endpoint:** `POST /api/descomprimir`
- **Entrada:** `FormData` con campo `archivo` (`.bigo`)
- **Respuesta (`200 OK`):**
  - `nombre_salida` (`*_recuperado.txt`), `integro` (`true` o `false`), `sha256_esperado`, `sha256_calculado`, `tamano_recuperado`
  - `archivo_txt_b64`: texto recuperado en Base64, para mostrarlo y para descargarlo identico.
    El texto ya no se envia tambien en plano (`texto_recuperado`): duplicado, un libro de 3 MB
    producia una respuesta de 7.3 MB
  - *(contrato)* `nombre_original`: deducido del nombre del `.bigo` (`libro.bigo` → `libro.txt`)
  - *(contrato)* `bytes`, `sha256_guardado`, `sha256_recuperado`: iguales a `tamano_recuperado`, `sha256_esperado`, `sha256_calculado`
  - Si el SHA-256 no coincide, responde `200` con `integro: false` y las dos huellas para compararlas.
    Si los datos están tan dañados que no se pueden decodificar, responde `400` con el error