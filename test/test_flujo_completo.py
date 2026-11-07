"""Prueba de integración del flujo de main() con un cliente de Telegram FALSO.

No se conecta a Telegram: se reemplaza TelegramClient por una clase simulada.
"""
import asyncio
import json

import subir_a_telegram as app


class ClienteFalso:
    """Imita solo lo que usa el programa."""

    subidas = []

    def __init__(self, *args, **kwargs):
        pass

    async def start(self):
        return self

    async def get_entity(self, canal):
        return "destino-falso"

    async def upload_file(self, ruta, **kwargs):
        return f"handle:{ruta}"

    async def send_file(self, destino, file=None, **kwargs):
        ClienteFalso.subidas.append(kwargs.get("caption"))

    async def disconnect(self):
        pass


def _preparar(tmp_path, monkeypatch, *flags):
    carpeta = tmp_path / "entrada"
    carpeta.mkdir()
    archivo = carpeta / "doc.txt"
    archivo.write_text("contenido de prueba")

    monkeypatch.setattr(app, "TelegramClient", ClienteFalso)
    monkeypatch.setattr(app, "CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.setattr(app, "REGISTRO_SUBIDOS", str(tmp_path / "subidos.json"))
    monkeypatch.setenv("TG_API_ID", "123")
    monkeypatch.setenv("TG_API_HASH", "hash-de-prueba")
    monkeypatch.setenv("TG_CANAL", "@canal")
    monkeypatch.setattr(
        "sys.argv",
        ["subir_a_telegram.py", "--lang", "es", "--carpeta", str(carpeta),
         "--todo", "--pausa-min", "0", "--pausa-max", "0", *flags],
    )
    ClienteFalso.subidas = []
    return archivo


def test_subida_normal_registra_el_archivo(tmp_path, monkeypatch):
    archivo = _preparar(tmp_path, monkeypatch)

    asyncio.run(app.main())

    assert ClienteFalso.subidas == ["doc.txt"]
    registro = json.loads((tmp_path / "subidos.json").read_text(encoding="utf-8"))
    assert len(registro) == 1
    assert archivo.exists()  # sin --borrar-local no se elimina


def test_dry_run_no_sube_ni_registra(tmp_path, monkeypatch):
    _preparar(tmp_path, monkeypatch, "--dry-run")

    asyncio.run(app.main())

    assert ClienteFalso.subidas == []
    assert not (tmp_path / "subidos.json").exists()


def test_borrar_local_elimina_y_registra_la_subida(tmp_path, monkeypatch):
    """DEFECTO CONOCIDO: esta prueba debe FALLAR en el código original.

    Con --borrar-local el archivo se elimina y luego main() intenta calcular
    su clave con ruta.stat(), lo que lanza FileNotFoundError.
    """
    archivo = _preparar(tmp_path, monkeypatch, "--borrar-local")

    asyncio.run(app.main())

    assert ClienteFalso.subidas == ["doc.txt"]
    assert not archivo.exists()  # se eliminó localmente
    registro = json.loads((tmp_path / "subidos.json").read_text(encoding="utf-8"))
    assert len(registro) == 1  # y quedó registrado como subido

def test_fallo_inesperado_no_borra_el_archivo_ni_lo_registra(tmp_path, monkeypatch):
    """Si la subida falla, --borrar-local NUNCA debe eliminar el archivo."""

    class ClienteQueFalla(ClienteFalso):
        async def send_file(self, destino, file=None, **kwargs):
            raise ValueError("fallo simulado")

    archivo = _preparar(tmp_path, monkeypatch, "--borrar-local")
    monkeypatch.setattr(app, "TelegramClient", ClienteQueFalla)

    asyncio.run(app.main())

    assert archivo.exists()  # se conserva
    assert not (tmp_path / "subidos.json").exists()  # no se registra