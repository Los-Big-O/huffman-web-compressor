import pytest

from huffman.formato import descomprimir_bigo, empaquetar_bigo, inspeccionar_bigo


def test_ciclo_completo_comprimir_inspeccionar_descomprimir():
    texto = "En un lugar de la Mancha, de cuyo nombre no quiero acordarme... ¡Ñandú! 123\n" * 10
    original = texto.encode("utf-8")

    resultado = empaquetar_bigo(original)
    archivo_bigo = resultado["archivo_bigo"]
    assert archivo_bigo.startswith(b"BIGO")

    inspeccion = inspeccionar_bigo(archivo_bigo, "quijote.bigo")
    assert inspeccion["metricas"]["tamano_original_bytes"] == len(original)
    assert inspeccion["metricas"]["tamano_comprimido_bytes"] == len(archivo_bigo)
    assert inspeccion["metricas"]["reduccion_porcentaje"] > 0

    descomprimido = descomprimir_bigo(archivo_bigo)
    assert descomprimido["integro"] is True
    assert descomprimido["datos_recuperados"] == original
    assert descomprimido["texto_recuperado"] == texto


def test_detecta_archivo_corrupto_por_hash():
    original = b"ABRACADABRA" * 20
    archivo_bigo = bytearray(empaquetar_bigo(original)["archivo_bigo"])
    # Alteramos el ultimo byte de datos comprimidos
    archivo_bigo[-1] ^= 0xFF

    with pytest.raises(ValueError):
        descomprimir_bigo(bytes(archivo_bigo))


def test_archivo_vacio_y_un_solo_simbolo():
    for caso in [b"", b"zzzzzzzzzz"]:
        bigo = empaquetar_bigo(caso)["archivo_bigo"]
        rec = descomprimir_bigo(bigo)
        assert rec["integro"] is True
        assert rec["datos_recuperados"] == caso