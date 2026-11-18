"""Pruebas del adaptador: la respuesta del equipo + los campos del contrato (docs/api.md)."""


from huffman.adaptador import (
    CAMPOS_CABECERA,
    campos_compresion,
    campos_descompresion,
    campos_inspeccion,
    estructura_bigo,
)
from huffman.formato import (
    CABECERA_FIJA,
    descomprimir_bigo,
    empaquetar_bigo,
    inspeccionar_bigo,
)

CLAVES_METRICAS = {
    "original_bytes", "comprimido_bytes", "ahorro_bytes", "reduccion_porcentaje",
    "razon_compresion", "simbolos_distintos", "total_bits", "bits_relleno", "encabezado_bytes",
}
CLAVES_FILA = {"byte", "simbolo", "frecuencia", "porcentaje", "codigo", "longitud", "bits_totales"}


def _comprimir(datos: bytes, nombre="prueba.bigo"):
    resultado = empaquetar_bigo(datos)
    return resultado, campos_compresion(resultado, nombre)


def _hojas_y_internos(nodo, hojas, internos):
    """Recorre el árbol del contrato y separa hojas de nodos internos."""
    if nodo is None:
        return
    if "izquierdo" in nodo:
        internos.append(nodo)
        _hojas_y_internos(nodo["izquierdo"], hojas, internos)
        _hojas_y_internos(nodo["derecho"], hojas, internos)
    else:
        hojas.append(nodo)


# ------------------------------------------------------------- ejemplo de referencia


def test_abracadabra_coincide_con_el_ejemplo_verificado_a_mano():
    resultado, campos = _comprimir(b"ABRACADABRA")

    codigos = {fila["simbolo"]: fila["codigo"] for fila in campos["tabla"]}
    assert codigos == {"A": "0", "C": "100", "D": "101", "B": "110", "R": "111"}

    # 23 bits válidos: el último grupo tiene 7 porque el bit de relleno no se muestra.
    assert campos["bits_muestra"] == "01101110 10001010 1101110"
    assert sum(fila["bits_totales"] for fila in campos["tabla"]) == 23
    assert campos["metricas"]["total_bits"] == 23
    assert campos["metricas"]["bits_relleno"] == 1

    inspeccion = campos_inspeccion(
        resultado["archivo_bigo"], "abra.bigo", inspeccionar_bigo(resultado["archivo_bigo"])
    )
    assert inspeccion["hex_muestra"] == "6E 8A DC"


# ---------------------------------------------------------------- compresión


def test_compresion_trae_los_campos_del_contrato():
    resultado, campos = _comprimir("Hola, mundo\n".encode("utf-8"), "hola.bigo")

    assert campos["nombre_bigo"] == "hola.bigo"
    assert CLAVES_METRICAS <= campos["metricas"].keys()
    assert all(CLAVES_FILA <= fila.keys() for fila in campos["tabla"])
    # El .bigo no se duplica: el frontend lee "archivo_bigo_b64" del equipo.
    assert "archivo_bigo_base64" not in campos


def test_las_metricas_conservan_los_nombres_del_equipo():
    resultado, campos = _comprimir(b"conservar los nombres del equipo")
    # Agregar, no reemplazar: cada clave del equipo sigue con su mismo valor.
    for clave, valor in resultado["metricas"].items():
        assert campos["metricas"][clave] == valor
    assert campos["metricas"]["original_bytes"] == resultado["metricas"]["tamano_original_bytes"]


def test_texto_vacio_no_falla():
    _, campos = _comprimir(b"")
    assert campos["arbol"] is None
    assert campos["tabla"] == []
    assert campos["bits_muestra"] == ""


# ---------------------------------------------------------------------- árbol


def test_arbol_las_hojas_no_tienen_izquierdo_y_los_internos_si():
    _, campos = _comprimir("¡Ñandú, acción!".encode("utf-8"))
    hojas, internos = [], []
    _hojas_y_internos(campos["arbol"], hojas, internos)

    assert all(set(h) == {"peso", "byte", "simbolo"} for h in hojas)
    assert all(set(n) == {"peso", "izquierdo", "derecho"} for n in internos)
    # La "ñ" en UTF-8 son dos bytes no ASCII: se muestran en hexadecimal.
    assert "0xC3" in {h["simbolo"] for h in hojas}
    # El peso de la raíz es el total de bytes del texto.
    assert campos["arbol"]["peso"] == len("¡Ñandú, acción!".encode("utf-8"))


def test_arbol_de_un_solo_simbolo():
    _, campos = _comprimir(b"aaaa")
    assert campos["arbol"] == {
        "peso": 4,
        "izquierdo": {"peso": 4, "byte": 97, "simbolo": "a"},
        "derecho": None,
    }


# ------------------------------------------------------------------ inspección


def test_los_campos_del_encabezado_suman_lo_mismo_que_el_formato_del_equipo():
    # Si el equipo cambia CABECERA_FIJA, esta prueba avisa que hay que
    # actualizar CAMPOS_CABECERA del adaptador.
    import struct

    assert sum(struct.calcsize(">" + c) for _, c in CAMPOS_CABECERA) == CABECERA_FIJA.size


def test_estructura_cubre_todo_el_archivo_sin_huecos():
    resultado, _ = _comprimir(b"En un lugar de la Mancha")
    bigo = resultado["archivo_bigo"]
    secciones = estructura_bigo(resultado["metricas"]["simbolos_unicos"], len(bigo))

    assert sum(s["bytes"] for s in secciones) == len(bigo)
    for anterior, siguiente in zip(secciones, secciones[1:]):
        assert siguiente["inicio"] == anterior["inicio"] + anterior["bytes"]


def test_inspeccion_trae_los_campos_del_contrato():
    resultado, _ = _comprimir(b"inspeccionar sin descomprimir")
    bigo = resultado["archivo_bigo"]
    campos = campos_inspeccion(bigo, "libro.bigo", inspeccionar_bigo(bigo, "libro.bigo"))

    assert campos["archivo"] == {"nombre": "libro.bigo", "extension": ".bigo", "bytes": len(bigo)}
    assert campos["formato"] == {"firma": "BIGO", "version": 1}
    assert campos["sha256"] == resultado["sha256"]
    # El formato del equipo aún no guarda nombre ni fecha: van vacíos, no inventados.
    assert campos["nombre_original"] is None
    assert campos["fecha"] is None
    assert CLAVES_METRICAS <= campos["metricas"].keys()


# --------------------------------------------------------------- descompresión


def test_descompresion_trae_los_campos_del_contrato():
    original = "Ñandú, cigüeña y acción\n".encode("utf-8") * 20
    bigo = empaquetar_bigo(original)["archivo_bigo"]
    campos = campos_descompresion(descomprimir_bigo(bigo), "libro.bigo")

    # El texto no se duplica: el frontend lee "archivo_txt_b64" del equipo.
    assert "texto_base64" not in campos
    assert campos["integro"] is True
    assert campos["bytes"] == len(original)
    assert campos["sha256_guardado"] == campos["sha256_recuperado"]
    assert campos["nombre_original"] == "libro.txt"
