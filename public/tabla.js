"use strict";

/* tabla.js: Capítulo II. Dibuja la tabla de frecuencias y códigos.
   La usan el Capítulo II (al comprimir) y el inspector (tabla reconstruida). */

function mostrarTabla(contenedor, filas) {
  contenedor.className = "";
  const maximo = Math.max(1, ...filas.map((fila) => fila.frecuencia));
  const totalBits = filas.reduce((suma, fila) => suma + fila.bits_totales, 0);

  const resumen = crear(
    "p",
    "resumen",
    `${filas.length} símbolos distintos · ${totalBits.toLocaleString("es-MX")} bits en total. ` +
      "Los símbolos más frecuentes tienen los códigos más cortos.",
  );

  const tabla = crear("table", "tabla");
  const encabezado = crear("tr");
  const numericas = ["%", "Bits del código", "Bits en total"];
  for (const titulo of ["Símbolo", "Apariciones", "%", "Código Huffman", "Bits del código", "Bits en total"]) {
    const th = crear("th", numericas.includes(titulo) ? "numero" : null, titulo);
    th.scope = "col";
    encabezado.append(th);
  }
  const thead = crear("thead");
  thead.append(encabezado);
  tabla.append(thead);

  const cuerpo = crear("tbody");
  for (const fila of filas) {
    const tr = crear("tr");

    const barra = crear("div", "barra");
    const relleno = crear("div", "barra-relleno");
    relleno.style.width = `${(120 * fila.frecuencia) / maximo}px`; // barra proporcional
    barra.append(relleno, crear("span", null, fila.frecuencia.toLocaleString("es-MX")));
    const celdaBarra = crear("td");
    celdaBarra.append(barra);

    tr.append(
      crear("td", "simbolo", fila.simbolo),
      celdaBarra,
      crear("td", "numero", `${fila.porcentaje.toFixed(2)}`),
      crear("td", "codigo", fila.codigo),
      crear("td", "numero", String(fila.longitud)),
      crear("td", "numero", fila.bits_totales.toLocaleString("es-MX")),
    );
    cuerpo.append(tr);
  }
  tabla.append(cuerpo);

  const marco = crear("div", "marco-tabla");
  marco.append(tabla);
  contenedor.replaceChildren(resumen, marco);
}
