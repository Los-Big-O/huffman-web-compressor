from huffman.arbol import construir_arbol
from huffman.codigos import generar_codigos
from huffman.frecuencias import calcular_frecuencias


def codigos_de(texto: bytes):
    return generar_codigos(construir_arbol(calcular_frecuencias(texto)))


def test_codigos_de_abracadabra():
    # Resultado esperado con nuestra regla de desempate (verificado a mano):
    # A=0, C=100, D=101, B=110, R=111
    codigos = codigos_de(b"ABRACADABRA")
    assert codigos == {
        ord("A"): "0",
        ord("C"): "100",
        ord("D"): "101",
        ord("B"): "110",
        ord("R"): "111",
    }


def test_ningun_codigo_es_prefijo_de_otro():
    codigos = list(codigos_de("En un lugar de la Mancha, de cuyo nombre...".encode("utf-8")).values())
    for a in codigos:
        for b in codigos:
            if a != b:
                assert not b.startswith(a)


def test_los_mas_frecuentes_tienen_codigos_mas_cortos():
    frecuencias = calcular_frecuencias(b"AAAAAAAABBBC")
    codigos = generar_codigos(construir_arbol(frecuencias))
    assert len(codigos[ord("A")]) <= len(codigos[ord("B")]) <= len(codigos[ord("C")])


def test_un_solo_simbolo_tiene_codigo_cero():
    assert codigos_de(b"aaaa") == {ord("a"): "0"}


def test_arbol_vacio():
    assert generar_codigos(None) == {}
