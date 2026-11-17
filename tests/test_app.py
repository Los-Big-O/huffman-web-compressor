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


def test_flujo_api_comprimir_inspeccionar_descomprimir():
    cliente = app.test_client()
    texto_original = "Prueba de API Huffman\n" * 5

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
    assert json_desc["texto_recuperado"] == texto_original