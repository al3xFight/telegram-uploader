"""Interfaz para reportar el avance de las subidas, independiente de la interfaz de usuario.

La lógica llama a estos métodos; la consola, la GUI o las pruebas deciden qué hacer con ellos.
Esta clase no hace nada por defecto, así que sirve también como reportero silencioso.
"""


class ReporteProgreso:
    """Reportero de avance: no hace nada. Las interfaces lo sobrescriben."""

    def __enter__(self):
        return self

    def __exit__(self, *excepcion):
        return False

    def iniciar_total(self, total: int) -> None:
        """Se llama una vez, con la cantidad de archivos a subir."""

    def iniciar_archivo(self, nombre: str, total_bytes: int):
        """Empieza un archivo. Devuelve un identificador para las llamadas siguientes."""

    def actualizar_archivo(self, id_tarea, bytes_hechos: int) -> None:
        """Avance de un archivo, en bytes."""

    def terminar_archivo(self, id_tarea) -> None:
        """El archivo ya no está en curso (terminó o falló)."""

    def avanzar_total(self) -> None:
        """Un archivo más completado."""
