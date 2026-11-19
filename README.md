# Huffman Web Compressor

Aplicación web que comprime y descomprime archivos de texto con el **algoritmo de Huffman**
(técnica voraz), implementado a mano, y guarda el resultado en un formato binario propio:
**`.bigo`**. Actividad integradora de Análisis de Algoritmos (2026B).

**Aplicación en línea:** https://huffman-web-compressor-lemon.vercel.app/

## Equipo Los Big-O

- Aldo Damián Gutiérrez Medina
- Alan Arturo Uribe Pérez
- Karol Nungaray Escobedo

## Qué hace

La página es un libro con seis capítulos que siguen el proceso completo:

| Capítulo | Qué se hace |
|---|---|
| I · El texto | Cargar un `.txt` del equipo o buscar un libro en Project Gutenberg. |
| II · Las frecuencias | Tabla con cada símbolo, su frecuencia, porcentaje, código y bits totales. |
| III · El árbol | El árbol de Huffman dibujado en SVG; al pasar sobre una hoja se resalta su código. |
| IV · La compresión | Tamaño original y comprimido (bytes y KB/MB), ahorro, % de reducción, razón de compresión, símbolos; descarga del `.bigo`. |
| V · El códice | Inspector: con **solo el `.bigo`** muestra versión, tamaños, métricas, mapa de secciones, tabla, árbol reconstruido, total de bits y bits de relleno. |
| VI · La restitución | Botón explícito para descomprimir, verificación de integridad (SHA-256 y comparación byte a byte) y descarga del `.txt` recuperado. |

## Cómo ejecutarlo

Probado con Python 3.14.

```bash
python -m pip install -r requirements.txt   # Flask y pytest
python app.py                               # abre http://127.0.0.1:5000
python -m pytest                            # pruebas automatizadas
```

## El algoritmo

Huffman asigna códigos binarios más cortos a los símbolos más frecuentes. Trabajamos con
**bytes** (0–255), no con caracteres: así un texto UTF-8 con acentos o ñ se recupera idéntico.

| Paso | Archivo | Qué hace | Complejidad |
|---|---|---|---|
| 1. Frecuencias | `huffman/frecuencias.py` | Cuenta cuántas veces aparece cada byte. | O(n) |
| 2. Árbol (voraz) | `huffman/arbol.py` | Cola de prioridad (`heapq`): saca los dos nodos de menor peso, los une y repite hasta dejar la raíz. | O(k log k) |
| 3. Códigos | `huffman/codigos.py` | Recorre el árbol: izquierda = `0`, derecha = `1`. | O(k) |
| 4. Codificar y empaquetar | `huffman/bits.py` | Sustituye cada byte por su código y agrupa los bits de 8 en 8. | O(n · L) |
| 5. Formato `.bigo` | `huffman/formato.py` | Escribe encabezado, tabla de frecuencias y datos; lee y valida al descomprimir. | O(n · L) |
| 6. Decodificar | `huffman/bits.py` | Recorre el árbol bit por bit hasta cada hoja. | O(n · L) |

*n* = bytes del texto, *k* = símbolos distintos (máximo 256), *L* = longitud promedio del código.

**Por qué es voraz:** en cada paso toma la decisión que parece mejor en ese momento (unir los
dos nodos más ligeros) y nunca la deshace; para Huffman esa elección local da el código
prefijo óptimo.

**Desempate:** la cola guarda `(peso, orden_de_creacion, nodo)` y las hojas se crean en orden
de byte. Así el descompresor, que solo tiene la tabla de frecuencias, construye exactamente el
mismo árbol que el compresor.

**Ejemplo verificado a mano:** `ABRACADABRA` → A=`0`, B=`110`, R=`111`, C=`100`, D=`101`;
23 bits, 1 bit de relleno, datos `6E 8A DC`.

No se usa ninguna biblioteca de compresión (zlib, gzip, zipfile, bz2, lzma): solo `heapq` como
cola de prioridad, `hashlib` para SHA-256 y `struct` para escribir enteros binarios.

## Formato `.bigo`

