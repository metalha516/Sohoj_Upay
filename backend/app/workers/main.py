"""Background worker entrypoint."""

import asyncio
import contextlib
import logging
import signal
import sys

from app.core.config import get_settings
from app.core.logging import setup_logging

logger = logging.getLogger("worker")


async def run_worker() -> None:
    """Run background task worker."""
    settings = get_settings()
    setup_logging(log_level="DEBUG" if settings.debug else "INFO")
    logger.info(
        "Initializing background worker for %s in %s mode", settings.app_name, settings.environment
    )

    stop_event = asyncio.Event()

    def _signal_handler() -> None:
        logger.info("Received termination signal. Shutting down worker...")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, _signal_handler)

    logger.info("Worker ready. Listening for queue tasks...")
    while not stop_event.is_set():
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop_event.wait(), timeout=1.0)

    logger.info("Worker exited gracefully.")


if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
