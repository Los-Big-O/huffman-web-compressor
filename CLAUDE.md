# Huffman Web Compressor

Aplicación web que comprime y descomprime archivos de texto con el algoritmo de Huffman
(técnica voraz), usando un formato de archivo propio `.bigo`. Proyecto de la materia
Análisis de Algoritmos (2026B).

## Reglas obligatorias

- El algoritmo de Huffman se implementa a mano. PROHIBIDO usar zlib, gzip, zipfile, bz2,
  lzma o cualquier biblioteca de compresión.
- Permitido de la biblioteca estándar: `heapq` (solo como cola de prioridad), `hashlib`
  (SHA-256), `struct` (empaquetar enteros del encabezado), `collections.Counter`.
- Nunca guardar el texto original dentro del archivo `.bigo`.
- Nada de servicios de pago: hosting, APIs y dependencias deben ser gratuitos.
- Yo debo poder explicar cada línea en clase: escribe código simple y legible, con
  comentarios en español que expliquen el *porqué*, no solo el *qué*.
- Antes de implementar algo grande, explícame el plan y espera mi confirmación.

## Tecnología

- Python 3 + Flask (backend), HTML/CSS/JavaScript sin frameworks (frontend). El árbol se dibuja con SVG propio.
- Deployment en Vercel (plan gratuito). Vercel detecta la app Flask en `app.py` (variable `app`)
  y sirve los archivos de `public/` desde su CDN (no usar el `static_folder` de Flask en Vercel).
- Libros: API pública Gutendex (https://gutendex.com/books?search=...). El backend
  descarga el texto del libro (evita bloqueos CORS del navegador).
- Pruebas con pytest.

## Estructura del proyecto

```
app.py                  # App Flask y endpoints /api/...
huffman/
  frecuencias.py        # Tabla de frecuencias por byte
  arbol.py              # Nodos, cola de prioridad y construcción voraz
  codigos.py            # Generación de códigos a partir del árbol
  bits.py               # Codificación, empaquetado y desempaquetado de bits
  formato_bigo.py       # Escritura y lectura del archivo .bigo
  compresor.py          # Funciones de alto nivel: comprimir() y descomprimir()
public/                 # Interfaz web: index.html, estilos.css, app.js
tests/                  # Pruebas pytest
docs/formato.md         # Especificación del formato .bigo
docs/pruebas/           # Evidencias de pruebas
```

## Decisiones de diseño

- Huffman trabaja sobre BYTES (0–255), no sobre caracteres. Así UTF-8 (acentos, ñ) se
  recupera idéntico.
- Desempate fijo en la cola de prioridad: menor frecuencia primero; en empate, el nodo
  creado antes (usar un contador incremental en la tupla del heap). El compresor y el
  descompresor deben construir siempre el mismo árbol.
- Caso especial: si el texto tiene un solo símbolo distinto, su código es "0".
- Texto vacío: debe manejarse sin errores.

## Formato .bigo (versión 1, enteros en big-endian)

| Campo                | Tamaño            | Contenido                                  |
|----------------------|-------------------|--------------------------------------------|
| Firma                | 4 bytes           | `BIGO`                                     |
| Versión              | 1 byte            | 1                                          |
| Longitud del nombre  | 2 bytes           | bytes del nombre original                  |
| Nombre original      | variable          | UTF-8                                      |
| Fecha de creación    | 8 bytes           | marca de tiempo Unix                       |
| Tamaño original      | 8 bytes           | bytes del texto original                   |
| Hash SHA-256         | 32 bytes          | del texto original                         |
| Número de símbolos   | 2 bytes           | 1 a 256                                    |
| Tabla de frecuencias | 5 bytes × símbolo | 1 byte símbolo + 4 bytes frecuencia        |
| Bits de relleno      | 1 byte            | bits sin uso en el último byte (0–7)       |
| Total de bits        | 8 bytes           | bits codificados válidos                   |
| Datos comprimidos    | variable          | bits empaquetados                          |

## Comandos

- Instalar dependencias: `pip install -r requirements.txt`
- Correr local: `python app.py` y abrir http://127.0.0.1:5000
- Pruebas: `pytest`

## Flujo de trabajo con Git

- Trabajo en mi rama personal; nunca hacer commit directo en `main`.
- Commits pequeños, mensajes en español que digan qué hace el cambio y el issue: `Construye la tabla de frecuencias (#3)`.
- No hagas `git push` ni abras pull requests sin que yo lo pida.
- Toda función del paquete `huffman/` debe tener al menos una prueba en `tests/`.
