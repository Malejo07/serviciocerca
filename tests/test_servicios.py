"""Asignación equitativa de servicios, disponibilidad de técnicos y seguimiento de cumplimiento."""
import pytest

from app.dominio.asignacion import asignar_servicio, marcar_servicio, resumen_servicios
from app.dominio.carga import red_de_ejemplo
from app.dominio.errores import DatoInvalido, ElementoNoEncontrado, SinTecnicoDisponible
from app.main import crear_app
from tests.utilidades import cliente_como


@pytest.fixture
def red():
    return red_de_ejemplo()


def tecnico_de(r):
    return r["servicio"]["tecnico_id"]


# ---------- Disponibilidad sin borrar al técnico ----------

def test_cambiar_disponibilidad_conserva_al_tecnico(red):
    t = red.cambiar_disponibilidad("T2", True)
    assert t.disponible is True and red.tecnicos["T2"].nombre == "Luis"
    assert red.cambiar_disponibilidad("t3", False).disponible is False
    assert len(red.tecnicos) == 4


def test_cambiar_disponibilidad_errores(red):
    with pytest.raises(ElementoNoEncontrado):
        red.cambiar_disponibilidad("T99", True)
    with pytest.raises(DatoInvalido):
        red.cambiar_disponibilidad("T1", "si")


def test_un_tecnico_no_disponible_no_recibe_servicios(red):
    assert red.tecnicos["T2"].disponible is False  # Luis, en B1
    for _ in range(3):
        assert tecnico_de(asignar_servicio(red, "Z3")) == "T1"   # solo Ana


# ---------- Equidad ----------

def test_reparte_por_turnos_entre_tecnicos_de_la_misma_base(red):
    red.cambiar_disponibilidad("T2", True)   # Luis vuelve a estar disponible
    elegidos = [tecnico_de(asignar_servicio(red, "Z3")) for _ in range(4)]
    assert elegidos == ["T1", "T2", "T1", "T2"]


def test_prefiere_al_que_lleva_menos_servicios_aunque_llegue_mas_tarde(red):
    red.cambiar_disponibilidad("T4", True)   # Carlos y Marta en B2
    # Z5: B2 a 18 min. Marta y Carlos empatan en tiempo; se alternan.
    assert [tecnico_de(asignar_servicio(red, "Z5")) for _ in range(3)] == ["T3", "T4", "T3"]


def test_la_tolerancia_deja_competir_a_otra_base(red):
    red.cambiar_disponibilidad("T2", False)
    # Z1: B1 a 14 min (Ana). No hay otra base que llegue; solo Ana.
    # Z3 con tolerancia amplia no cambia nada porque B2 no llega.
    r = asignar_servicio(red, "Z3", tolerancia=100)
    assert tecnico_de(r) == "T1"
    # Z5: B2 a 18 min, B1 a 62. Con 10 min de tolerancia Ana queda fuera; con 50 compite.
    r = asignar_servicio(red, "Z5", tolerancia=10)
    assert tecnico_de(r) == "T3"
    estados = {c["tecnico_id"]: c["estado"] for c in r["candidatos"]}
    assert estados["T1"].startswith("Fuera de tolerancia (+44 min)") and estados["T3"] == "Asignado"
    # Ana ya lleva 1 servicio (Z3) y Marta 1 (Z5): con tolerancia 50 empatan en carga y gana la más rápida.
    assert tecnico_de(asignar_servicio(red, "Z5", tolerancia=50)) == "T3"
    # Marta lleva 2 y Ana 1: ahora la equidad manda y Ana atiende aunque tarde 44 min más.
    r = asignar_servicio(red, "Z5", tolerancia=50)
    assert tecnico_de(r) == "T1" and r["servicio"]["minutos"] == 62
    assert "se prefirió repartir la carga" in r["mensaje"]


def test_con_tolerancia_cero_gana_siempre_el_mas_rapido(red):
    for _ in range(3):
        assert tecnico_de(asignar_servicio(red, "Z5", tolerancia=0)) == "T3"


def test_la_asignacion_guarda_la_ruta_planificada(red):
    r = asignar_servicio(red, "Z3")
    s = r["servicio"]
    assert (s["id"], s["zona"], s["base"], s["camino"], s["minutos"], s["tramos"], s["estado"]) == \
           ("S1", "Z3", "B1", ["B1", "Z2", "Z3"], 15, 2, "ASIGNADO")
    assert "Ana atenderá Z3 (Aranjuez) desde B1, 15 min por B1 -> Z2 -> Z3" in r["mensaje"]


def test_los_ids_de_servicio_son_consecutivos(red):
    assert [asignar_servicio(red, "Z3")["servicio"]["id"] for _ in range(3)] == ["S1", "S2", "S3"]


# ---------- Casos sin técnico ----------

def test_zona_sin_conexion_no_se_asigna(red):
    with pytest.raises(SinTecnicoDisponible, match="no tiene trayectos"):
        asignar_servicio(red, "Z7")
    assert red.servicios == {}


def test_sin_tecnicos_disponibles_no_se_asigna(red):
    red.cambiar_disponibilidad("T1", False)
    with pytest.raises(SinTecnicoDisponible, match="sin técnicos disponibles"):
        asignar_servicio(red, "Z3")


def test_zona_inexistente_y_base_como_zona(red):
    with pytest.raises(ElementoNoEncontrado):
        asignar_servicio(red, "Z99")
    with pytest.raises(DatoInvalido, match="es una base"):
        asignar_servicio(red, "B1")


