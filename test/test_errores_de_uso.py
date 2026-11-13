"""La lógica reporta los errores de uso con excepciones, no con sys.exit ni consola."""
import asyncio
from types import SimpleNamespace

import pytest

from telegram_uploader import cli, subida
from telegram_uploader.errores import ErrorDeUso


def _args(**cambios):
    datos = dict(chunks_paralelos=None, pausa_min=None, pausa_max=None,
                 borrar_local=False, dry_run=False, paralelo=1)
    datos.update(cambios)
    return SimpleNamespace(**datos)


def _config(**cambios):
    datos = dict(api_id=123, api_hash="abc", canal="@canal",
                 chunks_paralelos=4, pausa_min=1.0, pausa_max=2.0)
    datos.update(cambios)
    return datos


def test_ajustes_validos_no_lanzan_error():
    api_id, api_hash, canal, opciones = cli.resolver_ajustes(_args(), _config())
    assert api_id == 123
    assert opciones.chunks_paralelos == 4


def test_api_id_no_numerico_lanza_error_de_uso():
    with pytest.raises(ErrorDeUso) as error:
        cli.resolver_ajustes(_args(), _config(api_id="abc"))
    assert error.value.clave == "err_api_id_invalid_saved"


def test_chunks_menor_que_1_lanza_error_de_uso():
    with pytest.raises(ErrorDeUso) as error:
        cli.resolver_ajustes(_args(chunks_paralelos=0), _config())
    assert error.value.clave == "err_chunks_min1"


def test_pausa_negativa_lanza_error_de_uso():
    with pytest.raises(ErrorDeUso) as error:
        cli.resolver_ajustes(_args(pausa_min=-1.0), _config())
    assert error.value.clave == "err_pausas_negative"

def test_carpeta_inexistente_lanza_error_de_uso(tmp_path):
    with pytest.raises(ErrorDeUso) as error:
        cli.validar_carpeta(str(tmp_path / "no_existe"))
    assert error.value.clave == "err_carpeta_not_found"


def test_carpeta_existente_devuelve_su_ruta(tmp_path):
    assert cli.validar_carpeta(str(tmp_path)) == tmp_path


def test_canal_inexistente_lanza_error_de_uso_con_pistas():
    class ClienteSinCanal:
        async def get_entity(self, canal):
            raise ValueError("canal no encontrado")

    with pytest.raises(ErrorDeUso) as error:
        asyncio.run(subida.resolver_destino(ClienteSinCanal(), "@canal"))
    assert error.value.clave == "err_channel_not_found"
    assert error.value.pistas == ("hint_check_channel", "hint_fix_config")