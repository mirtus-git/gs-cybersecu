"""Execution logger using stdlib sqlite3 and logging."""
from __future__ import annotations

import csv
import io
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from gscs.core.database import get_conn
from gscs.core.models import ExecutionLog, Script

_file_logger = logging.getLogger("gscs.exec")


def setup_file_logger(logs_dir: Path) -> None:
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.log"
    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%dT%H:%M:%SZ")
    )
    _file_logger.addHandler(handler)
    _file_logger.setLevel(logging.INFO)


def log_execution(
    script: Script,
    args: list[str],
    sandbox_mode: str,
    exit_code: int,
    duration: float,
    notes: str = "",
) -> ExecutionLog:
    success = exit_code == 0
    now = datetime.now(timezone.utc).isoformat()
    entry = ExecutionLog(
        script_id=script.id,
        script_name=script.name,
        executed_at=now,
        args_used=json.dumps(args),
        sandbox_mode=sandbox_mode,
        exit_code=exit_code,
        success=success,
        duration_seconds=round(duration, 3),
        notes=notes,
    )
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO execution_logs
               (script_id, script_name, executed_at, args_used, sandbox_mode,
                exit_code, success, duration_seconds, notes)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                entry.script_id, entry.script_name, entry.executed_at,
                entry.args_used, entry.sandbox_mode, entry.exit_code,
                int(entry.success), entry.duration_seconds, entry.notes,
            ),
        )
        entry.id = cur.lastrowid

    status = "SUCCESS" if success else f"FAILED(exit={exit_code})"
    _file_logger.info(
        "script=%s status=%s sandbox=%s duration=%.3fs args=%s",
        script.name, status, sandbox_mode, duration, json.dumps(args),
    )
    return entry


def get_logs(script_name: Optional[str] = None, last_n: Optional[int] = None) -> list[ExecutionLog]:
    with get_conn() as conn:
        if script_name:
            rows = conn.execute(
                "SELECT * FROM execution_logs WHERE script_name = ? ORDER BY executed_at DESC"
                + (f" LIMIT {int(last_n)}" if last_n else ""),
                (script_name,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM execution_logs ORDER BY executed_at DESC"
                + (f" LIMIT {int(last_n)}" if last_n else "")
            ).fetchall()
        return [ExecutionLog.from_row(tuple(r)) for r in rows]


def export_logs(logs: list[ExecutionLog], fmt: str) -> str:
    if fmt == "json":
        data = [
            {
                "id": log.id, "script": log.script_name,
                "executed_at": log.executed_at, "args": log.get_args(),
                "sandbox": log.sandbox_mode, "exit_code": log.exit_code,
                "success": log.success, "duration_seconds": log.duration_seconds,
                "notes": log.notes,
            }
            for log in logs
        ]
        return json.dumps(data, indent=2)
    if fmt == "csv":
        buf = io.StringIO()
        w = csv.DictWriter(
            buf,
            fieldnames=["id", "script", "executed_at", "args", "sandbox",
                        "exit_code", "success", "duration_seconds", "notes"],
        )
        w.writeheader()
        for log in logs:
            w.writerow({
                "id": log.id, "script": log.script_name,
                "executed_at": log.executed_at, "args": " ".join(log.get_args()),
                "sandbox": log.sandbox_mode, "exit_code": log.exit_code,
                "success": log.success, "duration_seconds": log.duration_seconds,
                "notes": log.notes,
            })
        return buf.getvalue()
    raise ValueError(f"Unsupported format: {fmt}")


def purge_old_logs(retention_days: int) -> int:
    if retention_days <= 0:
        return 0
    cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat()
    with get_conn() as conn:
        cur = conn.execute(
            "DELETE FROM execution_logs WHERE executed_at < ?", (cutoff,)
        )
        return cur.rowcount
