# AgentKobi

KOBİ''ler için otonom yapay zeka asistanı — sipariş takibi, stok uyarısı,
tedarikçi taslakları ve sabah brifingi.

## Stack
- **Backend:** FastAPI, SQLAlchemy (async), Celery + Redis, PostgreSQL
- **Frontend:** Next.js (App Router) + Tailwind + shadcn/ui
- **LLM:** Gemini / Groq / Claude (LangChain üzerinden)
- **Mesajlaşma:** WhatsApp Cloud API

## Hızlı Başlangıç

```bash
cp .env.example .env
docker compose up --build
```

- Backend: http://localhost:8000/docs
- Frontend: http://localhost:3000

## Modüller
- [x] Sabah Brifingi (`docs/Sabah_Brifingi_Adim_Adim_Rehber.docx`)
- [ ] Sipariş Ajanı
- [ ] Stok Ajanı
- [ ] Kargo Ajanı
- [ ] Tedarikçi Taslak Ajanı
