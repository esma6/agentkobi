# Esma — Teknik Notlar (LangGraph Orkestrasyonu, Validator, RAG)

> **Sorumluluk alanı:** State tasarımı, LangGraph orkestratörü, conditional
> routing, halüsinasyon önleme (validator + fallback), RAG kurulumu (FAISS).
> Bu modüller `backend/app/graph/`, `backend/app/validators/` ve
> `backend/app/rag/` altında bulunur.

## 1. Genel Mimari

Sabah brifingi modülü iki katmanlı bir orkestrasyon kullanır:

| Katman | Sorumluluk | Teknoloji |
|--------|-----------|-----------|
| **Zamanlama** | Her gün 08:00'''de tetikleme | Celery Beat |
| **Karar/Akış** | Hangi ajanın ne zaman, hangi sırayla çalışacağı | LangGraph |

Celery, LangGraph workflow'''unu sarmalayan ince bir wrapper'''dır. Bu ayrım:
- Zamanlama mantığını iş mantığından ayırır.
- LangGraph workflow'''u manuel API çağrısıyla da tetiklenebilir (demo butonu).
- Test edilebilirlik artar — workflow'''u Celery'''siz pytest'''ten çağırabilirim.

## 2. State Tasarımı (`graph/state.py`)

`AgentState`, tüm node'''ların okuyup yazdığı ortak veri yapısı.

**Tasarım kararları:**

1. **TypedDict + `total=False`**: Her field opsiyonel. Bir node sadece
   ilgilendiği alanları doldurur. Pydantic yerine TypedDict tercih ettim
   çünkü LangGraph'''in reducer mekanizması (Annotated tipler) Pydantic ile
   daha az pürüzsüz çalışıyor.

2. **`Annotated[list, operator.add]` reducers**: `errors` ve `trace`
   alanları, paralel node'''lardan gelen güncellemeleri **birleştirir**
   (overwrite etmez). Bu sayede 4 ajan paralel çalışırken her biri
   trace'''e eklediği kayıtlar kaybolmaz.

3. **Diğer alanlar (overwrite semantics)**: `briefing_draft`, `briefing_final`
   gibi tek-yazıcı alanlarda son yazan kazanır — bilinçli tercih, çünkü
   bu alanları sadece tek bir node yazıyor.

## 3. Orkestratör Akışı (`graph/orchestrator.py`)
START
│ (paralel fan-out)
├──► order ─────┐
├──► stock ─────┤
├──► shipping ──┼──► aggregator
└──► supplier ──┘        │
│ (conditional)
┌────────┴────────┐
│ quiet_day       │ busy_day
▼                 ▼
briefing_llm        rag
│
▼
briefing_llm
│
▼
validator ──► END
**Neden paralel fan-out?**
4 veri toplama ajanı birbirinden bağımsız (farklı tablolardan veri çeker).
Sıralı çalıştırmak ~4x latency demek. LangGraph'''te `START`'''tan birden
fazla node'''a edge çekmek otomatik paralel execution sağlar.

**Neden aggregator?**
Sakin gün kontrolü tek noktada yapılmalı; aksi halde her ajan kendi
karar verir, tutarsızlık oluşur.

## 4. Conditional Routing (`graph/routing.py`)

İki conditional edge var:

### `route_after_aggregator`
- **Quiet day** (sıfır sipariş, sıfır stok uyarısı, sıfır taslak):
  RAG'''i ve LLM çağrısını atlayıp doğrudan template'''e gider.
  *Mantık:* Boş bir gün için LLM'''e ödeme yapmak ve potansiyel
  halüsinasyon riskini almak gereksiz.
- **Busy day**: RAG'''e gider, sonra LLM, sonra validator.

### `route_after_validator`
- Geçtiyse: END.
- Geçmediyse: zaten validator template'''e düşürmüş, yine END.
- (Genişletme noktası: `requires_human_review=True` ise human-in-the-loop
  branch — şu an aynı END'''e gidiyor, sonra ayrı node ekleyeceğim.)

## 5. Halüsinasyon Önleme (`validators/`)

LLM çıktısına asla doğrudan güvenmiyorum. **İki katmanlı savunma:**

### Katman 1: `briefing_validator.py`

`extract_numbers()` regex'''i ile metindeki tüm sayıları çıkarıyor; bunları
`_payload_numbers()` ile gerçek payload'''dan üretilmiş allowlist'''le
karşılaştırıyor. Whitelist'''te sadece "saat, yıl, 0/1/24" gibi nötr
sayılar var.

**Örnek halüsinasyon yakalama:**
- Payload: `{"new_orders_yesterday": 12}`
- LLM çıktısı: "Dün **15** yeni sipariş geldi"
- Validator: `extracted={15}`, `allowed={12, 0, 1, 8, 24, 2025, 2026}`
  → `hallucinated={15}` → **fail**

