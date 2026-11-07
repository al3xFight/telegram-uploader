"""Pruebas que fijan el comportamiento ACTUAL de funciones puras y de persistencia."""
import json

import subir_a_telegram as app


# ---------- enmascarar ----------
def test_enmascarar_oculta_todo_menos_los_ultimos_4():
    assert app.enmascarar("abcdef123456") == "********3456"


def test_enmascarar_valor_corto_se_oculta_completo():
    assert app.enmascarar("abc") == "***"


def test_enmascarar_vacio_indica_sin_configurar():
    assert app.enmascarar("") == app.t("not_configured")


# ---------- resolver_canal ----------
def test_resolver_canal_id_numerico_negativo():
    assert app.resolver_canal("-1001234567890") == -1001234567890


def test_resolver_canal_usuario_se_conserva():
    assert app.resolver_canal(" @mi_canal ") == "@mi_canal"


# ---------- config ----------
def test_config_incompleta():
    assert app.config_incompleta({"api_id": "", "api_hash": "", "canal": ""})
    assert not app.config_incompleta({"api_id": 1, "api_hash": "x", "canal": "@c"})


def test_guardar_y_cargar_config(tmp_path, monkeypatch):
    monkeypatch.setattr(app, "CONFIG_PATH", tmp_path / "config.json")
    for var in ("TG_API_ID", "TG_API_HASH", "TG_CANAL"):
        monkeypatch.delenv(var, raising=False)
    config = dict(app.CONFIG_DEFAULTS, api_id=123, api_hash="hash", canal="@c")
    app.guardar_config(config)
    assert app.cargar_config()["api_id"] == 123
    assert not (tmp_path / "config.json.tmp").exists()  # escritura atómica


def test_variables_de_entorno_tienen_prioridad(tmp_path, monkeypatch):
    monkeypatch.setattr(app, "CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.setenv("TG_CANAL", "@desde_entorno")
    assert app.cargar_config()["canal"] == "@desde_entorno"


# ---------- registro de subidos ----------
def test_registro_ida_y_vuelta(tmp_path, monkeypatch):
    monkeypatch.setattr(app, "REGISTRO_SUBIDOS", str(tmp_path / "subidos.json"))
    app.guardar_registro({"k": {"nombre": "a.mp4"}})
    assert app.cargar_registro() == {"k": {"nombre": "a.mp4"}}


def test_registro_corrupto_devuelve_vacio(tmp_path, monkeypatch):
    ruta = tmp_path / "subidos.json"
    ruta.write_text("{esto no es json", encoding="utf-8")
    monkeypatch.setattr(app, "REGISTRO_SUBIDOS", str(ruta))
    assert app.cargar_registro() == {}


# ---------- clave de archivo ----------
def test_clave_archivo_es_estable_y_depende_del_contenido_basico(tmp_path):
    a = tmp_path / "a.txt"
    a.write_text("hola")
    clave1 = app.clave_archivo(a)
    assert clave1 == app.clave_archivo(a)
    a.write_text("hola mundo")  # cambia el tamaño
    assert app.clave_archivo(a) != clave1


# ---------- búsqueda de archivos ----------
def test_encontrar_archivos_solo_videos(tmp_path):
    (tmp_path / "v.mp4").write_bytes(b"x")
    (tmp_path / "nota.txt").write_text("x")
    nombres = {p.name for p in app.encontrar_archivos(tmp_path, solo_videos=True)}
    assert nombres == {"v.mp4"}


def test_encontrar_archivos_todo(tmp_path):
    (tmp_path / "v.mp4").write_bytes(b"x")
    (tmp_path / "nota.txt").write_text("x")
    nombres = {p.name for p in app.encontrar_archivos(tmp_path, solo_videos=False)}
    assert nombres == {"v.mp4", "nota.txt"}


# ---------- orden cronológico ----------
def test_orden_usa_fecha_del_nombre_si_no_hay_metadata(tmp_path):
    f = tmp_path / "video_2024-01-02_03-04-05.txt"
    f.write_text("x")
    esperado = app.datetime(2024, 1, 2, 3, 4, 5).timestamp()
    assert app.obtener_timestamp_orden(f) == esperado