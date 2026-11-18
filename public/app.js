"use strict";

/* app.js: lo que comparten todos los capítulos.
   - El "estado" de la página (el texto cargado y el .bigo actual).
   - Funciones de apoyo: formatear tamaños, crear elementos, hablar con el servidor.
   - El Capítulo I: cargar el .txt y pedir la compresión.
   Los demás capítulos viven en su propio archivo (tabla.js, arbol.js, ...). */

const estado = {
  original: null,        // Uint8Array con los bytes del .txt cargado
  nombreOriginal: null,  // "quijote.txt"
  compresion: null,      // respuesta de /api/comprimir
  bigo: null,            // Uint8Array del .bigo actual (recién comprimido o cargado)
  nombreBigo: null,      // "quijote.bigo"
};

/* ---------- Funciones de apoyo ---------- */

// Crea un elemento HTML. Usamos textContent (no innerHTML) para que un nombre
// de archivo con "<" o ">" nunca se interprete como código.
function crear(etiqueta, clase, texto) {
  const elemento = document.createElement(etiqueta);
  if (clase) elemento.className = clase;
  if (texto !== undefined && texto !== null) elemento.textContent = texto;
  return elemento;
}

// 2310000 -> "2,310,000 bytes"
function formatearBytes(bytes) {
  return `${bytes.toLocaleString("es-MX")} bytes`;
}

// 2310000 -> "2.20 MB"; 5300 -> "5.18 KB"; 800 -> "800 B"
function formatearTamano(bytes) {
  const absoluto = Math.abs(bytes);
  if (absoluto < 1024) return `${bytes} B`;
  if (absoluto < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

// El servidor manda archivos en base64 dentro del JSON; aquí los volvemos bytes.
function base64ABytes(base64) {
  const binario = atob(base64);
  const bytes = new Uint8Array(binario.length);
  for (let i = 0; i < binario.length; i++) bytes[i] = binario.charCodeAt(i);
  return bytes;
}

// Descarga bytes como archivo, sin pasar otra vez por el servidor.
function descargar(bytes, nombre, tipo = "application/octet-stream") {
  const enlace = document.createElement("a");
  enlace.href = URL.createObjectURL(new Blob([bytes], { type: tipo }));
  enlace.download = nombre;
  enlace.click();
  setTimeout(() => URL.revokeObjectURL(enlace.href), 1000);
}

function mostrarAviso(id, mensaje, tipo = "") {
  const aviso = document.getElementById(id);
  aviso.textContent = mensaje;
  aviso.className = `aviso ${tipo}`;
  aviso.hidden = !mensaje;
}

// Envía un archivo a un endpoint del servidor (contrato en docs/api.md).
async function enviarArchivo(ruta, archivo) {
  const formulario = new FormData();
  formulario.append("archivo", archivo);
  let respuesta;
  try {
    respuesta = await fetch(ruta, { method: "POST", body: formulario });
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

// Marca un capítulo del índice como terminado.
function marcarCapitulo(id) {
  const enlace = document.querySelector(`.indice a[data-capitulo="${id}"]`);
  if (enlace) enlace.classList.add("hecho");
}

// Prepara una zona para soltar archivos (arrastrar y soltar o clic).
function prepararZonaCarga(idZona, idEntrada, alElegir) {
  const zona = document.getElementById(idZona);
  const entrada = document.getElementById(idEntrada);
  entrada.addEventListener("change", () => {
    if (entrada.files.length) alElegir(entrada.files[0]);
    entrada.value = ""; // permite volver a elegir el mismo archivo
  });
  zona.addEventListener("dragover", (evento) => {
    evento.preventDefault();
    zona.classList.add("encima");
  });
  zona.addEventListener("dragleave", () => zona.classList.remove("encima"));
  zona.addEventListener("drop", (evento) => {
    evento.preventDefault();
    zona.classList.remove("encima");
    if (evento.dataTransfer.files.length) alElegir(evento.dataTransfer.files[0]);
  });
}

/* ---------- Capítulo I: cargar el texto y comprimir ---------- */

async function cargarTexto(archivo) {
  if (!archivo.name.toLowerCase().endsWith(".txt")) {
    mostrarAviso("aviso-texto", "Solo se aceptan archivos .txt.", "error");
    return;
  }

  estado.original = new Uint8Array(await archivo.arrayBuffer());
  estado.nombreOriginal = archivo.name;

  // Vista previa del manuscrito: solo el inicio, para no saturar la página.
  document.getElementById("texto-nombre").textContent =
    `${archivo.name} · ${formatearBytes(archivo.size)} (${formatearTamano(archivo.size)})`;
  const inicio = new TextDecoder("utf-8").decode(estado.original.slice(0, 1500));
  document.getElementById("texto-muestra").textContent =
    inicio + (estado.original.length > 1500 ? "\n…" : "");
  document.getElementById("vista-texto").hidden = false;

  mostrarAviso("aviso-texto", "Contando símbolos, construyendo el árbol y comprimiendo…", "cargando");
  try {
    const datos = await enviarArchivo("/api/comprimir", archivo);
    estado.compresion = datos;
    // El .bigo llega una sola vez, con el nombre del backend del equipo
    // (archivo_bigo_b64), para no pasar el límite de 4.5 MB de Vercel.
    estado.bigo = base64ABytes(datos.archivo_bigo_b64);
    estado.nombreBigo = datos.nombre_bigo;
    mostrarAviso("aviso-texto", "");
    mostrarResultados(datos);
  } catch (error) {
    mostrarAviso("aviso-texto", error.message, "error");
  }
}

// Reparte la respuesta del servidor entre los capítulos.
// Cada módulo es opcional: si su archivo no está cargado, ese capítulo se omite.
function mostrarResultados(datos) {
  marcarCapitulo("cap-texto");
  if (typeof mostrarTabla === "function") {
    mostrarTabla(document.getElementById("tabla-frecuencias"), datos.tabla);
    marcarCapitulo("cap-frecuencias");
  }
  if (typeof dibujarArbol === "function") {
    dibujarArbol(document.getElementById("arbol"), datos.arbol);
    marcarCapitulo("cap-arbol");
  }
  if (typeof mostrarMetricas === "function") {
    mostrarMetricas(datos);
    marcarCapitulo("cap-compresion");
  }
  if (typeof prepararDescompresion === "function") {
    prepararDescompresion();
  }
  document.getElementById("cap-frecuencias").scrollIntoView({ behavior: "smooth" });
}

document.addEventListener("DOMContentLoaded", () => {
  prepararZonaCarga("zona-txt", "entrada-txt", cargarTexto);
});
