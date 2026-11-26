"""Pruebas de las utilidades del empaquetado (herramientas/empaquetar.py)."""

import hashlib

from herramientas import empaquetar

LINEA_ERRONEA = '            with open(exe_path, "ab", encoding="utf-8") as exef:'
LINEA_CORRECTA = '            with open(exe_path, "ab") as exef:'


def test_corregir_texto_quita_encoding_de_la_apertura_binaria():
    original = "antes\n" + LINEA_ERRONEA + "\n    despues\n"
    esperado = "antes\n" + LINEA_CORRECTA + "\n    despues\n"
    assert empaquetar.corregir_texto(original) == esperado


def test_corregir_texto_no_cambia_un_texto_ya_correcto():
    corregido = "antes\n" + LINEA_CORRECTA + "\n"
    assert empaquetar.corregir_texto(corregido) == corregido


def test_sha256_de_coincide_con_hashlib(tmp_path):
    archivo = tmp_path / "datos.bin"
    contenido = b"telegram uploader" * 1000
    archivo.write_bytes(contenido)
    assert empaquetar.sha256_de(archivo) == hashlib.sha256(contenido).hexdigest()


def test_version_soportada_solo_acepta_la_verificada():
    assert empaquetar.version_soportada("1.1.2") is True
    assert empaquetar.version_soportada("1.1.3") is False
    assert empaquetar.version_soportada("1.0.9") is False