"""Lógica de la interfaz gráfica que no necesita pantalla ni Flet."""
from telegram_uploader.gui_modelo import EstadoProgreso, ReporteEstado, fraccion_total


def test_total_y_avance_global_avisan_a_la_pantalla():
    avisos = []
    reporte = ReporteEstado(avisos.append)

    reporte.iniciar_total(3)
    reporte.avanzar_total()

    assert reporte.estado.total_archivos == 3
    assert reporte.estado.completados == 1
    assert len(avisos) == 2  # un aviso por cada cambio


def test_archivo_en_curso_avanza_y_desaparece_al_terminar():
    reporte = ReporteEstado(lambda estado: None)

    tarea = reporte.iniciar_archivo("a.mp4", 1000)
    reporte.actualizar_archivo(tarea, 250)

    assert reporte.estado.archivos[tarea].nombre == "a.mp4"
    assert reporte.estado.archivos[tarea].hechos == 250
    assert reporte.estado.archivos[tarea].porcentaje == 25.0

    reporte.terminar_archivo(tarea)
    assert tarea not in reporte.estado.archivos


def test_cada_archivo_recibe_un_identificador_distinto():
    reporte = ReporteEstado(lambda estado: None)
    primero = reporte.iniciar_archivo("a.mp4", 10)
    segundo = reporte.iniciar_archivo("b.mp4", 10)
    assert primero != segundo
    assert len(reporte.estado.archivos) == 2


def test_porcentaje_de_un_archivo_vacio_es_cero():
    reporte = ReporteEstado(lambda estado: None)
    tarea = reporte.iniciar_archivo("vacio.txt", 0)
    assert reporte.estado.archivos[tarea].porcentaje == 0.0

def test_fraccion_total_es_el_avance_entre_cero_y_uno():
    assert fraccion_total(EstadoProgreso(total_archivos=4, completados=1)) == 0.25
    assert fraccion_total(EstadoProgreso()) == 0.0  # sin total no se divide entre cero
    assert fraccion_total(EstadoProgreso(total_archivos=2, completados=5)) == 1.0