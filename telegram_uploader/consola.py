"""Consola y registro de eventos compartidos por todo el programa."""
import logging

from rich.console import Console
from rich.logging import RichHandler

console = Console()

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
)
log = logging.getLogger("telegram_uploader")
