"""El idioma elegido con --lang debe reflejarse en los mensajes del programa."""
import asyncio
import logging

import subir_a_telegram as app


def _ejecutar_en_carpeta_vacia(tmp_path, monkeypatch, idioma):
    carpeta = tmp_path / "vacia"
    carpeta.mkdir()
    monkeypatch.setattr(app, "CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.setattr(app, "REGISTRO_SUBIDOS", str(tmp_path / "subidos.json"))
    monkeypatch.setenv("TG_API_ID", "123")
    monkeypatch.setenv("TG_API_HASH", "hash-de-prueba")
    monkeypatch.setenv("TG_CANAL", "@canal")
    monkeypatch.setattr(
        "sys.argv",
        ["subir_a_telegram.py", "--lang", idioma, "--carpeta", str(carpeta), "--todo"],
    )
    asyncio.run(app.main())


def test_lang_es_muestra_mensajes_en_espanol(tmp_path, monkeypatch, caplog):
    caplog.set_level(logging.INFO)
    _ejecutar_en_carpeta_vacia(tmp_path, monkeypatch, "es")
    assert "No hay nada nuevo para subir" in caplog.text


def test_lang_en_muestra_mensajes_en_ingles(tmp_path, monkeypatch, caplog):
    caplog.set_level(logging.INFO)
    _ejecutar_en_carpeta_vacia(tmp_path, monkeypatch, "en")
    assert "Nothing new to upload" in caplog.text