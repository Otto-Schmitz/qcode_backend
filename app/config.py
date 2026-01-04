import os
from pathlib import Path

# Diretório base do backend
BASE_DIR = Path(__file__).resolve().parent.parent

# Diretório onde as imagens de QR Code serão gravadas e servidas
STORAGE_DIR = BASE_DIR / "storage"

# URL pública base (para construir links de tracking). Ajuste em produção.
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")

