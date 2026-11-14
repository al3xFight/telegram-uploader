"""Interfaz gráfica de escritorio con Flet.

Es el único módulo que importa Flet. La lógica que no necesita pantalla vive en
gui_modelo.py, que sí se prueba con pytest. Requiere: pip install -r requirements-gui.txt
"""
import asyncio
from functools import partial
import time

import flet as ft

from .config import cargar_config, config_incompleta, guardar_config
from .consola import log
from .constantes import VERSION
from .errores import ErrorDeUso
from .gui_modelo import (
    AjustesVentana,
    ManejadorEventos,
    PuenteLogin,
    ReporteEstado,
    crear_solicitud,
    fraccion_total,
    necesita_confirmacion,
    validar_formulario,
)
from .i18n import t, traductor
from .registro import cargar_registro
from .servicio import buscar_pendientes, ejecutar_servicio

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

PREGUNTAS_LOGIN = {
    "telefono": "gui_login_telefono",
    "codigo": "gui_login_codigo",
    "contrasena": "gui_login_contrasena",
}


async def pedir_dato_login(page: ft.Page, clave: str) -> str:
    """Muestra un diálogo y devuelve lo que escriba la persona. Si cancela, lanza ErrorDeUso."""
    respuesta = asyncio.get_running_loop().create_future()
    es_secreto = clave == "contrasena"
    campo = ft.TextField(label=t(PREGUNTAS_LOGIN[clave]), width=420, autofocus=True,
                         password=es_secreto, can_reveal_password=es_secreto)

    def terminar(aceptar: bool):
        def al_pulsar(_evento):
            valor = campo.value if aceptar else None
            page.pop_dialog()
            if not respuesta.done():
                respuesta.set_result(valor)
        return al_pulsar

    campo.on_submit = terminar(True)
    page.show_dialog(ft.AlertDialog(
        modal=True,
        title=ft.Text(t("gui_login_title")),
        content=campo,
        actions=[
            ft.TextButton(content=ft.Text(t("gui_btn_cancelar")), on_click=terminar(False)),
            ft.Button(content=ft.Text(t("gui_btn_aceptar")), on_click=terminar(True)),
        ],
    ))
    valor = await respuesta
    if not valor:
        raise ErrorDeUso("gui_err_login_cancelado")
    return valor.strip()


INTERVALO_REDIBUJO = 0.25  # segundos mínimos entre dos redibujos del progreso
MAX_EVENTOS = 300  # mensajes que conserva la lista de eventos


