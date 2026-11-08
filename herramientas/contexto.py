#!/usr/bin/env python3
"""
Genera un archivo de texto con el contexto del proyecto para pegarlo a un asistente de IA.

Incluye: la guía ARQUITECTURA.md, un mapa generado automáticamente a partir del código
(módulos, quién depende de quién, funciones, opciones de línea de comandos, claves de
configuración) y el código fuente completo o solo el de los módulos que indiques.

Uso:
    python herramientas/contexto.py                      # guía + mapa + TODO el código
    python herramientas/contexto.py --mapa               # guía + mapa (sin código, muy corto)
    python herramientas/contexto.py --modulos subida     # guía + mapa + subida y sus dependencias
    python herramientas/contexto.py --modulos cli --con-pruebas
    python herramientas/contexto.py -o otro.txt          # cambia el archivo de salida

Solo usa la biblioteca estándar de Python.
"""
import argparse
import ast
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PAQUETE = RAIZ / "telegram_uploader"
NOMBRE_PAQUETE = PAQUETE.name


# ---------------------------------------------------------------------------
# Análisis del código (sin ejecutarlo)
# ---------------------------------------------------------------------------

def listar_modulos() -> list:
    return sorted(p.stem for p in PAQUETE.glob("*.py") if p.stem != "__init__")


def analizar(modulo: str) -> ast.Module:
    return ast.parse((PAQUETE / f"{modulo}.py").read_text(encoding="utf-8"))


def dependencias_internas(modulo: str) -> list:
    """Módulos del paquete que importa `modulo` (por `from .x import ...`)."""
    deps = set()
    for nodo in ast.walk(analizar(modulo)):
        if isinstance(nodo, ast.ImportFrom) and nodo.level == 1 and nodo.module:
            deps.add(nodo.module.split(".")[0])
    return sorted(deps)


def con_dependencias(modulos: list) -> list:
    """Cierre transitivo: los módulos pedidos más todo lo que necesitan."""
    pendientes, vistos = list(modulos), set()
    while pendientes:
        actual = pendientes.pop()
        if actual in vistos:
            continue
        vistos.add(actual)
        pendientes.extend(dependencias_internas(actual))
    return sorted(vistos)


def firma(nodo) -> str:
    args = ast.unparse(nodo.args)
    retorno = f" -> {ast.unparse(nodo.returns)}" if nodo.returns else ""
    prefijo = "async def" if isinstance(nodo, ast.AsyncFunctionDef) else "def"
    return f"{prefijo} {nodo.name}({args}){retorno}"


def primera_linea(nodo) -> str:
    doc = ast.get_docstring(nodo)
    return doc.strip().splitlines()[0] if doc else ""


def resumen_modulo(modulo: str) -> list:
    arbol = analizar(modulo)
    lineas = []
    for nodo in arbol.body:
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)) and not nodo.name.startswith("_"):
            nota = primera_linea(nodo)
            lineas.append(f"    {firma(nodo)}" + (f"   # {nota}" if nota else ""))
        elif isinstance(nodo, ast.ClassDef):
            nota = primera_linea(nodo)
            lineas.append(f"    class {nodo.name}" + (f"   # {nota}" if nota else ""))
    return lineas


def valor_literal(modulo: str, nombre: str):
    for nodo in analizar(modulo).body:
        if isinstance(nodo, ast.Assign) and isinstance(nodo.targets[0], ast.Name) and nodo.targets[0].id == nombre:
            return ast.literal_eval(nodo.value)
    return None


def opciones_cli() -> list:
    """Opciones de línea de comandos con su texto de ayuda en español."""
    textos = (valor_literal("i18n", "STRINGS") or {}).get("es", {})
    opciones = []
    for nodo in ast.walk(analizar("cli")):
        es_add = (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute)
                  and nodo.func.attr == "add_argument")
        if not es_add or not nodo.args or not isinstance(nodo.args[0], ast.Constant):
            continue
        ayuda = ""
        for kw in nodo.keywords:
            if kw.arg == "help" and isinstance(kw.value, ast.Call) and kw.value.args:
                clave = ast.literal_eval(kw.value.args[0])
                ayuda = textos.get(clave, clave)
        opciones.append((nodo.args[0].value, ayuda))
    return opciones


