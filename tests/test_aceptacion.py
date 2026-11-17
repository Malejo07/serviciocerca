"""Pruebas de F4: aceptación de éxito, zona inexistente, red desconectada y peso inválido (docs/F4-consola.md)."""
from app.dominio.aceptacion import ejecutar_aceptacion, generar_reporte_markdown


def _escenario(resultado, id_escenario):
    return next(e for e in resultado["escenarios"] if e["id"] == id_escenario)


def test_los_cuatro_escenarios_se_cumplen():
    r = ejecutar_aceptacion()
    assert [e["id"] for e in r["escenarios"]] == ["exito", "zona_inexistente", "red_desconectada", "peso_invalido"]
    assert r["total"] == 4 and r["cumplidos"] == 4 and r["todos_cumplidos"] is True
    assert all(e["cumple"] and e["pasos"] for e in r["escenarios"])


def test_cada_paso_trae_accion_esperado_obtenido_y_codigo():
    for escenario in ejecutar_aceptacion()["escenarios"]:
        for paso in escenario["pasos"]:
            assert set(paso) == {"accion", "esperado", "obtenido", "codigo_http", "cumple"}
            assert paso["cumple"] is True and paso["obtenido"]


def test_exito_incluye_la_alternativa_de_menor_costo():
    pasos = _escenario(ejecutar_aceptacion(), "exito")["pasos"]
    assert [p["codigo_http"] for p in pasos] == [200, 200, 200]
    assert "15 min" in pasos[1]["obtenido"] and "20 min" in pasos[1]["obtenido"]
    assert "Marta" in pasos[2]["obtenido"]


def test_zona_inexistente_responde_404_con_mensaje_claro():
    pasos = _escenario(ejecutar_aceptacion(), "zona_inexistente")["pasos"]
    assert [p["codigo_http"] for p in pasos] == [404, 404]
    assert all("Z99" in p["obtenido"] for p in pasos)


def test_red_desconectada_no_es_un_error():
    pasos = _escenario(ejecutar_aceptacion(), "red_desconectada")["pasos"]
    assert [p["codigo_http"] for p in pasos] == [200, 200, 200]
    assert "desconectada" in pasos[0]["obtenido"] and "desconectada" in pasos[1]["obtenido"]
    assert "no tiene trayectos" in pasos[2]["obtenido"]


def test_peso_invalido_se_rechaza_y_la_red_no_cambia():
    pasos = _escenario(ejecutar_aceptacion(), "peso_invalido")["pasos"]
    assert [p["codigo_http"] for p in pasos] == [400, 400, 400]
    assert "mayor que 0" in pasos[0]["obtenido"] and "mayor que 0" in pasos[1]["obtenido"]
    assert "B1 -> Z1" in pasos[2]["obtenido"]
    assert "sin cambios" in pasos[0]["esperado"]


def test_se_puede_ejecutar_varias_veces_con_el_mismo_resultado():
    primero = ejecutar_aceptacion()
    segundo = ejecutar_aceptacion()
    assert primero == segundo


def test_reporte_markdown_resume_y_detalla_los_escenarios():
    texto = generar_reporte_markdown(ejecutar_aceptacion())
    assert texto.startswith("# Evidencia de aceptación")
    assert "4 de 4 escenarios cumplidos" in texto
    for titulo in ("Consulta normal", "Zona que no existe", "Zona sin conexión", "Tiempo inválido"):
        assert titulo in texto
    assert "| Paso | Esperado | Obtenido | HTTP | Resultado |" in texto
    assert "No existe el nodo 'Z99'." in texto


def test_el_reporte_no_rompe_las_tablas_con_barras_verticales():
    resultado = ejecutar_aceptacion()
    resultado["escenarios"][0]["pasos"][0]["obtenido"] = "a | b\nc"
    texto = generar_reporte_markdown(resultado)
    assert "a \\| b c" in texto
