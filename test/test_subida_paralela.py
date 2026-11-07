"""Prueba de la subida por fragmentos en paralelo (archivos > 10 MB)."""
import asyncio

import subir_a_telegram as app


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

    asyncio.run(app.upload_file_paralelo(
        cliente, ruta, 4, lambda actual, total: avances.append(actual)))

    assert sorted(cliente.partes) == list(range(22))  # 11 MB / 512 KB
    assert max(avances) == ruta.stat().st_size


def test_subida_paralela_acepta_callback_asincrono(tmp_path):
    ruta = _archivo_grande(tmp_path)
    cliente = ClienteFalso()
    avances = []

    async def callback(actual, total):
        avances.append(actual)

    asyncio.run(app.upload_file_paralelo(cliente, ruta, 4, callback))

    assert max(avances) == ruta.stat().st_size