def mapa() -> str:
    modulos = listar_modulos()
    usados_por = {m: [] for m in modulos}
    for m in modulos:
        for d in dependencias_internas(m):
            if d in usados_por:
                usados_por[d].append(m)

    out = ["=" * 78, "MAPA DEL PROYECTO (generado automáticamente a partir del código)", "=" * 78, ""]
    for m in modulos:
        arbol = analizar(m)
        total = len((PAQUETE / f"{m}.py").read_text(encoding="utf-8").splitlines())
        out.append(f"{NOMBRE_PAQUETE}/{m}.py  ({total} líneas) - {primera_linea(arbol)}")
        out.append(f"    depende de: {', '.join(dependencias_internas(m)) or '(nada)'}")
        out.append(f"    lo usan:    {', '.join(usados_por[m]) or '(nadie; es un punto de entrada)'}")
        out.extend(resumen_modulo(m))
        out.append("")

    out += ["Opciones de línea de comandos:"]
    out += [f"    {flag:<20} {ayuda}" for flag, ayuda in opciones_cli()]
    out += ["", "Claves de configuración (config.json) y valor por defecto:"]
    for clave, valor in (valor_literal("constantes", "CONFIG_DEFAULTS") or {}).items():
        out.append(f"    {clave:<18} {valor!r}")
    claves_es = (valor_literal("i18n", "STRINGS") or {}).get("es", {})
    claves_en = (valor_literal("i18n", "STRINGS") or {}).get("en", {})
    out += ["", f"Textos de interfaz (i18n): {len(claves_es)} en español, {len(claves_en)} en inglés."]
    faltan = sorted(set(claves_es) ^ set(claves_en))
    if faltan:
        out.append(f"    ATENCIÓN: claves presentes en un solo idioma: {', '.join(faltan)}")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# Armado del archivo de contexto
# ---------------------------------------------------------------------------

def bloque(titulo: str, ruta: Path) -> str:
    texto = ruta.read_text(encoding="utf-8").rstrip("\n")
    return f"\n{'#' * 78}\n# ARCHIVO: {titulo}\n{'#' * 78}\n{texto}\n"


def construir(modulos_pedidos, solo_mapa: bool, con_pruebas: bool) -> str:
    partes = []
    guia = RAIZ / "ARQUITECTURA.md"
    if guia.exists():
        partes.append(bloque("ARQUITECTURA.md", guia))
    partes.append("\n" + mapa())

    if not solo_mapa:
        elegidos = con_dependencias(modulos_pedidos) if modulos_pedidos else listar_modulos()
        partes.append(f"\n>>> Código incluido: {', '.join(elegidos)}\n")
        partes.append(bloque("subir_a_telegram.py", RAIZ / "subir_a_telegram.py"))
        for m in elegidos:
            partes.append(bloque(f"{NOMBRE_PAQUETE}/{m}.py", PAQUETE / f"{m}.py"))
        if con_pruebas:
            for prueba in sorted((RAIZ / "tests").glob("*.py")):
                partes.append(bloque(f"tests/{prueba.name}", prueba))
    return "".join(partes)


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera el contexto del proyecto para pegar a una IA.")
    parser.add_argument("--mapa", action="store_true", help="Solo guía y mapa, sin código fuente.")
    parser.add_argument("--modulos", nargs="+", metavar="MODULO",
                        help="Incluye solo estos módulos y los que ellos necesitan.")
    parser.add_argument("--con-pruebas", action="store_true", help="Agrega también los archivos de tests/.")
    parser.add_argument("-o", "--salida", default="contexto.txt", help="Archivo de salida (por defecto contexto.txt).")
    args = parser.parse_args()

    desconocidos = [m for m in (args.modulos or []) if m not in listar_modulos()]
    if desconocidos:
        print(f"Módulos desconocidos: {', '.join(desconocidos)}. Disponibles: {', '.join(listar_modulos())}")
        return 1

    texto = construir(args.modulos, args.mapa, args.con_pruebas)
    destino = Path(args.salida)
    destino.write_text(texto, encoding="utf-8")
    print(f"Contexto guardado en {destino} ({len(texto.splitlines())} líneas, "
          f"~{len(texto) // 4} tokens estimados). Ábrelo, copia todo y pégalo a la IA.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
