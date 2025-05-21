import logging

import structlog

from resinkit_api.core.config import settings


def configure_logging():
    """
    Configure structlog based on settings from config.py which loads from .env files.

    Configuration:
        LOG_LEVEL: Sets the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default is INFO.
        LOG_JSON_FORMAT: When set to True, logs will be output in JSON format. Default is False (console format).

    Returns:
        A configured structlog logger
    """
    # Get settings from config
    log_level = settings.LOG_LEVEL.upper()
    use_json = settings.LOG_JSON_FORMAT

    # Configure processors based on format
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_source,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if use_json:
        # JSON formatting - more concise exception formatting
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Console formatting - more concise exception rendering
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(colors=False, exception_formatter=structlog.dev.plain_traceback),
        ]
    # Configure structlog
    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    # Configure stdlib logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(message)s [%(name)s %(filename)s]",
        force=True,
    )
    logging.getLogger("stripe").setLevel(logging.ERROR)

    # Configure Python logging to see SQLAlchemy logs
    logging.basicConfig()  # Basic configuration
    logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)

    return structlog.get_logger()


def get_logger(name=None, **context) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger with optional context.

    Args:
        name: Optional name for the logger
        **context: Additional context to bind to the logger

    Returns:
        A configured structlog logger with bound context
    """
    logger = structlog.get_logger(name)
    if context:
        logger = logger.bind(**context)
    return logger
