"""Pruebas del acceso por roles (docs/acceso-por-roles.md)."""
import pytest
from fastapi.testclient import TestClient

from app.main import crear_app
from app.seguridad import NOMBRE_COOKIE, hashear_clave, verificar_clave
from tests.utilidades import cliente_como

CLAVES = {"admin": "Admin2026!", "configurador": "Config2026!", "tecnico": "Tecnico2026!"}
MENSAJE_CREDENCIALES = "Usuario o contraseña incorrectos."


def entrar(cliente, usuario, clave):
    return cliente.post("/api/sesion", json={"usuario": usuario, "clave": clave})


# ---------- Inicio y cierre de sesión ----------

@pytest.mark.parametrize("usuario, rol, permisos", [
    ("admin", "administrador", ["administrar", "configurar", "consultar", "revisar"]),
    ("configurador", "configurador", ["configurar", "consultar", "revisar"]),
    ("tecnico", "tecnico", ["consultar", "reportar"]),
])
def test_cada_usuario_entra_con_su_rol_y_permisos(usuario, rol, permisos):
    cliente = TestClient(crear_app())
    r = entrar(cliente, usuario, CLAVES[usuario])
    assert r.status_code == 200
    datos = r.json()
    assert datos["usuario"] == usuario and datos["rol"] == rol and datos["permisos"] == permisos
    assert cliente.get("/api/sesion").json() == datos


def test_el_usuario_no_distingue_mayusculas_ni_espacios():
    assert entrar(TestClient(crear_app()), "  Admin ", CLAVES["admin"]).status_code == 200


def test_clave_incorrecta_y_usuario_inexistente_responden_igual():
    cliente = TestClient(crear_app())
    mala = entrar(cliente, "admin", "x")
    desconocido = entrar(cliente, "nadie", "x")
    assert mala.status_code == desconocido.status_code == 401
    assert mala.json() == desconocido.json() == {"error": MENSAJE_CREDENCIALES}
    assert NOMBRE_COOKIE not in mala.cookies


def test_el_inicio_de_sesion_pide_usuario_y_clave():
    r = TestClient(crear_app()).post("/api/sesion", json={"usuario": "admin"})
    assert r.status_code == 400 and "clave" in " ".join(r.json()["detalles"])


def test_la_cookie_no_la_lee_javascript_y_no_viaja_entre_sitios():
    r = entrar(TestClient(crear_app()), "admin", CLAVES["admin"])
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie


def test_cerrar_sesion_la_invalida_en_el_servidor():
    app = crear_app()
    cliente = TestClient(app)
    token = entrar(cliente, "admin", CLAVES["admin"]).cookies[NOMBRE_COOKIE]
    assert cliente.delete("/api/sesion").json() == {"mensaje": "Sesión cerrada."}
    assert cliente.get("/api/sesion").status_code == 401
    # Aunque alguien conserve la cookie anterior, ya no vale.
    cliente.cookies.set(NOMBRE_COOKIE, token)
    assert cliente.get("/api/sesion").status_code == 401


def test_una_cookie_inventada_no_da_acceso():
    cliente = TestClient(crear_app())
    cliente.cookies.set(NOMBRE_COOKIE, "inventada")
    assert cliente.get("/api/red").status_code == 401


def test_la_sesion_expira():
    ahora = [1000.0]
    app = crear_app(reloj=lambda: ahora[0], duracion_sesion=60)
    cliente = cliente_como("admin", app)
    assert cliente.get("/api/red").status_code == 200
    ahora[0] += 61
    r = cliente.get("/api/red")
    assert r.status_code == 401 and r.json() == {"error": "Debe iniciar sesión."}


def test_tras_cinco_intentos_fallidos_se_bloquea_un_rato():
    ahora = [1000.0]
    cliente = TestClient(crear_app(reloj=lambda: ahora[0]))
    for _ in range(5):
        assert entrar(cliente, "admin", "mala").status_code == 401
    r = entrar(cliente, "admin", CLAVES["admin"])
    assert r.status_code == 429 and "Demasiados intentos" in r.json()["error"]
    ahora[0] += 31
    assert entrar(cliente, "admin", CLAVES["admin"]).status_code == 200


