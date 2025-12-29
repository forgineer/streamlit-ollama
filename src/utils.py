import logging

from config import STREAMLIT_OLLAMA_LOG_FORMAT, STREAMLIT_OLLAMA_LOG_LEVEL


def logger(level: str = STREAMLIT_OLLAMA_LOG_LEVEL, 
           format: str = STREAMLIT_OLLAMA_LOG_FORMAT) -> logging.Logger:
    """
    Setup and return a logger with the specified level and format.

    :param level: The logging level as supported by Streamlit (e.g., "DEBUG", "INFO").
    :param format: The logging format string as supported by Streamlit.
    :return: Configured logger instance.
    """

    from logging.config import dictConfig

    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": format,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": level.upper(),
                "stream": "ext://sys.stdout",
            }
        },
        "loggers": {
            "streamlit-ollama": {
                "handlers": ["console"],
                "level": level.upper(),
                "propagate": False,
            }
        }
    })

    return logging.getLogger("streamlit-ollama")
