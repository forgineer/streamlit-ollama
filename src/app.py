import config
import streamlit as st

from ollama import ChatResponse, Client as OllamaClient, ListResponse


# Configure logging
# Streamlit's logging doesn't seem to work as expected; a custom one will be established for now.
log = config.logger()


# Streamlit page configuration
# This controls the browser tab title and icon (favicon)
st.set_page_config(
    page_title="Streamlit-Ollama",
    page_icon=config.STREAMLIT_OLLAMA_ASSISTANT_AVATAR
)


# Initialize Ollama Client connection to the specified host
try:
    ollama: OllamaClient = OllamaClient(
        host=config.STREAMLIT_OLLAMA_HOST
    )
except Exception as e:
    log.error(f"Failed to initialize Ollama Client API for host {config.STREAMLIT_OLLAMA_HOST}. Error: {e}")


# Configuration sidebar
with st.sidebar:
    st.title('Streamlit-Ollama')

    # Fetch available models from Ollama
    list_models: ListResponse = ollama.list()
    
    # This is so hacky looking it hurts
    # The ListResponse.models is a list of Model objects, each having a 'model' attribute
    # We extract just the model names for display in the selectbox
    models: list = sorted([model.model for model in list_models.models])
    
    # Maintain selected model state across interactions
    # If not present, default to the first model in the list
    if 'selected_model_index' not in st.session_state:
        st.session_state['selected_model_index'] = 0

    selected_model = st.selectbox('Select a model',
                                  options=models, 
                                  index=st.session_state['selected_model_index'])
    st.session_state['selected_model_index'] = models.index(selected_model)
    log.debug(f'Current model selected: {selected_model}, index: {st.session_state["selected_model_index"]}')


# Main app loop
# Initialize chat messages in session state rith a greeting
if "messages" not in st.session_state:
    if config.STREAMLIT_OLLAMA_ASSISTANT_GREETING:
        st.session_state["messages"] = [{"role": "assistant", "content": config.STREAMLIT_OLLAMA_ASSISTANT_GREETING}]
    else:
        st.session_state["messages"] = []

# Display all messages in the chat history
# This will re-render on each interaction
for msg in st.session_state.messages:
    avatar = config.STREAMLIT_OLLAMA_ASSISTANT_AVATAR if msg["role"] == "assistant" else config.STREAMLIT_OLLAMA_USER_AVATAR
    st.chat_message(msg["role"], avatar=avatar).write(msg["content"])

# Chat input box
# The app will wait here for user input
if prompt := st.chat_input(placeholder=selected_model):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user", avatar=config.STREAMLIT_OLLAMA_USER_AVATAR).write(prompt)

    # Call the Ollama API for a streaming chat response
    # Show a "thinking" spinner while waiting for the response
    with st.spinner("Thinking..."):
        log.debug(f"Using model: {selected_model} for chat response.")
        response_stream: ChatResponse = ollama.chat(model = selected_model, 
                                                    messages = st.session_state.messages,
                                                    stream=True,
                                                    keep_alive=config.STREAMLIT_OLLAMA_CLIENT_KEEPALIVE)

        # Within the chat message context, stream the response
        with st.chat_message("assistant", avatar=config.STREAMLIT_OLLAMA_ASSISTANT_AVATAR):
            def response_streamer():
                 """Generator function to stream response chunks."""
                 for chunk in response_stream:
                     yield chunk.message.content
            
            # Stream the response and capture the full content for the session state
            full_response: str = st.write_stream(response_streamer)  # Dynamically update the assistant's message
            st.session_state.messages.append({"role": "assistant", "content": full_response})
