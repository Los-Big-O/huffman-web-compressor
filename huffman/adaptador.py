"""Adaptador entre el backend del equipo y el contrato de la API (docs/api.md).

El backend del equipo (huffman/formato.py) responde con sus propios nombres de
campos. La interfaz (public/) espera los nombres del contrato. En lugar de
reescribir uno de los dos, este módulo AGREGA los campos del contrato a la
respuesta del equipo, sin quitar los suyos, para no romper sus pruebas.

La única excepción es "arbol": los dos formatos usan la misma clave con forma
distinta, así que aquí se reemplaza por la versión del contrato.

Los campos GRANDES no se duplican: el .bigo en base64 (archivo_bigo_b64) y el
texto recuperado en base64 (archivo_txt_b64) conservan el nombre del equipo y
el frontend los lee así. Mandarlos dos veces con otro nombre haría que un libro
de 3 MB pasara el límite de 4.5 MB por respuesta de Vercel.
"""

import os
import struct

from huffman.bits import TABLA_BITS
from huffman.formato import CABECERA_FIJA, ENTRADA_TABLA, FIRMA_MAGICA
from huffman.frecuencias import describir_simbolo

# Cuántos bytes comprimidos se muestran como ejemplo: 32 bytes = 256 bits.
BYTES_MUESTRA = 32

# Campos del encabezado fijo del .bigo del equipo, en orden, con su código de
# struct. Deben sumar CABECERA_FIJA.size; una prueba lo verifica para enterarnos
# si el equipo cambia el formato.
CAMPOS_CABECERA = [
    ("Firma", "4s"),
    ("Versión", "B"),
    ("Tamaño original", "Q"),
    ("Total de bits", "Q"),
    ("Hash SHA-256", "32s"),
    ("Número de símbolos", "H"),
]


# ---------------------------------------------------------------- piezas sueltas


def adaptar_metricas(metricas: dict) -> dict:
    """Agrega los nombres del contrato a las métricas del equipo."""
    return {
        **metricas,
        "original_bytes": metricas["tamano_original_bytes"],
        "comprimido_bytes": metricas["tamano_comprimido_bytes"],
        "simbolos_distintos": metricas["simbolos_unicos"],
        "encabezado_bytes": metricas["tamano_cabecera_bytes"],
        # ahorro_bytes, reduccion_porcentaje, razon_compresion, total_bits y
        # bits_relleno ya se llaman igual en los dos lados.
    }


def adaptar_tabla(filas: list[dict]) -> list[dict]:
    """Agrega 'longitud' y 'bits_totales' a cada fila de la tabla del equipo.

    bits_totales = frecuencia × longitud del código: cuántos bits ocupa ese
    símbolo en el texto comprimido. La suma de todas las filas da total_bits.
    """
    return [
        {
            **fila,
            "longitud": fila["longitud_bits"],
            "bits_totales": fila["frecuencia"] * fila["longitud_bits"],
        }
        for fila in filas
    ]


def adaptar_arbol(nodo: dict | None) -> dict | None:
    """Convierte el árbol del equipo a la forma del contrato.

    - Hoja: {peso, byte, simbolo}. No lleva la clave "izquierdo": así la
      reconoce el frontend (arbol.js revisa izquierdo === undefined).
    - Nodo interno: {peso, izquierdo, derecho}. Con un solo símbolo distinto
      la raíz tiene la hoja a la izquierda y derecho = None (null en JSON).
    """
    if nodo is None:
        return None
    if nodo["es_hoja"]:
        # En el árbol del equipo, "simbolo" es el número de byte.
        return {
            "peso": nodo["peso"],
            "byte": nodo["simbolo"],
            "simbolo": describir_simbolo(nodo["simbolo"]),
        }
    return {
        "peso": nodo["peso"],
        "izquierdo": adaptar_arbol(nodo["izquierdo"]),
        "derecho": adaptar_arbol(nodo["derecho"]),
    }


def muestra_bits(datos_comprimidos: bytes, total_bits: int) -> str:
    """Primeros 256 bits VÁLIDOS en grupos de 8: "01101110 10001010 1101110".

    Se cortan en total_bits para no mostrar los bits de relleno como si fueran
    datos; por eso el último grupo puede tener menos de 8.
    """
    bits = "".join(TABLA_BITS[b] for b in datos_comprimidos[:BYTES_MUESTRA])
    bits = bits[: min(total_bits, BYTES_MUESTRA * 8)]
    return " ".join(bits[i : i + 8] for i in range(0, len(bits), 8))


