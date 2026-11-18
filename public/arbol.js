"use strict";

/* arbol.js: Capítulo III. Dibuja el árbol de Huffman en SVG.

   Cómo se acomodan los nodos:
   - Altura (y): la profundidad del nodo. La raíz arriba, cada nivel 72 px abajo.
   - Horizontal (x): las hojas se reparten de izquierda a derecha en el orden en
     que aparecen al recorrer el árbol; cada nodo interno queda centrado entre
     sus dos hijos.
   Al pasar el cursor por una hoja se resalta su camino y se muestra su código. */

const SVG = "http://www.w3.org/2000/svg";
const SEPARACION = 46;  // px entre hojas vecinas
const NIVEL = 72;       // px entre niveles
const MARGEN = 34;

function crearSvg(etiqueta, atributos = {}, texto) {
  const elemento = document.createElementNS(SVG, etiqueta);
  for (const [nombre, valor] of Object.entries(atributos)) elemento.setAttribute(nombre, valor);
  if (texto !== undefined) elemento.textContent = texto;
  return elemento;
}

// Etiquetas cortas para que quepan dentro de un círculo.
function simboloCorto(simbolo) {
  const cortos = { espacio: "␣", "salto de línea": "↵", retorno: "␍", tabulador: "⇥" };
  if (cortos[simbolo]) return cortos[simbolo];
  if (simbolo.startsWith("0x")) return simbolo.slice(2);
  return simbolo;
}

// 2412345 -> "2.4M"; 240721 -> "241k". Así los pesos grandes caben en el círculo.
function pesoCorto(peso) {
  if (peso >= 1e6) return `${(peso / 1e6).toFixed(1)}M`;
  if (peso >= 1e4) return `${Math.round(peso / 1e3)}k`;
  return String(peso);
}

// Recorre el árbol y calcula la posición de cada nodo.
function calcularPosiciones(raiz) {
  const nodos = [];
  let siguienteHoja = 0;
  let profundidadMaxima = 0;

  function recorrer(nodo, profundidad, camino) {
    profundidadMaxima = Math.max(profundidadMaxima, profundidad);
    const ubicado = { nodo, profundidad, camino, hijos: [] };
    if (nodo.izquierdo === undefined) {
      ubicado.x = siguienteHoja++; // es una hoja
    } else {
      if (nodo.izquierdo) ubicado.hijos.push(recorrer(nodo.izquierdo, profundidad + 1, camino + "0"));
      if (nodo.derecho) ubicado.hijos.push(recorrer(nodo.derecho, profundidad + 1, camino + "1"));
      ubicado.x = ubicado.hijos.reduce((suma, hijo) => suma + hijo.x, 0) / ubicado.hijos.length;
    }
    nodos.push(ubicado);
    return ubicado;
  }

  recorrer(raiz, 0, "");
  return { nodos, hojas: siguienteHoja, profundidadMaxima };
}

function dibujarArbol(contenedor, raiz) {
  contenedor.className = "";
  if (!raiz) {
    contenedor.replaceChildren(crear("p", "pendiente", "El texto está vacío: no hay árbol que dibujar."));
    return;
  }

  const { nodos, hojas, profundidadMaxima } = calcularPosiciones(raiz);
  const ancho = Math.max(320, MARGEN * 2 + (hojas - 1) * SEPARACION);
  const alto = MARGEN * 2 + profundidadMaxima * NIVEL + 24;
  const X = (n) => MARGEN + n.x * SEPARACION;
  const Y = (n) => MARGEN + n.profundidad * NIVEL;

  const svg = crearSvg("svg", {
    width: ancho,
    height: alto,
    viewBox: `0 0 ${ancho} ${alto}`,
    role: "img",
    "aria-label": `Árbol de Huffman con ${hojas} hojas y raíz de peso ${raiz.peso}`,
  });
  const capaAristas = crearSvg("g");
  const capaNodos = crearSvg("g");
  svg.append(capaAristas, capaNodos);

  // Aristas (líneas) con su bit: 0 hacia la izquierda, 1 hacia la derecha.
  for (const padre of nodos) {
    for (const hijo of padre.hijos) {
      capaAristas.append(
        crearSvg("line", {
          x1: X(padre), y1: Y(padre), x2: X(hijo), y2: Y(hijo),
          class: "arbol-arista", "data-camino": hijo.camino,
        }),
      );
      const bit = hijo.camino.slice(-1);
      const medioX = (X(padre) + X(hijo)) / 2 + (bit === "0" ? -9 : 9);
      const medioY = (Y(padre) + Y(hijo)) / 2 - 4;
      capaAristas.append(crearSvg("text", { x: medioX, y: medioY, "text-anchor": "middle", class: "arbol-bit" }, bit));
    }
  }

  const pie = crear("p", "arbol-pie", "Pasa el cursor sobre una hoja para ver el camino que forma su código.");
  const leyenda = crear(
    "p",
    "arbol-pie",
    "␣ espacio · ↵ salto de línea · Las etiquetas en cursiva (C3, B1…) son bytes en hexadecimal: " +
      "en UTF-8, cada letra acentuada o ñ ocupa dos bytes.",
  );

  // Nodos: círculos con el peso; las hojas además llevan su símbolo.
  for (const ubicado of nodos) {
    const { nodo } = ubicado;
    const esHoja = nodo.izquierdo === undefined;
    const grupo = crearSvg("g", { class: esHoja ? "arbol-hoja" : "arbol-interno" });
    grupo.append(crearSvg("circle", { cx: X(ubicado), cy: Y(ubicado), r: 17 }));

    if (esHoja) {
      // Los bytes que no son ASCII (mitades de una "ñ" o un acento) llevan otro estilo.
      const claseSimbolo = nodo.simbolo.startsWith("0x") ? "arbol-simbolo arbol-hex" : "arbol-simbolo";
      grupo.append(
        crearSvg("text", { x: X(ubicado), y: Y(ubicado) + 5, "text-anchor": "middle", class: claseSimbolo }, simboloCorto(nodo.simbolo)),
        crearSvg("text", { x: X(ubicado), y: Y(ubicado) + 32, "text-anchor": "middle", class: "arbol-peso" }, pesoCorto(nodo.peso)),
        crearSvg("title", {}, `${nodo.simbolo} · ${nodo.peso} apariciones · código ${ubicado.camino || "0"}`),
      );
      grupo.setAttribute("tabindex", "0");
      const resaltar = () => resaltarCamino(svg, grupo, ubicado.camino, nodo.simbolo, pie);
      grupo.addEventListener("mouseenter", resaltar);
      grupo.addEventListener("focus", resaltar);
    } else {
      grupo.append(
        crearSvg("text", { x: X(ubicado), y: Y(ubicado) + 4, "text-anchor": "middle", class: "arbol-peso" }, pesoCorto(nodo.peso)),
      );
    }
    capaNodos.append(grupo);
  }

  const marco = crear("div", "marco-arbol");
  marco.append(svg);
  contenedor.replaceChildren(marco, pie, leyenda);
}

// Resalta las aristas cuyo camino es el inicio del código de la hoja.
function resaltarCamino(svg, grupo, camino, simbolo, pie) {
  svg.querySelectorAll(".arbol-hoja.activa").forEach((hoja) => hoja.classList.remove("activa"));
  grupo.classList.add("activa");
  svg.querySelectorAll(".arbol-arista").forEach((arista) => {
    arista.classList.toggle("camino", camino.startsWith(arista.dataset.camino));
  });
  pie.replaceChildren(`Código de «${simbolo}»: `, crear("strong", null, camino || "0"));
}
