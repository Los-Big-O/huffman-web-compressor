"use strict";

/* metricas.js: Capítulo IV. Muestra cuánto se redujo el archivo y permite
   descargar el .bigo. crearTarjetas() también la usa el inspector. */

function crearTarjeta(etiqueta, valor, detalle, destacada = false) {
  const tarjeta = crear("div", destacada ? "tarjeta destacada" : "tarjeta");
  tarjeta.append(crear("span", "etiqueta", etiqueta), crear("span", "valor", valor), crear("span", "detalle", detalle));
  return tarjeta;
}

// Recibe el objeto "metricas" de la API y devuelve las tarjetas y los detalles.
function crearTarjetas(m) {
  const contenedor = crear("div");
  const tarjetas = crear("div", "tarjetas");
  const crecio = m.ahorro_bytes < 0;

  tarjetas.append(
    crearTarjeta("Original", formatearTamano(m.original_bytes), formatearBytes(m.original_bytes)),
    crearTarjeta("Comprimido", formatearTamano(m.comprimido_bytes), formatearBytes(m.comprimido_bytes)),
    crearTarjeta(
      crecio ? "Aumento" : "Ahorro",
      formatearTamano(Math.abs(m.ahorro_bytes)),
      formatearBytes(Math.abs(m.ahorro_bytes)),
    ),
    crearTarjeta(
      "Reducción",
      `${m.reduccion_porcentaje.toFixed(1)} %`,
      crecio ? "el encabezado pesa más que el ahorro" : "del tamaño original",
      true,
    ),
    crearTarjeta("Razón", `${m.razon_compresion.toFixed(2)} : 1`, "original ÷ comprimido"),
    crearTarjeta("Símbolos", m.simbolos_distintos.toLocaleString("es-MX"), "bytes distintos"),
  );

  const detalles = crear("ul", "detalles");
  const detalle = (texto, valor) => {
    const li = crear("li", null, `${texto}: `);
    li.append(crear("strong", null, valor));
    detalles.append(li);
  };
  detalle("Bits codificados", m.total_bits.toLocaleString("es-MX"));
  detalle("Bits de relleno en el último byte", String(m.bits_relleno));
  detalle("Encabezado del .bigo", formatearBytes(m.encabezado_bytes));

  contenedor.append(tarjetas, detalles);
  return contenedor;
}

// Bloque oscuro con los primeros bits del texto ya codificado.
function crearCifrado(titulo, bits, nota) {
  const bloque = crear("div", "cifrado");
  bloque.append(crear("p", "etiqueta", titulo), crear("pre", null, bits || "(sin bits)"));
  if (nota) bloque.append(crear("p", "nota", nota));
  return bloque;
}

function mostrarMetricas(datos) {
  const contenedor = document.getElementById("metricas");
  contenedor.className = "";
  contenedor.replaceChildren(
    crearTarjetas(datos.metricas),
    crearCifrado(
      "Escritura cifrada · primeros bits",
      datos.bits_muestra,
      `${datos.metricas.total_bits.toLocaleString("es-MX")} bits en total, agrupados de 8 en 8 como se guardan en bytes.`,
    ),
  );
  document.getElementById("acciones-compresion").hidden = false;
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("boton-descargar-bigo").addEventListener("click", () => {
    if (estado.bigo) descargar(estado.bigo, estado.nombreBigo);
  });

  // Lleva el .bigo recién creado al inspector (Capítulo V).
  document.getElementById("boton-inspeccionar-actual").addEventListener("click", () => {
    if (!estado.bigo || typeof inspeccionarArchivo !== "function") return;
    inspeccionarArchivo(new File([estado.bigo], estado.nombreBigo));
    document.getElementById("cap-codice").scrollIntoView({ behavior: "smooth" });
  });
});
