# Issue3 - LLM Analysis Operations

## Start the API server (local)

```bash
pip install -r services/python-ai/requirements.txt
PYTHONPATH=services/python-ai/app \
  uvicorn api:app --host 0.0.0.0 --port 8000
```

## Start the API server (Docker)

```bash
docker compose up -d python-ai
```

## Request analysis via HTTP

```bash
curl -X POST "http://localhost:8000/news-events/1/analysis"
```

Notes:
- The `news-events/{id}` path expects `news_events.id` (BIGINT).
- Configure the provider via env vars (see `.env.example`): `LLM_PROVIDER`, `OPENAI_API_KEY` or `GOOGLE_API_KEY`.



                 ┌───────────────┐
                 │   news_event  │
                 └───────┬───────┘
                         │
                         ▼
                 ┌───────────────┐
                 │  job created  │
                 │  status=pending
                 └───────┬───────┘
                         │ worker claim
                         ▼
                 ┌───────────────┐
                 │   running     │
                 └───────┬───────┘
                         │
        ┌────────────────┼─────────────────┐
        │                │                 │
        ▼                ▼                 ▼
   JSON invalid     Timeout error    Quota error
   retryable        retryable        non-retryable
        │                │                 │
        ▼                ▼                 ▼
   attempts++       attempts++          failed
        │                │
        └───────retry────┘
               │
               ▼
         running again
               │
               ▼
          succeeded