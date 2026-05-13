#!/usr/bin/env bash
# =============================================================================
# AgentKobi — Backend entrypoint
# =============================================================================
# 1) Postgres hazır olana kadar bekle (compose healthcheck zaten yapıyor ama
#    "double belt") 
# 2) Alembic migration'larını uygula
# 3) AUTO_SEED=1 ise (default) ve DB boşsa CSV verilerini yükle
# 4) Uvicorn'u başlat
# =============================================================================
set -e

echo "================================================================"
echo "  AgentKobi backend başlatılıyor..."
echo "================================================================"

# -----------------------------------------------------------------------------
# 1) Postgres'i bekle
# -----------------------------------------------------------------------------
echo ">> Postgres'e bağlanılıyor..."
python - <<'PYEOF'
import os
import sys
import time
import socket
from urllib.parse import urlparse

url = os.environ.get("DATABASE_URL", "postgresql+asyncpg://agentkobi:changeme@postgres:5432/agentkobi")
# asyncpg/psycopg2 prefix'lerini kaldır
clean = url.split("://", 1)[1] if "://" in url else url
clean = "postgresql://" + clean
parsed = urlparse(clean)
host = parsed.hostname or "postgres"
port = parsed.port or 5432

for i in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"   Postgres {host}:{port} ulaşılabilir.")
            sys.exit(0)
    except OSError:
        print(f"   ({i+1}/60) Postgres henüz hazır değil, 1s bekleniyor...")
        time.sleep(1)
print("   HATA: Postgres'e bağlanılamadı.", file=sys.stderr)
sys.exit(1)
PYEOF

# -----------------------------------------------------------------------------
# 2) Alembic migration
# -----------------------------------------------------------------------------
echo ""
echo ">> Alembic migration'lar uygulanıyor..."
alembic upgrade head || {
    echo "   UYARI: Alembic migration başarısız oldu. Devam ediliyor..."
}

# -----------------------------------------------------------------------------
# 3) Seed (sadece DB boşsa)
# -----------------------------------------------------------------------------
if [ "${AUTO_SEED:-1}" = "1" ]; then
    echo ""
    echo ">> Seed kontrolü yapılıyor..."

    NEEDS_SEED=$(python - <<'PYEOF'
import asyncio
import sys
from sqlalchemy import select, func
from app.core.db import AsyncSessionLocal
from app.models.orm import Order

async def check():
    async with AsyncSessionLocal() as db:
        count = (await db.execute(select(func.count()).select_from(Order))).scalar_one()
        return count

try:
    n = asyncio.run(check())
    print("YES" if n == 0 else "NO")
except Exception as e:
    print(f"   Seed kontrolünde hata: {e}", file=sys.stderr)
    print("YES")  # hata durumunda güvenli taraf: seed yapmayı dene
PYEOF
)

    if echo "$NEEDS_SEED" | tail -n 1 | grep -q "YES"; then
        echo "   DB boş — seed başlatılıyor..."
        python -m app.db.seed.seed_from_csv || {
            echo "   UYARI: Seed başarısız oldu. API yine de başlatılacak."
        }
    else
        echo "   DB zaten dolu, seed atlanıyor."
    fi
else
    echo ">> AUTO_SEED=0, seed atlanıyor."
fi

# -----------------------------------------------------------------------------
# 4) Uvicorn başlat
# -----------------------------------------------------------------------------
echo ""
echo "================================================================"
echo "  Uvicorn başlatılıyor (http://0.0.0.0:8000)"
echo "================================================================"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
