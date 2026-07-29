import logging
import json
import sys
import time
from contextvars import ContextVar

# Context variables for tracing
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="unknown")
user_id_var: ContextVar[str] = ContextVar("user_id", default="unauthenticated")

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "trace_id": trace_id_var.get(),
            "user_id": user_id_var.get()
        }
        
        # Inject standard parsed latency if present in log message (hack for simplicity)
        if "Latency:" in record.getMessage():
            try:
                parts = record.getMessage().split("|")
                for part in parts:
                    if "Latency:" in part:
                        val = part.split("Latency:")[1].strip().replace("ms", "").replace("s", "")
                        log_obj["latency_metric"] = float(val)
            except Exception:
                pass

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_obj)

def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    
    # Prevent uvicorn/fastapi from double logging
    logging.getLogger("uvicorn.access").handlers = []
    
    return logger

setup_logger()
