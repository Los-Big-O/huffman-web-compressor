"""Paso 1 de Huffman: contar cuántas veces aparece cada símbolo.

Trabajamos con BYTES (números del 0 al 255) y no con caracteres.
Así, un texto en UTF-8 con acentos o ñ se recupera idéntico: una "ñ" ocupa
2 bytes y cada uno se cuenta por separado.
"""


def calcular_frecuencias(datos: bytes) -> dict[int, int]:
    """Devuelve un diccionario {byte: número de apariciones}.

    Ejemplo: calcular_frecuencias(b"ABRACADABRA")
    -> {65: 5, 66: 2, 82: 2, 67: 1, 68: 1}   (65 es la "A" en ASCII)
    """
    frecuencias: dict[int, int] = {}
    for byte in datos:
        # get(byte, 0) devuelve 0 la primera vez que vemos ese byte.
        frecuencias[byte] = frecuencias.get(byte, 0) + 1
    return frecuencias


def describir_simbolo(byte: int) -> str:
    """Convierte un byte en un texto legible para mostrarlo en la interfaz.

    Los caracteres invisibles se muestran con un nombre, y los bytes que no son
    ASCII (por ejemplo, las dos mitades de una "ñ" en UTF-8) en hexadecimal.
    """
    especiales = {32: "espacio", 10: "salto de línea", 13: "retorno", 9: "tabulador"}
    if byte in especiales:
        return especiales[byte]
    if 33 <= byte <= 126:  # caracteres ASCII imprimibles
        return chr(byte)
    return f"0x{byte:02X}"
