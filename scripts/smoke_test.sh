#!/usr/bin/env bash
# =============================================================================
# AgentKobi — Smoke Test
# =============================================================================
# docker compose up ile sistem ayağa kalktıktan sonra çalıştır:
#   bash scripts/smoke_test.sh
#
# Tüm REST endpoint'lerini sırayla çağırır ve özet bir rapor basar.
# Demo videosu çekmeden önce her şeyin çalıştığını doğrular.
# =============================================================================
set -u

BASE="${API_BASE:-http://localhost:8000}"
PASS=0
FAIL=0

# Renkler
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check() {
    local name="$1"
    local url="$2"
    local method="${3:-GET}"
    local body="${4:-}"

    printf "  %-40s " "$name"

    local args=(-s -o /tmp/resp.json -w '%{http_code}')
    if [ "$method" = "POST" ]; then
        args+=(-X POST -H 'Content-Type: application/json' -d "$body")
    fi

    local code
    code=$(curl "${args[@]}" "$BASE$url" 2>/dev/null || echo "000")

    if [ "$code" = "200" ]; then
        printf "${GREEN}✓ OK${NC} (HTTP $code)\n"
        PASS=$((PASS + 1))
        return 0
    else
        printf "${RED}✗ FAIL${NC} (HTTP $code)\n"
        if [ -s /tmp/resp.json ]; then
            echo "    └─ response:" 
            head -c 200 /tmp/resp.json | sed 's/^/       /'
            echo
        fi
        FAIL=$((FAIL + 1))
        return 1
    fi
}

echo "================================================================"
echo "  AgentKobi Smoke Test"
echo "  Hedef: $BASE"
echo "================================================================"
echo

# -----------------------------------------------------------------------------
# 1) Health
# -----------------------------------------------------------------------------
echo "[1/3] Health & temel API"
check "GET  /health"                "/health"
check "GET  /api/dashboard/stats"   "/api/dashboard/stats"
echo

# -----------------------------------------------------------------------------
# 2) Veri endpoint'leri
# -----------------------------------------------------------------------------
echo "[2/3] Veri endpoint'leri"
check "GET  /api/orders"            "/api/orders"
check "GET  /api/orders?status=shipped" "/api/orders?status=shipped"
check "GET  /api/products"          "/api/products"
check "GET  /api/products?low_stock=true" "/api/products?low_stock=true"
check "GET  /api/stock/critical"    "/api/stock/critical"
check "GET  /api/customers"         "/api/customers"
check "GET  /api/supplier-drafts"   "/api/supplier-drafts"
echo

# -----------------------------------------------------------------------------
# 3) Brifing
# -----------------------------------------------------------------------------
echo "[3/3] Brifing pipeline (LangGraph + ajanlar)"
check "POST /api/briefing/run"      "/api/briefing/run" "POST" '{
    "business_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "business_name": "Demo İşletme",
    "owner_name": "Demo Sahibi",
    "trigger_source": "smoke_test"
}'

# Brifing içeriğini de göster
if [ -s /tmp/resp.json ]; then
    echo
    echo "  Üretilen brifing önizleme:"
    python3 -c "
import json, sys
try:
    d = json.load(open('/tmp/resp.json'))
    b = d.get('briefing', '')
    fb = d.get('used_fallback', False)
    errs = d.get('errors', [])
    print('    ' + b[:300].replace('\n', '\n    '))
    if fb:
        print('    [INFO] used_fallback=True (LLM atlandı, template kullanıldı)')
    if errs:
        print('    [INFO] errors:', errs[:2])
except Exception as e:
    print('    (parse hatası:', e, ')')
" 2>/dev/null
fi

# -----------------------------------------------------------------------------
# Veri doluluğu kontrolü
# -----------------------------------------------------------------------------
echo
echo "[Bonus] Veri doluluk kontrolü"
TOTAL_ORDERS=$(curl -s "$BASE/api/dashboard/stats" | python3 -c "import json,sys;print(json.load(sys.stdin).get('total_orders',0))" 2>/dev/null || echo "0")
TOTAL_PRODUCTS=$(curl -s "$BASE/api/products?per_page=1" | python3 -c "import json,sys;print(json.load(sys.stdin).get('total',0))" 2>/dev/null || echo "0")
CRITICAL=$(curl -s "$BASE/api/stock/critical" | python3 -c "import json,sys;print(json.load(sys.stdin).get('count',0))" 2>/dev/null || echo "0")

printf "  %-40s " "Toplam sipariş"
if [ "$TOTAL_ORDERS" -gt 0 ]; then
    printf "${GREEN}%s${NC}\n" "$TOTAL_ORDERS"
else
    printf "${YELLOW}0 — seed çalışmamış olabilir${NC}\n"
fi

printf "  %-40s " "Toplam ürün"
if [ "$TOTAL_PRODUCTS" -gt 0 ]; then
    printf "${GREEN}%s${NC}\n" "$TOTAL_PRODUCTS"
else
    printf "${YELLOW}0${NC}\n"
fi

printf "  %-40s " "Kritik stok"
printf "${GREEN}%s${NC}\n" "$CRITICAL"

# -----------------------------------------------------------------------------
# Özet
# -----------------------------------------------------------------------------
echo
echo "================================================================"
TOTAL=$((PASS + FAIL))
if [ "$FAIL" -eq 0 ]; then
    printf "  ${GREEN}TÜM TESTLER BAŞARILI${NC}: $PASS/$TOTAL\n"
    echo "  Demo videosunu çekmeye hazırsın 🎬"
    echo "================================================================"
    exit 0
else
    printf "  ${RED}BAZI TESTLER BAŞARISIZ${NC}: $PASS/$TOTAL OK, $FAIL FAIL\n"
    echo "  Logs için: docker compose logs backend"
    echo "================================================================"
    exit 1
fi
