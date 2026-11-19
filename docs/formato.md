# Formato `.bigo` (versión 1)

Formato binario propio del equipo **Los Big-O** para guardar un texto comprimido con
Huffman. Lo escribe y lo lee `huffman/formato.py` (`empaquetar_bigo`, `inspeccionar_bigo`,
`descomprimir_bigo`). El `.bigo` **no guarda el texto original**: solo lo necesario para
reconstruir el árbol y decodificar los bits.

Todos los enteros van en **big-endian** (el byte más significativo primero), que es lo que
indica el `>` en los `struct.Struct` del código.

## Estructura byte por byte

| Inicio | Tamaño | Campo | Tipo (`struct`) | Contenido |
|---:|---:|---|---|---|
| 0 | 4 | Firma | `4s` | Los bytes ASCII `BIGO` (`42 49 47 4F`). Si no están, el archivo se rechaza. |
| 4 | 1 | Versión | `B` | `1`. Otra versión se rechaza con "Versión de formato no soportada". |
| 5 | 8 | Tamaño original | `Q` | Bytes del texto original. Sirve para las métricas y para verificar la integridad. |
| 13 | 8 | Total de bits | `Q` | Bits codificados **válidos**. Con él se descartan los bits de relleno del último byte. |
| 21 | 32 | Hash SHA-256 | `32s` | Huella del texto original; se compara con la del texto recuperado. |
| 53 | 2 | Número de símbolos (N) | `H` | Bytes distintos del texto: 0 a 256. |
| 55 | 9 × N | Tabla de frecuencias | `B` + `Q` por entrada | N entradas ordenadas por byte: 1 byte del símbolo + 8 bytes de frecuencia. |
| 55 + 9N | resto | Datos comprimidos | — | Los códigos de Huffman de todo el texto, empaquetados de 8 en 8 bits. |

- **Encabezado fijo:** 55 bytes (`CABECERA_FIJA = struct.Struct(">4sBQQ32sH")`).
- **Encabezado total:** `55 + 9 × N` bytes. Las métricas usan el tamaño del `.bigo` completo,
  encabezado incluido.
- **Bits de relleno:** no se guardan; se calculan con `(8 - total_bits % 8) % 8`.

### Por qué se guarda la tabla y no el árbol

El árbol se puede reconstruir desde las frecuencias si el algoritmo siempre desempata igual
(ver "Desempate" abajo). Guardar la tabla es simple y de tamaño fijo por símbolo.

## Ejemplo: `ABRACADABRA`

Texto de 11 bytes, 5 símbolos distintos. Códigos (verificados a mano):

| Símbolo | Byte | Frecuencia | Código |
|---|---:|---:|---|
| A | `41` | 5 | `0` |
| B | `42` | 2 | `110` |
| R | `52` | 2 | `111` |
| C | `43` | 1 | `100` |
| D | `44` | 1 | `101` |

Total: 5·1 + 2·3 + 2·3 + 1·3 + 1·3 = **23 bits**.

### El archivo completo (103 bytes)

| Inicio | Campo | Bytes en hexadecimal | Significado |
|---:|---|---|---|
| 0 | Firma | `42 49 47 4F` | "BIGO" |
| 4 | Versión | `01` | 1 |
| 5 | Tamaño original | `00 00 00 00 00 00 00 0B` | 11 bytes |
| 13 | Total de bits | `00 00 00 00 00 00 00 17` | 23 bits → 1 bit de relleno |
| 21 | SHA-256 | `26 DF D8 16 1B 49 75 A5 B1 A2 C0 D8 5B 8C A4 08`<br>`C6 A1 57 58 08 4A 65 E3 12 BF B1 16 CD E5 19 BC` | huella de "ABRACADABRA" |
| 53 | Número de símbolos | `00 05` | 5 |
| 55 | Entrada 1 | `41 00 00 00 00 00 00 00 05` | A aparece 5 veces |
| 64 | Entrada 2 | `42 00 00 00 00 00 00 00 02` | B aparece 2 veces |
| 73 | Entrada 3 | `43 00 00 00 00 00 00 00 01` | C aparece 1 vez |
| 82 | Entrada 4 | `44 00 00 00 00 00 00 00 01` | D aparece 1 vez |
| 91 | Entrada 5 | `52 00 00 00 00 00 00 00 02` | R aparece 2 veces |
| 100 | Datos | `6E 8A DC` | los 23 bits + 1 de relleno |

### Cómo salen los datos `6E 8A DC`

```
A   B   R   A C   A D   A B   R   A
0 110 111   0 100 0 101 0 110 111 0      ← 23 bits

01101110  10001010  1101110 + 0          ← grupos de 8; el último se rellena con un 0
   6E        8A        DC
```

Al descomprimir, `desempaquetar` convierte `6E 8A DC` en 24 bits y se queda con los primeros
23 (el total guardado en el byte 13). Después `decodificar` recorre el árbol: `0` = izquierda,
`1` = derecha; al llegar a una hoja escribe su byte y vuelve a la raíz.

Este ejemplo muestra la limitación de los textos cortos: 11 bytes originales → 103 bytes
comprimidos, porque el encabezado (100 bytes) pesa más que lo que ahorra Huffman. Con textos
de varios KB el encabezado deja de importar y el archivo sí se reduce.

## Desempate (para que el árbol sea siempre el mismo)

`huffman/arbol.py` mete en la cola de prioridad tuplas `(peso, orden_de_creacion, nodo)`:

1. sale primero el nodo de menor peso;
2. si pesan lo mismo, el que se creó antes;
3. las hojas se crean en orden de byte (0, 1, 2, …).

Como el compresor y el descompresor leen la misma tabla y siguen las mismas reglas,
construyen exactamente el mismo árbol y, por lo tanto, los mismos códigos.

## Casos especiales

- **Un solo símbolo distinto** (`"aaaa"`): la raíz tiene la hoja a la izquierda y el código
  es `0`.
- **Texto vacío:** N = 0, total de bits = 0, sin datos; se descomprime a un texto vacío.
- **Bytes, no caracteres:** se cuentan bytes (0–255). Una "ñ" en UTF-8 son dos bytes
  (`C3 B1`) y cada uno tiene su código, así que cualquier texto se recupera idéntico.

## Validaciones al leer

| Problema | Resultado |
|---|---|
| Archivo más corto que 55 bytes | Error: demasiado pequeño |
| Firma distinta de `BIGO` | Error: firma inválida |
| Versión distinta de 1 | Error: versión no soportada |
| Tabla de frecuencias incompleta | Error: archivo corrupto |
| Bits que no llevan a una hoja | Error al decodificar (respuesta 400) |
| SHA-256 recuperado ≠ guardado | Se devuelve `integro: false` con las dos huellas (respuesta 200) |

## Pendiente

El formato v1 todavía no guarda el **nombre original** ni la **fecha de creación**. Para
agregarlos habría que crear la versión 2 (cambiar `VERSION_FORMATO` y `CABECERA_FIJA`) y
actualizar `huffman/adaptador.py`, cuya prueba avisa si cambia el encabezado.
