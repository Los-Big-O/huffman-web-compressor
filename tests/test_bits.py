from huffman.arbol import construir_arbol
from huffman.bits import codificar, desempaquetar, empaquetar
from huffman.codigos import generar_codigos
from huffman.frecuencias import calcular_frecuencias


def test_abracadabra_codificado_a_mano():
    # A B   R   A C   A D   A B   R   A
    # 0 110 111 0 100 0 101 0 110 111 0  -> 23 bits
    datos = b"ABRACADABRA"
    codigos = generar_codigos(construir_arbol(calcular_frecuencias(datos)))
    bits = codificar(datos, codigos)
    assert bits == "01101110100010101101110"
    assert len(bits) == 23


def test_empaquetar_agrega_relleno():
    empaquetado, relleno = empaquetar("01101110100010101101110")
    # 23 bits -> 3 bytes, con 1 bit de relleno en el último
    assert relleno == 1
    assert empaquetado == bytes([0b01101110, 0b10001010, 0b11011100])


def test_sin_relleno_cuando_son_multiplo_de_8():
    empaquetado, relleno = empaquetar("10000001")
    assert relleno == 0
    assert empaquetado == bytes([0b10000001])


def test_desempaquetar_quita_el_relleno():
    bits = "01101110100010101101110"
    empaquetado, _ = empaquetar(bits)
    assert desempaquetar(empaquetado, len(bits)) == bits


def test_texto_vacio():
    assert empaquetar("") == (b"", 0)
    assert desempaquetar(b"", 0) == ""
