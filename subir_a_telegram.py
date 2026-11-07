#!/usr/bin/env python3
"""
Telegram Uploader — sube videos u otros archivos grandes a un canal/grupo
privado de Telegram usando tu propia cuenta (no un bot), vía Telethon.

Telegram Uploader — upload videos and large files to a private Telegram
channel/group using your own account (not a bot), via Telethon.

Repo / full usage: see README.md
"""

import argparse
import asyncio
import hashlib
import json
import logging
import mimetypes
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

try:
    from telethon import TelegramClient, helpers
    from telethon.errors import FloodWaitError, RPCError
    from telethon.tl.types import DocumentAttributeVideo, InputFileBig
    from telethon.tl.functions.upload import SaveBigFilePartRequest
except ImportError:
    print("Falta instalar telethon / Missing telethon dependency:\n    pip install -r requirements.txt")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import (
        Progress,
        TextColumn,
        BarColumn,
        TaskProgressColumn,
        DownloadColumn,
        TransferSpeedColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
    )
    from rich.logging import RichHandler
except ImportError:
    print("Falta instalar rich / Missing rich dependency:\n    pip install -r requirements.txt")
    sys.exit(1)

VERSION = "1.1.0"
SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.json"
SESSION_NAME = str(SCRIPT_DIR / "sesion_telegram")

EXTENSIONES_VIDEO = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".3gp"}
REGISTRO_SUBIDOS = str(SCRIPT_DIR / "subidos.json")
MAX_REINTENTOS_ERROR = 3
UMBRAL_ARCHIVO_GRANDE = 10 * 1024 * 1024

CONFIG_DEFAULTS = {
    "idioma": "",
    "api_id": "",
    "api_hash": "",
    "canal": "",
    "chunks_paralelos": 8,
    "pausa_min": 3.0,
    "pausa_max": 6.0,
}

console = Console()

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, show_path=False)]
)
log = logging.getLogger("telegram_uploader")


# ---------------------------------------------------------------------
# Internacionalización (i18n) / Internationalization
# ---------------------------------------------------------------------