class PantallaSubida:
    """Pantalla de subida: carpeta, opciones, progreso y eventos."""

    def __init__(self, config: dict, page: ft.Page):
        self.config = config
        self.page = page
        self.carpeta = ft.TextField(label=t("gui_label_carpeta"), expand=True)
        self.selector = ft.FilePicker()
        page.services.append(self.selector)
        self.todo = ft.Checkbox(label=t("gui_check_todo"), value=False)
        self.borrar = ft.Checkbox(label=t("gui_check_borrar"), value=False)
        self.simulacion = ft.Checkbox(label=t("gui_check_dry"), value=False)
        self.resultado = ft.Text("", selectable=True)
        self.texto_total = ft.Text("")
        self.barra_total = ft.ProgressBar(value=0, width=560)
        self.filas = ft.Column(spacing=4)
        self.eventos = ft.ListView(height=220, auto_scroll=True, spacing=2)
        self.boton_subir = ft.Button(content=ft.Text(t("gui_btn_subir")),
                                     icon=ft.Icons.UPLOAD, on_click=self.al_subir)
        self.ultimo_dibujo = 0.0
        self.vista = self._construir_vista()

    def _construir_vista(self) -> ft.Column:
        elegir = ft.Button(content=ft.Text(t("gui_btn_elegir")),
                           icon=ft.Icons.FOLDER_OPEN, on_click=self.al_elegir)
        revisar = ft.Button(content=ft.Text(t("gui_btn_revisar")), on_click=self.al_revisar)
        return ft.Column(
            [ft.Text(t("gui_nav_subida"), size=24, weight=ft.FontWeight.BOLD),
             ft.Row([self.carpeta, elegir]),
             self.todo, self.borrar, self.simulacion,
             ft.Row([revisar, self.boton_subir]),
             self.resultado, self.texto_total, self.barra_total, self.filas,
             ft.Text(t("gui_label_eventos"), weight=ft.FontWeight.BOLD), self.eventos],
            spacing=12,
        )

    def leer_ajustes(self) -> AjustesVentana:
        return AjustesVentana(solo_videos=not self.todo.value,
                              borrar_local=self.borrar.value,
                              dry_run=self.simulacion.value)

    def mostrar_error(self, error: ErrorDeUso) -> None:
        self.resultado.value = "\n".join([t(error.clave, **error.datos),
                                          *(t(pista) for pista in error.pistas)])
        self.resultado.color = ft.Colors.RED

    def dibujar(self, estado, forzar: bool = False) -> None:
        """Redibuja el progreso, con un límite de frecuencia para no saturar la ventana."""
        ahora = time.monotonic()
        if not forzar and ahora - self.ultimo_dibujo < INTERVALO_REDIBUJO:
            return
        self.ultimo_dibujo = ahora
        self.texto_total.value = (f"{t('progress_total_label')}  "
                                  f"{estado.completados}/{estado.total_archivos}")
        self.barra_total.value = fraccion_total(estado)
        self.filas.controls = [
            ft.Row([ft.Text(tarea.nombre[:30], width=240),
                    ft.ProgressBar(value=tarea.porcentaje / 100, width=300),
                    ft.Text(f"{tarea.porcentaje:.0f}%")])
            for tarea in estado.archivos.values()
        ]
        self.page.update()

    def agregar_evento(self, nivel: str, texto: str) -> None:
        color = (ft.Colors.RED if nivel in ("ERROR", "CRITICAL")
                 else ft.Colors.ORANGE if nivel == "WARNING" else None)
        self.eventos.controls.append(ft.Text(texto, size=12, color=color))
        del self.eventos.controls[:-MAX_EVENTOS]
        self.page.update()

    async def confirmar_borrado(self) -> bool:
        decision = asyncio.get_running_loop().create_future()

        def decidir(valor: bool):
            def al_pulsar(_evento):
                self.page.pop_dialog()
                if not decision.done():
                    decision.set_result(valor)
            return al_pulsar

        self.page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text(t("gui_confirm_borrar_title")),
            content=ft.Text(t("gui_confirm_borrar_body")),
            actions=[
                ft.TextButton(content=ft.Text(t("gui_btn_cancelar")), on_click=decidir(False)),
                ft.Button(content=ft.Text(t("gui_btn_confirmar_borrar")), on_click=decidir(True)),
            ],
        ))
        return await decision

    async def al_elegir(self, _evento):
        ruta = await self.selector.get_directory_path(dialog_title=t("gui_label_carpeta"))
        if ruta:
            self.carpeta.value = ruta
            self.page.update()

    def al_revisar(self, _evento):
        try:
            solicitud = crear_solicitud(self.config, self.carpeta.value or "", self.leer_ajustes())
        except ErrorDeUso as e:
            self.mostrar_error(e)
        else:
            archivos, pendientes = buscar_pendientes(
                solicitud.carpeta, solicitud.solo_videos, cargar_registro())
            self.resultado.value = (f"{t('log_found_files', n=len(archivos))}\n"
                                    f"{t('log_pending_files', n=len(pendientes))}")
            self.resultado.color = None
        self.page.update()

    async def al_subir(self, _evento):
        ajustes = self.leer_ajustes()
        try:
            solicitud = crear_solicitud(self.config, self.carpeta.value or "", ajustes)
        except ErrorDeUso as e:
            self.mostrar_error(e)
            self.page.update()
            return
        if necesita_confirmacion(ajustes) and not await self.confirmar_borrado():
            return
        await self._ejecutar(solicitud)

    async def _ejecutar(self, solicitud) -> None:
        self.resultado.value = ""
        self.eventos.controls.clear()
        self.boton_subir.disabled = True
        self.page.update()
        reporte = ReporteEstado(self.dibujar)
        manejador = ManejadorEventos(self.agregar_evento)
        log.addHandler(manejador)
        try:
            login = PuenteLogin(partial(pedir_dato_login, self.page)).callbacks()
            await ejecutar_servicio(solicitud, reporte, login)
        except ErrorDeUso as e:
            self.mostrar_error(e)
        except Exception as e:  # noqa: BLE001 - se informa en la ventana en vez de cerrarla
            self.resultado.value = str(e)
            self.resultado.color = ft.Colors.RED
        finally:
            log.removeHandler(manejador)
            self.boton_subir.disabled = False
            self.dibujar(reporte.estado, forzar=True)

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

    subida = PantallaSubida(config, page).vista
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
