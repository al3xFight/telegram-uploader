"""Errores de uso del programa, independientes de cualquier interfaz.

La lógica los lanza; cada interfaz (consola o gráfica) decide cómo mostrarlos.
Llevan la clave del texto y sus datos, no un mensaje ya formateado, para que
cada interfaz lo traduzca con su propio idioma.
"""


class ErrorDeUso(Exception):
    """Entrada o configuración inválida que impide continuar."""

    def __init__(self, clave: str, **datos):
        super().__init__(clave)
        self.clave = clave
        self.datos = datos
