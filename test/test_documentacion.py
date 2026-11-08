"""La documentación y la herramienta de contexto no deben quedar desactualizadas respecto al código."""
import re
import subprocess
import sys
from pathlib import Path

from telegram_uploader import constantes
from telegram_uploader.i18n import STRINGS

RAIZ = Path(__file__).resolve().parent.parent


def test_la_version_coincide_con_el_changelog():
    texto = (RAIZ / "CHANGELOG.md").read_text(encoding="utf-8")
    primera = re.search(r"^## \[(\d+\.\d+\.\d+)\]", texto, re.MULTILINE).group(1)
    assert primera == constantes.VERSION


def test_arquitectura_menciona_todos_los_modulos():
    texto = (RAIZ / "ARQUITECTURA.md").read_text(encoding="utf-8")
    modulos = [p.stem for p in (RAIZ / "telegram_uploader").glob("*.py")
               if p.stem not in ("__init__", "__main__")]
    faltan = [m for m in modulos if f"{m}.py" not in texto]
    assert not faltan, f"ARQUITECTURA.md no menciona: {faltan}"


def test_i18n_tiene_las_mismas_claves_en_ambos_idiomas():
    assert set(STRINGS["es"]) == set(STRINGS["en"])


def test_contexto_se_genera_e_incluye_los_modulos(tmp_path):
    salida = tmp_path / "contexto.txt"
    resultado = subprocess.run(
        [sys.executable, str(RAIZ / "herramientas" / "contexto.py"), "--mapa", "-o", str(salida)],
        capture_output=True, text=True, check=False,
    )
    assert resultado.returncode == 0, resultado.stderr
    texto = salida.read_text(encoding="utf-8")
    assert "telegram_uploader/subida.py" in texto
    assert "ARQUITECTURA.md" in texto


def test_contexto_con_modulos_incluye_sus_dependencias(tmp_path):
    salida = tmp_path / "contexto.txt"
    subprocess.run(
        [sys.executable, str(RAIZ / "herramientas" / "contexto.py"), "--modulos", "registro", "-o", str(salida)],
        capture_output=True, text=True, check=True,
    )
    texto = salida.read_text(encoding="utf-8")
    assert "# ARCHIVO: telegram_uploader/constantes.py" in texto  # dependencia de registro
    assert "# ARCHIVO: telegram_uploader/subida.py" not in texto  # no relacionado
