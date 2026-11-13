"""El servicio ejecuta el flujo completo sin depender de la consola."""
import asyncio

from test_flujo_completo import ClienteFalso, _preparar

from telegram_uploader import servicio, subida
from telegram_uploader.progreso import ReporteProgreso
from telegram_uploader.servicio import CallbacksLogin, Solicitud


def _solicitud(carpeta):
    return Solicitud(api_id=1, api_hash="hash", canal="@canal", carpeta=carpeta,
                     solo_videos=False,
                     opciones=subida.OpcionesSubida(pausa_min=0, pausa_max=0))


def test_servicio_sube_y_devuelve_el_resultado(tmp_path, monkeypatch):
    archivo = _preparar(tmp_path, monkeypatch)

    resultado = asyncio.run(servicio.ejecutar_servicio(
        _solicitud(archivo.parent), ReporteProgreso()))

    assert (resultado.encontrados, resultado.pendientes, resultado.subidos) == (1, 1, 1)
    assert ClienteFalso.subidas == ["doc.txt"]


def test_servicio_pasa_las_funciones_de_login_al_cliente(tmp_path, monkeypatch):
    class ClienteConLogin(ClienteFalso):
        recibido = None

        async def start(self, **kwargs):
            ClienteConLogin.recibido = kwargs

    archivo = _preparar(tmp_path, monkeypatch)
    monkeypatch.setattr(subida, "TelegramClient", ClienteConLogin)
    telefono, codigo, contrasena = (lambda: "1"), (lambda: "2"), (lambda: "3")
    login = CallbacksLogin(telefono=telefono, codigo=codigo, contrasena=contrasena)

    asyncio.run(servicio.ejecutar_servicio(
        _solicitud(archivo.parent), ReporteProgreso(), login))

    assert ClienteConLogin.recibido == {
        "phone": telefono, "code_callback": codigo, "password": contrasena}