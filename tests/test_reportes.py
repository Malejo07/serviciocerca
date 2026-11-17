"""Perfil técnico: ve solo sus rutas, reporta la visita y las novedades; quien revisa decide si se cumplió."""
import pytest
from fastapi.testclient import TestClient

from app.dominio.asignacion import asignar_servicio, marcar_servicio, reportar_visita, resumen_servicios
from app.dominio.carga import red_de_ejemplo
from app.dominio.errores import DatoInvalido, ElementoNoEncontrado, ServicioAjeno
from app.main import crear_app
from app.seguridad import NOMBRE_COOKIE, Usuario
from tests.utilidades import cliente_como


@pytest.fixture
def red():
    r = red_de_ejemplo()
    asignar_servicio(r, "Z3")   # S1 -> Ana (T1)
    asignar_servicio(r, "Z5")   # S2 -> Marta (T3)
    return r


# ---------- Reporte de la visita ----------

def test_el_reporte_deja_el_servicio_por_revisar(red):
    s = reportar_visita(red, "S1", "  Visita   realizada.  ", fecha="2026-11-16T10:00:00+00:00")
    assert s["estado"] == "POR_REVISAR"
    assert s["reporte"] == {"texto": "Visita realizada.", "fecha": "2026-11-16T10:00:00+00:00", "novedad": None}
    assert s["revision"] is None


def test_reporte_con_novedad(red):
    s = reportar_visita(red, "S1", "Llegué tarde.", "trafico", "Vía cerrada por obras")
    assert s["reporte"]["novedad"] == {"tipo": "TRAFICO", "tipo_nombre": "Tráfico o vía cerrada", "detalle": "Vía cerrada por obras"}
    assert resumen_servicios(red)["total"]["con_novedad"] == 1


@pytest.mark.parametrize("texto", ["", "   ", None])
def test_reporte_vacio_se_rechaza(red, texto):
    with pytest.raises(DatoInvalido, match="reporte no puede estar vacío"):
        reportar_visita(red, "S1", texto)
    assert red.servicios["S1"].reporte is None and red.servicios["S1"].estado.value == "ASIGNADO"


def test_reporte_demasiado_largo(red):
    with pytest.raises(DatoInvalido, match="1000 caracteres"):
        reportar_visita(red, "S1", "x" * 1001)


def test_novedad_incompleta_o_invalida(red):
    with pytest.raises(DatoInvalido, match="Tipo de novedad inválido"):
        reportar_visita(red, "S1", "ok", None, "Falta el tipo")
    with pytest.raises(DatoInvalido, match="Tipo de novedad inválido"):
        reportar_visita(red, "S1", "ok", "LLUVIA", "Llovía")
    with pytest.raises(DatoInvalido, match="detalle de la novedad no puede estar vacío"):
        reportar_visita(red, "S1", "ok", "TRAFICO", "  ")
    assert red.servicios["S1"].reporte is None


def test_el_tecnico_solo_reporta_sus_servicios(red):
    with pytest.raises(ServicioAjeno, match="no está asignado a usted"):
        reportar_visita(red, "S2", "No es mío", tecnico_id="T1")
    assert red.servicios["S2"].reporte is None
    assert reportar_visita(red, "S1", "Es mío", tecnico_id="t1")["estado"] == "POR_REVISAR"


def test_servicio_inexistente(red):
    with pytest.raises(ElementoNoEncontrado):
        reportar_visita(red, "S9", "ok")


def test_el_tecnico_puede_corregir_su_reporte_antes_de_la_revision(red):
    reportar_visita(red, "S1", "Primer texto")
    s = reportar_visita(red, "S1", "Texto corregido", "OTRO", "Detalle")
    assert s["reporte"]["texto"] == "Texto corregido" and s["estado"] == "POR_REVISAR"


# ---------- Revisión ----------

