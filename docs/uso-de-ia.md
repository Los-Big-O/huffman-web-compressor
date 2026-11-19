# Uso de IA

La actividad pide registrar qué se le pidió a la IA y cómo se validó el resultado.
Herramienta: Claude Code (modelo Claude Opus), usado por Damián en su rama.
En cada tarea, las decisiones fueron mías; la IA propuso, escribió código y lo probó,
y cada commit me lo explicó antes de hacerse.

## Antes de Claude Code: Claude en claude.ai

Estas partes se generaron conversando con Claude en claude.ai; yo copié el resultado al
repositorio, lo revisé y lo subí con commits míos.

### Planeación

- **Pedido:** dividir la actividad en tareas y días, decidir el reparto con el equipo y
  definir decisiones de diseño (Huffman sobre bytes, desempate fijo del árbol, guardar la tabla
  de frecuencias en lugar del árbol, contrato de la API entre backend y frontend).
- **Validación:** se contrastó con el enunciado de la actividad y con lo que el profesor
  indicó como primordial. El plan original de 4 días se ajustó después a lo que el equipo
  fue subiendo a `main`.

### Núcleo del algoritmo (día 1, rama `Damian`, fusionada en el PR #19)

- **Pedido:** frecuencias por byte, árbol de Huffman con cola de prioridad voraz (`heapq`),
  generación de códigos y codificación/empaquetado de bits, sin bibliotecas de compresión.
- **Resultado:** `huffman/frecuencias.py`, `arbol.py`, `codigos.py` y `bits.py`
  (`decodificar` lo agregó después el equipo).
- **Validación:** pruebas con pytest (`tests/test_frecuencias.py`, `test_arbol.py`,
  `test_codigos.py` y `test_bits.py`: 21 pruebas hoy) y el ejemplo "ABRACADABRA" verificado
  a mano (A=0, C=100, D=101, B=110, R=111; 23 bits; bytes `6E 8A DC`).

### Frontend (estilo "libro antiguo")

- **Pedido:** una interfaz sin frameworks con un capítulo por paso de la actividad, árbol
  dibujado en SVG propio y todo construido con `textContent` (nunca `innerHTML` con datos del
  usuario).
- **Validación:** prueba en el navegador del flujo completo (cargar, tabla, árbol, métricas,
  inspector, descompresión) antes de subirlo; después, de nuevo con el backend del equipo
  (ver 2026-11-17, punto 5).

## 2026-11-17 · Integración del backend del equipo con el frontend (rama `Damian-frontend`)

### 1. Revisar lo que subió el equipo a `main`

- **Pedido:** revisar los commits nuevos de `main`, correr las pruebas y decir si el backend
  cumple el contrato de `docs/api.md`.
- **Resultado:** el algoritmo es correcto, pero los nombres de los campos JSON no coinciden
  con el contrato del frontend; una prueba del equipo falla (espera compresión con un texto
  de 110 bytes, y el encabezado de 55 bytes + 9 por símbolo lo impide).
- **Validación:** `python -m pytest` (26 pasan, 1 falla); "ABRACADABRA" comparado con el
  ejemplo verificado a mano (códigos A=0, C=100, D=101, B=110, R=111 y bytes `6E 8A DC`);
  textos UTF-8, de un solo símbolo y vacío recuperados idénticos.

### 2. Adaptador al contrato (#20)

- **Pedido:** un adaptador en el backend que agregue los campos del contrato sin quitar los
  del equipo ni tocar sus pruebas.
- **Resultado:** `huffman/adaptador.py` y los endpoints de `app.py` conectados a él.
- **Decisión mía tras una medición de la IA:** con un libro de 3 MB, `/api/descomprimir`
  respondía 7.3 MB (el texto iba dos veces), más que el límite de 4.5 MB de Vercel. Pedí no
  duplicar los campos grandes: el frontend lee `archivo_bigo_b64` y `archivo_txt_b64` del
  equipo y se quitó `texto_recuperado` de la respuesta (ahora 4.0 MB).
- **Validación:** `tests/test_adaptador.py` (10 pruebas), `tests/test_contrato_api.py`
  (libro de 3 MB debajo de 4 500 000 bytes y recuperado byte a byte, claves del contrato,
  413); comparación prueba por prueba contra `origin/main`: las 26 que pasaban siguen pasando.

