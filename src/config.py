"""
This module contains configuration constants and helpful functions for the Streamlit-Ollama app.

The 'config.toml' file in the .streamlit directory is used for Streamlit-specific 
configurations and will not accept custom configurations.
"""
import logging


# The default Ollama host URL. By default it is assumed to be running on localhost.
STREAMLIT_OLLAMA_HOST: str = "http://localhost:11434"

# Logging configurations
STREAMLIT_OLLAMA_LOG_LEVEL: str = "INFO"
STREAMLIT_OLLAMA_LOG_FORMAT: str = "%(asctime)s: %(levelname)s: %(message)s"

# Path to the avatar image used for the assistant and user in the chat interface
STREAMLIT_OLLAMA_ASSISTANT_AVATAR: str = "images/ollama-avatar.png"
STREAMLIT_OLLAMA_USER_AVATAR: str = None

# Custom greeting message for the assistant
# This will be the initial message from the assistant when the chat starts
# If set to None or an empty string, no greeting will be shown
STREAMLIT_OLLAMA_ASSISTANT_GREETING: str = "How can I help you?"


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