STRINGS = {
    "es": {
        "banner_subtitle": "Sube videos y archivos grandes a tu canal privado, con tu propia cuenta.",
        "lang_prompt_title": "Idioma / Language",
        "lang_prompt_body": "Seleccione un idioma / Select a language:\n  [1] Español\n  [2] English",
        "lang_prompt_input": "Opción / Option",
        "lang_invalid": "Opción inválida, se usará Español por defecto.",
        "wizard_title_first": "🛠️  Configuración inicial",
        "wizard_title_redo": "🛠️  Reconfigurar",
        "wizard_intro": (
            "Se necesita el [bold]api_id[/bold] y el [bold]api_hash[/bold] de Telegram.\n"
            "Puede obtenerlos gratis (con su cuenta de Telegram) en:\n"
            "  [cyan]https://my.telegram.org/apps[/cyan]\n\n"
            "También se necesita el canal o grupo privado de destino — debe ser\n"
            "miembro o administrador de ese canal con la misma cuenta que se usará aquí.\n"
            "Puede indicar el @usuario (ej: [italic]@mi_nube_personal[/italic]) o el ID\n"
            "numérico (ej: [italic]-1001234567890[/italic])."
        ),
        "label_api_id": "api_id",
        "label_api_hash": "api_hash",
        "label_canal": "Canal de destino (@usuario o ID)",
        "err_required": "Este campo es obligatorio.",
        "err_api_id_numeric": "El api_id debe ser numérico.",
        "err_min": "Debe ser mayor o igual a {minimo}.",
        "err_invalid_number": "Ingrese un número válido.",
        "speed_settings_intro": "Ajustes de velocidad y ritmo (puede dejar los valores sugeridos con ENTER):",
        "label_chunks": "Fragmentos en paralelo por archivo (velocidad, recomendado 8)",
        "label_pausa_min": "Pausa mínima entre subidas en segundos (anti-spam)",
        "label_pausa_max": "Pausa máxima entre subidas en segundos",
        "config_saved": "✅ Configuración guardada en config.json",
        "config_table_title": "Configuración actual",
        "row_idioma": "0. Idioma",
        "row_api_id": "1. api_id",
        "row_api_hash": "2. api_hash",
        "row_canal": "3. Canal de destino",
        "row_chunks": "4. Fragmentos en paralelo",
        "row_pausa_min": "5. Pausa mínima (s)",
        "row_pausa_max": "6. Pausa máxima (s)",
        "not_configured": "(sin configurar)",
        "menu_options_line": "[bold]0-6[/bold] editar ese campo   [bold]R[/bold] rehacer todo   [bold]S[/bold] salir",
        "menu_prompt": ">",
        "menu_invalid": "Opción inválida.",
        "menu_saved": "✅ Guardado.",
        "welcome_title": "👋 Bienvenido",
        "welcome_body": (
            "Primera vez que se ejecuta el script en esta carpeta: se configurará ahora.\n"
            "(Luego se puede cambiar cualquier valor con [bold]--config[/bold], sin editar archivos manualmente.)"
        ),
        "no_config_yet": "Todavía no hay configuración guardada — se creará ahora.",
        "err_api_id_invalid_saved": "❌ api_id inválido en la configuración. Ejecute con --config para corregirlo.",
        "err_chunks_min1": "❌ --chunks-paralelos debe ser al menos 1",
        "err_pausas_negative": "❌ Las pausas no pueden ser negativas",
        "warn_paralelo_order": "⚠️  --paralelo {n} activo: el orden de aparición en el canal puede no ser estrictamente cronológico.",
        "tip_cryptg": "💡 Sugerencia: instale 'cryptg' (pip install cryptg) para subidas mucho más rápidas (cifrado en C en vez de Python puro). No es obligatorio, pero se nota bastante.",
        "warn_ffmpeg_missing": "⚠️  ffmpeg no está instalado: no se generarán miniaturas ni se podrá ordenar por metadata del video. Instálelo para la mejor experiencia (ver README).",
        "prompt_carpeta": "📁 Ruta de la carpeta a subir",
        "err_carpeta_not_found": "❌ No se encuentra la carpeta: {carpeta}",
        "log_found_files": "📁 Se encontraron {n} archivo(s) en total.",
        "log_pending_files": "🆕 {n} archivo(s) pendiente(s) de subir.",
        "log_nothing_new": "No hay nada nuevo para subir. 🎉",
        "err_channel_not_found": "❌ No se pudo encontrar el canal {canal!r}: {error}",
        "hint_check_channel": "   Verifique que el nombre/ID sea correcto y que la cuenta esté unida a ese canal.",
        "hint_fix_config": "   Puede corregirlo con: python3 subir_a_telegram.py --config",
        "progress_total_label": "🚀 Progreso total",
        "log_uploading": "📤 Subiendo: {nombre} ({mb:.1f} MB)",
        "dry_run_note": "   (dry-run, no se sube de verdad)",
        "err_flood_too_many": "❌ Demasiadas esperas por límite de Telegram con {nombre}, se omite por ahora.",
        "warn_flood_wait": "⏳ Telegram pide esperar {segundos}s (límite de subidas). Esperando...",
        "err_persistent": "❌ Error persistente subiendo {nombre}: {error}",
        "warn_retry": "⚠️  Error subiendo {nombre} ({error}). Reintento {intento}/{maximo} en {espera}s...",
        "err_unexpected": "❌ Error inesperado subiendo {nombre}: {error}",
        "log_done": "✅ Listo: {nombre}",
        "log_deleted_local": "🗑️  Archivo local eliminado: {nombre}",
        "log_pause": "⏸️  Pausa de {segundos:.1f}s antes de la próxima subida (anti-spam)...",
        "log_finished": "🏁 Finalizado. {ok}/{total} archivo(s) subido(s) con éxito.",
        "log_interrupted": "\n⏹️  Interrumpido por el usuario. Cerrando...",
        "arg_desc": "Telegram Uploader — sube archivos grandes a un canal privado de Telegram con tu cuenta.",
        "arg_epilog": "Más información y guía completa en README.md",
        "arg_config_help": "Abre el menú de configuración (api_id, api_hash, canal, velocidad, idioma) y sale sin subir nada.",
        "arg_carpeta_help": "Carpeta con los archivos a subir. Si no se indica, se pregunta por consola.",
        "arg_todo_help": "Sube todos los archivos, no solo videos.",
        "arg_borrar_local_help": "Elimina el archivo local tras subirlo con éxito.",
        "arg_paralelo_help": "Cantidad de ARCHIVOS subidos simultáneamente (por defecto 1, mantiene el orden estricto).",
        "arg_chunks_help": "Sobrescribe, solo para esta ejecución, el valor guardado en la configuración.",
        "arg_pausa_min_help": "Sobrescribe la pausa mínima guardada (segundos).",
        "arg_pausa_max_help": "Sobrescribe la pausa máxima guardada (segundos).",
        "arg_dry_run_help": "Simula la ejecución sin subir nada de verdad.",
        "arg_debug_help": "Muestra registros de diagnóstico adicionales.",
        "arg_lang_help": "Fuerza el idioma para esta ejecución (es/en), sin modificar la configuración guardada.",
    },
    "en": {
        "banner_subtitle": "Upload large videos and files to your private channel, using your own account.",
        "lang_prompt_title": "Idioma / Language",
        "lang_prompt_body": "Seleccione un idioma / Select a language:\n  [1] Español\n  [2] English",
        "lang_prompt_input": "Opción / Option",
        "lang_invalid": "Invalid option, defaulting to English.",
        "wizard_title_first": "🛠️  Initial setup",
        "wizard_title_redo": "🛠️  Reconfigure",
        "wizard_intro": (
            "You'll need your Telegram [bold]api_id[/bold] and [bold]api_hash[/bold].\n"
            "Get them for free (with your Telegram account) at:\n"
            "  [cyan]https://my.telegram.org/apps[/cyan]\n\n"
            "You'll also need the destination private channel or group — you must be\n"
            "a member or admin of that channel with the same account you'll use here.\n"
            "You can use the @username (e.g. [italic]@my_personal_cloud[/italic]) or the\n"
            "numeric ID (e.g. [italic]-1001234567890[/italic])."
        ),
        "label_api_id": "api_id",
        "label_api_hash": "api_hash",
        "label_canal": "Destination channel (@username or ID)",
        "err_required": "This field is required.",
        "err_api_id_numeric": "api_id must be numeric.",
        "err_min": "Must be greater than or equal to {minimo}.",
        "err_invalid_number": "Enter a valid number.",
        "speed_settings_intro": "Speed and pacing settings (press ENTER to keep the suggested values):",
        "label_chunks": "Parallel chunks per file (speed, recommended 8)",
        "label_pausa_min": "Minimum pause between uploads in seconds (anti-spam)",
        "label_pausa_max": "Maximum pause between uploads in seconds",
        "config_saved": "✅ Configuration saved to config.json",
        "config_table_title": "Current configuration",
        "row_idioma": "0. Language",
        "row_api_id": "1. api_id",
        "row_api_hash": "2. api_hash",
        "row_canal": "3. Destination channel",
        "row_chunks": "4. Parallel chunks",
        "row_pausa_min": "5. Minimum pause (s)",
        "row_pausa_max": "6. Maximum pause (s)",
        "not_configured": "(not configured)",
        "menu_options_line": "[bold]0-6[/bold] edit that field   [bold]R[/bold] redo everything   [bold]S[/bold] save & exit",
        "menu_prompt": ">",
        "menu_invalid": "Invalid option.",
        "menu_saved": "✅ Saved.",
        "welcome_title": "👋 Welcome",
        "welcome_body": (
            "First time running the script in this folder: let's set it up now.\n"
            "(You can change any value later with [bold]--config[/bold], with no manual file editing.)"
        ),
        "no_config_yet": "There's no saved configuration yet — let's create it now.",
        "err_api_id_invalid_saved": "❌ Invalid api_id in the saved configuration. Run with --config to fix it.",
        "err_chunks_min1": "❌ --chunks-paralelos must be at least 1",
        "err_pausas_negative": "❌ Pauses cannot be negative",
        "warn_paralelo_order": "⚠️  --paralelo {n} is active: the order files appear in the channel may not be strictly chronological.",
        "tip_cryptg": "💡 Tip: install 'cryptg' (pip install cryptg) for much faster uploads (C encryption instead of pure Python). Not required, but the difference is noticeable.",
        "warn_ffmpeg_missing": "⚠️  ffmpeg is not installed: thumbnails won't be generated and chronological ordering will be less accurate. Install it for the best experience (see README).",
        "prompt_carpeta": "📁 Path of the folder to upload",
        "err_carpeta_not_found": "❌ Folder not found: {carpeta}",
        "log_found_files": "📁 Found {n} file(s) in total.",
        "log_pending_files": "🆕 {n} file(s) pending upload.",
        "log_nothing_new": "Nothing new to upload. 🎉",
        "err_channel_not_found": "❌ Could not find channel {canal!r}: {error}",
        "hint_check_channel": "   Check that the name/ID is correct and that the account has joined that channel.",
        "hint_fix_config": "   You can fix it with: python3 subir_a_telegram.py --config",
        "progress_total_label": "🚀 Total progress",
        "log_uploading": "📤 Uploading: {nombre} ({mb:.1f} MB)",
        "dry_run_note": "   (dry-run, nothing is actually uploaded)",
        "err_flood_too_many": "❌ Too many Telegram rate-limit waits for {nombre}, skipping it for now.",
        "warn_flood_wait": "⏳ Telegram asked to wait {segundos}s (upload rate limit). Waiting...",
        "err_persistent": "❌ Persistent error uploading {nombre}: {error}",
        "warn_retry": "⚠️  Error uploading {nombre} ({error}). Retry {intento}/{maximo} in {espera}s...",
        "err_unexpected": "❌ Unexpected error uploading {nombre}: {error}",
        "log_done": "✅ Done: {nombre}",
        "log_deleted_local": "🗑️  Local file deleted: {nombre}",
        "log_pause": "⏸️  Pausing {segundos:.1f}s before the next upload (anti-spam)...",
        "log_finished": "🏁 Finished. {ok}/{total} file(s) uploaded successfully.",
        "log_interrupted": "\n⏹️  Interrupted by user. Closing...",
        "arg_desc": "Telegram Uploader — upload large files to a private Telegram channel with your account.",
        "arg_epilog": "See README.md for full documentation.",
        "arg_config_help": "Open the configuration menu (api_id, api_hash, channel, speed, language) and exit without uploading.",
        "arg_carpeta_help": "Folder with the files to upload. If not given, it's asked interactively.",
        "arg_todo_help": "Upload all files, not just videos.",
        "arg_borrar_local_help": "Delete the local file after a successful upload.",
        "arg_paralelo_help": "How many FILES are uploaded at the same time (default 1, keeps strict order).",
        "arg_chunks_help": "Overrides, only for this run, the value saved in the configuration.",
        "arg_pausa_min_help": "Overrides the saved minimum pause (seconds).",
        "arg_pausa_max_help": "Overrides the saved maximum pause (seconds).",
        "arg_dry_run_help": "Simulate the run without uploading anything for real.",
        "arg_debug_help": "Show extra diagnostic logs.",
        "arg_lang_help": "Force the language for this run (es/en), without changing the saved configuration.",
    },
}

