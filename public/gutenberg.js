"use strict";

/* gutenberg.js: segunda forma de cargar un texto en el Capítulo I. Busca libros
   en Project Gutenberg y los comprime SIN descargarlos al navegador: el servidor
   los baja (/api/gutenberg/comprimir) y responde igual que /api/comprimir.

   Diferencia con un .txt local: el navegador no tiene los bytes del libro, solo
   una vista previa. Por eso en el Capítulo VI se verifica la integridad con
   SHA-256, pero no se puede comparar byte a byte con el original. */

// Pide JSON al servidor. Igual que enviarArchivo() de app.js, pero sin archivo.
async function pedirJSON(ruta, opciones = {}) {
  let respuesta;
  try {
    respuesta = await fetch(ruta, opciones);
  } catch {
    throw new Error("No se pudo conectar con el servidor.");
  }
  let datos;
  try {
    datos = await respuesta.json();
  } catch {
    throw new Error(`El servidor respondió con un error (${respuesta.status}).`);
  }
  if (!respuesta.ok) throw new Error(datos.error || "Ocurrió un error en el servidor.");
  return datos;
}

// Una ficha de catálogo por libro: título, autores, descargas y botón.
function crearFichaLibro(libro) {
  const item = crear("li", "libro-ficha");
  const textos = crear("div");
  textos.append(
    crear("p", "libro-titulo", libro.titulo),
    crear("p", "libro-autor", `${libro.autores} · ${libro.descargas.toLocaleString("es-MX")} descargas`),
  );
  const boton = crear("button", "boton", "Comprimir este libro");
  boton.type = "button";
  boton.addEventListener("click", () => comprimirLibro(libro, boton));
  item.append(textos, boton);
  return item;
}

async function buscarLibros(evento) {
  evento.preventDefault();
  const consulta = document.getElementById("gutenberg-consulta").value.trim();
  const lista = document.getElementById("gutenberg-resultados");
  if (!consulta) {
    mostrarAviso("aviso-gutenberg", "Escribe un título, autor o palabra clave.", "error");
    return;
  }

  mostrarAviso("aviso-gutenberg", "Consultando el catálogo de Project Gutenberg…", "cargando");
  lista.replaceChildren();
  let datos;
  try {
    datos = await pedirJSON(`/api/gutenberg/buscar?q=${encodeURIComponent(consulta)}`);
  } catch (error) {
    mostrarAviso("aviso-gutenberg", error.message, "error");
    return;
  }

  if (!datos.libros.length) {
    mostrarAviso("aviso-gutenberg", "No se encontraron libros con texto plano para esa búsqueda.");
    return;
  }
  mostrarAviso("aviso-gutenberg", "");
  lista.replaceChildren(...datos.libros.map(crearFichaLibro));
}

async function comprimirLibro(libro, boton) {
  boton.disabled = true;
  mostrarAviso("aviso-gutenberg", `Descargando y comprimiendo «${libro.titulo}»…`, "cargando");

  let datos;
  try {
    datos = await pedirJSON("/api/gutenberg/comprimir", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url_txt: libro.url_txt, titulo: libro.titulo }),
    });
  } catch (error) {
    mostrarAviso("aviso-gutenberg", error.message, "error");
    boton.disabled = false;
    return;
  }
  mostrarAviso("aviso-gutenberg", "");
  boton.disabled = false;

  // El navegador no tiene los bytes del libro: original queda en null para que
  // el Capítulo VI no intente compararlo byte a byte.
  estado.original = null;
  estado.nombreOriginal = datos.nombre_original;
  estado.compresion = datos;
  estado.bigo = base64ABytes(datos.archivo_bigo_b64);
  estado.nombreBigo = datos.nombre_bigo;

  const bytes = datos.metricas.original_bytes;
  document.getElementById("texto-nombre").textContent =
    `${libro.titulo} · ${libro.autores} · ${formatearBytes(bytes)} (${formatearTamano(bytes)})`;
  document.getElementById("texto-muestra").textContent = `${datos.vista_previa_texto}\n…`;
  document.getElementById("vista-texto").hidden = false;

  mostrarResultados(datos);
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("gutenberg-formulario").addEventListener("submit", buscarLibros);
});
