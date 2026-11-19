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

from huffman.adaptador import campos_compresion, campos_descompresion, campos_inspeccion
from huffman.formato import descomprimir_bigo, empaquetar_bigo, inspeccionar_bigo

app = Flask(__name__, static_folder="public", static_url_path="")

GUTENDEX_API = "https://gutendex.com/books"
USER_AGENT = "HuffmanWebCompressor"

# Vercel acepta como máximo 4.5 MB por petición; con 4 MB dejamos margen para
# los encabezados del multipart. Es el límite que promete docs/api.md.
LIMITE_BYTES = 4 * 1024 * 1024


@app.before_request
def rechazar_archivos_grandes():
    """Responde 413 con JSON antes de leer un archivo demasiado grande.

    Se revisa aquí (y no dentro de cada endpoint) porque los endpoints atrapan
    cualquier excepción y la convertirían en un 400 genérico.
    """
    if request.content_length and request.content_length > LIMITE_BYTES:
        return jsonify({"error": "El archivo pasa de 4 MB, el máximo permitido"}), 413


# Tamaño máximo de un libro de Gutenberg. Su .bigo viaja en base64 (≈ 4/3 del
# tamaño), así que con 3 MB la respuesta cabe en los 4.5 MB de Vercel.
LIMITE_LIBRO_BYTES = 3 * 1024 * 1024


def _es_url_de_gutenberg(url: str) -> bool:
    """True solo si la URL es http(s) y su dominio es gutenberg.org o un subdominio.

    No basta con que "gutenberg.org" aparezca en el texto: así se colarían
    "https://otro.com/?gutenberg.org" o "https://gutenberg.org.otro.com/". Por
    eso se revisa el nombre del servidor (hostname) que extrae urlparse; también
    ignora trucos como "https://gutenberg.org@otro.com/" (el servidor es otro.com).
    """
    partes = urllib.parse.urlparse(url)
    servidor = (partes.hostname or "").lower()
    return partes.scheme in ("http", "https") and (
        servidor == "gutenberg.org" or servidor.endswith(".gutenberg.org")
    )


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

        respuesta = {
            "nombre_original": nombre_original,
            "nombre_salida": nombre_salida,
            "version": f"BIGO v{resultado['version']}",
            "sha256": resultado["sha256"],
            "metricas": resultado["metricas"],
            "tabla": resultado["tabla"],
            "arbol": resultado["arbol"],
            "archivo_bigo_b64": bigo_b64,
        }
        # Agrega los campos del contrato (docs/api.md) que usa el frontend.
        respuesta.update(campos_compresion(resultado, nombre_salida))
        return jsonify(respuesta)
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

    if not url_txt or not _es_url_de_gutenberg(url_txt):
        return jsonify({"error": "URL de Project Gutenberg invalida"}), 400

    try:
        req = urllib.request.Request(url_txt, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=20) as resp:
            # urlopen sigue redirecciones: se revisa también la URL final, para
            # no terminar descargando de otro sitio.
            if not _es_url_de_gutenberg(resp.geturl()):
                return jsonify({"error": "La descarga salió de Project Gutenberg"}), 400
            # Se lee como máximo un byte más que el límite: basta para saber si
            # lo pasa, sin bajar el libro completo.
            datos = resp.read(LIMITE_LIBRO_BYTES + 1)

        if len(datos) > LIMITE_LIBRO_BYTES:
            return jsonify({
                "error": "El libro pesa más de 3 MB, el máximo que se puede comprimir "
                         "en línea. Elige otro libro o una edición más corta."
            }), 413

        if not datos:
            return jsonify({"error": "El libro descargado esta vacio"}), 400

        resultado = empaquetar_bigo(datos)
        nombre_limpio = "".join(c if c.isalnum() or c in " _-" else "_" for c in titulo)[:50].strip()
        nombre_salida = f"{nombre_limpio or 'gutenberg'}.bigo"
        bigo_b64 = base64.b64encode(resultado["archivo_bigo"]).decode("ascii")

        respuesta = {
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
        # Misma respuesta que /api/comprimir, con los campos del contrato.
        respuesta.update(campos_compresion(resultado, nombre_salida))
        return jsonify(respuesta)
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
        # Agrega los campos del contrato (docs/api.md) que usa el inspector.
        reporte.update(campos_inspeccion(contenido, archivo.filename, reporte))
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

        respuesta = {
            "nombre_salida": nombre_txt,
            "integro": resultado["integro"],
            "sha256_esperado": resultado["sha256_esperado"],
            "sha256_calculado": resultado["sha256_calculado"],
            "tamano_recuperado": resultado["tamano_recuperado"],
            # El texto va UNA sola vez, en base64 (archivo_txt_b64). Antes
            # también iba como "texto_recuperado": con un libro de 3 MB la
            # respuesta pesaba 7.3 MB y pasaba el límite de 4.5 MB de Vercel.
            # El frontend decodifica el base64 para mostrar el texto.
            "archivo_txt_b64": txt_b64,
        }
        # Agrega los campos del contrato (docs/api.md) que usa el frontend.
        respuesta.update(campos_descompresion(resultado, archivo.filename))
        return jsonify(respuesta)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


if __name__ == "__main__":
    app.run(debug=True)