"""Reanudación de subidas por fragmentos dentro de una misma ejecución."""
import asyncio
from types import SimpleNamespace

import pytest
from telethon.errors import FilePartMissingError

from telegram_uploader import subida

TAM_PARTE = 512 * 1024


class ClienteFalso:
    def __init__(self):
        self.partes = []

    async def __call__(self, peticion):
        self.partes.append(peticion.file_part)
        return True


class ClienteRegistrador(ClienteFalso):
    """Además de las partes, guarda el file_id y los bytes de cada una."""

    def __init__(self):
        super().__init__()
        self.ids = set()
        self.datos = {}

    async def __call__(self, peticion):
        self.ids.add(peticion.file_id)
        self.datos[peticion.file_part] = peticion.bytes
        return await super().__call__(peticion)


class ClienteQueFallaUnaVez(ClienteRegistrador):
    """Falla una sola vez al subir la parte indicada (corte de red simulado)."""

    def __init__(self, parte_que_falla):
        super().__init__()
        self.parte_que_falla = parte_que_falla
        self.ya_fallo = False

    async def __call__(self, peticion):
        if peticion.file_part == self.parte_que_falla and not self.ya_fallo:
            self.ya_fallo = True
            raise ConnectionError("corte simulado")
        return await super().__call__(peticion)


class ClienteLento(ClienteFalso):
    """La parte 2 falla enseguida; las demás tardan un poco en completarse."""

    async def __call__(self, peticion):
        if peticion.file_part == 2:
            raise ConnectionError("corte simulado")
        await asyncio.sleep(0.05)
        return await super().__call__(peticion)


class ClienteQueFallaAlEnviar(ClienteRegistrador):
    """La primera llamada a send_file lanza el error indicado."""

    def __init__(self, error):
        super().__init__()
        self.error = error
        self.envios = 0

    async def send_file(self, destino, file=None, **kwargs):
        self.envios += 1
        if self.envios == 1:
            raise self.error

class RegistroFalso:
    """Reemplaza al log para comprobar qué mensajes ve el usuario."""

    def __init__(self):
        self.mensajes = []

    def info(self, mensaje):
        self.mensajes.append(mensaje)

    warning = info
    error = info

async def _sin_espera(_segundos):
    return None


def _archivo_grande(tmp_path):
    ruta = tmp_path / "grande.bin"
    ruta.write_bytes(b"\0" * (11 * 1024 * 1024))  # 22 partes de 512 KB
    return ruta


def _enviar(cliente, ruta):
    ctx = SimpleNamespace(client=cliente, destino="destino")
    return asyncio.run(subida.enviar_con_reintentos(
        ctx, subida.OpcionesSubida(), ruta, subida.MetadatosArchivo(), None))


def test_reintento_no_reenvia_las_partes_ya_subidas(tmp_path):
    ruta = _archivo_grande(tmp_path)
    cliente = ClienteQueFallaUnaVez(parte_que_falla=10)
    estado = subida.EstadoSubida()
    avances = []

    with pytest.raises(ConnectionError):
        asyncio.run(subida.upload_file_paralelo(cliente, ruta, 2, estado=estado))
    ya_subidas = set(estado.completadas)
    assert ya_subidas
    assert 10 not in ya_subidas

    cliente.partes.clear()
    asyncio.run(subida.upload_file_paralelo(
        cliente, ruta, 2, lambda actual, total: avances.append(actual), estado=estado))

    assert not set(cliente.partes) & ya_subidas  # no repite lo ya subido
    assert estado.completadas == set(range(22))
    assert len(cliente.ids) == 1  # mismo file_id en los dos intentos
    assert avances[0] == len(ya_subidas) * TAM_PARTE  # la barra arranca en lo ya subido
    assert max(avances) == ruta.stat().st_size


def test_si_una_parte_falla_no_quedan_partes_en_segundo_plano(tmp_path):
    ruta = _archivo_grande(tmp_path)
    cliente = ClienteLento()

    async def escenario():
        with pytest.raises(ConnectionError):
            await subida.upload_file_paralelo(cliente, ruta, 4)
        await asyncio.sleep(0.2)
        return list(cliente.partes)

    assert asyncio.run(escenario()) == []


def test_error_al_enviar_reutiliza_las_partes_ya_subidas(tmp_path, monkeypatch):
    monkeypatch.setattr(subida.asyncio, "sleep", _sin_espera)
    ruta = _archivo_grande(tmp_path)
    cliente = ClienteQueFallaAlEnviar(ConnectionError("corte simulado"))

    assert _enviar(cliente, ruta) is True

    assert cliente.envios == 2
    assert len(cliente.ids) == 1  # no se volvió a subir con otro file_id
    assert len(cliente.partes) == 22  # cada parte se subió una sola vez


def test_partes_ausentes_en_telegram_reinician_con_un_file_id_nuevo(tmp_path, monkeypatch):
    monkeypatch.setattr(subida.asyncio, "sleep", _sin_espera)
    registro = RegistroFalso()
    monkeypatch.setattr(subida, "log", registro)
    ruta = _archivo_grande(tmp_path)
    cliente = ClienteQueFallaAlEnviar(FilePartMissingError(None, capture=3))

    assert _enviar(cliente, ruta) is True

    assert cliente.envios == 2
    assert len(cliente.ids) == 2  # las partes caducaron: se empezó de cero
    assert len(cliente.partes) == 44
    assert subida.t("warn_parts_expired", nombre=ruta.name, parte=3) in registro.mensajes


def test_al_reanudar_se_avisa_cuantos_fragmentos_ya_estaban_subidos(tmp_path, monkeypatch):
    registro = RegistroFalso()
    monkeypatch.setattr(subida, "log", registro)
    ruta = _archivo_grande(tmp_path)
    cliente = ClienteQueFallaUnaVez(parte_que_falla=10)
    estado = subida.EstadoSubida()

    with pytest.raises(ConnectionError):
        asyncio.run(subida.upload_file_paralelo(cliente, ruta, 2, estado=estado))
    hechas = len(estado.completadas)
    assert registro.mensajes == []  # en el primer intento no hay nada que reanudar

    asyncio.run(subida.upload_file_paralelo(cliente, ruta, 2, estado=estado))

    esperado = subida.t("log_resuming", nombre=ruta.name, hechas=hechas, total=22)
    assert esperado in registro.mensajes


def test_partes_enviadas_reproducen_el_archivo_original(tmp_path):
    ruta = tmp_path / "datos.bin"
    contenido = bytes(range(256)) * (11 * 1024 * 4)  # 11 MB no uniformes
    ruta.write_bytes(contenido)
    cliente = ClienteQueFallaUnaVez(parte_que_falla=10)
    estado = subida.EstadoSubida()

    with pytest.raises(ConnectionError):
        asyncio.run(subida.upload_file_paralelo(cliente, ruta, 2, estado=estado))
    asyncio.run(subida.upload_file_paralelo(cliente, ruta, 2, estado=estado))

    reconstruido = b"".join(cliente.datos[i] for i in sorted(cliente.datos))
    assert reconstruido == contenido
