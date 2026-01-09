# SentinelStream

A high-performance AI trading framework combining Java execution and Python intelligence.

## Quick Start

```bash
docker compose up --build

# Ping services
curl http://localhost:8080  # Java Core
curl http://localhost:8000  # Python AI
```

## Architecture

- **TimescaleDB**: Time-series data storage
- **Redis**: In-memory cache and message broker
- **Java Core**: The Executioner (Spring Boot 3.2, Java 21) - Port 8080
- **Python AI**: The Intelligence (FastAPI, Python 3.11) - Port 8000
