from huffman.arbol import construir_arbol
from huffman.frecuencias import calcular_frecuencias


def hojas(nodo):
    """Devuelve las hojas del árbol de izquierda a derecha."""
    if nodo is None:
        return []
    if nodo.es_hoja():
        return [nodo]
    return hojas(nodo.izquierdo) + hojas(nodo.derecho)


def test_la_raiz_suma_el_total_de_bytes():
    datos = b"ABRACADABRA"
    raiz = construir_arbol(calcular_frecuencias(datos))
    assert raiz.peso == len(datos)


def test_cada_simbolo_es_una_hoja():
    raiz = construir_arbol(calcular_frecuencias(b"ABRACADABRA"))
    assert sorted(h.simbolo for h in hojas(raiz)) == sorted(b"ABCDR")


def test_la_a_es_la_mas_cercana_a_la_raiz():
    # La A es la más frecuente (5 de 11), así que queda como hijo directo de la raíz.
    raiz = construir_arbol(calcular_frecuencias(b"ABRACADABRA"))
    assert raiz.izquierdo.es_hoja()
    assert raiz.izquierdo.simbolo == ord("A")


def test_el_arbol_sale_igual_sin_importar_el_orden_de_la_tabla():
    # El descompresor lee la tabla en otro orden: el árbol debe ser idéntico.
    frecuencias = calcular_frecuencias(b"ABRACADABRA")
    al_reves = dict(reversed(list(frecuencias.items())))
    simbolos_1 = [h.simbolo for h in hojas(construir_arbol(frecuencias))]
    simbolos_2 = [h.simbolo for h in hojas(construir_arbol(al_reves))]
    assert simbolos_1 == simbolos_2


def test_un_solo_simbolo():
    raiz = construir_arbol({ord("a"): 4})
    assert raiz.peso == 4
    assert raiz.izquierdo.simbolo == ord("a")
    assert raiz.derecho is None


def test_tabla_vacia():
    assert construir_arbol({}) is None
