"""Prueba de la subida por fragmentos en paralelo (archivos > 10 MB)."""
import asyncio

from telegram_uploader import subida


class ClienteFalso:
    def __init__(self):
        self.partes = []

    async def __call__(self, peticion):
        self.partes.append(peticion.file_part)
        return True


def _archivo_grande(tmp_path):
    ruta = tmp_path / "grande.bin"
    ruta.write_bytes(b"\0" * (11 * 1024 * 1024))  # > UMBRAL_ARCHIVO_GRANDE
    return ruta


def test_subida_paralela_envia_todas_las_partes_y_reporta_progreso(tmp_path):
    ruta = _archivo_grande(tmp_path)
    cliente = ClienteFalso()
    avances = []

    asyncio.run(subida.upload_file_paralelo(
        cliente, ruta, 4, lambda actual, total: avances.append(actual)))

    assert sorted(cliente.partes) == list(range(22))  # 11 MB / 512 KB
    assert max(avances) == ruta.stat().st_size


def test_subida_paralela_acepta_callback_asincrono(tmp_path):
    ruta = _archivo_grande(tmp_path)
    cliente = ClienteFalso()
    avances = []

    async def callback(actual, total):
        avances.append(actual)

    asyncio.run(subida.upload_file_paralelo(cliente, ruta, 4, callback))

    assert max(avances) == ruta.stat().st_size

def test_tamano_archivo(tmp_path):
    archivo = tmp_path / "datos.bin"
    archivo.write_bytes(b"abc")
    assert subida.tamano_archivo(archivo) == 3


def test_leer_parte_devuelve_el_fragmento(tmp_path):
    archivo = tmp_path / "datos.bin"
    archivo.write_bytes(b"0123456789")
    assert subida.leer_parte(archivo, 3, 4) == b"3456"