# 🐘 PostgreSQL Geçişi — Takım Rehberi

> **Yazar:** Esma · **Tarih:** Mayıs 2026  
> **PR:** `feat/esma-postgres-endpoints` → `main`

Bu döküman, projede yapılan **CSV → PostgreSQL** geçişini ve ondan sonra takımın ne yapması gerektiğini açıklar. Eğer bir backend modülü ekleyecek (LangGraph node, Celery task, WhatsApp webhook) veya frontend'i bağlayacak biriyseniz buraya bakın.

---

## 📌 TL;DR

| Önce | Sonra |
|---|---|
| Endpoint'ler CSV dosyalarından `pandas` ile okuyordu | Endpoint'ler PostgreSQL'den async SQLAlchemy ile okuyor |
| Veri restart'ta yeniden yükleniyordu (RAM'de) | Veri kalıcı (Docker volume `postgres_data`) |
| Schema yoktu, sadece CSV başlıkları | 6 tablo + index'ler (Alembic ile yönetiliyor) |
| Yeni veri eklemek = CSV'yi düzenleyip restart | Yeni veri eklemek = INSERT SQL veya ORM çağrısı |

**Frontend tarafında değişiklik gerekmez** — endpoint URL'leri ve response yapısı aynı.

---

## 🚀 Hızlı Başlangıç (Sıfırdan Kuran Birine)

```cmd
# Repo'yu çek
git clone https://github.com/esma6/agentkobi.git
cd agentkobi

# .env dosyasını oluştur (değerler hazır gelir)
copy .env.example .env

# Servisleri başlat
docker compose up -d postgres redis
docker compose up -d backend

# İLK KEZ kuranlar için: migration + seed
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.db.seed.seed_from_csv
```

Backend hazır: <http://localhost:8000/docs>

---

## 🗂️ Yeni Dosya Yapısı

```
backend/
├── alembic.ini                    # ⭐ YENİ — Alembic konfigürasyonu
├── app/
│   ├── core/                      # ⭐ YENİ KLASÖR
│   │   ├── config.py              # .env okuyan Settings sınıfı (Pydantic v2)
│   │   └── db.py                  # Async engine + get_session() dependency
│   │
│   ├── models/
│   │   ├── base.py                # ⭐ YENİ — SQLAlchemy DeclarativeBase
│   │   ├── orm.py                 # ⭐ YENİ — 6 tablo (Business, Customer, ...)
│   │   └── tools.py               # ESKİ — LangGraph tool'ları (dokunulmadı)
│   │
│   ├── schemas/                   # ⭐ YENİ KLASÖR
│   │   └── api.py                 # Pydantic v2 request/response şemaları
│   │
│   ├── db/
│   │   ├── loader.py              # ESKİ — CSV loader (artık kullanılmıyor*)
│   │   ├── *.csv                  # ESKİ — seed kaynağı olarak duruyor
│   │   ├── migrations/            # ⭐ YENİ — Alembic
│   │   │   ├── env.py
│   │   │   ├── script.py.mako
│   │   │   └── versions/
│   │   │       └── 2eede5c3e3e3_initial_schema.py
│   │   └── seed/                  # ⭐ YENİ
│   │       └── seed_from_csv.py   # CSV → Postgres yükleyici
│   │
│   └── api/
│       └── routes.py              # ⚠️ DEĞİŞTİ — artık SQLAlchemy kullanıyor
```

*`loader.py` LangGraph node'ları/tool'lar tarafından hâlâ import ediliyor (örn. `app/models/tools.py`, `app/graph/...`). Bunlar henüz DB'ye geçirilmedi; bilinçli bir tercih çünkü:
- LangGraph workflow'unu kırmamak için (Esma'nın orchestrator/validator kısmı sağlam),
- Her ajan tool'u ayrı bir PR'da DB'ye geçecek (incremental migration).

Yani **`/api/briefing/run`** endpoint'i hâlâ CSV'leri okuyor (LangGraph üzerinden). **`/api/orders`, `/api/products`, `/api/customers`** ise tamamen Postgres'ten okuyor.

---

## 🛢️ Veritabanı Şeması

