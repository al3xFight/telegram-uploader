"""Salidas de error y reanudación de main(), verificadas desde el comportamiento externo."""
import asyncio

import pytest
from test_flujo_completo import ClienteFalso, _preparar

import subir_a_telegram as app


def test_carpeta_inexistente_termina_con_error(tmp_path, monkeypatch):
    _preparar(tmp_path, monkeypatch)
    monkeypatch.setattr("sys.argv", ["subir_a_telegram.py", "--lang", "es",
                                     "--carpeta", str(tmp_path / "no_existe")])
    with pytest.raises(SystemExit) as salida:
        asyncio.run(app.main())
    assert salida.value.code == 1


def test_chunks_paralelos_menor_que_1_termina_con_error(tmp_path, monkeypatch):
    _preparar(tmp_path, monkeypatch, "--chunks-paralelos", "0")
    with pytest.raises(SystemExit) as salida:
        asyncio.run(app.main())
    assert salida.value.code == 1


def test_api_id_no_numerico_termina_con_error(tmp_path, monkeypatch):
    _preparar(tmp_path, monkeypatch)
    monkeypatch.setenv("TG_API_ID", "abc")
    with pytest.raises(SystemExit) as salida:
        asyncio.run(app.main())
    assert salida.value.code == 1


def test_canal_inexistente_termina_con_error_y_desconecta(tmp_path, monkeypatch):
    class ClienteSinCanal(ClienteFalso):
        desconectado = False

        async def get_entity(self, canal):
            raise ValueError("canal no encontrado")

        async def disconnect(self):
            ClienteSinCanal.desconectado = True

    _preparar(tmp_path, monkeypatch)
    monkeypatch.setattr(app, "TelegramClient", ClienteSinCanal)
    with pytest.raises(SystemExit) as salida:
        asyncio.run(app.main())
    assert salida.value.code == 1
    assert ClienteSinCanal.desconectado


def test_segunda_ejecucion_no_vuelve_a_subir(tmp_path, monkeypatch):
    _preparar(tmp_path, monkeypatch)
    asyncio.run(app.main())
    assert ClienteFalso.subidas == ["doc.txt"]

    asyncio.run(app.main())  # mismo archivo, ya registrado
    assert ClienteFalso.subidas == ["doc.txt"]  # no se repite