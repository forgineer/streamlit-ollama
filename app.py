import logging
import streamlit as st

from logging.config import dictConfig
from ollama import Client as OllamaClient, ListResponse


# Configure logging
# Streamlit's logging doesn't seem to work as expected; a custom one will be established for now.
dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': st.get_option("logger.messageFormat"),  # Use Streamlit's logger format
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        "console": {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'level': st.get_option("logger.level").upper(),  # Use Streamlit's logger level
            'stream': "ext://sys.stdout",
        }
    },
    'loggers': {
        'streamlit-ollama': {
            'handlers': ['console'],
            'level': st.get_option("logger.level").upper(),  # Use Streamlit's logger level
            'propagate': False,
        }
    }
})

log = logging.getLogger('streamlit-ollama')

ollama_avatar: str = 'images/ollama-avatar.png'

# Streamlit page configuration
st.set_page_config(
    page_title="Streamlit-Ollama",
    page_icon=ollama_avatar
)

# Load Ollama client configuration from Streamlit secrets
ollama_client_secrets: dict = st.secrets.get("ollama_client", {})
log.debug(f"Ollama client secrets: {ollama_client_secrets}")

# Extract host configuration. Assume localhost if not provided.
ollama_host: str = ollama_client_secrets.get("host", "http://localhost:11434")
log.debug(f"Ollama host: {ollama_host}")

try:
    ollama: OllamaClient = OllamaClient(
        host=ollama_host
    )
except Exception as e:
    log.error(f"Failed to initialize Ollama Client API: {e}")

# Configuration sidebar
with st.sidebar:
    st.title("Configuration")
    list_models: ListResponse = ollama.list()
    models: list = sorted([model.model for model in list_models.models]) # This is so hacky looking it hurts
    selected_model = st.selectbox('Select a model', options=models, index=0)
    log.debug(f'Current model selected: {selected_model}')

# Main app
st.title('Streamlit-Ollama')
st.caption('A Streamlit chatbot powered by Ollama.')

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    avatar = ollama_avatar if msg["role"] == "assistant" else None
    st.chat_message(msg["role"], avatar=avatar).write(msg["content"])

if prompt := st.chat_input(placeholder=selected_model):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    log.debug(f'User prompt received: {prompt}')
    log.info(f'Total messages in session: {st.session_state.messages}')

    # Call Ollama API
    with st.spinner("Thinking..."):
        log.debug(f'Using model: {selected_model} for chat response.')
        response_stream = ollama.chat(model = selected_model, 
                                      #messages = st.session_state.messages, # TODO: Make this a configurable option
                                      messages = [{"role": "user", "content": prompt}],
                                      stream=True)

        # Within the chat message context...
        with st.chat_message("assistant", avatar=ollama_avatar):
            def response_streamer():
                 """Generator function to stream response chunks."""
                 for chunk in response_stream:
                     yield chunk.message.content
            
            # Stream the response and capture the full content for the session state
            full_response: str = st.write_stream(response_streamer)  # Dynamically update the assistant's message
            st.session_state.messages.append({"role": "assistant", "content": full_response})
