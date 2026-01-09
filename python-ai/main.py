import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
import redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    
    try:
        r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        r.ping()
        print("Sentinel-Python: Redis Connection [OK]")
    except Exception as e:
        print("Sentinel-Python: Redis Connection [FAIL]")
    
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"status": "SentinelStream Intelligence Online"}
