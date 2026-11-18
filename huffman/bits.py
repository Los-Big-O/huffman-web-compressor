"""Paso 4 de Huffman: convertir el texto en bits y guardarlos en bytes.

1. codificar: sustituye cada byte del texto por su código ("0", "110", ...).
2. empaquetar: agrupa los bits de 8 en 8 para formar bytes reales.
   Si el total no es múltiplo de 8, se rellena el último byte con ceros
   y se anota cuántos bits de relleno se agregaron.
3. desempaquetar: hace el camino inverso (lo usa el descompresor).
"""

# decodificar() usa Nodo en su firma. Sin este import, Python 3.12 y 3.13
# lanzan NameError al importar el módulo (3.14 evalúa las anotaciones tarde).
from huffman.arbol import Nodo

# Tabla para convertir rápido un byte en sus 8 bits: TABLA_BITS[5] == "00000101"
TABLA_BITS = [format(numero, "08b") for numero in range(256)]


def codificar(datos: bytes, codigos: dict[int, str]) -> str:
    """Devuelve el texto como una cadena de '0' y '1'."""
    return "".join(codigos[byte] for byte in datos)


def empaquetar(bits: str) -> tuple[bytes, int]:
    """Convierte una cadena de bits en bytes.

    Devuelve (bytes empaquetados, número de bits de relleno del último byte).
    Ejemplo: "0110111" (7 bits) -> se agrega 1 bit de relleno -> "01101110".
    """
    relleno = (8 - len(bits) % 8) % 8
    bits_completos = bits + "0" * relleno
    empaquetado = bytes(
        int(bits_completos[i : i + 8], 2) for i in range(0, len(bits_completos), 8)
    )
    return empaquetado, relleno


def desempaquetar(datos: bytes, total_bits: int) -> str:
    """Convierte bytes en bits y descarta el relleno usando el total de bits válidos."""
    bits = "".join(TABLA_BITS[byte] for byte in datos)
    return bits[:total_bits]

def decodificar(bits: str, raiz: Nodo | None) -> bytes:
    """Recorre el arbol de Huffman con la secuencia de bits y recupera los bits"""
    if not bits or raiz is None:
        return b""

    salida = bytearray()
    actual = raiz

    for bit in bits:
        if bit == "0":
            actual = actual.izquierdo
        elif bit == "1":
            actual = actual.derecho
        else:
            raise ValueError(f"Bit invalido encontrado: {bit!r}")

        if actual is None:
            raise ValueError("Secuencia de bits corrupta: Camino inexistente en el arbol")

        if actual.es_hoja():
            salida.append(actual.simbolo)
            actual = raiz

    if actual is not raiz:
        raise ValueError("Secuencia de bits incompleta: Termino fuera de una hoja")

    return bytes(salida)