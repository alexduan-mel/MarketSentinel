from __future__ import annotations

import argparse
import logging
import os
import socket
import time
from dataclasses import dataclass
from datetime import timedelta
from typing import Iterable

import psycopg2

from analysis.service import analyze_news_event

@dataclass(frozen=True)
class JobRow:
    id: int
    job_uuid: str
    news_event_id: int
    job_type: str
    trace_id: str
    attempts: int


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analysis job worker")
    parser.add_argument("--poll-interval", type=int, default=3, help="Seconds between polls")
    parser.add_argument("--batch-size", type=int, default=10, help="Jobs to claim per loop")
    parser.add_argument("--once", action="store_true", help="Process once and exit")
    parser.add_argument("--worker-id", default=None, help="Worker identifier for locking")
    return parser.parse_args()


def _configure_logging() -> None:
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def _connect_db():
    host = os.getenv("POSTGRES_HOST")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    name = os.getenv("POSTGRES_DB")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    missing = [key for key, value in {
        "POSTGRES_HOST": host,
        "POSTGRES_DB": name,
        "POSTGRES_USER": user,
        "POSTGRES_PASSWORD": password,
    }.items() if not value]
    if missing:
        raise SystemExit(f"Missing DB environment variables: {', '.join(missing)}")
    return psycopg2.connect(
        host=host,
        port=port,
        dbname=name,
        user=user,
        password=password,
    )


def _claim_jobs(conn, batch_size: int, worker_id: str) -> list[JobRow]:
    sql = (
        "WITH cte AS ("
        "  SELECT id, job_uuid, news_event_id, job_type, trace_id, attempts "
        "  FROM analysis_jobs "
        "  WHERE status = 'pending' "
        "    AND next_run_at <= NOW() "
        "    AND attempts < 3 "
        "  ORDER BY next_run_at ASC, created_at ASC "
        "  FOR UPDATE SKIP LOCKED "
        "  LIMIT %s"
        ") "
        "UPDATE analysis_jobs j "
        "SET status = 'running', locked_at = NOW(), locked_by = %s, updated_at = NOW() "
        "FROM cte "
        "WHERE j.id = cte.id "
        "RETURNING j.id, j.job_uuid::text, j.news_event_id, j.job_type, j.trace_id::text, cte.attempts"
    )
    with conn.cursor() as cursor:
        cursor.execute(sql, (batch_size, worker_id))
        rows = cursor.fetchall()
    conn.commit()
    return [JobRow(*row) for row in rows]


def _load_news_event(conn, news_event_id: int) -> tuple[int, str, str]:
    sql = "SELECT id, news_id, title FROM news_events WHERE id = %s"
    with conn.cursor() as cursor:
        cursor.execute(sql, (news_event_id,))
        row = cursor.fetchone()
    if not row:
        raise RuntimeError(f"news_event_not_found: {news_event_id}")
    return row[0], row[1], row[2]


def _mark_done(conn, job_id: int) -> None:
    sql = (
        "UPDATE analysis_jobs "
        "SET status = 'done', updated_at = NOW(), last_error = NULL "
        "WHERE id = %s"
    )
    with conn.cursor() as cursor:
        cursor.execute(sql, (job_id,))
    conn.commit()


def _mark_failed(conn, job_id: int, attempts: int, error: str) -> None:
    next_attempts = attempts + 1
    backoff_seconds = min((2 ** next_attempts) * 10, 300)
    sql = (
        "UPDATE analysis_jobs "
        "SET status = 'failed', attempts = attempts + 1, last_error = %s, "
        "next_run_at = NOW() + (%s || ' seconds')::interval, updated_at = NOW() "
        "WHERE id = %s"
    )
    with conn.cursor() as cursor:
        cursor.execute(sql, (error[:500], backoff_seconds, job_id))
    conn.commit()


def _process_jobs(conn, jobs: Iterable[JobRow], logger: logging.Logger) -> None:
    for job in jobs:
        try:
            if job.job_type == "llm_analysis":
                result = analyze_news_event(job.news_event_id)
                if result.get("status") == "succeeded":
                    _mark_done(conn, job.id)
                    logger.info(
                        "processed job %s job_uuid %s for news_event_id %s",
                        job.id,
                        job.job_uuid,
                        job.news_event_id,
                    )
                else:
                    _mark_failed(conn, job.id, job.attempts, result.get("error_message", "analysis_failed"))
                    logger.error(
                        "job_failed job_id=%s job_uuid=%s news_event_id=%s error=%s",
                        job.id,
                        job.job_uuid,
                        job.news_event_id,
                        result.get("error_message"),
                    )
                continue

            event_id, news_id, _title = _load_news_event(conn, job.news_event_id)
            logger.info(
                "processed job %s job_uuid %s for news_event_id %s news_id %s",
                job.id,
                job.job_uuid,
                event_id,
                news_id,
            )
            _mark_done(conn, job.id)
        except Exception as exc:  # noqa: BLE001
            _mark_failed(conn, job.id, job.attempts, str(exc))


def main() -> int:
    _configure_logging()
    args = _parse_args()
    logger = logging.getLogger(__name__)

    worker_id = args.worker_id
    if not worker_id:
        worker_id = f"{socket.gethostname()}:{os.getpid()}"

    with _connect_db() as conn:
        while True:
            jobs = _claim_jobs(conn, args.batch_size, worker_id)
            if not jobs:
                if args.once:
                    break
                time.sleep(max(args.poll_interval, 1))
                continue

            _process_jobs(conn, jobs, logger)

            if args.once:
                break

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
