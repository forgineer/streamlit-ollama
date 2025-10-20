import logging
import streamlit as st

from logging.config import dictConfig
from ollama import Client as OllamaClient


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

# Load Ollama client configuration from Streamlit secrets
ollama_client: dict = st.secrets.get("ollama_client", {})
log.debug(f"Ollama client config: {ollama_client}")

ollama: OllamaClient = OllamaClient(
    host="http://kryten3:11434"
)

# Configuration sidebar
#with st.sidebar:
#    st.title("Configuration")
#    ollama_host = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")

# Main app
st.title("Streamlit-Ollama")
st.caption("A Streamlit chatbot powered by Ollama")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    avatar = 'images/ollama-assistant.png' if msg["role"] == "assistant" else None
    st.chat_message(msg["role"], avatar=avatar).write(msg["content"])

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user", avatar='😀').write(prompt)

    # Call Ollama API
    with st.spinner("Thinking..."):
        response_stream = ollama.chat(model = 'gemma3:12b', 
                                      messages = st.session_state.messages,
                                      stream=True)

        with st.chat_message("assistant", avatar='images/ollama-assistant.png'):
            def response_streamer():
                 for chunk in response_stream:
                     yield chunk.message.content

            st.write_stream(response_streamer)  # Dynamically update the assistant's message

    #st.write_stream(stream_response(response))
    #msg = response.message.content
    #st.session_state.messages.append({"role": "assistant", "content": msg})
    #st.chat_message("assistant", avatar='images/ollama-assistant.png').write(msg)