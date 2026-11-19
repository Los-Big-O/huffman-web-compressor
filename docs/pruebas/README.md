# Pruebas mínimas y evidencias

Las cuatro pruebas que pide la actividad, hechas en la aplicación en línea
(https://huffman-web-compressor-lemon.vercel.app/). Las capturas van en
`docs/pruebas/capturas/` con el nombre que indica cada sección.

## Resumen

| # | Prueba | Archivo usado | Original | `.bigo` | Reducción | Símbolos | Integridad | Resultado |
|---|---|---|---:|---:|---:|---:|---|---|
| 1 | Texto pequeño | `abracadabra.txt` | | | | | | |
| 2 | Libro de Project Gutenberg | | | | | | | |
| 3 | Integridad (`.bigo` alterado) | | | | | | | |
| 4 | Archivo nuevo | | | | | | | |

En **Integridad** anota: "SHA-256 ✓ · byte a byte ✓", "SHA-256 ✓" (Gutenberg no permite la
comparación byte a byte) o "Alterado ✗". En **Resultado**: ✅ si salió lo esperado, ❌ si no.

## 1. Texto pequeño

**Objetivo:** comprobar el algoritmo con un ejemplo que se puede verificar a mano.

1. Crea `abracadabra.txt` con el texto `ABRACADABRA` (sin salto de línea al final).
2. Cárgalo en el Capítulo I.
3. Revisa la tabla (II), el árbol (III) y las métricas (IV).
4. Descomprime en el Capítulo VI.

**Esperado:** códigos A=`0`, B=`110`, R=`111`, C=`100`, D=`101`; 23 bits y 1 de relleno;
11 bytes → 103 bytes (el `.bigo` pesa más: el encabezado ocupa 100 bytes); datos en
hexadecimal `6E 8A DC` (se ven en el Capítulo V); sellos "Íntegro" e "Idéntico byte a byte".

| Captura | Archivo |
|---|---|
| Tabla de frecuencias y códigos | `capturas/1-tabla.png` |
| Árbol | `capturas/1-arbol.png` |
| Métricas | `capturas/1-metricas.png` |
| Restitución con los dos sellos | `capturas/1-restitucion.png` |

<!-- Pega aquí las capturas, por ejemplo: ![Tabla](capturas/1-tabla.png) -->

**Observaciones:**

## 2. Libro de Project Gutenberg

**Objetivo:** comprimir un texto largo y real, y ver que el ahorro supera al encabezado.

1. En el Capítulo I busca un libro (por ejemplo, "Cervantes") y pulsa «Comprimir este libro».
   Si el buscador no responde, descarga el libro como *Plain Text UTF-8* desde gutenberg.org y
   cárgalo como `.txt`.
2. Revisa las métricas (IV), descarga el `.bigo` e inspecciónalo (V).
3. Descomprime (VI).

**Esperado:** reducción positiva (en textos reales medimos entre 28 % y 36 %); sello
"Íntegro". Si el libro vino del buscador, no aparece la comparación byte a byte; si se cargó
como `.txt`, también aparece "Idéntico byte a byte".

| Captura | Archivo |
|---|---|
| Búsqueda o libro cargado | `capturas/2-libro.png` |
| Métricas | `capturas/2-metricas.png` |
| Inspector | `capturas/2-inspector.png` |
| Restitución | `capturas/2-restitucion.png` |

**Observaciones:**

## 3. Integridad

**Objetivo:** comprobar que un `.bigo` modificado se detecta.

1. Comprime cualquier texto y descarga su `.bigo`.
2. Ábrelo con un editor hexadecimal (por ejemplo, la extensión *Hex Editor* de VS Code) y cambia
   el **byte 21** (el primero del hash SHA-256; el editor lo muestra en la posición `0x15`).
   Guárdalo con otro nombre.
3. Inspecciónalo en el Capítulo V y descomprímelo en el VI.

**Esperado:** sello "Alterado" y las dos huellas SHA-256 distintas. Si en lugar del hash se
cambia un byte de los datos comprimidos, el archivo puede quedar imposible de decodificar y
aparece un mensaje de error: también cuenta como detección.

| Captura | Archivo |
|---|---|
| Byte cambiado en el editor hexadecimal | `capturas/3-hex.png` |
| Sello "Alterado" con las dos huellas | `capturas/3-alterado.png` |

**Observaciones:**

## 4. Archivo nuevo

**Objetivo:** usar un texto que no se usó durante el desarrollo, con acentos y ñ.

1. Elige un `.txt` nuevo en español (por ejemplo, de Wikisource) de al menos unos KB.
2. Comprímelo, descarga el `.bigo` y **recarga la página**.
3. Carga solo el `.bigo` en el Capítulo V y descomprímelo en el VI, sin el `.txt` original.
4. Abre el `.txt` descargado y compáralo con el original.

**Esperado:** el inspector muestra tabla, árbol y métricas con solo el `.bigo`; sello
"Íntegro"; los acentos y la ñ se ven bien en el texto recuperado.

| Captura | Archivo |
|---|---|
| Métricas del archivo nuevo | `capturas/4-metricas.png` |
| Inspector con solo el `.bigo` | `capturas/4-inspector.png` |
| Texto recuperado con acentos | `capturas/4-recuperado.png` |

**Observaciones:**

## Pruebas automatizadas relacionadas

Cada prueba manual tiene una automática equivalente (`python -m pytest`):

| Prueba manual | Pruebas automáticas |
|---|---|
| 1. Texto pequeño | `tests/test_adaptador.py::test_abracadabra_coincide_con_el_ejemplo_verificado_a_mano` |
| 2. Libro de Gutenberg | `tests/test_gutenberg.py`, `tests/test_contrato_api.py::test_un_libro_de_3_mb_cabe_en_el_limite_de_vercel` |
| 3. Integridad | `tests/test_integridad.py`, `tests/test_formato.py::test_detecta_archivo_corrupto_por_hash` |
| 4. Archivo nuevo | `tests/test_formato.py::test_ciclo_completo_comprimir_inspeccionar_descomprimir` |
