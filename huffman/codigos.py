"""Paso 3 de Huffman: asignar un código binario a cada símbolo.

Recorremos el árbol desde la raíz: ir a la izquierda agrega un "0" y ir a la
derecha agrega un "1". El camino hasta cada hoja es el código de ese símbolo.

Como los símbolos solo están en las hojas, ningún código es el inicio de otro
(códigos "libres de prefijos"). Gracias a eso se pueden decodificar sin separadores.
"""

from huffman.arbol import Nodo


def generar_codigos(raiz: Nodo | None) -> dict[int, str]:
    """Devuelve un diccionario {byte: código}, por ejemplo {65: "0", 66: "110"}."""
    codigos: dict[int, str] = {}
    if raiz is None:
        return codigos

    # Recorrido con una pila en lugar de recursión: cada elemento es
    # (nodo, camino recorrido hasta ese nodo).
    pila = [(raiz, "")]
    while pila:
        nodo, camino = pila.pop()
        if nodo.es_hoja():
            codigos[nodo.simbolo] = camino
            continue
        if nodo.derecho is not None:
            pila.append((nodo.derecho, camino + "1"))
        if nodo.izquierdo is not None:
            pila.append((nodo.izquierdo, camino + "0"))
    return codigos
