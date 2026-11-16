"""Servidor web de Huffman Web Compressor.

Vercel busca una variable llamada "app" en este archivo (app.py) para desplegarla.
Los archivos de la interfaz (HTML, CSS, JS) viven en la carpeta public/.
"""

from flask import Flask, send_from_directory

# static_folder="public" y static_url_path="" sirven public/ en la raíz del sitio
# cuando corremos en local. En Vercel, la carpeta public/ la sirve su CDN.
app = Flask(__name__, static_folder="public", static_url_path="")


@app.route("/")
def inicio():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/salud")
def salud():
    """Ruta de prueba: confirma que el servidor responde."""
    return {"estado": "ok"}


if __name__ == "__main__":
    app.run(debug=True)
