"""Internacionalización: textos en español e inglés y el traductor activo."""
from rich.panel import Panel

from .consola import console


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
        "log_resuming": "🔁 Reanudando {nombre}: {hechas} de {total} fragmentos ya estaban subidos",
        "warn_parts_expired": "⚠️  Telegram ya no conserva algunos fragmentos de {nombre} (parte {parte}); se vuelve a subir desde cero",
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
        "log_resuming": "🔁 Resuming {nombre}: {hechas} of {total} parts were already uploaded",
        "warn_parts_expired": "⚠️  Telegram no longer holds some parts of {nombre} (part {parte}); uploading again from the start",
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


class Traductor:
    """Traduce claves de texto al idioma activo ("es" o "en")."""

    def __init__(self, idioma: str = "es"):
        self.idioma = idioma

    def traducir(self, clave: str, **kwargs) -> str:
        texto = STRINGS.get(self.idioma, STRINGS["en"]).get(clave, clave)
        return texto.format(**kwargs) if kwargs else texto


traductor = Traductor("es")  # el idioma se ajusta en tiempo de ejecución


def t(clave: str, **kwargs) -> str:
    return traductor.traducir(clave, **kwargs)


def elegir_idioma_interactivo() -> str:
    console.print(Panel(STRINGS["es"]["lang_prompt_body"], title="Idioma / Language", border_style="blue"))
    respuesta = input("Opción / Option [1/2]: ").strip()
    if respuesta == "2":
        return "en"
    if respuesta not in ("1", "2", ""):
        console.print("[yellow]" + STRINGS["es"]["lang_invalid"] + "[/yellow]")
    return "es"
