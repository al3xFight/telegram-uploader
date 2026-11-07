import sys
from pathlib import Path

# Permite "import subir_a_telegram" desde la carpeta tests/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))