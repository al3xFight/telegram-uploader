"""Validación del formulario de configuración de la GUI, sin pantalla."""
import pytest

from telegram_uploader.errores import ErrorDeUso
from telegram_uploader.gui_modelo import validar_formulario


def _campos(**cambios):
    datos = dict(api_id="123", api_hash=" abc ", canal="@canal",
                 chunks_paralelos="8", pausa_min="1.5", pausa_max="3")
    datos.update(cambios)
    return datos


def test_formulario_valido_devuelve_cada_valor_con_su_tipo():
    config = validar_formulario(_campos())
    assert config == {"api_id": 123, "api_hash": "abc", "canal": "@canal",
                      "chunks_paralelos": 8, "pausa_min": 1.5, "pausa_max": 3.0}


@pytest.mark.parametrize("campo, valor, clave", [
    ("api_id", "abc", "err_api_id_numeric"),
    ("api_id", "", "err_api_id_numeric"),
    ("api_hash", "   ", "err_required"),
    ("canal", "", "err_required"),
    ("chunks_paralelos", "x", "err_invalid_number"),
    ("chunks_paralelos", "0", "err_chunks_min1"),
    ("pausa_min", "x", "err_invalid_number"),
    ("pausa_max", "-1", "err_pausas_negative"),
])
def test_formulario_invalido_lanza_error_de_uso_con_el_campo(campo, valor, clave):
    with pytest.raises(ErrorDeUso) as error:
        validar_formulario(_campos(**{campo: valor}))
    assert error.value.clave == clave
    assert error.value.datos["campo"] == campo


def test_el_error_no_incluye_el_api_hash():
    with pytest.raises(ErrorDeUso) as error:
        validar_formulario(_campos(api_hash="hash-secreto", api_id="abc"))
    assert "hash-secreto" not in repr(error.value.datos)