IDIOMA_ACTUAL = "es"  # se ajusta en tiempo de ejecución


def t(clave: str, **kwargs) -> str:
    texto = STRINGS.get(IDIOMA_ACTUAL, STRINGS["en"]).get(clave, clave)
    return texto.format(**kwargs) if kwargs else texto


def elegir_idioma_interactivo() -> str:
    console.print(Panel(STRINGS["es"]["lang_prompt_body"], title="Idioma / Language", border_style="blue"))
    respuesta = input("Opción / Option [1/2]: ").strip()
    if respuesta == "2":
        return "en"
    if respuesta not in ("1", "2", ""):
        console.print("[yellow]" + STRINGS["es"]["lang_invalid"] + "[/yellow]")
    return "es"


# ---------------------------------------------------------------------
# Configuración: wizard interactivo + menú de edición
# ---------------------------------------------------------------------

def cargar_config() -> dict:
    config = dict(CONFIG_DEFAULTS)
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                guardado = json.load(f)
            for clave in CONFIG_DEFAULTS:
                if clave in guardado:
                    config[clave] = guardado[clave]
        except (json.JSONDecodeError, OSError):
            log.warning("⚠️  config.json existe pero no se pudo leer / could not be read. Se usarán valores por defecto / using defaults.")

    if os.environ.get("TG_API_ID"):
        config["api_id"] = os.environ["TG_API_ID"]
    if os.environ.get("TG_API_HASH"):
        config["api_hash"] = os.environ["TG_API_HASH"]
    if os.environ.get("TG_CANAL"):
        config["canal"] = os.environ["TG_CANAL"]

    return config