def test_un_acierto_reinicia_el_conteo_de_fallos():
    cliente = TestClient(crear_app())
    for _ in range(4):
        entrar(cliente, "admin", "mala")
    assert entrar(cliente, "admin", CLAVES["admin"]).status_code == 200
    for _ in range(4):
        assert entrar(cliente, "admin", "mala").status_code == 401


# ---------- Permisos por rol ----------

RUTAS = {
    "ver_red": ("get", "/api/red", None),
    "cobertura": ("get", "/api/cobertura?origen=B1&zona=Z1", None),
    "alcance": ("get", "/api/cobertura/alcance/B1", None),
    "menor_costo": ("get", "/api/menor-costo?origen=B1&zona=Z1", None),
    "mejor_base": ("get", "/api/menor-costo/mejor-base?zona=Z1", None),
    "nodo": ("post", "/api/nodos", {"id": "Z90", "nombre": "Nueva", "tipo": "ZONA"}),
    "tecnico": ("post", "/api/tecnicos", {"id": "T9", "nombre": "Nuevo", "base_id": "B1", "disponible": True}),
    "trayecto": ("post", "/api/trayectos", {"origen": "B2", "destino": "Z1", "minutos": 3, "bidireccional": True}),
    "disponibilidad": ("patch", "/api/tecnicos/T3", {"disponible": True}),
    "asignar": ("post", "/api/servicios", {"zona": "Z3"}),
    "ver_servicios": ("get", "/api/servicios", None),
    "marcar_servicio": ("patch", "/api/servicios/S1", {"estado": "CUMPLIDO"}),
    "reportar_visita": ("post", "/api/servicios/S1/reporte", {"texto": "Visita realizada."}),
    "reiniciar_servicios": ("delete", "/api/servicios", None),
    "ejemplo": ("post", "/api/red/ejemplo", None),
    "vaciar": ("delete", "/api/red", None),
    "aceptacion": ("get", "/api/aceptacion", None),
    "evidencia": ("get", "/api/aceptacion/evidencia", None),
}
PERMITIDAS = {
    "tecnico": {"ver_red", "cobertura", "alcance", "menor_costo", "mejor_base", "ver_servicios", "reportar_visita"},
    "configurador": {"ver_red", "cobertura", "alcance", "menor_costo", "mejor_base", "nodo", "tecnico", "trayecto", "ejemplo",
                     "disponibilidad", "asignar", "ver_servicios", "marcar_servicio"},
    "admin": set(RUTAS) - {"reportar_visita"},   # reportar visitas es del técnico
}


def peticion(cliente, clave):
    metodo, ruta, cuerpo = RUTAS[clave]
    return getattr(cliente, metodo)(ruta, **({"json": cuerpo} if cuerpo else {}))


@pytest.mark.parametrize("clave", RUTAS)
def test_sin_sesion_ninguna_ruta_protegida_responde(clave):
    r = peticion(TestClient(crear_app()), clave)
    assert r.status_code == 401 and r.json() == {"error": "Debe iniciar sesión."}


@pytest.mark.parametrize("usuario", ["admin", "configurador", "tecnico"])
@pytest.mark.parametrize("clave", RUTAS)
def test_matriz_de_permisos(usuario, clave):
    app = crear_app()
    cliente = cliente_como(usuario, app)
    cliente_como("admin", app).post("/api/red/ejemplo")  # red cargada para que las rutas permitidas funcionen
    cliente_como("admin", app).post("/api/servicios", json={"zona": "Z3"})  # existe el servicio S1
    r = peticion(cliente, clave)
    if clave in PERMITIDAS[usuario]:
        assert r.status_code < 300, r.text
    else:
        assert r.status_code == 403
        assert r.json()["error"].startswith("El rol ") and "no tiene permiso" in r.json()["error"]