### 3. Import faltante en `bits.py` (#19)

- **Hallazgo de la IA:** `decodificar` usa `Nodo` en su firma sin importarlo. En Python 3.14
  funciona porque las anotaciones se evalúan tarde; en 3.12/3.13 la app no arrancaría.
- **Validación:** antes del arreglo, leer `decodificar.__annotations__` lanzaba `NameError`;
  después devuelve los tipos. Pruebas completas.

### 4. Integridad con `integro: false` (#20)

- **Pedido:** que `descomprimir_bigo` devuelva `integro: false` con las dos huellas en lugar
  de lanzar un error, para mostrarlas en la interfaz. Revisé el diff antes del commit.
- **Validación:** `tests/test_integridad.py` altera solo un byte del hash guardado: el texto
  se recupera idéntico pero `integro` es `false` y el endpoint responde 200. La prueba de
  corrupción del equipo sigue pasando (su error viene de la decodificación).

### 5. Frontend (#2, #9, #10, #11, #12, #13)

- **Pedido:** subir el frontend que ya tenía (estilo libro antiguo, un JS por capítulo),
  leer los campos grandes con el nombre del equipo y ocultar en el inspector los datos
  opcionales vacíos (nombre y fecha) sin mostrar "Invalid Date".
- **Validación:** `node --check` en los seis archivos JS; Flask sirve todos los archivos
  (200); prueba manual en el navegador hecha por mí con un texto pequeño (ABRACADABRA) y uno
  grande de Wikisource: carga, tabla, árbol, métricas, inspector y descompresión. Pendiente
  repetirla con un libro de Project Gutenberg (el sitio estaba en mantenimiento).

### Incidente

Durante la sesión, `huffman/formato.py` apareció duplicado (504 líneas en lugar de 251)
sin que la IA lo editara, probablemente por el editor. La IA se detuvo y avisó; lo restauré
con `git restore` y se verificaron las 251 líneas y las pruebas.

## 2026-11-18 · Revisión final contra la actividad (Claude Code)

### 1. Documentación del formato (`docs/formato.md`)

- **Pedido:** el formato `.bigo` del equipo byte por byte, con ABRACADABRA en hexadecimal.
- **Validación:** los bytes salen del `.bigo` real que genera `empaquetar_bigo`; el SHA-256 de
  "ABRACADABRA" se comprobó por fuera de Python con `sha256sum`.

### 2. Buscador de Project Gutenberg en el Capítulo I

- **Pedido:** usar `/api/gutenberg/buscar` y `/api/gutenberg/comprimir` desde la interfaz.
- **Validación:** `tests/test_gutenberg.py` simula las respuestas de Gutendex y Gutenberg
  (los sitios estaban en mantenimiento): búsqueda, compresión con los campos del contrato y
  descompresión idéntica. `node --check` del JavaScript. **Pendiente:** probarlo en el
  navegador cuando Gutenberg vuelva a estar disponible.

### 3. README

- **Pedido:** README completo con integrantes, deploy, algoritmo, resultados y limitaciones.
- **Validación:** los resultados de compresión se midieron con textos reales (y se
  verificó que cada uno se recupera idéntico); se comprobó que la URL del deploy responde.

### 4. Guía de pruebas mínimas (`docs/pruebas/README.md`)

- **Pedido:** una tabla para las cuatro pruebas mínimas, lista para mis capturas.
- **Validación:** las pruebas automáticas que cita existen y pasan.

### 5. Prueba del equipo que fallaba

- **Pedido:** corregir `test_flujo_api_comprimir_inspeccionar_descomprimir` (de Alan) con un
  texto más largo y documentar aparte la limitación de los textos cortos.
- **Hallazgo:** su última línea usaba `texto_recuperado`, que se quitó de la respuesta el
  2026-11-17; no se notaba porque la prueba fallaba antes. Ahora compara `archivo_txt_b64`.
- **Validación:** `python -m pytest` con 0 fallas (46 pruebas).

## Limitaciones conocidas

- El formato v1 del equipo no guarda nombre original ni fecha; se les pidió agregarlos.
- En textos muy cortos el `.bigo` pesa más que el original (lo documenta
  `test_texto_muy_corto_el_bigo_pesa_mas_que_el_original`).