| Tablo | İçindekiler |
|---|---|
| `businesses` | KOBİ'ler (multi-tenant anahtarı). Şu an demo için tek kayıt var. |
| `customers` | Müşteriler. `business_id` ile işletmeye bağlı. |
| `products` | Ürünler. SKU, stok, fiyat, kritik eşik. |
| `orders` | Siparişler. `customer_id` + `business_id` FK. Durumlar: `pending`, `confirmed`, `preparing`, `shipped`, `delivered`, `cancelled`. |
| `order_items` | Sipariş kalemleri (her sipariş 1+ ürün içerebilir). |
| `supplier_drafts` | LLM tarafından üretilen tedarikçi e-postası taslakları. Onay bekler. |

Görsel olarak görmek için pgAdmin/DBeaver/TablePlus ile bağlanabilirsiniz:
- Host: `localhost`
- Port: `5432`
- User: `agentkobi`
- Password: `changeme`
- DB: `agentkobi`

Veya CLI ile:

```cmd
docker compose exec postgres psql -U agentkobi -d agentkobi -c "\dt"
```

### Demo `business_id`

Tüm veri tek bir işletmeye bağlı:
```
a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

Bu değer `.env`'de `DEMO_BUSINESS_ID` olarak da var; kod içinde `settings.DEMO_BUSINESS_ID` ile erişin.

---

## 🛠️ Sık Kullanılacak Komutlar

### 🔁 Schema değiştiğinde (yeni tablo veya kolon ekledim)

`app/models/orm.py`'yi düzenle, sonra:

```cmd
docker compose exec backend alembic revision --autogenerate -m "açıklayıcı isim"
docker compose exec backend alembic upgrade head
```

**Önemli:** Migration dosyasını otomatik üretildikten sonra **gözden geçirin**. Autogenerate her şeyi doğru yakalamayabilir (özellikle indeks adı değişikliği, kolon yeniden adlandırma).

### ⏪ Migration'ı geri al

```cmd
docker compose exec backend alembic downgrade -1
```

### 🌱 Veriyi sıfırla (test için)

`seed_from_csv.py` idempotent: önce tabloları boşaltır, sonra yükler. Yani tekrar çalıştırmak güvenli:

```cmd
docker compose exec backend python -m app.db.seed.seed_from_csv
```

### 🧨 Her şeyi sıfırla (volume dahil)

> **DİKKAT:** Bu komut Postgres volume'unu silip her şeyi sıfırlar.

```cmd
docker compose down -v
docker compose up -d postgres redis backend
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.db.seed.seed_from_csv
```

### 📊 Verilere bak

```cmd
docker compose exec postgres psql -U agentkobi -d agentkobi
```

`psql` prompt'unda:
- `\dt` — tabloları listele
- `\d orders` — orders tablosunun şemasını göster
- `SELECT COUNT(*) FROM orders;` — kayıt sayısı
- `\q` — çık

---

## 📡 API Kontratı (Frontend Ekibi İçin)

Endpoint'lerin **response yapısı değişmedi**, yani frontend'de değişiklik gerekmez. Ama referans olsun diye:

### `GET /api/dashboard/stats`

```json
{
  "total_orders": 112,
  "total_revenue": 12345.67,
  "active_orders": 80,
  "shipped_orders": 15,
  "cancelled_orders": 10,
  "critical_stock_count": 8,
  "status_distribution": { "Beklemede": 20, "Onaylandı": 30, ... },
  "status_revenue": { "Beklemede": 1500.0, ... }
}
```

### `GET /api/orders?status=preparing&page=1&per_page=20`

```json
{
  "total": 25,
  "page": 1,
  "per_page": 20,
  "pages": 2,
  "items": [
    {
      "id": "...",
      "order_number": 42,
      "status": "preparing",
      "status_label": "Hazırlanıyor",
      "total_amount": 80.0,
      "...": "..."
    }
  ]
}
```

### `GET /api/products?low_stock=true`

`low_stock=true` ise sadece kritik stoğu listeler. Aynı sayfalama yapısı.

### `GET /api/customers`

Sayfalı müşteri listesi, `total_orders` çoktan aza sıralı.

### `GET /api/stock/critical`

```json
{
  "count": 8,
  "items": [
    {
      "sku": "KOP-001",
      "name": "Organik Domates",
      "stock_quantity": 30,
      "reorder_threshold": 50,
      "eksik_miktar": 20,
      "doluluk_yuzde": 60.0,
      "price": 24.9
    }
  ]
}
```

Swagger UI tüm endpoint'leri canlı denemenize izin verir: <http://localhost:8000/docs>

---

## 👨‍💻 Diğer Takım Üyeleri İçin

### 🟠 Utku — Backend & Celery

**Senin tarafında değişen ne?** Hiçbir şey acil değil. Ama biliyor ol:

1. **WhatsApp webhook**'unu yazarken `app/core/db.py`'deki `get_session()` dependency'sini kullan:
   ```python
   from fastapi import Depends
   from sqlalchemy.ext.asyncio import AsyncSession
   from app.core.db import get_session
   from app.models.orm import Customer

   @router.post("/webhook")
   async def webhook(payload: dict, db: AsyncSession = Depends(get_session)):
       # phone number ile müşteri bul vs.
       result = await db.execute(
           select(Customer).where(Customer.phone == payload["from"])
       )
       customer = result.scalar_one_or_none()
       ...
   ```

2. **Celery task'ları** (sabah brifingi, kargo monitor) için ayrı bir senkron session lazım — Celery async'i tam desteklemiyor. Önerim: `app/core/db.py`'ye `SyncSessionLocal` ekle veya doğrudan task içinde `asyncio.run()` kullan. İlk yaklaşımda ısrar edersen yardım ederim.

3. **`/api/briefing/run`** endpoint'i şimdilik LangGraph workflow'unu eskisi gibi çağırıyor (CSV üzerinden). Bunu DB'ye geçirmek ayrı bir iş. Demo için aciliyeti yok.

### 🟢 Alperen — Frontend & Demo

**Senin tarafında değişen ne?** Hiçbir şey. Endpoint URL'leri ve JSON yapısı aynı. Sadece şunlar daha güvenilir oldu:
- Veriler restart'ta kaybolmuyor.
- Yanıt süreleri biraz daha tutarlı (CSV her seferinde okunmuyordu zaten, ama olsun).

Yapacağın tek şey: `npm run dev` ile frontend'i çalıştır ve `http://localhost:3000`'a git. Backend `http://localhost:8000`'da hazır.