def guardar_config(config: dict) -> None:
    datos = {clave: config[clave] for clave in CONFIG_DEFAULTS}
    tmp = CONFIG_PATH.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)
    os.replace(tmp, CONFIG_PATH)


def config_incompleta(config: dict) -> bool:
    return not (config.get("api_id") and config.get("api_hash") and config.get("canal"))


def enmascarar(valor) -> str:
    valor = str(valor)
    if not valor:
        return t("not_configured")
    if len(valor) <= 4:
        return "*" * len(valor)
    return "*" * (len(valor) - 4) + valor[-4:]


def pedir_texto(mensaje: str, valor_actual: str = "", obligatorio: bool = True) -> str:
    while True:
        sugerido = f" [{valor_actual}]" if valor_actual else ""
        respuesta = input(f"{mensaje}{sugerido}: ").strip()
        if not respuesta and valor_actual:
            return valor_actual
        if not respuesta and obligatorio:
            console.print(f"   [yellow]⚠️  {t('err_required')}[/yellow]")
            continue
        return respuesta


def pedir_numero(mensaje: str, valor_actual, tipo=float, minimo=None):
    while True:
        respuesta = input(f"{mensaje} [{valor_actual}]: ").strip()
        if not respuesta:
            return valor_actual
        try:
            valor = tipo(respuesta)
            if minimo is not None and valor < minimo:
                console.print(f"   [yellow]⚠️  {t('err_min', minimo=minimo)}[/yellow]")
                continue
            return valor
        except ValueError:
            console.print(f"   [yellow]⚠️  {t('err_invalid_number')}[/yellow]")


