"""Pruebas de los endpoints de Project Gutenberg sin conectarse a internet.

Se reemplaza urllib.request.urlopen por una respuesta simulada (monkeypatch), así
las pruebas no dependen de que Gutendex o gutenberg.org estén disponibles.
"""

import base64
import io
import json
import urllib.request

import pytest

from app import LIMITE_LIBRO_BYTES, app

URL_LIBRO = "https://www.gutenberg.org/ebooks/2000.txt.utf-8"

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


class RespuestaSimulada(io.BytesIO):
    """Imita lo que devuelve urlopen: se lee como un archivo y sabe su URL final."""

    def __init__(self, contenido: bytes, url_final: str):
        super().__init__(contenido)
        self.url_final = url_final

    def geturl(self):
        return self.url_final


def _simular_urlopen(monkeypatch, contenido: bytes, url_final: str = URL_LIBRO):
    """Hace que urllib.request.urlopen devuelva 'contenido' sin salir a internet.

    url_final simula a dónde llevó la descarga (después de las redirecciones).
    """
    monkeypatch.setattr(
        urllib.request, "urlopen", lambda *args, **kwargs: RespuestaSimulada(contenido, url_final)
    )


def _comprimir_libro(url_txt: str):
    return app.test_client().post(
        "/api/gutenberg/comprimir", json={"url_txt": url_txt, "titulo": "Don Quijote"}
    )


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


# --------------------------------------------- dominio de la URL (no solo el texto)


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/libro.txt",
        "https://example.com/?gutenberg.org",          # aparece en el texto, no es el dominio
        "https://gutenberg.org.example.com/libro.txt", # dominio que solo empieza igual
        "https://example.com/gutenberg.org/libro.txt", # en la ruta, no en el dominio
        "https://gutenberg.org@example.com/libro.txt", # el servidor real es example.com
        "https://notgutenberg.org/libro.txt",          # termina igual, pero es otro dominio
        "ftp://www.gutenberg.org/libro.txt",           # solo se permite http o https
    ],
)
def test_comprimir_rechaza_urls_fuera_del_dominio_de_gutenberg(monkeypatch, url):
    def no_debe_descargar(*args, **kwargs):
        raise AssertionError("No debió intentar descargar " + url)

    monkeypatch.setattr(urllib.request, "urlopen", no_debe_descargar)
    respuesta = _comprimir_libro(url)
    assert respuesta.status_code == 400
    assert "invalida" in respuesta.get_json()["error"]


@pytest.mark.parametrize(
    "url",
    ["https://gutenberg.org/ebooks/2000.txt.utf-8", "http://www.gutenberg.org/cache/epub/2000/pg2000.txt"],
)
def test_comprimir_acepta_gutenberg_y_sus_subdominios(monkeypatch, url):
    _simular_urlopen(monkeypatch, LIBRO, url_final=url)
    assert _comprimir_libro(url).status_code == 200


def test_comprimir_rechaza_una_redireccion_a_otro_sitio(monkeypatch):
    # La URL pedida es de Gutenberg, pero la descarga terminó en otro dominio.
    _simular_urlopen(monkeypatch, LIBRO, url_final="https://example.com/libro.txt")
    respuesta = _comprimir_libro(URL_LIBRO)
    assert respuesta.status_code == 400
    assert "salió de Project Gutenberg" in respuesta.get_json()["error"]


# ------------------------------------------------------------ límite de 3 MB


def test_comprimir_rechaza_un_libro_de_mas_de_3_mb(monkeypatch):
    _simular_urlopen(monkeypatch, b"a" * (LIMITE_LIBRO_BYTES + 1))
    respuesta = _comprimir_libro(URL_LIBRO)
    assert respuesta.status_code == 413
    assert "3 MB" in respuesta.get_json()["error"]
