"""Interfaz gráfica de escritorio con Flet.

Es el único módulo que importa Flet. La lógica que no necesita pantalla vive en
gui_modelo.py, que sí se prueba con pytest. Requiere: pip install -r requirements-gui.txt
"""
import flet as ft

from .config import cargar_config, guardar_config
from .constantes import VERSION
from .errores import ErrorDeUso
from .gui_modelo import validar_formulario
from .i18n import t, traductor

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


async def main(page: ft.Page):
    config = cargar_config()
    traductor.idioma = config["idioma"] if config.get("idioma") in ("es", "en") else "es"
    page.title = f"Telegram Uploader v{VERSION}"
    page.padding = 24
    page.scroll = ft.ScrollMode.AUTO
    page.add(construir_pantalla_config(config, page.update))


def ejecutar() -> None:
    ft.run(main)


if __name__ == "__main__":
    ejecutar()
