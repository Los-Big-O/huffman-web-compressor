import base64
import io

from app import app


def test_el_servidor_responde():
    cliente = app.test_client()
    respuesta = cliente.get("/api/salud")
    assert respuesta.status_code == 200
    assert respuesta.get_json() == {"estado": "ok"}


def test_la_pagina_principal_carga():
    cliente = app.test_client()
    respuesta = cliente.get("/")
    assert respuesta.status_code == 200
    assert b"Huffman" in respuesta.data


# Texto de unos 5 KB, en español y con acentos. Tiene que ser largo: el .bigo lleva
# un encabezado de 55 bytes + 9 por símbolo, y en textos cortos pesa más que el
# original (ver test_texto_muy_corto_el_bigo_pesa_mas_que_el_original).
TEXTO_LARGO = (
    "El algoritmo de Huffman asigna códigos más cortos a los símbolos más frecuentes.\n"
    "En cada paso, la estrategia voraz une los dos nodos de menor peso del árbol.\n"
    "¿Funcionará con acentos, eñes y signos de interrogación? ¡Claro que sí!\n"
) * 22


def test_flujo_api_comprimir_inspeccionar_descomprimir():
    cliente = app.test_client()
    texto_original = TEXTO_LARGO

    # 1. Comprimir via API subiendo un archivo .txt simulado
    datos_form = {
        "archivo": (io.BytesIO(texto_original.encode("utf-8")), "prueba.txt")
    }
    resp_comp = cliente.post(
        "/api/comprimir", data=datos_form, content_type="multipart/form-data"
    )
    assert resp_comp.status_code == 200
    json_comp = resp_comp.get_json()
    assert json_comp["nombre_salida"] == "prueba.bigo"
    assert json_comp["metricas"]["reduccion_porcentaje"] > 0
    assert json_comp["arbol"] is not None

    bytes_bigo = base64.b64decode(json_comp["archivo_bigo_b64"])

    # 2. Inspeccionar unicamente el archivo .bigo
    resp_insp = cliente.post(
        "/api/inspeccionar",
        data={"archivo": (io.BytesIO(bytes_bigo), "prueba.bigo")},
        content_type="multipart/form-data",
    )
    assert resp_insp.status_code == 200
    json_insp = resp_insp.get_json()
    assert json_insp["version"] == "BIGO v1"
    assert json_insp["metricas"]["tamano_original_bytes"] == len(texto_original.encode("utf-8"))
    assert "vista_binaria" in json_insp

    # 3. Descomprimir y verificar integridad
    resp_desc = cliente.post(
        "/api/descomprimir",
        data={"archivo": (io.BytesIO(bytes_bigo), "prueba.bigo")},
        content_type="multipart/form-data",
    )
    assert resp_desc.status_code == 200
    json_desc = resp_desc.get_json()
    assert json_desc["integro"] is True
    # El texto llega solo en base64 (archivo_txt_b64): "texto_recuperado" se quitó de
    # la respuesta para no duplicarlo y no pasar el límite de 4.5 MB de Vercel.
    recuperado = base64.b64decode(json_desc["archivo_txt_b64"]).decode("utf-8")
    assert recuperado == texto_original


def test_texto_muy_corto_el_bigo_pesa_mas_que_el_original():
    """Documenta una limitación del formato, no un error.

    Con 110 bytes de texto, el encabezado del .bigo (55 bytes + 9 por símbolo)
    pesa más de lo que ahorra Huffman: la "reducción" sale negativa. Aun así el
    texto se recupera idéntico.
    """
    cliente = app.test_client()
    texto_corto = ("Prueba de API Huffman\n" * 5).encode("utf-8")  # 110 bytes

    json_comp = cliente.post(
        "/api/comprimir",
        data={"archivo": (io.BytesIO(texto_corto), "corto.txt")},
        content_type="multipart/form-data",
    ).get_json()
    metricas = json_comp["metricas"]
    assert metricas["tamano_comprimido_bytes"] > metricas["tamano_original_bytes"]
    assert metricas["reduccion_porcentaje"] < 0

    bytes_bigo = base64.b64decode(json_comp["archivo_bigo_b64"])
    json_desc = cliente.post(
        "/api/descomprimir",
        data={"archivo": (io.BytesIO(bytes_bigo), "corto.bigo")},
        content_type="multipart/form-data",
    ).get_json()
    assert json_desc["integro"] is True
    assert base64.b64decode(json_desc["archivo_txt_b64"]) == texto_corto