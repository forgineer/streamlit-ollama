import config
import os
import streamlit as st

from db import ChatDB
from ollama import ChatResponse, Client as OllamaClient, ListResponse


# Ensure data directory exists for storing the SQLite database and other files
if os.path.exists("data") is False:
    os.mkdir("data")


# Configure logging
# Streamlit's logging doesn't seem to work as expected; a custom one will be established for now.
log = config.logger()


# Streamlit page configuration
# This controls the browser tab title and icon (favicon)
st.set_page_config(
    page_title="Streamlit-Ollama",
    page_icon=config.STREAMLIT_OLLAMA_ASSISTANT_AVATAR
)


# Initialize ChatDB instance
# This will manage chat history persistence
chat_db: ChatDB = ChatDB(connection_name="streamlit_ollama_db")


# Initialize Ollama Client connection to the specified host
try:
    ollama: OllamaClient = OllamaClient(
        host=config.STREAMLIT_OLLAMA_HOST
    )
except Exception as e:
    log.error(f"Failed to initialize Ollama Client API for host {config.STREAMLIT_OLLAMA_HOST}. Error: {e}")


# Initialize session state variables on first run
if "chat_id" not in st.session_state:
    st.session_state["chat_id"] = None

if "messages" not in st.session_state:
    st.session_state["messages"] = []


@st.dialog("Save your chat", width="medium")
def save_chat():
    """
    Dialog to save the current chat session to the database.
    """
    chat_name: str = st.text_input("Give it a unique name or description:")
    if st.button("Save", width="stretch", type="primary"):
        chat_id: int = chat_db.save_chat(name=chat_name, 
                                         model=st.session_state["selected_model"], 
                                         messages=st.session_state["messages"])
        st.session_state["chat_id"] = chat_id
        st.rerun()


@st.dialog("Are you sure you want to delete this chat?", width="medium")
def delete_chat(chat_id: int):
    """
    Dialog to ensure you want to delete the saved chat.
    """
    if st.button("Delete", width="stretch", type="primary"):
        chat_db.delete_chat(chat_id=chat_id)
        st.session_state["messages"] = []
        st.session_state["chat_id"] = None
        st.rerun()


# Update saved chat model when changed from sidebar
def update_chat_model():
    """
    Update the model used for the current chat in the database.
    """
    if st.session_state["chat_id"]:
        chat_db.update_chat_model(chat_id=st.session_state["chat_id"],
                                  model=st.session_state["selected_model"])


with st.sidebar:
    st.title('Streamlit-Ollama')

    if len(st.session_state["messages"]) > 0:
        if st.button('New Chat', width="stretch"):
            st.session_state["messages"] = []
            st.session_state["chat_id"] = None
            st.rerun()

    # Fetch available models from Ollama
    list_models: ListResponse = ollama.list()
    
    # This is so hacky looking it hurts
    # The ListResponse.models is a list of Model objects, each having a 'model' attribute
    # We extract just the model names for display in the selectbox
    models: list = sorted([model.model for model in list_models.models])
    
    # Determine default model selection
    # Check for last used model from chat history
    if st.session_state.get("selected_model") is None:
        last_model: str = chat_db.last_used_model()

        if last_model and last_model in models:
            st.session_state['selected_model_index'] = models.index(last_model)
        else:
            st.session_state['selected_model_index'] = 0  # Fallback to the first model in the list
    else:
        if st.session_state["selected_model"] in models:
            st.session_state['selected_model_index'] = models.index(st.session_state["selected_model"])
        else:
            st.session_state['selected_model_index'] = 0  # Fallback to the first model in the list

    st.session_state["selected_model"] = st.selectbox('Select a model', 
                                                      options=models, 
                                                      index=st.session_state['selected_model_index'],
                                                      on_change=update_chat_model())
    st.session_state['selected_model_index'] = models.index(st.session_state["selected_model"])
    log.debug(f'Current model selected: {st.session_state["selected_model"]}, index: {st.session_state["selected_model_index"]}')

    if st.session_state["chat_id"] is None and len(st.session_state["messages"]) > 0:
        if st.button("Save Chat", width="stretch"):
            save_chat()
    elif st.session_state["chat_id"] and len(st.session_state["messages"]) > 1:
        if st.button("Delete Chat", width="stretch", type="primary"):
            delete_chat(chat_id=st.session_state["chat_id"])

    with st.container():
        st.markdown("### Saved Chats")
        saved_chats = chat_db.list_chats()
        if not saved_chats:
            st.info("You have no saved chats.")
        else:
            for chat in saved_chats:
                chat_id, chat_name, chat_model, chat_timestamp = chat
                if st.button(f"{chat_name}\r\n ({chat_model})", key=f"chat_{chat_id}"):
                    # Load chat messages from the database
                    st.session_state["messages"] = chat_db.get_chat_messages(chat_id=chat_id)
                    st.session_state["selected_model"] = chat_model
                    st.session_state["chat_id"] = chat_id
                    st.rerun()


# Initialize chat messages in session state rith a greeting
if len(st.session_state["messages"]) == 0:
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
if prompt := st.chat_input(placeholder=st.session_state["selected_model"]):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user", avatar=config.STREAMLIT_OLLAMA_USER_AVATAR).write(prompt)

    if st.session_state["chat_id"]:
        chat_db.save_chat_message(chat_id=st.session_state["chat_id"],
                                  model=st.session_state["selected_model"],
                                  role="user",
                                  content=prompt)

    # Call the Ollama API for a streaming chat response
    # Show a "thinking" spinner while waiting for the response
    with st.spinner("Thinking..."):
        log.debug(f"Using model: {st.session_state["selected_model"]} for chat response.")
        response_stream: ChatResponse = ollama.chat(model = st.session_state["selected_model"], 
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
            if st.session_state["chat_id"]:
                chat_db.save_chat_message(chat_id=st.session_state["chat_id"],
                                          model=st.session_state["selected_model"],
                                          role="assistant",
                                          content=full_response)
