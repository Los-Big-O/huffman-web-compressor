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