Bu yaklaşımın **bilinçli sınırlamaları:**
- Yazıyla yazılmış sayıları (\"on iki\") yakalamaz. Ama sistem
  prompt'''unda LLM'''e \"sayıları rakamla yaz\" kuralı var.
- Yüzde işareti, ondalık nokta vs. edge-case'''leri test edilmedi.
  Demo için yeter; production için fuzz testing gerekir.

### Katman 2: `fallback.py`

LLM tamamen down olsa veya validator fail etse bile sistem mesaj
üretmeli. `render_template_briefing()` saf string formatlama —
yapay zeka kullanmıyor, asla halüsinasyon yapmaz. Output'''u
deterministik. Demo'''nun \"hiç bir şey patlamayacak\" garantisi.

**`used_fallback` flag'''i** state'''e yazılıyor — dashboard'''da
\"Bu brifing template'''den geldi\" rozetiyle gösterilecek
(transparency). Jüriye \"sistemin ne zaman LLM'''e güvendiğini,
ne zaman güvenmediğini gösterebiliyoruz\" demek için kritik.

## 6. RAG (FAISS) Kurulumu (`rag/`)

**Neden FAISS, neden pgvector değil?**

| Kriter | FAISS | pgvector |
|--------|-------|----------|
| Kurulum | pip install, sıfır config | Postgres extension, sürüm uyumu |
| Hız (küçük dataset) | Çok hızlı | Hızlı |
| Persistance | Disk dosyası | DB |
| Demo riski | Düşük | Orta (extension uyum sorunları) |

Demo'''da ~100-1000 brifing aralığında çalışacağız. FAISS bu boyutta
20ms altında dönüyor; pgvector kurmanın getireceği ek karmaşıklığa
değmez.

**Embedding modeli:** `sentence-transformers/all-MiniLM-L6-v2`
- 384 boyut, lokal, ücretsiz, CPU'''da hızlı.
- Türkçe için ideal değil — gerçek production'''da
  `intfloat/multilingual-e5-base` veya `BAAI/bge-m3` kullanmalı.
- Demo için yeterli; trade-off bilinçli.

**Retrieval'''ın brifinge ne katkısı var?**
LLM'''e few-shot örnekleri statik vermek yerine, "geçmişteki en benzer
gün nasıl özetlenmişti?" sorusuna dinamik cevap veriyoruz. Tutarlı
ton + tarihsel bağlam. Bu, brifingi mekanik özetlemeden \"asistan\"
hissine yaklaştırır.

## 7. Bilinen Sınırlamalar / Gelecek İşler

- `requires_human_review` branch'''i şu an pasif. Stok %95 üstü
  kritikse veya validator art arda 2 fail verirse human-in-the-loop'''a
  yönlendirilmeli.
- FAISS index'''i tek-business — multi-tenant olunca business_id'''ye
  göre namespace'''leme gerek.
- Validator regex'''i Türkçe ondalık (\"3,5\") yakalıyor ama bilimsel
  notasyon (\"1e3\") yakalamıyor. Brifingde olmayacağını varsayıyorum.
- LangGraph'''in checkpoint'''leme özelliğini kullanmıyoruz; her run
  sıfırdan başlıyor. State persistance (Redis-backed) eklenirse
  retry/resume mümkün olur.

## 8. Test Etme

Henüz unit test yazmadım — bir sonraki commit'''te:
- `tests/unit/test_validator.py`: 5 hallucination senaryosu
- `tests/unit/test_fallback.py`: 4 input → expected text
- `tests/integration/test_workflow.py`: stub'''lı uçtan uca

Manuel test:
```bash
python -c "import asyncio; from app.graph.orchestrator import run_workflow; print(asyncio.run(run_workflow('test-business-123')))"
```

## 9. Utku ile Entegrasyon Noktaları

Benim tarafım Utku'''nun ajan modüllerini şu interface ile bekliyor:

```python
# app/agents/order_agent.py içinde olmalı:
async def run(business_id: str) -> dict: ...

# app/agents/stock_agent.py:
async def run(business_id: str) -> list[dict]: ...

# app/agents/shipping_agent.py:
async def run(business_id: str) -> dict: ...

# app/agents/supplier_agent.py:
async def run(business_id: str) -> list[dict]: ...

# app/agents/briefing_agent.py:
async def run(
    order_data: dict,
    stock_data: list[dict],
    supplier_drafts: list[dict],
    rag_context: list[str],
) -> str: ...
```

Bu interface'''ler hazır olmadığı sürece `nodes.py` stub döndürüyor;
graph yine de uçtan uca çalışıyor. Yani Utku'''nun çalışması beni,
benim çalışmam Utku'''yu **bloklamıyor**.

Ilk 4 ajan icin implementasyon eklendi:
- `app/agents/order_agent.py`
- `app/agents/stock_agent.py`
- `app/agents/shipping_agent.py`
- `app/agents/supplier_agent.py`
- `app/agents/briefing_agent.py` Gemini ile AI brifing üretir; hata olursa
  `nodes.py` template fallback'e düşer.

Tek tek denemek icin:

```bash
cd backend
python -c "import asyncio; from app.agents.order_agent import run; print(asyncio.run(run('a1b2c3d4-e5f6-7890-abcd-ef1234567890')))"
python -c "import asyncio; from app.agents.stock_agent import run; data=asyncio.run(run('a1b2c3d4-e5f6-7890-abcd-ef1234567890')); print(len(data)); print(data[:1])"
python -c "import asyncio; from app.agents.shipping_agent import run; print(asyncio.run(run('a1b2c3d4-e5f6-7890-abcd-ef1234567890')))"
python -c "import asyncio; from app.agents.supplier_agent import run; data=asyncio.run(run('a1b2c3d4-e5f6-7890-abcd-ef1234567890')); print(len(data)); print(data[:1])"
```

Graph icinde denemek icin:

```bash
cd backend
python -c "import asyncio; from app.graph.orchestrator import run_workflow; result=asyncio.run(run_workflow('a1b2c3d4-e5f6-7890-abcd-ef1234567890')); print(result['order_data']); print(len(result['stock_data'])); print(result['shipping_data']); print(len(result['supplier_drafts'])); print(result['briefing_final'])"
```
