"""Configuración del usuario: lectura, escritura atómica, asistente y menú de edición."""
import json
import os

from rich.panel import Panel
from rich.table import Table

from .consola import console, log
from .constantes import CONFIG_DEFAULTS, CONFIG_PATH
from .i18n import elegir_idioma_interactivo, t, traductor


CARACTERES_VISIBLES = 4  # cuántos caracteres finales se muestran al enmascarar


def config_existe() -> bool:
    """Indica si ya hay un archivo de configuración guardado."""
    return CONFIG_PATH.exists()


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
            log.warning(
                "⚠️  config.json existe pero no se pudo leer / could not be read. "
                "Se usarán valores por defecto / using defaults."
            )

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
    if len(valor) <= CARACTERES_VISIBLES:
        return "*" * len(valor)
    return "*" * (len(valor) - CARACTERES_VISIBLES) + valor[-CARACTERES_VISIBLES:]


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

    config["idioma"] = traductor.idioma
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
    while True:
        console.print()
        mostrar_config(config)
        console.print(f"\n{t('menu_options_line')}")
        opcion = input(f"{t('menu_prompt')} ").strip().lower()

        if opcion == "0":
            nuevo_idioma = elegir_idioma_interactivo()
            traductor.idioma = nuevo_idioma
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


def ejecutar_modo_config(config: dict) -> None:
    """Modo --config: asistente si falta configuración, menú de edición si ya existe."""
    if config_incompleta(config):
        console.print(f"[yellow]{t('no_config_yet')}[/yellow]\n")
        asistente_configuracion(config, primera_vez=True)
    else:
        menu_configuracion(config)


def asegurar_configuracion(config: dict) -> dict:
    """Devuelve una configuración completa, lanzando el asistente si hace falta."""
    if config_incompleta(config):
        console.print(Panel(t("welcome_body"), title=t("welcome_title"), border_style="green"))
        return asistente_configuracion(config, primera_vez=True)
    if not config.get("idioma"):
        config["idioma"] = traductor.idioma
        guardar_config(config)
    return config
