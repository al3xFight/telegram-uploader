"""Empaqueta la interfaz gráfica como ejecutable de Windows con ``flet pack``.

Uso, desde la carpeta del proyecto y con requirements-build.txt instalado:

    python -m herramientas.empaquetar

Antes de empaquetar corrige un error conocido de flet-cli 1.1.2 en Windows (abre
un archivo en modo binario indicando una codificación) y, al terminar, calcula el
hash SHA-256 del ejecutable para publicarlo junto a él.
"""

import hashlib
import importlib.metadata
import shutil
import subprocess
import sys
from pathlib import Path

from telegram_uploader.constantes import DIRECTORIO_BASE, VERSION

VERSION_FLET_CLI = "1.1.2"
NOMBRE_EJECUTABLE = "TelegramUploader"
LANZADOR = DIRECTORIO_BASE / "subir_a_telegram_gui.py"
ARCHIVO_CON_ERROR = "flet_cli/__pyinstaller/win_utils.py"
LINEA_ERRONEA = 'with open(exe_path, "ab", encoding="utf-8") as exef:'
LINEA_CORRECTA = 'with open(exe_path, "ab") as exef:'
TAMANO_BLOQUE = 1024 * 1024


def corregir_texto(texto: str) -> str:
    """Quita el argumento ``encoding`` de la apertura binaria defectuosa."""
    return texto.replace(LINEA_ERRONEA, LINEA_CORRECTA)


def sha256_de(ruta: Path) -> str:
    """Calcula el hash SHA-256 de un archivo leyéndolo por bloques."""
    resumen = hashlib.sha256()
    with ruta.open("rb") as archivo:
        while bloque := archivo.read(TAMANO_BLOQUE):
            resumen.update(bloque)
    return resumen.hexdigest()


def version_soportada(version: str) -> bool:
    """Indica si la versión de flet-cli es la que se verificó a mano."""
    return version == VERSION_FLET_CLI


def ruta_flet() -> str | None:
    """Localiza el comando ``flet`` del entorno actual."""
    junto_a_python = Path(sys.executable).with_name("flet.exe")
    if junto_a_python.exists():
        return str(junto_a_python)
    return shutil.which("flet")


def parchear_flet_cli() -> bool:
    """Corrige flet-cli instalado. Devuelve True si tuvo que cambiar algo."""
    distribucion = importlib.metadata.distribution("flet-cli")
    ruta = Path(str(distribucion.locate_file(ARCHIVO_CON_ERROR)))
    texto = ruta.read_bytes().decode("utf-8")
    corregido = corregir_texto(texto)
    if corregido == texto:
        return False
    ruta.write_bytes(corregido.encode("utf-8"))
    return True


def verificar_requisitos() -> str | None:
    """Devuelve un mensaje de error si falta algo para empaquetar, o None."""
    try:
        version = importlib.metadata.version("flet-cli")
    except importlib.metadata.PackageNotFoundError:
        return "Falta flet-cli. Instala: pip install -r requirements-build.txt"
    if not version_soportada(version):
        return f"flet-cli {version} no está verificado; se esperaba {VERSION_FLET_CLI}."
    if ruta_flet() is None:
        return "No se encontró el comando flet en este entorno."
    if not LANZADOR.exists():
        return f"No existe el lanzador {LANZADOR.name}."
    return None


def construir_comando(flet: str) -> list[str]:
    """Arma el comando de ``flet pack`` con carpeta de salida (no un solo archivo)."""
    return [
        flet,
        "pack",
        str(LANZADOR),
        "-n",
        NOMBRE_EJECUTABLE,
        "-D",
        "--product-version",
        VERSION,
    ]


def empaquetar() -> int:
    """Genera el ejecutable y muestra su hash. Devuelve el código de salida."""
    error = verificar_requisitos()
    if error:
        print(error)
        return 1
    if parchear_flet_cli():
        print("Se corrigió el error de apertura binaria en flet-cli.")
    comando = construir_comando(ruta_flet() or "flet")
    resultado = subprocess.run(comando, cwd=DIRECTORIO_BASE, check=False)  # noqa: S603
    if resultado.returncode != 0:
        return resultado.returncode
    exe = DIRECTORIO_BASE / "dist" / NOMBRE_EJECUTABLE / f"{NOMBRE_EJECUTABLE}.exe"
    if not exe.exists():
        print(f"No se encontró el ejecutable esperado: {exe}")
        return 1
    print(f"SHA-256 de {exe.name}: {sha256_de(exe)}")
    return 0


if __name__ == "__main__":
    sys.exit(empaquetar())
