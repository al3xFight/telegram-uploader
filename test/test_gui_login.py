"""El puente de inicio de sesión de la GUI: pide los datos a la pantalla y no los conserva."""
import asyncio
import logging

from test_flujo_completo import ClienteFalso, _preparar

from telegram_uploader import servicio, subida
from telegram_uploader.gui_modelo import PuenteLogin
from telegram_uploader.progreso import ReporteProgreso
from telegram_uploader.servicio import Solicitud

RESPUESTAS = {"telefono": "+58000", "codigo": "12345", "contrasena": "secreto-2fa"}


async def _pedir(clave):
    return RESPUESTAS[clave]


def test_el_puente_pide_cada_dato_a_la_pantalla_y_lo_devuelve():
    pedidos = []

    async def pedir(clave):
        pedidos.append(clave)
        return RESPUESTAS[clave]

    login = PuenteLogin(pedir).callbacks()

    assert asyncio.run(login.telefono()) == "+58000"
    assert asyncio.run(login.codigo()) == "12345"
    assert asyncio.run(login.contrasena()) == "secreto-2fa"
    assert pedidos == ["telefono", "codigo", "contrasena"]


def test_el_puente_no_conserva_los_datos_sensibles():
    puente = PuenteLogin(_pedir)
    login = puente.callbacks()
    asyncio.run(login.codigo())
    asyncio.run(login.contrasena())

    guardado = repr(vars(puente)) + repr(vars(login))
    assert "12345" not in guardado
    assert "secreto-2fa" not in guardado


def test_el_puente_no_escribe_los_datos_en_el_registro(caplog):
    caplog.set_level(logging.DEBUG)
    login = PuenteLogin(_pedir).callbacks()
    asyncio.run(login.codigo())
    asyncio.run(login.contrasena())

    assert "12345" not in caplog.text
    assert "secreto-2fa" not in caplog.text


def test_el_servicio_recibe_los_datos_del_puente_al_iniciar_sesion(tmp_path, monkeypatch):
    class ClienteConLogin(ClienteFalso):
        datos = None

        async def start(self, **kwargs):
            ClienteConLogin.datos = (await kwargs["phone"](),
                                     await kwargs["code_callback"](),
                                     await kwargs["password"]())

    archivo = _preparar(tmp_path, monkeypatch)
    monkeypatch.setattr(subida, "TelegramClient", ClienteConLogin)
    solicitud = Solicitud(1, "hash", "@canal", archivo.parent, False,
                          subida.OpcionesSubida(pausa_min=0, pausa_max=0))

    asyncio.run(servicio.ejecutar_servicio(
        solicitud, ReporteProgreso(), PuenteLogin(_pedir).callbacks()))

    assert ClienteConLogin.datos == ("+58000", "12345", "secreto-2fa")