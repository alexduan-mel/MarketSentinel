# SentinelStream

A high-performance AI trading framework combining Java execution and Python intelligence.

## Quick Start

```bash
docker compose up --build

# Ping services
curl http://localhost:8080  # Java Core
curl http://localhost:8000  # Python AI

# Monitor storage worker
docker compose logs -f storage-worker

# Check Redis queue length
docker compose exec redis redis-cli LLEN news_ingest_queue

# Check database records
docker compose exec timescaledb psql -U sentinel -d sentinelstream -c "SELECT COUNT(*) FROM news_events;"
```

## Architecture

- **TimescaleDB**: Time-series data storage (Port 5432)
- **Redis**: Message queue and cache (Port 6379)
- **Java Core**: The Executioner (Spring Boot 3.2, Java 21) - Port 8080
- **Python AI**: The Intelligence (FastAPI, Python 3.11) - Port 8000
- **Storage Worker**: News persistence service (Producer-Consumer pattern)


Event-Driven Market Intelligence Engine
SentinelStream is a distributed system built to capture financial news in real-time and use Large Language Models (LLMs) to predict market moves. It features a built-in "paper trading" system that automatically tests AI predictions against live market prices to verify their accuracy.

Core Features
AI Cross-Verification: Compares results from different AI models (like GPT and Gemini) to catch mistakes and ensure the generated signals are reliable.

Automated Market Scanning: Scans news feeds to automatically identify and monitor companies or sectors, helping detect major market events even if they aren't on your main watch list.

Real-Time Paper Trading:

Signal Monitoring: The engine listens for new AI signals through Redis.

Instant Execution: The system captures the current market price from the Java core and executes a "virtual trade" to test the signal.

Profit Tracking: Automatically tracks the profit and loss (PnL) and success rate for every prediction.

High-Speed Ingestion: Built with Java 21 (Virtual Threads) to handle high-frequency market data and a Python Intelligence Layer for fast AI processing.

Explainable Dashboard: An interactive Streamlit frontend that shows price trends alongside the AI's step-by-step reasoning for each signal.

Tech Stack
Languages: Java 21, Python 3.12.

Frameworks: Spring Boot, FastAPI, Streamlit.

Infrastructure: Redis (Messaging), PostgreSQL / TimescaleDB (Time-series data).

AI Tools: Gemini API, OpenAI API, Windsurf (AI-assisted development).

Deployment: GCP (Google Cloud Platform), Docker.
