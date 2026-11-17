"""Servidor web de Huffman Web Compressor.

Vercel busca una variable llamada "app" en este archivo (app.py) para desplegarla.
Los archivos de la interfaz (HTML, CSS, JS) viven en la carpeta public/.
"""

import base64
import json
import os
import urllib.parse
import urllib.request

from flask import Flask, jsonify, request, send_from_directory

from huffman.formato import descomprimir_bigo, empaquetar_bigo, inspeccionar_bigo

app = Flask(__name__, static_folder="public", static_url_path="")

GUTENDEX_API = "https://gutendex.com/books"
USER_AGENT = "HuffmanWebCompressor"


def _nombre_base_sin_ext(nombre: str) -> str:
    base = os.path.basename(nombre or "documento")
    raiz, _ = os.path.splitext(base)
    return raiz or "documento"


@app.route("/")
def inicio():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/salud")
def salud():
    """Ruta de prueba: confirma que el servidor responde"""
    return {"estado": "ok"}


@app.route("/api/comprimir", methods=["POST"])
def api_comprimir():
    try:
        if "archivo" in request.files and request.files["archivo"].filename:
            archivo = request.files["archivo"]
            nombre_original = archivo.filename
            datos = archivo.read()
        else:
            cuerpo = request.get_json(silent=True) or {}
            texto = cuerpo.get("texto", "")
            nombre_original = cuerpo.get("nombre_archivo", "texto.txt")
            datos = texto.encode("utf-8")

        if not datos:
            return jsonify({"error": "El texto o archivo esta vacio"}), 400

        resultado = empaquetar_bigo(datos)
        nombre_salida = f"{_nombre_base_sin_ext(nombre_original)}.bigo"
        bigo_b64 = base64.b64encode(resultado["archivo_bigo"]).decode("ascii")

        return jsonify(
            {
                "nombre_original": nombre_original,
                "nombre_salida": nombre_salida,
                "version": f"BIGO v{resultado['version']}",
                "sha256": resultado["sha256"],
                "metricas": resultado["metricas"],
                "tabla": resultado["tabla"],
                "arbol": resultado["arbol"],
                "archivo_bigo_b64": bigo_b64,
            }
        )
    except Exception as exc:
        return jsonify({"error": f"Error al comprimir: {exc}"}), 400


@app.route("/api/gutenberg/buscar", methods=["GET"])
def api_gutenberg_buscar():
    consulta = request.args.get("q", "").strip()
    if not consulta:
        return jsonify({"error": "Escribe un titulo, autor o palabra clave"}), 400

    try:
        url = f"{GUTENDEX_API}?search={urllib.parse.quote(consulta)}"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        libros = []
        for item in data.get("results", [])[:12]:
            formatos = item.get("formats", {})
            url_txt = None
            for clave in (
                "text/plain; charset=utf-8",
                "text/plain; charset=us-ascii",
                "text/plain",
            ):
                candidato = formatos.get(clave)
                if candidato and not candidato.endswith(".zip"):
                    url_txt = candidato
                    break

            if not url_txt:
                for clave, candidato in formatos.items():
                    if clave.startswith("text/plain") and not candidato.endswith(".zip"):
                        url_txt = candidato
                        break

            if url_txt:
                autores = [a.get("name", "Desconocido") for a in item.get("authors", [])]
                libros.append(
                    {
                        "id": item.get("id"),
                        "titulo": item.get("title", "Sin título"),
                        "autores": ", ".join(autores) if autores else "Autor desconocido",
                        "descargas": item.get("download_count", 0),
                        "url_txt": url_txt,
                    }
                )

        return jsonify({"libros": libros})
    except Exception as exc:
        return jsonify({"error": f"No se pudo consultar Project Gutenberg: {exc}"}), 502


@app.route("/api/gutenberg/comprimir", methods=["POST"])
def api_gutenberg_comprimir():
    cuerpo = request.get_json(silent=True) or {}
    url_txt = cuerpo.get("url_txt", "").strip()
    titulo = cuerpo.get("titulo", "libro_gutenberg").strip()

    if not url_txt or "gutenberg.org" not in url_txt:
        return jsonify({"error": "URL de Project Gutenberg invalida"}), 400

    try:
        req = urllib.request.Request(url_txt, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=20) as resp:
            datos = resp.read()

        if not datos:
            return jsonify({"error": "El libro descargado esta vacio"}), 400

        resultado = empaquetar_bigo(datos)
        nombre_limpio = "".join(c if c.isalnum() or c in " _-" else "_" for c in titulo)[:50].strip()
        nombre_salida = f"{nombre_limpio or 'gutenberg'}.bigo"
        bigo_b64 = base64.b64encode(resultado["archivo_bigo"]).decode("ascii")

        return jsonify(
            {
                "nombre_original": f"{nombre_limpio}.txt",
                "nombre_salida": nombre_salida,
                "version": f"BIGO v{resultado['version']}",
                "sha256": resultado["sha256"],
                "metricas": resultado["metricas"],
                "tabla": resultado["tabla"],
                "arbol": resultado["arbol"],
                "archivo_bigo_b64": bigo_b64,
                "vista_previa_texto": datos[:600].decode("utf-8", errors="replace"),
            }
        )
    except Exception as exc:
        return jsonify({"error": f"No se pudo descargar el libro: {exc}"}), 502


@app.route("/api/inspeccionar", methods=["POST"])
def api_inspeccionar():
    if "archivo" not in request.files or not request.files["archivo"].filename:
        return jsonify({"error": "Debes seleccionar un archivo .bigo"}), 400

    archivo = request.files["archivo"]
    contenido = archivo.read()

    try:
        reporte = inspeccionar_bigo(contenido, archivo.filename)
        return jsonify(reporte)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/api/descomprimir", methods=["POST"])
def api_descomprimir():
    if "archivo" not in request.files or not request.files["archivo"].filename:
        return jsonify({"error": "Debes seleccionar un archivo .bigo"}), 400

    archivo = request.files["archivo"]
    contenido = archivo.read()

    try:
        resultado = descomprimir_bigo(contenido)
        nombre_txt = f"{_nombre_base_sin_ext(archivo.filename)}_recuperado.txt"
        txt_b64 = base64.b64encode(resultado["datos_recuperados"]).decode("ascii")

        return jsonify(
            {
                "nombre_salida": nombre_txt,
                "integro": resultado["integro"],
                "sha256_esperado": resultado["sha256_esperado"],
                "sha256_calculado": resultado["sha256_calculado"],
                "tamano_recuperado": resultado["tamano_recuperado"],
                "texto_recuperado": resultado["texto_recuperado"],
                "archivo_txt_b64": txt_b64,
            }
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


if __name__ == "__main__":
    app.run(debug=True)