"""Telegram Uploader: sube videos y archivos grandes a un canal privado de Telegram con tu propia cuenta."""
import sys

try:
    import rich  # noqa: F401
    import telethon  # noqa: F401
except ImportError as e:
    print(f"Falta instalar dependencias / Missing dependency ({e.name}):\n    pip install -r requirements.txt")
    sys.exit(1)
