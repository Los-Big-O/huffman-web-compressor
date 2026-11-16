"""Paso 2 de Huffman: construir el árbol con la estrategia voraz.

Idea voraz: en cada paso tomamos los DOS nodos de menor peso y los unimos en
un nodo nuevo cuyo peso es la suma. Repetimos hasta que queda un solo nodo: la raíz.

Para sacar siempre el de menor peso usamos una cola de prioridad (min-heap)
del módulo heapq de Python. heapq solo nos da la cola; la estrategia voraz,
los nodos y el árbol son código nuestro.
"""

import heapq
import itertools


class Nodo:
    """Un nodo del árbol de Huffman.

    - Hoja: guarda un símbolo (un byte) y su frecuencia.
    - Nodo interno: no tiene símbolo; su peso es la suma de sus dos hijos.
    """

    def __init__(self, peso, simbolo=None, izquierdo=None, derecho=None):
        self.peso = peso
        self.simbolo = simbolo
        self.izquierdo = izquierdo
        self.derecho = derecho

    def es_hoja(self) -> bool:
        return self.izquierdo is None and self.derecho is None

    def __repr__(self):
        if self.es_hoja():
            return f"Hoja({self.simbolo}, {self.peso})"
        return f"Nodo({self.peso})"


def construir_arbol(frecuencias: dict[int, int]) -> Nodo | None:
    """Construye el árbol de Huffman a partir de la tabla de frecuencias.

    Regla de desempate (para que el árbol salga SIEMPRE igual):
    1. Sale primero el nodo de menor peso.
    2. Si dos pesan lo mismo, sale primero el que se creó antes.
       Por eso cada entrada del heap es (peso, orden_de_creacion, nodo).
    3. Las hojas se crean en orden de byte (0, 1, 2, ...), no en el orden en
       que aparecen en el texto. Así el descompresor, que lee la tabla del
       archivo .bigo, construye exactamente el mismo árbol que el compresor.
    """
    if not frecuencias:
        return None

    contador = itertools.count()  # 0, 1, 2, ... marca el orden de creación
    cola = []
    for simbolo in sorted(frecuencias):
        hoja = Nodo(frecuencias[simbolo], simbolo=simbolo)
        heapq.heappush(cola, (hoja.peso, next(contador), hoja))

    # Caso especial: un solo símbolo distinto (por ejemplo "aaaa").
    # Le ponemos una raíz con la hoja a la izquierda para que su código sea "0".
    if len(cola) == 1:
        hoja = cola[0][2]
        return Nodo(hoja.peso, izquierdo=hoja)

    # Paso voraz: unir los dos de menor peso hasta que quede uno.
    while len(cola) > 1:
        peso_a, _, menor = heapq.heappop(cola)
        peso_b, _, segundo = heapq.heappop(cola)
        padre = Nodo(peso_a + peso_b, izquierdo=menor, derecho=segundo)
        heapq.heappush(cola, (padre.peso, next(contador), padre))

    return cola[0][2]
