"""Interfaz de línea de comandos: argumentos y flujo principal del programa."""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

from rich.panel import Panel

from .config import (
    asegurar_configuracion,
    cargar_config,
    config_existe,
    ejecutar_modo_config,
)
from .consola import console, log
from .constantes import VERSION
from .i18n import elegir_idioma_interactivo, t, traductor
from .medios import FFMPEG_DISPONIBLE, encontrar_archivos, obtener_timestamp_orden
from .registro import cargar_registro, clave_archivo
from .subida import (
    OpcionesSubida,
    crear_cliente,
    ejecutar_subidas,
    resolver_destino,
)


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=t("arg_desc"), epilog=t("arg_epilog"))
    parser.add_argument("--config", action="store_true", help=t("arg_config_help"))
    parser.add_argument("--carpeta", default=None, help=t("arg_carpeta_help"))
    parser.add_argument("--todo", action="store_true", help=t("arg_todo_help"))
    parser.add_argument("--borrar-local", action="store_true", help=t("arg_borrar_local_help"))
    parser.add_argument("--paralelo", type=int, default=1, help=t("arg_paralelo_help"))
    parser.add_argument("--chunks-paralelos", type=int, default=None, help=t("arg_chunks_help"))
    parser.add_argument("--pausa-min", type=float, default=None, help=t("arg_pausa_min_help"))
    parser.add_argument("--pausa-max", type=float, default=None, help=t("arg_pausa_max_help"))
    parser.add_argument("--dry-run", action="store_true", help=t("arg_dry_run_help"))
    parser.add_argument("--debug", action="store_true", help=t("arg_debug_help"))
    parser.add_argument("--lang", choices=["es", "en"], default=None, help=t("arg_lang_help"))
    parser.add_argument("--version", action="version", version=f"Telegram Uploader {VERSION}")
    return parser


def configurar_idioma(config: dict, argv: list) -> None:
    """Fija el idioma activo. Prioridad: --lang (temporal) > config guardada > preguntar."""
    lang_cli = None
    if "--lang" in argv:
        idx = argv.index("--lang")
        if idx + 1 < len(argv):
            lang_cli = argv[idx + 1]

    if lang_cli in ("es", "en"):
        traductor.idioma = lang_cli
    elif config.get("idioma") in ("es", "en"):
        traductor.idioma = config["idioma"]
    elif "-h" in argv or "--help" in argv:
        traductor.idioma = "es"  # --help no debe quedar esperando input
    else:
        traductor.idioma = elegir_idioma_interactivo()
        if not config_existe():
            config["idioma"] = traductor.idioma  # se confirma al guardar el resto en el wizard


def mostrar_banner() -> None:
    console.print(Panel.fit(
        f"[bold]📡 Telegram Uploader[/bold] [dim]v{VERSION}[/dim]\n{t('banner_subtitle')}",
        border_style="blue",
    ))


def resolver_ajustes(args, config: dict):
    """Combina configuración guardada y argumentos; valida y termina si algo es inválido.

    Devuelve (api_id, api_hash, canal, opciones).
    """
    try:
        api_id = int(config["api_id"])
    except (TypeError, ValueError):
        console.print(f"[red]{t('err_api_id_invalid_saved')}[/red]")
        sys.exit(1)

    chunks_paralelos = args.chunks_paralelos if args.chunks_paralelos is not None else int(config["chunks_paralelos"])
    pausa_min = args.pausa_min if args.pausa_min is not None else float(config["pausa_min"])
    pausa_max = args.pausa_max if args.pausa_max is not None else float(config["pausa_max"])

    if chunks_paralelos < 1:
        console.print(f"[red]{t('err_chunks_min1')}[/red]")
        sys.exit(1)
    if pausa_min < 0 or pausa_max < 0:
        console.print(f"[red]{t('err_pausas_negative')}[/red]")
        sys.exit(1)
    if pausa_max > 0 and pausa_min > pausa_max:
        pausa_min, pausa_max = pausa_max, pausa_min

    opciones = OpcionesSubida(
        borrar_local=args.borrar_local, dry_run=args.dry_run,
        pausa_min=pausa_min, pausa_max=pausa_max, chunks_paralelos=chunks_paralelos,
        archivos_simultaneos=args.paralelo,
    )
    return api_id, str(config["api_hash"]), config["canal"], opciones


def mostrar_avisos(args) -> None:
    """Avisos no bloqueantes sobre el entorno y las opciones elegidas."""
    if args.paralelo > 1:
        log.warning(t("warn_paralelo_order", n=args.paralelo))

    try:
        import cryptg  # noqa: F401
    except ImportError:
        log.warning(t("tip_cryptg"))

    if not FFMPEG_DISPONIBLE:
        log.warning(t("warn_ffmpeg_missing"))


def obtener_carpeta(ruta_indicada) -> Path:
    """Pide la carpeta por consola si no se indicó, y comprueba que exista."""
    ruta_carpeta = ruta_indicada
    while not ruta_carpeta:
        ruta_carpeta = input(f"{t('prompt_carpeta')}: ").strip().strip('"').strip("'")

    carpeta = Path(ruta_carpeta).expanduser()
    if not carpeta.is_dir():
        console.print(f"[red]{t('err_carpeta_not_found', carpeta=carpeta)}[/red]")
        sys.exit(1)
    return carpeta


def buscar_pendientes(carpeta: Path, solo_videos: bool, registro: dict):
    """Devuelve (todos_los_archivos, pendientes), ambos en orden cronológico."""
    archivos = list(encontrar_archivos(carpeta, solo_videos=solo_videos))
    archivos.sort(key=obtener_timestamp_orden)
    pendientes = [a for a in archivos if clave_archivo(a) not in registro]
    return archivos, pendientes


async def main():
    config = cargar_config()
    configurar_idioma(config, sys.argv)
    mostrar_banner()

    args = construir_parser().parse_args()
    if args.debug:
        log.setLevel(logging.DEBUG)

    if args.config:
        ejecutar_modo_config(config)
        return

    config = asegurar_configuracion(config)
    api_id, api_hash, canal, opciones = resolver_ajustes(args, config)
    mostrar_avisos(args)
    carpeta = obtener_carpeta(args.carpeta)

    registro = cargar_registro()
    archivos, pendientes = buscar_pendientes(carpeta, solo_videos=not args.todo, registro=registro)
    log.info(t("log_found_files", n=len(archivos)))
    log.info(t("log_pending_files", n=len(pendientes)))
    if not pendientes:
        log.info(t("log_nothing_new"))
        return

    client = crear_cliente(api_id, api_hash)
    try:
        await client.start()
        destino = await resolver_destino(client, canal)
        subidos_ok = await ejecutar_subidas(client, destino, pendientes, registro, opciones)
        log.info(t("log_finished", ok=subidos_ok, total=len(pendientes)))
    except KeyboardInterrupt:
        log.warning(t("log_interrupted"))
    finally:
        await client.disconnect()


def ejecutar() -> None:
    """Punto de entrada: lanza el programa principal."""
    asyncio.run(main())
