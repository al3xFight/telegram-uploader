"""Pruebas de la carpeta donde viven los datos del usuario (script o ejecutable)."""

import sys
from pathlib import Path

from telegram_uploader import constantes


def test_en_desarrollo_usa_la_carpeta_del_proyecto():
    esperado = Path(constantes.__file__).resolve().parent.parent
    assert constantes.calcular_directorio_base() == esperado


def test_empaquetado_usa_la_carpeta_del_ejecutable(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "TelegramUploader.exe"))
    assert constantes.calcular_directorio_base() == tmp_path.resolve()


def test_directorio_base_coincide_con_la_funcion():
    assert constantes.DIRECTORIO_BASE == constantes.calcular_directorio_base()