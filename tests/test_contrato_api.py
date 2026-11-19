"""Pruebas de los endpoints contra el contrato (docs/api.md) y el límite de Vercel."""

import base64
import io
import random

from app import LIMITE_BIGO_BYTES, LIMITE_BYTES, app

# Vercel acepta como máximo 4.5 MB por respuesta. Usamos 4 500 000 bytes (y no
# 4.5 × 1024 × 1024) para quedar del lado seguro.
LIMITE_RESPUESTA = 4_500_000

PARRAFO = (
    "En un lugar de la Mancha, de cuyo nombre no quiero acordarme, no ha mucho "
    "tiempo que vivía un hidalgo de los de lanza en astillero, adarga antigua, "
    "rocín flaco y galgo corredor. ¡Ñandú! 123\n"
)


def _subir(cliente, ruta, datos, nombre):
    return cliente.post(
        ruta,
        data={"archivo": (io.BytesIO(datos), nombre)},
        content_type="multipart/form-data",
    )


def test_un_libro_de_3_mb_cabe_en_el_limite_de_vercel():
    original = (PARRAFO * (3_000_000 // len(PARRAFO) + 1)).encode("utf-8")[:3_000_000]
    cliente = app.test_client()

    comp = _subir(cliente, "/api/comprimir", original, "libro.txt")
    assert comp.status_code == 200
    assert len(comp.data) < LIMITE_RESPUESTA

    bigo = base64.b64decode(comp.get_json()["archivo_bigo_b64"])
    desc = _subir(cliente, "/api/descomprimir", bigo, "libro.bigo")
    assert desc.status_code == 200
    assert len(desc.data) < LIMITE_RESPUESTA
    # Y el texto recuperado sigue siendo idéntico, byte a byte.
    assert base64.b64decode(desc.get_json()["archivo_txt_b64"]) == original


def test_cada_endpoint_trae_las_claves_del_contrato():
    cliente = app.test_client()
    original = (PARRAFO * 5).encode("utf-8")

    comp = _subir(cliente, "/api/comprimir", original, "libro.txt").get_json()
    assert {"nombre_original", "nombre_bigo", "metricas", "tabla", "arbol",
            "bits_muestra", "archivo_bigo_b64"} <= comp.keys()
    bigo = base64.b64decode(comp["archivo_bigo_b64"])

    insp = _subir(cliente, "/api/inspeccionar", bigo, "libro.bigo").get_json()
    assert {"archivo", "formato", "nombre_original", "fecha", "sha256", "metricas",
            "estructura", "tabla", "arbol", "bits_muestra", "hex_muestra"} <= insp.keys()

    desc = _subir(cliente, "/api/descomprimir", bigo, "libro.bigo").get_json()
    assert {"nombre_original", "bytes", "integro", "sha256_guardado",
            "sha256_recuperado", "archivo_txt_b64"} <= desc.keys()
    # El texto ya no va repetido como texto plano.
    assert "texto_recuperado" not in desc


def test_archivo_de_mas_de_3_mb_responde_413():
    cliente = app.test_client()
    respuesta = _subir(cliente, "/api/comprimir", b"a" * (LIMITE_BYTES + 1), "grande.txt")
    assert respuesta.status_code == 413
    assert "3 MB" in respuesta.get_json()["error"]


def test_bigo_de_mas_de_3_mb_mas_4_kb_responde_413():
    # Un .bigo tiene 4 KB más de margen que un .txt, pero también tiene límite.
    cliente = app.test_client()
    respuesta = _subir(cliente, "/api/descomprimir", b"B" * (LIMITE_BIGO_BYTES + 1), "grande.bigo")
    assert respuesta.status_code == 413
    assert "4 KB" in respuesta.get_json()["error"]


def test_el_peor_caso_en_el_limite_cabe_en_vercel():
    """Un archivo casi de 3 MB que casi no se comprime (bytes al azar, los 256 símbolos).

    Es el caso más pesado que el servidor acepta: ni la compresión ni la
    descompresión deben pasar el límite de respuesta de Vercel.
    """
    # Se dejan 1000 bytes de margen para los encabezados del multipart.
    original = random.Random(0).randbytes(LIMITE_BYTES - 1000)
    cliente = app.test_client()

    comp = _subir(cliente, "/api/comprimir", original, "azar.txt")
    assert comp.status_code == 200
    assert len(comp.data) < LIMITE_RESPUESTA

    bigo = base64.b64decode(comp.get_json()["archivo_bigo_b64"])
    desc = _subir(cliente, "/api/descomprimir", bigo, "azar.bigo")
    assert desc.status_code == 200
    assert len(desc.data) < LIMITE_RESPUESTA
    assert base64.b64decode(desc.get_json()["archivo_txt_b64"]) == original