def asistente_configuracion(config_actual: dict, primera_vez: bool) -> dict:
    config = dict(config_actual)

    console.print(Panel(
        t("wizard_intro"),
        title=t("wizard_title_first") if primera_vez else t("wizard_title_redo"),
        border_style="blue",
    ))

    while True:
        try:
            config["api_id"] = int(pedir_texto(t("label_api_id"), str(config.get("api_id") or "")))
            break
        except ValueError:
            console.print(f"   [yellow]⚠️  {t('err_api_id_numeric')}[/yellow]")

    config["api_hash"] = pedir_texto(t("label_api_hash"), str(config.get("api_hash") or ""))
    config["canal"] = pedir_texto(t("label_canal"), str(config.get("canal") or ""))

    console.print()
    console.print(f"[dim]{t('speed_settings_intro')}[/dim]")
    config["chunks_paralelos"] = int(pedir_numero(
        t("label_chunks"), config.get("chunks_paralelos", 8), tipo=int, minimo=1))
    config["pausa_min"] = pedir_numero(
        t("label_pausa_min"), config.get("pausa_min", 3.0), tipo=float, minimo=0)
    config["pausa_max"] = pedir_numero(
        t("label_pausa_max"), config.get("pausa_max", 6.0), tipo=float, minimo=0)
    if config["pausa_max"] < config["pausa_min"]:
        config["pausa_min"], config["pausa_max"] = config["pausa_max"], config["pausa_min"]

    config["idioma"] = IDIOMA_ACTUAL
    guardar_config(config)
    console.print(f"\n[green]{t('config_saved')}[/green]\n")
    return config


def mostrar_config(config: dict) -> None:
    tabla = Table(title=t("config_table_title"), show_header=False, border_style="blue")
    tabla.add_column(style="bold")
    tabla.add_column()
    tabla.add_row(t("row_idioma"), "Español" if config.get("idioma") == "es" else "English")
    tabla.add_row(t("row_api_id"), str(config["api_id"]) or t("not_configured"))
    tabla.add_row(t("row_api_hash"), enmascarar(config["api_hash"]))
    tabla.add_row(t("row_canal"), str(config["canal"]) or t("not_configured"))
    tabla.add_row(t("row_chunks"), str(config["chunks_paralelos"]))
    tabla.add_row(t("row_pausa_min"), str(config["pausa_min"]))
    tabla.add_row(t("row_pausa_max"), str(config["pausa_max"]))
    console.print(tabla)


def menu_configuracion(config: dict) -> dict:
    global IDIOMA_ACTUAL
    while True:
        console.print()
        mostrar_config(config)
        console.print(f"\n{t('menu_options_line')}")
        opcion = input(f"{t('menu_prompt')} ").strip().lower()

        if opcion == "0":
            nuevo_idioma = elegir_idioma_interactivo()
            IDIOMA_ACTUAL = nuevo_idioma
            config["idioma"] = nuevo_idioma
        elif opcion == "1":
            try:
                config["api_id"] = int(pedir_texto(t("label_api_id"), str(config["api_id"])))
            except ValueError:
                console.print(f"   [yellow]⚠️  {t('err_api_id_numeric')}[/yellow]")
                continue
        elif opcion == "2":
            config["api_hash"] = pedir_texto(t("label_api_hash"), str(config["api_hash"]))
        elif opcion == "3":
            config["canal"] = pedir_texto(t("label_canal"), str(config["canal"]))
        elif opcion == "4":
            config["chunks_paralelos"] = int(pedir_numero(
                t("label_chunks"), config["chunks_paralelos"], tipo=int, minimo=1))
        elif opcion == "5":
            config["pausa_min"] = pedir_numero(t("label_pausa_min"), config["pausa_min"], tipo=float, minimo=0)
        elif opcion == "6":
            config["pausa_max"] = pedir_numero(t("label_pausa_max"), config["pausa_max"], tipo=float, minimo=0)
        elif opcion == "r":
            config = asistente_configuracion(config, primera_vez=False)
            continue
        elif opcion == "s":
            guardar_config(config)
            console.print(f"[green]{t('menu_saved')}[/green]")
            return config
        else:
            console.print(f"[yellow]{t('menu_invalid')}[/yellow]")
            continue

        guardar_config(config)


