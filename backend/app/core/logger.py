import logging
import json
import time
import os
from pathlib import Path
from typing import Any, Dict, Optional
import uuid

class TruncatingFileHandler(logging.FileHandler):
    def __init__(self, filename: Path, max_bytes: int) -> None:
        super().__init__(filename)
        self.max_bytes = max_bytes

    def emit(self, record: logging.LogRecord) -> None:
        try:
            if os.path.exists(self.baseFilename) and os.path.getsize(self.baseFilename) >= self.max_bytes:
                self.acquire()
                try:
                    if self.stream:
                        self.stream.close()
                        self.stream = None
                    self.stream = self._open()
                finally:
                    self.release()
        except Exception:
            pass
        super().emit(record)

class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
        }
        
        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
            
        return json.dumps(log_data)

def get_logger(name: str):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = StructuredFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        log_dir = Path(__file__).resolve().parent.parent.parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = TruncatingFileHandler(
            log_dir / "app.log",
            max_bytes=5 * 1024 * 1024,
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.setLevel(logging.INFO)
    return logger

# Common logger
logger = get_logger("agent_audit")

def log_audit_event(request_id: str, event: str, data: Optional[Dict[str, Any]] = None):
    extra = {"request_id": request_id}
    if data:
        extra["extra_data"] = data
    logger.info(event, extra=extra)
