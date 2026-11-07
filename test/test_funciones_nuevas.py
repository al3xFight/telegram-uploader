"""Pruebas directas de las funciones extraídas de main()."""
from types import SimpleNamespace

from telegram_uploader import cli, constantes, i18n, registro


def _args(**kwargs):
    base = dict(chunks_paralelos=None, pausa_min=None, pausa_max=None,
                borrar_local=False, dry_run=False, paralelo=1)
    base.update(kwargs)
    return SimpleNamespace(**base)


def _config():
    return dict(constantes.CONFIG_DEFAULTS, api_id=123, api_hash="h", canal="@c")


def test_resolver_ajustes_intercambia_pausas_invertidas():
    *_, opciones = cli.resolver_ajustes(_args(pausa_min=9.0, pausa_max=2.0), _config())
    assert (opciones.pausa_min, opciones.pausa_max) == (2.0, 9.0)


def test_resolver_ajustes_argumento_pisa_la_configuracion():
    *_, opciones = cli.resolver_ajustes(_args(chunks_paralelos=3, paralelo=2), _config())
    assert opciones.chunks_paralelos == 3
    assert opciones.archivos_simultaneos == 2


def test_buscar_pendientes_excluye_los_ya_registrados(tmp_path):
    nuevo = tmp_path / "nuevo.txt"
    viejo = tmp_path / "viejo.txt"
    nuevo.write_text("a")
    viejo.write_text("b")
    ya_subidos = {registro.clave_archivo(viejo): {"nombre": "viejo.txt"}}

    archivos, pendientes = cli.buscar_pendientes(tmp_path, solo_videos=False, registro=ya_subidos)

    assert len(archivos) == 2
    assert [p.name for p in pendientes] == ["nuevo.txt"]


def test_configurar_idioma_lang_cli_pisa_la_config():
    cli.configurar_idioma({"idioma": "es"}, ["prog", "--lang", "en"])
    assert i18n.traductor.idioma == "en"


def test_configurar_idioma_usa_la_config_guardada():
    cli.configurar_idioma({"idioma": "en"}, ["prog"])
    assert i18n.traductor.idioma == "en"


def test_configurar_idioma_con_help_no_pregunta():
    cli.configurar_idioma({"idioma": ""}, ["prog", "--help"])
    assert i18n.traductor.idioma == "es"