def test_el_revisor_decide_y_deja_nota(red):
    reportar_visita(red, "S1", "Listo")
    s = marcar_servicio(red, "S1", "cumplido", "  Todo en orden ", revisor="configurador", fecha="2026-11-16T11:00:00+00:00")
    assert s["estado"] == "CUMPLIDO"
    assert s["revision"] == {"revisor": "configurador", "fecha": "2026-11-16T11:00:00+00:00", "nota": "Todo en orden"}


def test_no_cumplido_y_corregir_la_decision(red):
    reportar_visita(red, "S1", "Cliente ausente", "CLIENTE_AUSENTE", "Nadie abrió")
    assert marcar_servicio(red, "S1", "NO_CUMPLIDO", "Reprogramar")["estado"] == "NO_CUMPLIDO"
    assert marcar_servicio(red, "S1", "CUMPLIDO")["revision"]["nota"] == ""


def test_un_servicio_revisado_no_acepta_otro_reporte_hasta_reabrirlo(red):
    reportar_visita(red, "S1", "Listo")
    marcar_servicio(red, "S1", "CUMPLIDO")
    with pytest.raises(DatoInvalido, match="ya fue revisado"):
        reportar_visita(red, "S1", "Otro texto")
    s = marcar_servicio(red, "S1", "ASIGNADO")        # reabrir: conserva el reporte
    assert s["estado"] == "POR_REVISAR" and s["revision"] is None and s["reporte"]["texto"] == "Listo"
    assert reportar_visita(red, "S1", "Otro texto")["reporte"]["texto"] == "Otro texto"


def test_reabrir_sin_reporte_vuelve_a_en_ruta(red):
    marcar_servicio(red, "S1", "NO_CUMPLIDO")
    assert marcar_servicio(red, "S1", "ASIGNADO")["estado"] == "ASIGNADO"


def test_por_revisar_no_se_puede_poner_a_mano(red):
    with pytest.raises(DatoInvalido, match="Estado inválido"):
        marcar_servicio(red, "S1", "POR_REVISAR")


def test_nota_muy_larga(red):
    with pytest.raises(DatoInvalido, match="500 caracteres"):
        marcar_servicio(red, "S1", "CUMPLIDO", "n" * 501)
    assert red.servicios["S1"].estado.value == "ASIGNADO"


def test_resumen_cuenta_por_revisar_y_el_cumplimiento_solo_los_cerrados(red):
    reportar_visita(red, "S1", "Listo")
    t = resumen_servicios(red)["tecnicos"][0]
    assert (t["por_revisar"], t["en_ruta"], t["cumplimiento"]) == (1, 0, None)
    marcar_servicio(red, "S1", "CUMPLIDO")
    t = resumen_servicios(red)["tecnicos"][0]
    assert (t["por_revisar"], t["cumplidos"], t["cumplimiento"]) == (0, 1, 100)


def test_resumen_para_un_solo_tecnico(red):
    r = resumen_servicios(red, solo_tecnico="T3")
    assert [t["id"] for t in r["tecnicos"]] == ["T3"] and [s["id"] for s in r["servicios"]] == ["S2"]
    assert r["total"]["asignados"] == 1
    vacio = resumen_servicios(red, solo_tecnico="")      # usuario sin técnico ligado: no ve nada
    assert vacio["tecnicos"] == [] and vacio["servicios"] == []


# ---------- API y perfiles ----------

@pytest.fixture
def app():
    a = crear_app(reloj=lambda: 1_800_000_000)
    admin = cliente_como("admin", a)
    admin.post("/api/red/ejemplo")
    admin.post("/api/servicios", json={"zona": "Z3"})   # S1 -> Ana
    admin.post("/api/servicios", json={"zona": "Z5"})   # S2 -> Marta
    # una segunda técnica con su propio usuario, para comprobar que no ve lo ajeno
    seg = a.state.seguridad
    seg.usuarios["marta"] = Usuario("marta", "tecnico", seg.usuarios["tecnico"].clave_hash, "T3")
    return a


