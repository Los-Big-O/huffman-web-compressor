"""Pruebas de los endpoints de Project Gutenberg sin conectarse a internet.

Se reemplaza urllib.request.urlopen por una respuesta simulada (monkeypatch), así
las pruebas no dependen de que Gutendex o gutenberg.org estén disponibles.
"""

import base64
import io
import json
import urllib.request

from app import app

LIBRO = ("En un lugar de la Mancha, de cuyo nombre no quiero acordarme… ¡Ñandú!\n" * 200).encode("utf-8")

CATALOGO = {
    "results": [
        {
            "id": 2000,
            "title": "Don Quijote",
            "authors": [{"name": "Cervantes Saavedra, Miguel de"}],
            "download_count": 12345,
            "formats": {
                "application/zip": "https://www.gutenberg.org/files/2000/2000.zip",
                "text/plain; charset=utf-8": "https://www.gutenberg.org/ebooks/2000.txt.utf-8",
            },
        },
        {   # Sin texto plano: no debe aparecer en los resultados.
            "id": 1,
            "title": "Solo HTML",
            "authors": [],
            "download_count": 1,
            "formats": {"text/html": "https://www.gutenberg.org/ebooks/1.html"},
        },
    ]
}


def _simular_urlopen(monkeypatch, contenido: bytes):
    """Hace que urllib.request.urlopen devuelva 'contenido' sin salir a internet."""
    monkeypatch.setattr(urllib.request, "urlopen", lambda *args, **kwargs: io.BytesIO(contenido))


def test_buscar_devuelve_solo_libros_con_texto_plano(monkeypatch):
    _simular_urlopen(monkeypatch, json.dumps(CATALOGO).encode("utf-8"))
    respuesta = app.test_client().get("/api/gutenberg/buscar?q=quijote")

    assert respuesta.status_code == 200
    libros = respuesta.get_json()["libros"]
    assert [libro["titulo"] for libro in libros] == ["Don Quijote"]
    assert libros[0]["url_txt"] == "https://www.gutenberg.org/ebooks/2000.txt.utf-8"


def test_comprimir_libro_trae_los_campos_que_usa_el_frontend(monkeypatch):
    _simular_urlopen(monkeypatch, LIBRO)
    respuesta = app.test_client().post(
        "/api/gutenberg/comprimir",
        json={"url_txt": "https://www.gutenberg.org/ebooks/2000.txt.utf-8", "titulo": "Don Quijote"},
    )

    assert respuesta.status_code == 200
    datos = respuesta.get_json()
    # Los mismos campos que /api/comprimir (gutenberg.js llama a mostrarResultados con ellos).
    assert {"nombre_original", "nombre_bigo", "metricas", "tabla", "arbol",
            "bits_muestra", "archivo_bigo_b64", "vista_previa_texto"} <= datos.keys()
    assert datos["nombre_bigo"] == "Don Quijote.bigo"
    assert datos["metricas"]["original_bytes"] == len(LIBRO)
    assert datos["metricas"]["reduccion_porcentaje"] > 0

    # El .bigo que llega se descomprime idéntico al libro "descargado".
    bigo = base64.b64decode(datos["archivo_bigo_b64"])
    desc = app.test_client().post(
        "/api/descomprimir",
        data={"archivo": (io.BytesIO(bigo), datos["nombre_bigo"])},
        content_type="multipart/form-data",
    ).get_json()
    assert desc["integro"] is True
    assert base64.b64decode(desc["archivo_txt_b64"]) == LIBRO


def test_comprimir_rechaza_una_url_que_no_es_de_gutenberg():
    respuesta = app.test_client().post(
        "/api/gutenberg/comprimir", json={"url_txt": "https://example.com/libro.txt", "titulo": "x"}
    )
    assert respuesta.status_code == 400
