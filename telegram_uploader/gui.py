"""Interfaz gráfica de escritorio con Flet.

Es el único módulo que importa Flet. La lógica que no necesita pantalla vive en
gui_modelo.py, que sí se prueba con pytest. Requiere: pip install -r requirements-gui.txt
"""
import flet as ft

from .config import cargar_config, config_incompleta, guardar_config
from .constantes import VERSION
from .errores import ErrorDeUso
from .gui_modelo import AjustesVentana, crear_solicitud, validar_formulario
from .i18n import t, traductor
from .registro import cargar_registro
from .servicio import buscar_pendientes

ETIQUETAS = {
    "api_id": "gui_label_api_id",
    "api_hash": "gui_label_api_hash",
    "canal": "gui_label_canal",
    "chunks_paralelos": "gui_label_chunks",
    "pausa_min": "gui_label_pausa_min",
    "pausa_max": "gui_label_pausa_max",
}
IDIOMAS = (("es", "Español"), ("en", "English"))  # nombres propios de cada idioma


def crear_formulario(config: dict) -> dict:
    """Un campo de texto por ajuste, con el valor guardado. El api_hash va oculto."""
    campos = {}
    for campo, clave_texto in ETIQUETAS.items():
        es_secreto = campo == "api_hash"
        campos[campo] = ft.TextField(
            label=t(clave_texto), value=str(config.get(campo, "")), width=420,
            password=es_secreto, can_reveal_password=es_secreto,
        )
    return campos


def guardar_formulario(config: dict, campos: dict, idioma: str) -> bool:
    """Valida lo escrito y lo guarda. Si algo falla, marca el campo y devuelve False."""
    for campo in campos.values():
        campo.error = None
    try:
        validados = validar_formulario({nombre: c.value for nombre, c in campos.items()})
    except ErrorDeUso as e:
        campos[e.datos["campo"]].error = t(e.clave, **e.datos)
        return False
    config.update(validados)
    config["idioma"] = idioma
    guardar_config(config)
    return True


def construir_pantalla_config(config: dict, actualizar) -> ft.Column:
    """Pantalla de configuración. `actualizar` redibuja la ventana."""
    campos = crear_formulario(config)
    idioma = ft.Dropdown(
        label=t("gui_label_idioma"), value=traductor.idioma, width=420,
        options=[ft.dropdown.Option(clave, nombre) for clave, nombre in IDIOMAS],
    )
    estado = ft.Text("")

    def al_guardar(_evento):
        if guardar_formulario(config, campos, idioma.value):
            estado.value = t("gui_config_guardada")
            estado.color = ft.Colors.GREEN
        else:
            estado.value = ""
        actualizar()

    return ft.Column(
        [ft.Text(t("gui_config_title"), size=24, weight=ft.FontWeight.BOLD),
         *campos.values(), idioma,
         ft.Button(content=ft.Text(t("gui_btn_guardar")), on_click=al_guardar),
         estado],
        spacing=12,
    )


def construir_pantalla_subida(config: dict, page: ft.Page) -> ft.Column:
    """Pantalla de subida: carpeta, opciones y revisión de lo que hay pendiente."""
    carpeta = ft.TextField(label=t("gui_label_carpeta"), expand=True)
    selector = ft.FilePicker()
    page.services.append(selector)
    todo = ft.Checkbox(label=t("gui_check_todo"), value=False)
    borrar = ft.Checkbox(label=t("gui_check_borrar"), value=False)
    simulacion = ft.Checkbox(label=t("gui_check_dry"), value=False)
    resultado = ft.Text("", selectable=True)

    async def al_elegir(_evento):
        ruta = await selector.get_directory_path(dialog_title=t("gui_label_carpeta"))
        if ruta:
            carpeta.value = ruta
            page.update()

    def al_revisar(_evento):
        ajustes = AjustesVentana(solo_videos=not todo.value, borrar_local=borrar.value,
                                 dry_run=simulacion.value)
        try:
            solicitud = crear_solicitud(config, carpeta.value or "", ajustes)
        except ErrorDeUso as e:
            resultado.value = t(e.clave, **e.datos)
            resultado.color = ft.Colors.RED
        else:
            archivos, pendientes = buscar_pendientes(
                solicitud.carpeta, solicitud.solo_videos, cargar_registro())
            resultado.value = (f"{t('log_found_files', n=len(archivos))}\n"
                               f"{t('log_pending_files', n=len(pendientes))}")
            resultado.color = None
        page.update()

    return ft.Column(
        [ft.Text(t("gui_nav_subida"), size=24, weight=ft.FontWeight.BOLD),
         ft.Row([carpeta, ft.Button(content=ft.Text(t("gui_btn_elegir")),
                                    icon=ft.Icons.FOLDER_OPEN, on_click=al_elegir)]),
         todo, borrar, simulacion,
         ft.Button(content=ft.Text(t("gui_btn_revisar")), on_click=al_revisar),
         resultado],
        spacing=12,
    )


def _mostrar(pantalla: ft.Column, otra: ft.Column, page: ft.Page):
    def al_pulsar(_evento):
        pantalla.visible = True
        otra.visible = False
        page.update()
    return al_pulsar


async def main(page: ft.Page):
    config = cargar_config()
    traductor.idioma = config["idioma"] if config.get("idioma") in ("es", "en") else "es"
    page.title = f"Telegram Uploader v{VERSION}"
    page.padding = 24
    page.scroll = ft.ScrollMode.AUTO

    subida = construir_pantalla_subida(config, page)
    ajustes = construir_pantalla_config(config, page.update)
    if config_incompleta(config):  # primera vez: empieza por la configuración
        subida.visible = False
    else:
        ajustes.visible = False

    page.add(
        ft.Row([
            ft.TextButton(content=ft.Text(t("gui_nav_subida")), on_click=_mostrar(subida, ajustes, page)),
            ft.TextButton(content=ft.Text(t("gui_config_title")), on_click=_mostrar(ajustes, subida, page)),
        ]),
        ft.Divider(),
        subida,
        ajustes,
    )


def ejecutar() -> None:
    ft.run(main)


if __name__ == "__main__":
    ejecutar()
