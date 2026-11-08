import sys
from pathlib import Path

# Permite "import subir_a_telegram" desde la carpeta test/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


import pytest


@pytest.fixture(autouse=True)
def idioma_por_defecto():
    """Cada prueba empieza en español, sin arrastrar el idioma de la anterior."""
    from telegram_uploader import i18n

    i18n.traductor.idioma = "es"
    yield
