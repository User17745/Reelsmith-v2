import json
import logging
from datetime import datetime, timezone


def configure_logging():
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def log_event(logger, event, **fields):
    payload = {
        "event": event,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    payload.update(fields)
    logger.info(json.dumps(payload))
