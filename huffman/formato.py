"""Formato .bigo para almacenar y reconstruir archivos comprimidos con Huffman

Estructura binaria del archivo .bigo:
- 4 bytes : "BIGO" (marca de archivo)
- 1 byte : version del formato (uint8)
- 8 bytes : tamaño orifinal en bites
- 8 bytes : Total de bits validos codificados
- 32 bytes : Hash SHA-256 del archivo original
- 2 bytes : Cantidad N de simbolos distintos en la tabla
- N * 9 B : Tabla de frecuencias -> N pares de [simbolo (1B uint8), frecuencia (8B uint64)]
- Resto : Bits binarios comprimidos empaquetados en bytes
"""
import hashlib
import struct

from huffman.arbol import Nodo, construir_arbol
from huffman.bits import TABLA_BITS, codificar, decodificar, empaquetar, desempaquetar
from huffman.codigos import generar_codigos
from huffman.frecuencias import calcular_frecuencias, describir_simbolo

FIRMA_MAGICA = b"BIGO"
VERSION_FORMATO = 1
EXTENSION_FORMATO = ".bigo"
CABECERA_FIJA = struct.Struct(">4sBQQ32sH")  # 4s: firma, B: version, Q: tamaño original, Q: total bits, 32s: hash, H: cantidad simbolos
ENTRADA_TABLA = struct.Struct(">BQ")  # B: simbolo, Q: frecuencia

def formatear_tamano(num_bytes: int) -> str:
    """Devuelve una representacion legible en B, KB o MB"""
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.2f} KB"
    return f"{num_bytes / (1024 * 1024):.2f} MB"

def serializar_arbol(nodo: Nodo | None) -> dict | None:
    """Convierte el arbol de Huffman en un diccionario JSON-serializable para el frontend"""
    if nodo is None:
        return None
    es_hoja = nodo.es_hoja()
    return{
        "peso": nodo.peso,
        "simbolo": nodo.simbolo,
        "etiqueta": describir_simbolo(nodo.simbolo) if es_hoja else str(nodo.peso),
        "es_hoja": es_hoja,
        "izquierdo": serializar_arbol(nodo.izquierdo),
        "derecho": serializar_arbol(nodo.derecho),
    }

def construir_tabla_visual(
    frecuencias: dict[int, int], codigos: dict[int, str], total_bytes: int
) -> list[dict]:
    """Genera la lista ordenada de simbolos con frecuencia, porcentaje y codigo"""
    filas = []
    for simbolo, freq in sorted(frecuencias.items(), key=lambda item: (-item[1], item[0])):
        porcentaje = (freq / total_bytes * 100) if total_bytes > 0 else 0.0
        filas.append(
            {
                "byte": simbolo,
                "simbolo": describir_simbolo(simbolo),
                "frecuencia": freq,
                "porcentaje": round(porcentaje, 2),
                "codigo": codigos.get(simbolo, ""),
                "longitud_bits": len(codigos.get(simbolo, "")),
            }
        )
    return filas

def calcular_metricas(
    tamano_original: int, tamano_comprimido: int, num_simbolos: int, total_bits: int
) -> dict:
    """Calcula todas las metricas de compresion requeridas"""
    ahorro_bytes = tamano_original - tamano_comprimido
    if tamano_original > 0:
        reduccion_pct = (ahorro_bytes / tamano_original) * 100
        razon = tamano_original / tamano_comprimido if tamano_comprimido > 0 else 0.0
    else:
        reduccion_pct = 0.0
        razon = 0.0

    return {
        "tamano_original_bytes": tamano_original,
        "tamano_original_legible": formatear_tamano(tamano_original),
        "tamano_comprimido_bytes": tamano_comprimido,
        "tamano_comprimido_legible": formatear_tamano(tamano_comprimido),
        "ahorro_bytes": ahorro_bytes,
        "ahorro_legible": formatear_tamano(abs(ahorro_bytes)),
        "reduccion_porcentaje": round(reduccion_pct, 2),
        "razon_compresion": round(razon, 2),
        "simbolos_unicos": num_simbolos,
        "total_bits": total_bits,
    }


def empaquetar_bigo(datos_originales: bytes) -> dict:
    """Ejecuta el pipeline completo de compresion y genera el binario .bigo"""
    tamano_original = len(datos_originales)
    sha256_digest = hashlib.sha256(datos_originales).digest()

    frecuencias = calcular_frecuencias(datos_originales)
    raiz = construir_arbol(frecuencias)
    codigos = generar_codigos(raiz)
    bits_cadena = codificar(datos_originales, codigos)
    datos_empaquetados, bits_relleno = empaquetar(bits_cadena)
    total_bits = len(bits_cadena)

    simbolos_ordenados = sorted(frecuencias.items())
    cabecera = CABECERA_FIJA.pack(
        FIRMA_MAGICA,
        VERSION_FORMATO,
        tamano_original,
        total_bits,
        sha256_digest,
        len(simbolos_ordenados),
    )
    tabla_binaria = b"".join(
        ENTRADA_TABLA.pack(simbolo, freq) for simbolo, freq in simbolos_ordenados
    )

    archivo_bigo = cabecera + tabla_binaria + datos_empaquetados
    tamano_comprimido = len(archivo_bigo)
    tamano_cabecera = len(cabecera) + len(tabla_binaria)

    metricas = calcular_metricas(
        tamano_original, tamano_comprimido, len(frecuencias), total_bits
    )
    metricas["tamano_cabecera_bytes"] = tamano_cabecera
    metricas["tamano_datos_bytes"] = len(datos_empaquetados)
    metricas["bits_relleno"] = bits_relleno

    return {
        "archivo_bigo": archivo_bigo,
        "version": VERSION_FORMATO,
        "sha256": sha256_digest.hex(),
        "metricas": metricas,
        "tabla": construir_tabla_visual(frecuencias, codigos, tamano_original),
        "arbol": serializar_arbol(raiz),
    }