# ---------------------------------------------------------------------
# Registro de subidos (dedupe) y orden cronológico
# ---------------------------------------------------------------------

def cargar_registro():
    if os.path.exists(REGISTRO_SUBIDOS):
        try:
            with open(REGISTRO_SUBIDOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            log.warning("⚠️  %s corrupto / corrupted, empezando registro nuevo / starting a new log.", REGISTRO_SUBIDOS)
            return {}
    return {}


def guardar_registro(registro):
    tmp = f"{REGISTRO_SUBIDOS}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(registro, f, indent=2, ensure_ascii=False)
    os.replace(tmp, REGISTRO_SUBIDOS)


def clave_archivo(ruta: Path) -> str:
    stat = ruta.stat()
    base = f"{ruta.name}-{stat.st_size}-{int(stat.st_mtime)}"
    return hashlib.sha256(base.encode()).hexdigest()


def encontrar_archivos(carpeta: Path, solo_videos: bool):
    for ruta in carpeta.rglob("*"):
        if ruta.is_file():
            if solo_videos and ruta.suffix.lower() not in EXTENSIONES_VIDEO:
                continue
            yield ruta


FILENAME_DATE_PATTERN = re.compile(r"(\d{4})-(\d{2})-(\d{2})[_-](\d{2})-(\d{2})-(\d{2})")
_FFPROBE_DISPONIBLE = shutil.which("ffprobe") is not None
_FFMPEG_DISPONIBLE = shutil.which("ffmpeg") is not None


def _get_video_creation_time(ruta: Path):
    if not _FFPROBE_DISPONIBLE:
        return None
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format_tags=creation_time",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(ruta),
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
        value = result.stdout.strip()
        if not value:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def obtener_timestamp_orden(ruta: Path) -> float:
    if ruta.suffix.lower() in EXTENSIONES_VIDEO:
        ts = _get_video_creation_time(ruta)
        if ts is not None:
            return ts

    match = FILENAME_DATE_PATTERN.search(ruta.name)
    if match:
        year, month, day, hour, minute, second = map(int, match.groups())
        try:
            return datetime(year, month, day, hour, minute, second).timestamp()
        except ValueError:
            pass

    return ruta.stat().st_mtime


def obtener_atributos_video(ruta: Path):
    if not _FFPROBE_DISPONIBLE:
        return None
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height:format=duration",
        "-of", "json",
        str(ruta),
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
        data = json.loads(result.stdout)
        stream = (data.get("streams") or [{}])[0]
        width = int(stream.get("width", 0) or 0)
        height = int(stream.get("height", 0) or 0)
        duration = float((data.get("format") or {}).get("duration", 0) or 0)
        if width and height:
            return width, height, duration
    except Exception:
        pass
    return None


def generar_miniatura(ruta: Path, duracion: float = 0.0):
    if not _FFMPEG_DISPONIBLE:
        return None

    momento = min(1.0, duracion / 2) if duracion > 0 else 0.5
    fd, destino_str = tempfile.mkstemp(suffix=".jpg", prefix="thumb_")
    os.close(fd)
    destino = Path(destino_str)

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(momento),
        "-i", str(ruta),
        "-frames:v", "1",
        "-vf", "scale=320:-2",
        "-q:v", "4",
        str(destino),
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        if result.returncode == 0 and destino.exists() and destino.stat().st_size > 0:
            return destino
    except Exception:
        pass

    try:
        destino.unlink(missing_ok=True)
    except Exception:
        pass
    return None


def resolver_canal(valor: str):
    valor = str(valor).strip()
    if valor.lstrip("-").isdigit():
        return int(valor)
    return valor


# ---------------------------------------------------------------------
# Subida en paralelo (chunks) + progreso + reintentos
# ---------------------------------------------------------------------

async def upload_file_paralelo(client, ruta: Path, chunks_paralelos: int, progress_callback=None):
    file_size = ruta.stat().st_size
    if file_size <= UMBRAL_ARCHIVO_GRANDE or chunks_paralelos <= 1:
        return await client.upload_file(str(ruta), part_size_kb=512, progress_callback=progress_callback)

    part_size = 512 * 1024
    part_count = (file_size + part_size - 1) // part_size
    file_id = helpers.generate_random_long()

    semaforo = asyncio.Semaphore(max(1, chunks_paralelos))
    subido = 0
    lock = asyncio.Lock()

    async def subir_parte(idx):
        nonlocal subido
        async with semaforo:
            with open(ruta, "rb") as f:
                f.seek(idx * part_size)
                parte = f.read(part_size)

            ok = await client(SaveBigFilePartRequest(file_id, idx, part_count, parte))
            if not ok:
                raise RuntimeError(f"Telegram rechazó la parte {idx}/{part_count}")

            if progress_callback:
                async with lock:
                    subido += len(parte)
                    await helpers._maybe_await(progress_callback(subido, file_size))

    await asyncio.gather(*(subir_parte(i) for i in range(part_count)))
    return InputFileBig(file_id, part_count, ruta.name)


async def subir_archivo(client, destino, ruta: Path, borrar_local: bool, semaforo: asyncio.Semaphore,
                         dry_run: bool, pausa_min: float, pausa_max: float, chunks_paralelos: int,
                         progress: Progress, task_global_id):
    async with semaforo:
        tamano_bytes = ruta.stat().st_size
        tamano_mb = tamano_bytes / (1024 * 1024)
        log.info(t("log_uploading", nombre=ruta.name, mb=tamano_mb))

        if dry_run:
            log.info(t("dry_run_note"))
            if task_global_id is not None:
                progress.advance(task_global_id, 1)
            return True

        task_id = progress.add_task(f"🎬 {ruta.name[:25].ljust(25)}", total=tamano_bytes)
        ultimo_progreso = 0

        def progreso(actual, total):
            nonlocal ultimo_progreso
            if actual - ultimo_progreso > 0:
                progress.update(task_id, completed=actual)
                ultimo_progreso = actual

        es_video = ruta.suffix.lower() in EXTENSIONES_VIDEO
        atributos = None
        mime_type = None
        miniatura = None
        if es_video:
            dims = obtener_atributos_video(ruta)
            duracion_video = 0.0
            if dims:
                ancho, alto, duracion_video = dims
                atributos = [DocumentAttributeVideo(
                    duration=int(duracion_video), w=ancho, h=alto, supports_streaming=True,
                )]
            mime_type = mimetypes.guess_type(ruta.name)[0] or "video/mp4"
            miniatura = generar_miniatura(ruta, duracion_video)

        intentos_flood = 0
        intentos_error = 0
        exito = False

        try:
            while True:
                try:
                    handle = await upload_file_paralelo(client, ruta, chunks_paralelos, progreso)
                    await client.send_file(
                        destino,
                        file=handle,
                        caption=ruta.name,
                        attributes=atributos,
                        mime_type=mime_type,
                        supports_streaming=es_video,
                        thumb=str(miniatura) if miniatura else None,
                    )
                    exito = True
                    break
                except FloodWaitError as e:
                    intentos_flood += 1
                    if intentos_flood > 5:
                        log.error(t("err_flood_too_many", nombre=ruta.name))
                        exito = False
                        break
                    log.warning(t("warn_flood_wait", segundos=e.seconds))
                    await asyncio.sleep(e.seconds + 1)
                except (RPCError, ConnectionError, OSError) as e:
                    intentos_error += 1
                    if intentos_error > MAX_REINTENTOS_ERROR:
                        log.error(t("err_persistent", nombre=ruta.name, error=e))
                        exito = False
                        break
                    espera = 5 * intentos_error
                    log.warning(t("warn_retry", nombre=ruta.name, error=e,
                                  intento=intentos_error, maximo=MAX_REINTENTOS_ERROR, espera=espera))
                    await asyncio.sleep(espera)
                except Exception as e:
                    log.error(t("err_unexpected", nombre=ruta.name, error=e))
                    exito = False
                    break
        finally:
            progress.remove_task(task_id)
            if miniatura:
                try:
                    miniatura.unlink(missing_ok=True)
                except Exception:
                    pass

        if not exito:
            return False

        if task_global_id is not None:
            progress.advance(task_global_id, 1)

        log.info(t("log_done", nombre=ruta.name))

        if borrar_local:
            ruta.unlink()
            log.info(t("log_deleted_local", nombre=ruta.name))

        if pausa_max > 0:
            espera = random.uniform(pausa_min, pausa_max)
            log.info(t("log_pause", segundos=espera))
            await asyncio.sleep(espera)

        return True


# ---------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------

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


async def main():
    global IDIOMA_ACTUAL

    config = cargar_config()

    # Determinar idioma: --lang (temporal) > guardado en config > preguntar
    lang_cli = None
    if "--lang" in sys.argv:
        idx = sys.argv.index("--lang")
        if idx + 1 < len(sys.argv):
            lang_cli = sys.argv[idx + 1]

    if lang_cli in ("es", "en"):
        IDIOMA_ACTUAL = lang_cli
    elif config.get("idioma") in ("es", "en"):
        IDIOMA_ACTUAL = config["idioma"]
    elif "-h" in sys.argv or "--help" in sys.argv:
        IDIOMA_ACTUAL = "es"  # --help no debe quedar esperando input
    else:
        IDIOMA_ACTUAL = elegir_idioma_interactivo()
        if not CONFIG_PATH.exists():
            config["idioma"] = IDIOMA_ACTUAL  # se confirma al guardar el resto en el wizard

    console.print(Panel.fit(
        f"[bold]📡 Telegram Uploader[/bold] [dim]v{VERSION}[/dim]\n{t('banner_subtitle')}",
        border_style="blue",
    ))

    parser = construir_parser()
    args = parser.parse_args()

    if args.debug:
        log.setLevel(logging.DEBUG)

    if args.config:
        if config_incompleta(config):
            console.print(f"[yellow]{t('no_config_yet')}[/yellow]\n")
            asistente_configuracion(config, primera_vez=True)
        else:
            menu_configuracion(config)
        return

    if config_incompleta(config):
        console.print(Panel(t("welcome_body"), title=t("welcome_title"), border_style="green"))
        config = asistente_configuracion(config, primera_vez=True)
    elif not config.get("idioma"):
        config["idioma"] = IDIOMA_ACTUAL
        guardar_config(config)

    try:
        api_id = int(config["api_id"])
    except (TypeError, ValueError):
        console.print(f"[red]{t('err_api_id_invalid_saved')}[/red]")
        sys.exit(1)

    api_hash = str(config["api_hash"])
    canal = config["canal"]
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

    if args.paralelo > 1:
        log.warning(t("warn_paralelo_order", n=args.paralelo))

    try:
        import cryptg  # noqa: F401
    except ImportError:
        log.warning(t("tip_cryptg"))

    if not _FFMPEG_DISPONIBLE:
        log.warning(t("warn_ffmpeg_missing"))

    ruta_carpeta = args.carpeta
    while not ruta_carpeta:
        ruta_carpeta = input(f"{t('prompt_carpeta')}: ").strip().strip('"').strip("'")

    carpeta = Path(ruta_carpeta).expanduser()
    if not carpeta.is_dir():
        console.print(f"[red]{t('err_carpeta_not_found', carpeta=carpeta)}[/red]")
        sys.exit(1)

    registro = cargar_registro()
    archivos = list(encontrar_archivos(carpeta, solo_videos=not args.todo))
    archivos.sort(key=obtener_timestamp_orden)
    pendientes = [a for a in archivos if clave_archivo(a) not in registro]

    log.info(t("log_found_files", n=len(archivos)))
    log.info(t("log_pending_files", n=len(pendientes)))

    if not pendientes:
        log.info(t("log_nothing_new"))
        return

    client = TelegramClient(
        SESSION_NAME, api_id, api_hash,
        connection_retries=5,
        retry_delay=1,
        request_retries=5,
        timeout=60,
        flood_sleep_threshold=60,
    )

    try:
        await client.start()

        try:
            destino = await client.get_entity(resolver_canal(canal))
        except (ValueError, RPCError) as e:
            console.print(f"[red]{t('err_channel_not_found', canal=canal, error=e)}[/red]")
            console.print(t("hint_check_channel"))
            console.print(t("hint_fix_config"))
            sys.exit(1)

        semaforo = asyncio.Semaphore(max(1, args.paralelo))
        subidos_ok = 0
        lock_registro = asyncio.Lock()

        progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=None),
            TaskProgressColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TextColumn("[dim]Elapsed:[/dim]"),
            TimeElapsedColumn(),
            TextColumn("[dim]ETA:[/dim]"),
            TimeRemainingColumn(),
            transient=False,
            refresh_per_second=10,
        )

        with progress:
            task_global_id = progress.add_task(t("progress_total_label"), total=len(pendientes))

            async def procesar(ruta):
                nonlocal subidos_ok
                exito = await subir_archivo(
                    client, destino, ruta, args.borrar_local, semaforo,
                    args.dry_run, pausa_min, pausa_max, chunks_paralelos,
                    progress, task_global_id,
                )
                if exito and not args.dry_run:
                    async with lock_registro:
                        registro[clave_archivo(ruta)] = {"nombre": ruta.name, "ruta_original": str(ruta)}
                        guardar_registro(registro)
                        subidos_ok += 1

            await asyncio.gather(*(procesar(ruta) for ruta in pendientes))

        log.info(t("log_finished", ok=subidos_ok, total=len(pendientes)))

    except KeyboardInterrupt:
        log.warning(t("log_interrupted"))
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())