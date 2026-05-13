# AgentKobi

KOBİ'ler için otonom yapay zeka asistanı — sipariş takibi, stok uyarısı,
tedarikçi taslakları ve sabah brifingi. LangGraph tabanlı multi-agent
mimari, FAISS RAG ile zenginleştirilmiş Gemini LLM çağrıları ve
halüsinasyon önleme validator katmanı içerir.

---

## İçindekiler
- [Mimari](#mimari)
- [Hızlı Başlangıç (Demo)](#hızlı-başlangıç-demo)
- [Demo Akışı (Video için)](#demo-akışı-video-için)
- [Smoke Test](#smoke-test)
- [Endpoint'ler](#endpointler)
- [Sorun Giderme](#sorun-giderme)
- [Geliştirici Notları](#geliştirici-notları)

---

## Mimari

```
┌──────────────┐      ┌───────────────────────────────────────────┐
│  Next.js 14  │ ───► │            FastAPI (REST + LangGraph)     │
│  (Frontend)  │      │                                           │
│  Dashboard   │      │  /api/dashboard/stats   /api/orders       │
│  Siparişler  │      │  /api/products          /api/customers    │
│  Ürünler     │      │  /api/stock/critical    /api/briefing/run │
│  Müşteriler  │      └───────────────────────────────────────────┘
│  Brifing     │                  │              │
└──────────────┘                  ▼              ▼
                          ┌─────────────┐  ┌──────────────────────┐
                          │ PostgreSQL  │  │  LangGraph Pipeline  │
                          │  + Alembic  │  │ order → stock        │
                          └─────────────┘  │   → shipping         │
                                           │   → supplier         │
                                           │   → aggregator       │
                                           │   → RAG (FAISS)      │
                                           │   → briefing (Gemini)│
                                           │   → validator        │
                                           └──────────────────────┘
```

**Stack:**
- **Backend:** FastAPI, SQLAlchemy (async) + asyncpg, Alembic, LangGraph, LangChain, FAISS, pandas, Pydantic v2
- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind, Recharts, lucide-react
- **DB:** PostgreSQL 16, Redis 7
- **LLM:** Google Gemini 2.5 Flash (langchain-google-genai)
- **Embeddings:** sentence-transformers / HuggingFace
- **Konteyner:** Docker Compose (4 servis: postgres, redis, backend, frontend)

---

## Hızlı Başlangıç (Demo)

### Önkoşullar
- Docker + Docker Compose v2
- (Opsiyonel) Google AI Studio API anahtarı — [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

> **Not:** API anahtarı **olmadan da** demo çalışır. Brifing endpoint'i
> deterministik fallback template kullanır. Gerçek LLM çıktısı görmek için
> anahtar gerekli.

### 1. Repo'yu klonla / aç
```bash
git clone <repo-url>
cd agentkobi-main
```

### 2. .env hazırla
```bash
# .env zaten repoda var, sadece API anahtarını doldur (opsiyonel)
nano .env   # GOOGLE_API_KEY=AIzaSy... satırını güncelle
```

### 3. Compose'u başlat
```bash
docker compose up --build
```

İlk açılışta otomatik olarak:
1. PostgreSQL ayağa kalkar ve healthcheck'ten geçer.
2. Backend container'ı entrypoint'i çalıştırır:
   - Alembic migration'ları uygular (tablolar oluşur).
   - DB boşsa CSV verilerini seed eder (112 sipariş, 45 ürün, 30 müşteri, 9 kritik stok, 48 tedarikçi taslağı).
   - Uvicorn başlar (`:8000`).
3. Frontend ayağa kalkar (`:3000`).

### 4. Erişim
- 🌐 **Frontend:** http://localhost:3000
- 📚 **Backend Swagger:** http://localhost:8000/docs
- ❤️  **Health:** http://localhost:8000/health

İlk açılış 1-2 dakika sürebilir (image build + sentence-transformers indirme).

---

## Demo Akışı (Video için)

3 dakikalık demo için önerilen senaryo:

| # | Ekran | Süre | Anlatım |
|---|-------|------|---------|
| 1 | http://localhost:3000 (Dashboard) | 0:00 - 0:30 | Toplam sipariş, ciro, kritik stok kutuları + pie chart + stok progress bar |
| 2 | http://localhost:3000/orders | 0:30 - 1:00 | 112 siparişin durum filtreleri, status_label TR çevirisi |
| 3 | http://localhost:3000/products | 1:00 - 1:30 | Düşük stok filtresi; kritik ürünleri vurgula |
| 4 | http://localhost:3000/customers | 1:30 - 2:00 | 30 müşteri, sipariş sayısına göre sıralı |
| 5 | http://localhost:3000/briefing | 2:00 - 3:00 | **"Şimdi Gönder"** butonuna tıkla → ajan pipeline animasyonu (order → stock → shipping → supplier → aggregator → RAG → briefing → validator) → Gemini'nin ürettiği sabah brifingi metni |

**Video çekmeden önce mutlaka çalıştır:**
```bash
bash scripts/smoke_test.sh
```

---

## Smoke Test

`docker compose up` sonrası tüm sistem hazır olduğunda:

```bash
bash scripts/smoke_test.sh
```

Çıktı örneği:
```
[1/3] Health & temel API
  GET  /health                              ✓ OK (HTTP 200)
  GET  /api/dashboard/stats                 ✓ OK (HTTP 200)

[2/3] Veri endpoint'leri
  GET  /api/orders                          ✓ OK (HTTP 200)
  GET  /api/orders?status=shipped           ✓ OK (HTTP 200)
  GET  /api/products                        ✓ OK (HTTP 200)
  GET  /api/products?low_stock=true         ✓ OK (HTTP 200)
  GET  /api/stock/critical                  ✓ OK (HTTP 200)
  GET  /api/customers                       ✓ OK (HTTP 200)
  GET  /api/supplier-drafts                 ✓ OK (HTTP 200)

[3/3] Brifing pipeline (LangGraph + ajanlar)
  POST /api/briefing/run                    ✓ OK (HTTP 200)

  Üretilen brifing önizleme:
    Günaydın! Dün 5 yeni sipariş geldi. Bugün 8 paket hazırlanmalı...

[Bonus] Veri doluluk kontrolü
  Toplam sipariş                            112
  Toplam ürün                               45
  Kritik stok                               9

================================================================
  TÜM TESTLER BAŞARILI: 10/10
  Demo videosunu çekmeye hazırsın 🎬
================================================================
```

---

## Endpoint'ler

| Method | Path | Açıklama |
|--------|------|----------|
| GET | `/health` | Liveness probe |
| GET | `/api/dashboard/stats` | Toplam sipariş/ciro/aktif/kargoda/iptal + status dağılımı |
| GET | `/api/orders` | Siparişler (filtre: `status`, sayfa: `page`, `per_page`) |
| GET | `/api/products` | Ürünler (filtre: `low_stock=true`) |
| GET | `/api/stock/critical` | Yeniden sipariş eşiğinin altındaki ürünler |
| GET | `/api/customers` | Müşteriler |
| GET | `/api/supplier-drafts` | Onay bekleyen tedarikçi taslakları |
| POST | `/api/briefing/run` | Sabah brifingi pipeline'ını manuel tetikle |

---

## Sorun Giderme

### Backend "Backend'e bağlanılamadı" hatası veriyor
```bash
docker compose logs backend
```
- Alembic hatası varsa: `docker compose down -v && docker compose up --build` ile temiz başlat.
- Postgres hazır değilse: birkaç saniye bekle, entrypoint zaten 60 saniyeye kadar bekliyor.

### Dashboard 0 gösteriyor (veri yok)
Seed çalışmamış. Manuel tetikle:
```bash
docker compose exec backend python -m app.db.seed.seed_from_csv
```

### Brifing endpoint'i 500 dönüyor
Tüm hatalar artık fallback'e düşüyor — 500 görürsen bir hata var:
```bash
docker compose logs backend | grep -i error
```

### Brifing "used_fallback: true" diyor
Bu **normal** — `GOOGLE_API_KEY` `.env`'de boşsa veya Gemini çağrısı başarısızsa
deterministik template kullanılıyor. Demo yine çalışır. Gerçek LLM çıktısı için
`.env` içine geçerli bir anahtar yapıştır ve `docker compose restart backend`.

### Port çakışması (3000, 5432, 6379, 8000 dolu)
`docker-compose.yml`'da port mapping'leri değiştir:
```yaml
ports:
  - "3001:3000"  # frontend
```

### Container'ları temizle
```bash
docker compose down -v   # volume'ları da sil (postgres verisi gider, seed yeniden çalışır)
```

---

## Geliştirici Notları

### Backend'i lokal (compose dışı) çalıştırma
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e .
# DATABASE_URL'i localhost'a çevir
export DATABASE_URL=postgresql+asyncpg://agentkobi:changeme@localhost:5432/agentkobi
alembic upgrade head
python -m app.db.seed.seed_from_csv
uvicorn app.main:app --reload
```

### Frontend'i lokal çalıştırma
```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

### LangGraph workflow'unu görmek
`backend/app/graph/orchestrator.py` — node'lar `nodes.py`'da, routing
mantığı `routing.py`'da. Workflow akışı: `order → stock → shipping →
supplier → aggregator → (sakin gün ise direct, değilse RAG) →
briefing_llm → validator → END`.

### Halüsinasyon Önleme
1. **Number extractor** (`validators/number_extractor.py`): brifing metnindeki
   tüm sayıları çıkarır.
2. **Validator** (`validators/briefing_validator.py`): sayıların DB verisiyle
   eşleştiğini doğrular.
3. **Fallback** (`validators/fallback.py`): validator geçmezse veya LLM down ise
   deterministik template ile brifing üretir.

### Modüller (Görev Dağılımı)
- [x] Sabah Brifingi (LangGraph + Gemini + RAG + Validator)
- [x] Sipariş Ajanı (`agents/order_agent.py`)
- [x] Stok Ajanı (`agents/stock_agent.py`)
- [x] Kargo Ajanı (`agents/shipping_agent.py`)
- [x] Tedarikçi Taslak Ajanı (`agents/supplier_agent.py`)
- [x] Müşteri Ajanı (`agents/customer_agent.py`)
- [ ] WhatsApp entegrasyonu (Plan B: web "Şimdi Gönder" butonu hazır)
- [ ] Celery + cron (manuel tetikleme çalışıyor)

---

## Lisans
Bu proje eğitim amaçlı yapılmıştır.
