# Uso de IA

La actividad pide registrar qué se le pidió a la IA y cómo se validó el resultado.
Herramienta: Claude Code (modelo Claude Opus), usado por Damián en su rama.
En cada tarea, las decisiones fueron mías; la IA propuso, escribió código y lo probó,
y cada commit me lo explicó antes de hacerse.

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

## Limitaciones conocidas

- El formato v1 del equipo no guarda nombre original ni fecha; se les pidió agregarlos.
- La prueba `test_flujo_api_comprimir_inspeccionar_descomprimir` del equipo sigue fallando
  por usar un texto demasiado corto; no la modifiqué porque es del equipo.
