"""Armado de la solicitud de subida desde la pantalla, sin Flet."""
import pytest

from telegram_uploader.errores import ErrorDeUso
from telegram_uploader.gui_modelo import AjustesVentana, crear_solicitud, necesita_confirmacion


def _config(**cambios):
    datos = dict(api_id=123, api_hash="hash", canal="@canal",
                 chunks_paralelos=8, pausa_min=1.0, pausa_max=2.0)
    datos.update(cambios)
    return datos


def test_solicitud_valida_combina_la_configuracion_y_los_ajustes(tmp_path):
    ajustes = AjustesVentana(borrar_local=True, solo_videos=False)

    solicitud = crear_solicitud(_config(), str(tmp_path), ajustes)

    assert (solicitud.api_id, solicitud.api_hash, solicitud.canal) == (123, "hash", "@canal")
    assert solicitud.carpeta == tmp_path
    assert solicitud.solo_videos is False
    assert solicitud.opciones.borrar_local is True
    assert solicitud.opciones.chunks_paralelos == 8
    assert solicitud.opciones.pausa_min == 1.0


def test_los_ajustes_de_la_ventana_tienen_prioridad_sobre_la_configuracion(tmp_path):
    ajustes = AjustesVentana(chunks_paralelos=3, dry_run=True)

    solicitud = crear_solicitud(_config(), str(tmp_path), ajustes)

    assert solicitud.opciones.chunks_paralelos == 3
    assert solicitud.opciones.dry_run is True


def test_configuracion_incompleta_lanza_error_de_uso(tmp_path):
    with pytest.raises(ErrorDeUso) as error:
        crear_solicitud(_config(api_id=""), str(tmp_path), AjustesVentana())
    assert error.value.clave == "gui_err_config_incompleta"


def test_sin_carpeta_lanza_error_de_uso():
    with pytest.raises(ErrorDeUso) as error:
        crear_solicitud(_config(), "   ", AjustesVentana())
    assert error.value.clave == "gui_err_sin_carpeta"


def test_carpeta_inexistente_lanza_error_de_uso(tmp_path):
    with pytest.raises(ErrorDeUso) as error:
        crear_solicitud(_config(), str(tmp_path / "no_existe"), AjustesVentana())
    assert error.value.clave == "err_carpeta_not_found"


def test_ajustes_invalidos_reutilizan_las_validaciones_de_la_consola(tmp_path):
    with pytest.raises(ErrorDeUso) as error:
        crear_solicitud(_config(), str(tmp_path), AjustesVentana(chunks_paralelos=0))
    assert error.value.clave == "err_chunks_min1"


def test_borrar_local_pide_confirmacion_salvo_en_simulacion():
    assert necesita_confirmacion(AjustesVentana(borrar_local=True)) is True
    assert necesita_confirmacion(AjustesVentana(borrar_local=True, dry_run=True)) is False
    assert necesita_confirmacion(AjustesVentana()) is False