def muestra_hex(datos_comprimidos: bytes) -> str:
    """Primeros 32 bytes comprimidos en hexadecimal: "6E 8A DC"."""
    return " ".join(f"{b:02X}" for b in datos_comprimidos[:BYTES_MUESTRA])


def estructura_bigo(num_simbolos: int, tamano_total: int) -> list[dict]:
    """Mapa de secciones del .bigo del equipo: [{campo, inicio, bytes}, ...]."""
    secciones = []
    inicio = 0
    for campo, codigo in CAMPOS_CABECERA:
        tamano = struct.calcsize(">" + codigo)
        secciones.append({"campo": campo, "inicio": inicio, "bytes": tamano})
        inicio += tamano

    tamano_tabla = num_simbolos * ENTRADA_TABLA.size
    secciones.append({"campo": "Tabla de frecuencias", "inicio": inicio, "bytes": tamano_tabla})
    inicio += tamano_tabla

    secciones.append({"campo": "Datos comprimidos", "inicio": inicio, "bytes": tamano_total - inicio})
    return secciones


# ------------------------------------------------- campos por endpoint (para app.py)


def campos_compresion(resultado: dict, nombre_bigo: str) -> dict:
    """Campos del contrato para /api/comprimir.

    resultado es lo que devuelve empaquetar_bigo(). Se mezcla con la respuesta
    del equipo usando dict.update(). El .bigo ya va en "archivo_bigo_b64" (del
    equipo), así que aquí no se repite.
    """
    metricas = resultado["metricas"]
    datos = resultado["archivo_bigo"][metricas["tamano_cabecera_bytes"] :]
    return {
        "nombre_bigo": nombre_bigo,
        "metricas": adaptar_metricas(metricas),
        "tabla": adaptar_tabla(resultado["tabla"]),
        "arbol": adaptar_arbol(resultado["arbol"]),
        "bits_muestra": muestra_bits(datos, metricas["total_bits"]),
    }


def campos_inspeccion(contenido: bytes, nombre_archivo: str, reporte: dict) -> dict:
    """Campos del contrato para /api/inspeccionar.

    reporte es lo que devuelve inspeccionar_bigo(), que ya validó firma y
    versión; por eso aquí se pueden leer directamente.
    """
    metricas = reporte["metricas"]
    datos = contenido[metricas["tamano_cabecera_bytes"] :]
    return {
        "archivo": {
            "nombre": nombre_archivo,
            "extension": os.path.splitext(nombre_archivo)[1],
            "bytes": len(contenido),
        },
        "formato": {
            "firma": FIRMA_MAGICA.decode("ascii"),
            "version": contenido[4],  # el byte que sigue a la firma
        },
        # El formato del equipo todavía no guarda nombre ni fecha. Se envían
        # vacíos (null) en lugar de inventarlos; el frontend oculta esas filas.
        "nombre_original": None,
        "fecha": None,
        "sha256": reporte["sha256_original"],
        "metricas": adaptar_metricas(metricas),
        "estructura": estructura_bigo(metricas["simbolos_unicos"], len(contenido)),
        "tabla": adaptar_tabla(reporte["tabla"]),
        "arbol": adaptar_arbol(reporte["arbol"]),
        "bits_muestra": muestra_bits(datos, metricas["total_bits"]),
        "hex_muestra": muestra_hex(datos),
    }


def campos_descompresion(resultado: dict, nombre_bigo: str) -> dict:
    """Campos del contrato para /api/descomprimir.

    resultado es lo que devuelve descomprimir_bigo(). El texto recuperado ya
    va en "archivo_txt_b64" (del equipo), así que aquí no se repite.
    """
    # Como el .bigo no guarda el nombre original, se deduce del nombre del
    # .bigo: "libro.bigo" -> "libro.txt". El frontend lo usa como nombre de
    # descarga ("libro_recuperado.txt").
    raiz = os.path.splitext(os.path.basename(nombre_bigo))[0] or "documento"
    return {
        "nombre_original": f"{raiz}.txt",
        "bytes": resultado["tamano_recuperado"],
        "integro": resultado["integro"],
        "sha256_guardado": resultado["sha256_esperado"],
        "sha256_recuperado": resultado["sha256_calculado"],
    }
