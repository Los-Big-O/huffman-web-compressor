"use strict";

/* descompresion.js: Capítulo VI. Descomprime el .bigo actual, verifica su
   integridad y permite descargar el texto recuperado.

   Dos verificaciones:
   1. SHA-256 (en el servidor): la huella del texto recuperado contra la guardada
      en el encabezado. Funciona aunque no tengamos el .txt original.
   2. Byte a byte (aquí, en el navegador): si en esta sesión se cargó el .txt
      original, se compara con el recuperado posición por posición. */

let textoRecuperado = null; // { bytes, nombre }

// Habilita el botón cuando hay un .bigo listo (recién comprimido o inspeccionado).
function prepararDescompresion() {
  if (!estado.bigo) return;
  document.getElementById("boton-descomprimir").disabled = false;
  const aviso = document.getElementById("estado-descompresion");
  aviso.className = "";
  aviso.textContent = `Listo para descomprimir: ${estado.nombreBigo} (${formatearBytes(estado.bigo.length)}).`;
}

function compararBytes(a, b) {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
  return true;
}

function crearSello(integro, titulo, texto) {
  const sello = crear("div", integro ? "sello" : "sello roto");
  const marca = crear("div", "sello-marca", integro ? "✓" : "✗");
  marca.setAttribute("aria-hidden", "true");
  const textos = crear("div");
  textos.append(crear("p", "sello-titulo", titulo), crear("p", "sello-texto", texto));
  sello.append(marca, textos);
  return sello;
}

async function descomprimirActual() {
  if (!estado.bigo) return;
  const boton = document.getElementById("boton-descomprimir");
  boton.disabled = true;
  mostrarAviso("aviso-restitucion", "Recorriendo el árbol bit por bit…", "cargando");

  let datos;
  try {
    datos = await enviarArchivo("/api/descomprimir", new File([estado.bigo], estado.nombreBigo));
  } catch (error) {
    mostrarAviso("aviso-restitucion", error.message, "error");
    boton.disabled = false;
    return;
  }
  mostrarAviso("aviso-restitucion", "");
  boton.disabled = false;

  // El texto llega una sola vez, en base64 (archivo_txt_b64, nombre del backend
  // del equipo): así se descarga idéntico, byte a byte, aunque no sea UTF-8.
  const bytes = base64ABytes(datos.archivo_txt_b64);
  textoRecuperado = { bytes, nombre: datos.nombre_original.replace(/\.txt$/i, "") + "_recuperado.txt" };

  const resultado = document.getElementById("resultado-descompresion");
  const partes = [];

  // 1. Verificación por SHA-256
  partes.push(
    crearSello(
      datos.integro,
      datos.integro ? "Íntegro" : "Alterado",
      datos.integro
        ? `La huella SHA-256 del texto recuperado coincide con la guardada en el archivo. ${formatearBytes(datos.bytes)} recuperados.`
        : "La huella SHA-256 no coincide: el archivo .bigo fue modificado o está dañado.",
    ),
  );
  const huellas = crear("p", "huellas");
  huellas.append(
    `Guardada:   ${datos.sha256_guardado}`, crear("br"),
    `Recuperada: ${datos.sha256_recuperado}`,
  );
  partes.push(huellas);

  // 2. Comparación byte a byte, solo si este .bigo viene del texto cargado en el
  //    Capítulo I. Se reconoce por la huella guardada (no por el nombre, que el
  //    formato v1 no guarda): si coincide con la de la compresión, es el mismo texto.
  if (estado.original && estado.compresion && datos.sha256_guardado === estado.compresion.sha256) {
    const iguales = compararBytes(estado.original, bytes);
    partes.push(
      crearSello(
        iguales,
        iguales ? "Idéntico byte a byte" : "Diferente al original",
        iguales
          ? `Se comparó cada uno de los ${formatearBytes(bytes.length)} con el .txt original cargado en el Capítulo I.`
          : "El texto recuperado no coincide con el .txt cargado en el Capítulo I.",
      ),
    );
  }

  // Vista del texto: solo el inicio si es muy largo, para no trabar la página.
  const LIMITE = 20000;
  const texto = new TextDecoder("utf-8").decode(bytes.slice(0, LIMITE));
  partes.push(
    crear("pre", "texto-restituido", texto + (bytes.length > LIMITE ? "\n\n… (texto completo en la descarga)" : "")),
  );

  const acciones = crear("div", "acciones");
  const botonDescarga = crear("button", "boton principal", `Descargar ${textoRecuperado.nombre}`);
  botonDescarga.type = "button";
  botonDescarga.addEventListener("click", () =>
    descargar(textoRecuperado.bytes, textoRecuperado.nombre, "text/plain;charset=utf-8"),
  );
  acciones.append(botonDescarga);
  partes.push(acciones);

  resultado.replaceChildren(...partes);
  resultado.hidden = false;
  marcarCapitulo("cap-restitucion");
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("boton-descomprimir").addEventListener("click", descomprimirActual);
});
