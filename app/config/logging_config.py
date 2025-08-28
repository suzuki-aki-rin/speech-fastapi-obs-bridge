from app.config.app_config import app_config
from sandbox import app


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,  # don't disable loggers from other libs
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(asctime)s | %(name)s | %(message)s",
            "use_colors": True,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
        },
        # A new, dedicated formatter for our application logger
        "recog_text_formatter": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(asctime)s | %(message)s",
            "datefmt": app_config.logging.timestamp_format,
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        # A new, dedicated file handler for our application logger
        "recog_text_handler": {
            "formatter": "recog_text_formatter",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": app_config.logging.filepath,
            # "filename": "fastapi_messages.log",
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 5,
        },
        # # A new, dedicated file handler for our application logger
        # "recog_text_handler": {
        #     "formatter": "recog_text_formatter",
        #     "class": "logging.handlers.RotatingFileHandler",
        #     "filename": "fastapi_messages.log",
        #     "maxBytes": 10485760,  # 10 MB
        #     "backupCount": 5,
        # },
    },
    "loggers": {
        # Uvicorn's own loggers
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
        # Your app’s logger
        "app": {"handlers": ["default"], "level": "INFO", "propagate": False},
        # Custom logger for our application, now using the new handler
        "recog_text_logger": {
            "handlers": ["recog_text_handler"],
            "level": "INFO",
            "propagate": False,
        },
    },
    # 👇 Root logger — catches everything else (sqlalchemy, httpx, fastapi internals, etc.)
    "root": {
        "handlers": ["default"],
        "level": "INFO",
    },
}
