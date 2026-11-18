"use strict";

/* inspector.js: Capítulo V. Examina un .bigo SIN descomprimirlo: lee su
   encabezado y reconstruye la tabla, los códigos y el árbol desde las frecuencias.
   La descompresión es un paso aparte y explícito (Capítulo VI). */

// Un color por sección del archivo, para el "mapa" del .bigo.
const COLORES_SECCION = ["#7A1F2B", "#B07A2A", "#2F5D3A", "#23395B", "#6B4423", "#8C7652", "#2B1D12"];

// "2026-11-17T03:19:00Z" -> fecha local legible. Si no viene fecha o no es
// válida, devuelve null para que esa fila se oculte (nunca "Invalid Date").
function formatearFecha(texto) {
  if (!texto) return null;
  const fecha = new Date(texto);
  return Number.isNaN(fecha.getTime()) ? null : fecha.toLocaleString("es-MX");
}

function crearFicha(datos) {
  const ficha = crear("dl", "ficha");
  const filas = [
    ["Archivo", datos.archivo.nombre],
    ["Extensión", datos.archivo.extension || "(sin extensión)"],
    ["Formato", `${datos.formato.firma} · versión ${datos.formato.version}`],
    // Opcionales: el formato v1 del equipo aún no guarda nombre ni fecha.
    ["Texto original", datos.nombre_original],
    ["Creado", formatearFecha(datos.fecha)],
    ["Huella SHA-256", datos.sha256 ? `${datos.sha256.slice(0, 16)}…` : null],
  ];
  for (const [clave, valor] of filas) {
    // Un dato que no viene (null, undefined o "") no se muestra.
    if (valor === null || valor === undefined || valor === "") continue;
    const fila = crear("div");
    const dd = crear("dd", null, valor);
    if (clave === "Huella SHA-256") dd.title = datos.sha256;
    fila.append(crear("dt", null, clave), dd);
    ficha.append(fila);
  }
  return ficha;
}

// Barra proporcional: cada sección del archivo ocupa el ancho que le toca.
function crearMapa(estructura, total) {
  const contenedor = crear("div");
  const mapa = crear("div", "mapa");
  mapa.setAttribute("role", "img");
  mapa.setAttribute("aria-label", "Proporción de cada sección dentro del archivo .bigo");
  const leyenda = crear("table", "mapa-leyenda");

  estructura.forEach((seccion, i) => {
    const color = COLORES_SECCION[i % COLORES_SECCION.length];
    const porcentaje = (100 * seccion.bytes) / total;

    const bloque = crear("span");
    bloque.style.background = color;
    bloque.style.flexGrow = String(Math.max(seccion.bytes, 1));
    bloque.title = `${seccion.campo}: ${seccion.bytes} bytes`;
    mapa.append(bloque);

    const fila = crear("tr");
    const muestra = crear("span", "muestra");
    muestra.style.background = color;
    const celdaMuestra = crear("td");
    celdaMuestra.append(muestra);
    fila.append(
      celdaMuestra,
      crear("td", null, seccion.campo),
      crear("td", "numero", `byte ${seccion.inicio.toLocaleString("es-MX")}`),
      crear("td", "numero", formatearBytes(seccion.bytes)),
      crear("td", "numero", `${porcentaje.toFixed(2)} %`),
    );
    leyenda.append(fila);
  });

  contenedor.append(mapa, leyenda);
  return contenedor;
}

async function inspeccionarArchivo(archivo) {
  if (!archivo.name.toLowerCase().endsWith(".bigo")) {
    mostrarAviso("aviso-codice", "Solo se aceptan archivos .bigo.", "error");
    return;
  }
  mostrarAviso("aviso-codice", "Leyendo el encabezado del códice…", "cargando");

  let datos;
  try {
    datos = await enviarArchivo("/api/inspeccionar", archivo);
  } catch (error) {
    mostrarAviso("aviso-codice", error.message, "error");
    return;
  }
  mostrarAviso("aviso-codice", "");

  // Este .bigo pasa a ser el que se descomprimirá en el Capítulo VI.
  estado.bigo = new Uint8Array(await archivo.arrayBuffer());
  estado.nombreBigo = archivo.name;

  document.getElementById("inspector-ficha").replaceChildren(crearFicha(datos));
  document.getElementById("inspector-metricas").replaceChildren(
    typeof crearTarjetas === "function" ? crearTarjetas(datos.metricas) : "",
  );
  document.getElementById("inspector-mapa").replaceChildren(crearMapa(datos.estructura, datos.archivo.bytes));
  if (typeof mostrarTabla === "function") mostrarTabla(document.getElementById("inspector-tabla"), datos.tabla);
  if (typeof dibujarArbol === "function") dibujarArbol(document.getElementById("inspector-arbol"), datos.arbol);

  const bits = typeof crearCifrado === "function"
    ? crearCifrado(
        "Primeros bits comprimidos",
        datos.bits_muestra,
        `En hexadecimal: ${datos.hex_muestra || "(vacío)"} · ${datos.metricas.total_bits.toLocaleString("es-MX")} bits válidos, ` +
          `${datos.metricas.bits_relleno} de relleno al final.`,
      )
    : crear("pre", null, datos.bits_muestra);
  document.getElementById("inspector-bits").replaceChildren(bits);

  document.getElementById("inspector").hidden = false;
  marcarCapitulo("cap-codice");
  if (typeof prepararDescompresion === "function") prepararDescompresion();
}

document.addEventListener("DOMContentLoaded", () => {
  prepararZonaCarga("zona-bigo", "entrada-bigo", inspeccionarArchivo);
});
