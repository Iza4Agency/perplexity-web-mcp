"""Trace logging module for perplexity-web-mcp API server.

Borrowing design principles from relay-ai:
- Logs un-truncated request/response payloads to ~/.config/perplexity-web-mcp/logs/api-trace.log
- Automatic secret redaction for auth tokens and API keys
- Resets log file on server start when trace mode is active (PWM_TRACE=1 or --trace)
"""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import re

CONFIG_DIR = Path.home() / ".config" / "perplexity-web-mcp"
LOGS_DIR = CONFIG_DIR / "logs"
TRACE_LOG_FILE = LOGS_DIR / "api-trace.log"

ENV_TRACE_KEY = "PWM_TRACE"

REDACTION_PATTERNS = [
    # Authorization / Bearer tokens
    (re.compile(r"Bearer\s+[A-Za-z0-9._\-+/=]+", re.IGNORECASE), "Bearer [REDACTED]"),
    (re.compile(r'("authorization"\s*:\s*")[^"]+', re.IGNORECASE), r'\1[REDACTED]'),
    (re.compile(r'(x-api-key"\s*:\s*")[^"]+', re.IGNORECASE), r'\1[REDACTED]'),
    # Session tokens / Cookies
    (re.compile(r'(session-token"\s*:\s*")[^"]+', re.IGNORECASE), r'\1[REDACTED]'),
    (re.compile(r'(session_token"\s*:\s*")[^"]+', re.IGNORECASE), r'\1[REDACTED]'),
    (re.compile(r"__secure-next-auth\.session-token=[^;\s]+", re.IGNORECASE), "__secure-next-auth.session-token=[REDACTED]"),
    # General API key prefixes
    (re.compile(r"\bsk-ant-[A-Za-z0-9_-]{8,}\b"), "sk-ant-[REDACTED]"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"), "sk-[REDACTED]"),
    (re.compile(r"\bAIza[A-Za-z0-9_-]{20,}\b"), "AIza[REDACTED]"),

]


def is_trace_enabled() -> bool:
    """Check if trace mode is enabled via environment variable."""
    return os.getenv(ENV_TRACE_KEY) == "1"


def get_trace_log_path() -> Path:
    """Get absolute path to the trace log file."""
    return TRACE_LOG_FILE


def reset_trace_log() -> None:
    """Reset trace log file for a new server session."""
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        LOGS_DIR.chmod(0o700)
        if TRACE_LOG_FILE.exists():
            TRACE_LOG_FILE.unlink()
        TRACE_LOG_FILE.touch(mode=0o600)
    except Exception:
        pass


def redact_trace_line(line: str) -> str:
    """Scrub sensitive credentials from a log line."""
    out = line
    for pattern, replacement in REDACTION_PATTERNS:
        out = pattern.sub(replacement, out)
    return out


def log_trace(message: str) -> None:
    """Log a message to the trace log if trace mode is enabled."""
    if not is_trace_enabled():
        return

    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        redacted = redact_trace_line(message)
        log_entry = f"[{timestamp}] {redacted}\n"

        with TRACE_LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(log_entry)
        TRACE_LOG_FILE.chmod(0o600)
    except Exception:
        pass