def _leer_estructura_bigo(contenido_bigo: bytes) -> dict:
    """Valida y extrae las secciones internas de un archivo .bigo"""
    if len(contenido_bigo) < CABECERA_FIJA.size:
        raise ValueError("El archivo es demasiado pequeño para ser un formato .bigo")

    (
        firma,
        version,
        tamano_original,
        total_bits,
        sha256_digest,
        num_simbolos,
    ) = CABECERA_FIJA.unpack_from(contenido_bigo, 0)

    if firma != FIRMA_MAGICA:
        raise ValueError("Firma invalida: el archivo no corresponde al formato .bigo")
    if version != VERSION_FORMATO:
        raise ValueError(f"Versión de formato no soportada: {version}.")

    offset = CABECERA_FIJA.size
    tamano_tabla = num_simbolos * ENTRADA_TABLA.size
    if len(contenido_bigo) < offset + tamano_tabla:
        raise ValueError("Archivo .bigo corrupto: tabla de frecuencias incompleta")

    frecuencias: dict[int, int] = {}
    for _ in range(num_simbolos):
        simbolo, freq = ENTRADA_TABLA.unpack_from(contenido_bigo, offset)
        frecuencias[simbolo] = freq
        offset += ENTRADA_TABLA.size

    datos_empaquetados = contenido_bigo[offset:]
    bits_relleno = (8 - (total_bits % 8)) % 8

    return {
        "version": version,
        "tamano_original": tamano_original,
        "total_bits": total_bits,
        "bits_relleno": bits_relleno,
        "sha256_digest": sha256_digest,
        "num_simbolos": num_simbolos,
        "frecuencias": frecuencias,
        "tamano_cabecera": offset,
        "datos_empaquetados": datos_empaquetados,
    }


def inspeccionar_bigo(contenido_bigo: bytes, nombre_archivo: str = "archivo.bigo") -> dict:
    """Inspecciona un archivo .bigo sin descomprimir el texto original"""
    info = _leer_estructura_bigo(contenido_bigo)
    raiz = construir_arbol(info["frecuencias"])
    codigos = generar_codigos(raiz)

    tamano_comprimido = len(contenido_bigo)
    metricas = calcular_metricas(
        info["tamano_original"],
        tamano_comprimido,
        info["num_simbolos"],
        info["total_bits"],
    )
    metricas["tamano_cabecera_bytes"] = info["tamano_cabecera"]
    metricas["tamano_datos_bytes"] = len(info["datos_empaquetados"])
    metricas["bits_relleno"] = info["bits_relleno"]

    # Muestra parcial y legible de los primeros 64 bytes comprimidos
    muestra_bytes = info["datos_empaquetados"][:64]
    grupos_bits = [TABLA_BITS[b] for b in muestra_bytes]
    vista_binaria = " ".join(grupos_bits)
    if len(info["datos_empaquetados"]) > 64:
        vista_binaria += " ..."

    return {
        "nombre_archivo": nombre_archivo,
        "extension": EXTENSION_FORMATO,
        "version": f"BIGO v{info['version']}",
        "sha256_original": info["sha256_digest"].hex(),
        "metricas": metricas,
        "tabla": construir_tabla_visual(
            info["frecuencias"], codigos, info["tamano_original"]
        ),
        "arbol": serializar_arbol(raiz),
        "vista_binaria": vista_binaria,
    }


def descomprimir_bigo(contenido_bigo: bytes) -> dict:
    """Descomprime un archivo .bigo y verifica su integridad SHA-256"""
    info = _leer_estructura_bigo(contenido_bigo)
    raiz = construir_arbol(info["frecuencias"])

    bits_validos = desempaquetar(info["datos_empaquetados"], info["total_bits"])
    datos_recuperados = decodificar(bits_validos, raiz)

    sha256_calculado = hashlib.sha256(datos_recuperados).digest()
    integro = (
        sha256_calculado == info["sha256_digest"]
        and len(datos_recuperados) == info["tamano_original"]
    )
    # Si las huellas no coinciden NO se lanza error: se devuelve integro=False
    # con las dos huellas, para que la interfaz pueda mostrarlas y compararlas.

    texto_recuperado = datos_recuperados.decode("utf-8", errors="replace")

    return {
        "datos_recuperados": datos_recuperados,
        "texto_recuperado": texto_recuperado,
        "integro": integro,
        "sha256_esperado": info["sha256_digest"].hex(),
        "sha256_calculado": sha256_calculado.hex(),
        "tamano_recuperado": len(datos_recuperados),
    }