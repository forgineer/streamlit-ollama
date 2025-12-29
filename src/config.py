"""
This module contains configuration constants and helpful functions for the Streamlit-Ollama app.

The 'config.toml' file in the .streamlit directory is used for Streamlit-specific 
configurations and will not accept custom configurations.
"""

# The default Ollama host URL. By default it is assumed to be running on localhost.
STREAMLIT_OLLAMA_HOST: str = "http://kryten3:11434"

# Page Layout configuration for Streamlit
STREAMLIT_OLLAMA_PAGE_LAYOUT: str = "wide"  # Options: "centered", "wide"

# Logging configurations
STREAMLIT_OLLAMA_LOG_LEVEL: str = "INFO"
STREAMLIT_OLLAMA_LOG_FORMAT: str = "%(asctime)s: %(levelname)s: %(message)s"

# Path to the avatar image used for the assistant in the chat interface
STREAMLIT_OLLAMA_LOGO: str = "images/logo.png"
STREAMLIT_OLLAMA_ASSISTANT_AVATAR: str = "images/assistant-avatar.png"
STREAMLIT_OLLAMA_USER_AVATAR: str = "images/user-avatar.png"

# Custom greeting message for the assistant
# This will be the initial message from the assistant when the chat starts
# If set to None or an empty string, no greeting will be shown
STREAMLIT_OLLAMA_ASSISTANT_GREETING: str = "How can I help you?"

# Additinal Ollama client configurations defaults
# Keepalive: Model keep-alive duration (for example 5m or 0 to unload immediately)
STREAMLIT_OLLAMA_CLIENT_KEEPALIVE: str = "30m"