@pytest.mark.parametrize("malo", [-1, float("nan"), float("inf"), "10", True, None])
def test_tolerancia_invalida(red, malo):
    with pytest.raises(DatoInvalido, match="tolerancia"):
        asignar_servicio(red, "Z3", tolerancia=malo)


# ---------- Cumplimiento y resumen ----------

def test_marcar_servicios_y_resumen_por_tecnico(red):
    red.cambiar_disponibilidad("T2", True)
    ids = [asignar_servicio(red, "Z3")["servicio"]["id"] for _ in range(3)]   # Ana, Luis, Ana
    marcar_servicio(red, ids[0], "cumplido")
    marcar_servicio(red, ids[1], "NO_CUMPLIDO")
    r = resumen_servicios(red)
    por_id = {t["id"]: t for t in r["tecnicos"]}
    assert (por_id["T1"]["asignados"], por_id["T1"]["cumplidos"], por_id["T1"]["en_ruta"], por_id["T1"]["cumplimiento"]) == (2, 1, 1, 100)
    assert (por_id["T2"]["asignados"], por_id["T2"]["no_cumplidos"], por_id["T2"]["cumplimiento"]) == (1, 1, 0)
    assert por_id["T3"]["asignados"] == 0 and por_id["T3"]["cumplimiento"] is None
    assert r["total"] == {"asignados": 3, "cumplidos": 1, "no_cumplidos": 1, "por_revisar": 0, "en_ruta": 1, "con_novedad": 0}
    assert [s["id"] for s in r["servicios"]] == ["S1", "S2", "S3"]


def test_el_resumen_incluye_a_todos_los_tecnicos(red):
    assert [t["id"] for t in resumen_servicios(red)["tecnicos"]] == ["T1", "T2", "T3", "T4"]


def test_corregir_un_estado(red):
    asignar_servicio(red, "Z3")
    marcar_servicio(red, "S1", "NO_CUMPLIDO")
    assert marcar_servicio(red, "s1", "CUMPLIDO")["estado"] == "CUMPLIDO"


def test_marcar_servicio_errores(red):
    with pytest.raises(ElementoNoEncontrado):
        marcar_servicio(red, "S9", "CUMPLIDO")
    asignar_servicio(red, "Z3")
    with pytest.raises(DatoInvalido, match="Estado inválido"):
        marcar_servicio(red, "S1", "HECHO")


def test_cargar_otra_red_reinicia_los_servicios():
    app = crear_app()
    c = cliente_como("admin", app)
    c.post("/api/red/ejemplo")
    c.post("/api/servicios", json={"zona": "Z3"})
    assert c.get("/api/servicios").json()["total"]["asignados"] == 1
    c.post("/api/red/ejemplo")
    assert c.get("/api/servicios").json()["total"]["asignados"] == 0


# ---------- API ----------

@pytest.fixture
def api():
    c = cliente_como("admin")
    c.post("/api/red/ejemplo")
    return c


def test_api_activar_tecnico_sin_borrarlo(api):
    r = api.patch("/api/tecnicos/T2", json={"disponible": True})
    assert r.status_code == 200 and r.json() == {"id": "T2", "nombre": "Luis", "base_id": "B1", "disponible": True}
    assert len(api.get("/api/red").json()["tecnicos"]) == 4


def test_api_disponibilidad_errores(api):
    assert api.patch("/api/tecnicos/T99", json={"disponible": True}).status_code == 404
    for cuerpo in ({}, {"disponible": "si"}, {"disponible": 1}):
        r = api.patch("/api/tecnicos/T2", json=cuerpo)
        assert r.status_code == 400 and r.json()["error"] == "Datos con formato incorrecto."


def test_api_asignar_y_consultar_resumen(api):
    r = api.post("/api/servicios", json={"zona": "Z3"})
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["servicio"]["tecnico_nombre"] == "Ana" and cuerpo["tolerancia"] == 10
    assert cuerpo["candidatos"][0]["estado"] == "Asignado"
    resumen = api.get("/api/servicios").json()
    assert resumen["total"]["asignados"] == 1 and resumen["servicios"][0]["id"] == "S1"


def test_api_errores_de_asignacion(api):
    assert api.post("/api/servicios", json={"zona": "Z7"}).status_code == 409
    assert api.post("/api/servicios", json={"zona": "Z99"}).status_code == 404
    assert api.post("/api/servicios", json={"zona": "B1"}).status_code == 400
    assert api.post("/api/servicios", json={"zona": "Z3", "tolerancia": -3}).status_code == 400
    assert api.post("/api/servicios", json={}).status_code == 400
    assert api.get("/api/servicios").json()["total"]["asignados"] == 0   # nada quedó a medias


def test_api_marcar_y_reiniciar(api):
    api.post("/api/servicios", json={"zona": "Z3"})
    r = api.patch("/api/servicios/S1", json={"estado": "CUMPLIDO"})
    assert r.status_code == 200 and r.json()["estado"] == "CUMPLIDO"
    assert api.patch("/api/servicios/S1", json={"estado": "X"}).status_code == 400
    assert api.patch("/api/servicios/S7", json={"estado": "CUMPLIDO"}).status_code == 404
    assert api.delete("/api/servicios").json() == {"mensaje": "Servicios reiniciados."}
    assert api.get("/api/servicios").json()["total"]["asignados"] == 0