---

## ⚠️ Sık Karşılaşılan Hatalar

| Hata | Çözüm |
|---|---|
| `relation "orders" does not exist` | Migration uygulanmamış. `docker compose exec backend alembic upgrade head` |
| `0 müşteri eklendi` veya tablolar boş | Seed çalıştırılmamış. `docker compose exec backend python -m app.db.seed.seed_from_csv` |
| `asyncpg.exceptions.InvalidPasswordError` | `.env` ile docker-compose env'i uyuşmuyor. `.env`'i kontrol et, `docker compose down && up -d` yap. |
| `port 5432 already in use` | Bilgisayarında başka bir Postgres çalışıyor. Servisi durdur ya da `docker-compose.yml`'de `5433:5432` yap (sonra `.env`'de de `localhost:5433`). |
| `psycopg2-binary` eksik | `pyproject.toml`'a eklendi. `docker compose build backend --no-cache` |
| Alembic "No 'script_location'" | `backend/` klasöründen çalıştırdığından emin ol (`alembic.ini` orada). Container içinden çalıştırırken zaten `/app` doğru dizin. |

---

## 🧪 Test

Şimdilik manuel test:
1. Swagger UI'dan her endpoint'i "Try it out" → "Execute" ile dene.
2. Tüm endpoint'ler `200 OK` ile JSON dönmeli.
3. `low_stock=true` ile sadece kritik ürünler gelmeli.
4. `?page=2&per_page=5` ile sayfalama çalışmalı.

Pytest tarafı henüz yok; demo öncesinde Esma birkaç happy-path testi yazacak.

---

## 🔮 Yapılacaklar / Gelecek İşler

- [ ] LangGraph tool'larını (`app/models/tools.py`) DB'ye taşı — şu an hâlâ CSV okuyor.
- [ ] Sabah brifingi Celery task'ı için DB session pattern'i.
- [ ] WhatsApp webhook'undan gelen müşteri bilgisinin `customers` tablosuyla eşleştirilmesi (Utku yapacak).
- [ ] Production deploy'da `DATABASE_URL`'i environment-specific yapma (Railway/Render).
- [ ] Pgbench veya basit load test (demo öncesi opsiyonel).

---

## 🙋 Sorular?

Esma'ya WhatsApp/Slack'ten yaz. Schema değişikliği yapacaksan **önce konuş**, çakışan migration olmasın.