def test_el_tecnico_ve_solo_sus_rutas(app):
    ana = cliente_como("tecnico", app).get("/api/servicios").json()
    assert [s["id"] for s in ana["servicios"]] == ["S1"] and [t["id"] for t in ana["tecnicos"]] == ["T1"]
    marta = cliente_como("marta", app).get("/api/servicios").json()
    assert [s["id"] for s in marta["servicios"]] == ["S2"]
    revisor = cliente_como("configurador", app).get("/api/servicios").json()
    assert [s["id"] for s in revisor["servicios"]] == ["S1", "S2"]


def test_sesion_del_tecnico_incluye_su_tecnico(app):
    assert cliente_como("tecnico", app).get("/api/sesion").json()["tecnico_id"] == "T1"
    assert cliente_como("admin", app).get("/api/sesion").json()["tecnico_id"] is None


def test_api_reporte_y_revision_de_punta_a_punta(app):
    tecnico, revisor = cliente_como("tecnico", app), cliente_como("configurador", app)
    r = tecnico.post("/api/servicios/S1/reporte", json={"texto": "Visita hecha", "novedad": {"tipo": "TRAFICO", "detalle": "Obras"}})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["estado"] == "POR_REVISAR" and cuerpo["reporte"]["fecha"].startswith("2027-01-15T") and cuerpo["reporte"]["novedad"]["tipo"] == "TRAFICO"
    r = revisor.patch("/api/servicios/S1", json={"estado": "CUMPLIDO", "nota": "Aprobado"})
    assert r.status_code == 200 and r.json()["revision"]["revisor"] == "configurador" and r.json()["revision"]["nota"] == "Aprobado"
    assert tecnico.get("/api/servicios").json()["servicios"][0]["revision"]["nota"] == "Aprobado"
    assert tecnico.post("/api/servicios/S1/reporte", json={"texto": "Otro"}).status_code == 400   # ya revisado


def test_el_tecnico_no_puede_reportar_un_servicio_ajeno(app):
    r = cliente_como("tecnico", app).post("/api/servicios/S2/reporte", json={"texto": "Intento"})
    assert r.status_code == 403 and r.json() == {"error": "Ese servicio no está asignado a usted."}
    assert cliente_como("admin", app).get("/api/servicios").json()["servicios"][1]["reporte"] is None


def test_un_tecnico_no_decide_ni_asigna(app):
    t = cliente_como("tecnico", app)
    assert t.patch("/api/servicios/S1", json={"estado": "CUMPLIDO"}).status_code == 403
    assert t.post("/api/servicios", json={"zona": "Z3"}).status_code == 403
    assert t.patch("/api/tecnicos/T1", json={"disponible": False}).status_code == 403
    assert t.delete("/api/servicios").status_code == 403


def test_revisores_no_reportan(app):
    for quien in ("configurador", "admin"):
        r = cliente_como(quien, app).post("/api/servicios/S1/reporte", json={"texto": "x"})
        assert r.status_code == 403 and "reportar visitas" in r.json()["error"]


def test_usuario_tecnico_sin_tecnico_ligado_no_ve_ni_reporta(app):
    seg = app.state.seguridad
    seg.usuarios["huerfano"] = Usuario("huerfano", "tecnico", seg.usuarios["tecnico"].clave_hash, None)
    c = cliente_como("huerfano", app)
    assert c.get("/api/servicios").json()["servicios"] == []
    assert c.post("/api/servicios/S1/reporte", json={"texto": "x"}).status_code == 403


def test_api_errores_de_reporte(app):
    t = cliente_como("tecnico", app)
    assert t.post("/api/servicios/S1/reporte", json={"texto": " "}).status_code == 400
    assert t.post("/api/servicios/S1/reporte", json={}).status_code == 400
    assert t.post("/api/servicios/S1/reporte", json={"texto": "x", "novedad": {"tipo": "ZZZ", "detalle": "d"}}).status_code == 400
    assert t.post("/api/servicios/S9/reporte", json={"texto": "x"}).status_code == 404