Firma `BIGO`, versión, tamaño original, total de bits válidos, hash SHA-256, tabla de
frecuencias y datos comprimidos. El texto original **no** se guarda. Detalle byte por byte,
con el ejemplo de ABRACADABRA en hexadecimal: **[docs/formato.md](docs/formato.md)**.

## Resultados de compresión

Medidos con `empaquetar_bigo` sobre textos reales. El tamaño comprimido es el del `.bigo`
completo, encabezado incluido. En todos los casos el texto recuperado fue idéntico (SHA-256).

| Texto | Original (bytes) | `.bigo` (bytes) | Reducción | Razón | Símbolos |
|---|---:|---:|---:|---:|---:|
| `ABRACADABRA` | 11 | 103 | −836.36 % | 0.11 | 5 |
| Frase corta en español (57 bytes) | 57 | 320 | −461.40 % | 0.18 | 26 |
| `CLAUDE.md` de este repositorio (español) | 10,287 | 7,436 | 27.71 % | 1.38 | 100 |
| `LICENSE.txt` de Python 3.14 (inglés) | 35,407 | 23,267 | 34.29 % | 1.52 | 82 |
| `NEWS.txt` de Python 3.14 (inglés, 2.1 MB) | 2,233,611 | 1,428,976 | 36.02 % | 1.56 | 148 |

En textos cortos el `.bigo` pesa **más** que el original: el encabezado mide 55 bytes más 9 por
cada símbolo distinto. A partir de unos pocos KB el ahorro de Huffman supera al encabezado.

Las pruebas mínimas de la actividad (texto pequeño, libro de Gutenberg, integridad y archivo
nuevo), con capturas: **[docs/pruebas/README.md](docs/pruebas/README.md)**.

## Tecnologías

- **Backend:** Python 3 y Flask.
- **Frontend:** HTML, CSS y JavaScript sin frameworks; el árbol se dibuja con SVG propio.
  Tipografías EB Garamond y Courier Prime (Google Fonts).
- **Pruebas:** pytest.
- **Deploy:** Vercel (plan gratuito). Búsqueda de libros con la API pública Gutendex.

## Estructura

```
app.py                 # servidor Flask: página y endpoints /api/...
huffman/               # algoritmo: frecuencias, arbol, codigos, bits, formato
huffman/adaptador.py   # campos que usa la interfaz (contrato de docs/api.md)
public/                # interfaz: index.html, estilos.css y un .js por capítulo
docs/                  # formato, API, uso de IA y pruebas
tests/                 # pruebas automatizadas
```

## Documentación

- [docs/formato.md](docs/formato.md): formato `.bigo` byte por byte.
- [docs/api.md](docs/api.md): contrato entre el servidor y la interfaz.
- [API.md](API.md): todos los campos que responde el backend.
- [docs/pruebas/README.md](docs/pruebas/README.md): pruebas mínimas y evidencias.
- [docs/uso-de-ia.md](docs/uso-de-ia.md): qué se hizo con IA y cómo se validó.

## Uso de IA

Usamos Claude (en claude.ai y en Claude Code) para planear, generar código, documentar y
revisar. Todo se validó con pruebas automatizadas, ejemplos verificados a mano, comparación
de hashes y pruebas en el navegador. El registro por tarea está en
[docs/uso-de-ia.md](docs/uso-de-ia.md).

## Limitaciones

- **Textos cortos:** el encabezado (55 bytes + 9 por símbolo) hace que el `.bigo` pese más que
  el original; la reducción solo aparece a partir de unos pocos KB.
- **Tamaño máximo de 3 MB:** Vercel acepta como máximo 4.5 MB por petición y por respuesta. Al
  descomprimir, el texto viaja en base64 (4/3 de su tamaño), así que el servidor rechaza los
  `.txt` y los libros de Gutenberg de más de 3 MB (error 413). Los `.bigo` pueden medir hasta
  3 MB + 4 KB, porque llevan el encabezado además del texto comprimido.
- **Nombre y fecha no se guardan:** el formato v1 todavía no incluye el nombre original ni la
  fecha de creación; el inspector oculta esas filas.
- **Project Gutenberg** depende de que gutendex.com y gutenberg.org estén disponibles. Con un
  libro de Gutenberg la integridad se verifica con SHA-256, pero no byte a byte, porque el
  navegador no descarga el libro original.
