"""Pruebas de integridad: un .bigo con el hash alterado se descomprime, pero no es íntegro."""

import io

from app import app
from huffman.formato import descomprimir_bigo, empaquetar_bigo

# El hash SHA-256 empieza después de firma (4) + versión (1) + tamaño original (8)
# + total de bits (8) = byte 21, y ocupa 32 bytes.
INICIO_HASH = 21


def _bigo_con_hash_alterado(original: bytes) -> bytes:
    """Cambia solo un byte del hash guardado; los datos comprimidos quedan intactos."""
    bigo = bytearray(empaquetar_bigo(original)["archivo_bigo"])
    bigo[INICIO_HASH] ^= 0xFF
    return bytes(bigo)


def test_hash_alterado_devuelve_integro_false_con_las_dos_huellas():
    original = b"ABRACADABRA" * 20
    resultado = descomprimir_bigo(_bigo_con_hash_alterado(original))

    # El texto se decodifica bien (los datos no se tocaron)...
    assert resultado["datos_recuperados"] == original
    # ...pero la huella guardada ya no coincide con la calculada.
    assert resultado["integro"] is False
    assert resultado["sha256_esperado"] != resultado["sha256_calculado"]


def test_el_endpoint_responde_200_con_integro_false():
    cliente = app.test_client()
    respuesta = cliente.post(
        "/api/descomprimir",
        data={"archivo": (io.BytesIO(_bigo_con_hash_alterado(b"Hola, mundo\n" * 10)), "hola.bigo")},
        content_type="multipart/form-data",
    )
    assert respuesta.status_code == 200
    datos = respuesta.get_json()
    assert datos["integro"] is False
    assert datos["sha256_guardado"] != datos["sha256_recuperado"]
