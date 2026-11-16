from huffman.frecuencias import calcular_frecuencias, describir_simbolo


def test_abracadabra_contado_a_mano():
    # A=5, B=2, R=2, C=1, D=1 (contado a mano)
    frecuencias = calcular_frecuencias(b"ABRACADABRA")
    assert frecuencias == {ord("A"): 5, ord("B"): 2, ord("R"): 2, ord("C"): 1, ord("D"): 1}


def test_la_suma_de_frecuencias_es_el_tamano_del_texto():
    datos = "El veloz murciélago hindú comía feliz cardillo y kiwi".encode("utf-8")
    assert sum(calcular_frecuencias(datos).values()) == len(datos)


def test_la_enie_cuenta_como_dos_bytes():
    frecuencias = calcular_frecuencias("ñ".encode("utf-8"))
    assert frecuencias == {0xC3: 1, 0xB1: 1}


def test_texto_vacio():
    assert calcular_frecuencias(b"") == {}


def test_describir_simbolo():
    assert describir_simbolo(ord("A")) == "A"
    assert describir_simbolo(32) == "espacio"
    assert describir_simbolo(10) == "salto de línea"
    assert describir_simbolo(0xC3) == "0xC3"
