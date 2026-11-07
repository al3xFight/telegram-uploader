import sys
from pathlib import Path

import pytest

# Permite "import subir_a_telegram" desde la carpeta test/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def idioma_por_defecto():
    """Cada prueba empieza en español, sin arrastrar el idioma de la anterior."""
    import subir_a_telegram as app

    app.traductor.idioma = "es"
    yield