def test_el_tecnico_no_modifica_la_red_aunque_lo_intente():
    app = crear_app()
    cliente_como("admin", app).post("/api/red/ejemplo")
    antes = cliente_como("tecnico", app).get("/api/red").json()
    tecnico = cliente_como("tecnico", app)
    tecnico.post("/api/nodos", json={"id": "Z9", "nombre": "X", "tipo": "ZONA"})
    tecnico.delete("/api/red")
    assert tecnico.get("/api/red").json() == antes


def test_el_mensaje_de_permiso_nombra_el_rol_y_la_accion():
    r = cliente_como("tecnico").post("/api/nodos", json={"id": "Z9", "nombre": "X", "tipo": "ZONA"})
    assert r.json()["error"] == "El rol Técnico no tiene permiso para configurar la red."
    r = cliente_como("configurador").delete("/api/red")
    assert r.json()["error"] == "El rol Configurador de red no tiene permiso para realizar tareas de administración."


# ---------- Contraseñas y configuración ----------

def test_las_claves_se_guardan_con_hash_y_sal():
    h1, h2 = hashear_clave("Secreta#1"), hashear_clave("Secreta#1")
    assert "Secreta#1" not in h1 and h1 != h2
    assert verificar_clave("Secreta#1", h1) and not verificar_clave("otra", h1)
    assert not verificar_clave("Secreta#1", "formato-roto")


def test_se_pueden_definir_claves_propias_con_variables_de_entorno(monkeypatch):
    monkeypatch.setenv("SERVICIOCERCA_CLAVE_ADMIN", "ClaveNueva#77")
    cliente = TestClient(crear_app())
    assert entrar(cliente, "admin", CLAVES["admin"]).status_code == 401
    assert entrar(cliente, "admin", "ClaveNueva#77").status_code == 200


def test_las_cuentas_de_demostracion_se_ofrecen_solo_sin_claves_propias(monkeypatch):
    for variable in ("ADMIN", "CONFIGURADOR", "CONSULTOR"):
        monkeypatch.delenv(f"SERVICIOCERCA_CLAVE_{variable}", raising=False)
    datos = TestClient(crear_app()).get("/api/acceso/demostracion").json()
    assert datos["activa"] is True
    assert [c["usuario"] for c in datos["cuentas"]] == ["admin", "configurador", "tecnico"]
    assert all(c["clave"] == CLAVES[c["usuario"]] for c in datos["cuentas"])

    monkeypatch.setenv("SERVICIOCERCA_CLAVE_TECNICO", "Otra#123")
    assert TestClient(crear_app()).get("/api/acceso/demostracion").json() == {"activa": False, "cuentas": []}


# ---------- Páginas ----------

def test_la_consola_sin_sesion_lleva_al_inicio_de_sesion():
    r = TestClient(crear_app()).get("/consola", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/acceso"


def test_la_pagina_de_acceso_es_publica_y_no_usa_fuentes_externas():
    r = TestClient(crear_app()).get("/acceso")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]
    assert "ServicioCerca" in r.text and "fonts.googleapis.com" not in r.text
    for ancla in ("form-acceso", "a-usuario", "a-clave", "btn-entrar", "btn-ver-clave"):
        assert f'id="{ancla}"' in r.text


def test_quien_ya_inicio_sesion_no_ve_la_pagina_de_acceso():
    r = cliente_como("tecnico").get("/acceso", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/consola"


def test_la_consola_trae_el_menu_de_usuario_y_la_confirmacion():
    r = cliente_como("tecnico").get("/consola")
    assert r.status_code == 200
    for ancla in ("menu-usuario", "btn-salir", "dlg-confirmar", "aviso-consulta"):
        assert f'id="{ancla}"' in r.text


def test_la_landing_sigue_siendo_publica():
    assert TestClient(crear_app()).get("/").status_code == 200
