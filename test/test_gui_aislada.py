"""Solo gui.py puede depender de Flet; el resto del programa debe funcionar sin él."""
import ast
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PAQUETE = RAIZ / "telegram_uploader"


def _importa_flet(ruta: Path) -> bool:
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import) and any(
                alias.name.split(".")[0] == "flet" for alias in nodo.names):
            return True
        if isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.module.split(".")[0] == "flet":
            return True
    return False


def test_solo_gui_importa_flet():
    importan = {p.name for p in PAQUETE.glob("*.py") if _importa_flet(p)}
    assert importan <= {"gui.py"}, f"Importan Flet módulos que no deberían: {importan}"


def test_el_nucleo_se_importa_sin_flet():
    codigo = (
        "import sys; sys.modules['flet'] = None\n"  # cualquier 'import flet' falla
        "import telegram_uploader.cli, telegram_uploader.servicio, telegram_uploader.gui_modelo\n"
    )
    resultado = subprocess.run([sys.executable, "-c", codigo], cwd=RAIZ,
                               capture_output=True, text=True, check=False)
    assert resultado.returncode == 0, resultado.stderr