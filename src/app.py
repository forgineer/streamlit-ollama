import config
import os
import streamlit as st
import utils

from db import ChatDB, ChatExistsError
from ollama import ChatResponse, Client as OllamaClient
from streamlit.connections import SQLConnection


# Ensure data directory exists for storing the SQLite database and other files
os.makedirs("data", exist_ok=True)


# Configure logging
# Streamlit's logging doesn't seem to work as expected; a custom one will be established for now.
log = utils.logger()


# Streamlit page configuration
# This controls the browser tab title and icon (favicon)
st.set_page_config(
    page_title="Streamlit-Ollama",
    page_icon=config.STREAMLIT_OLLAMA_LOGO,
    layout=config.STREAMLIT_OLLAMA_PAGE_LAYOUT
)


# Initialize ChatDB instance
# This will manage chat history persistence
try:
    connection: SQLConnection = st.connection(name="streamlit_ollama_db", type="sql")
    chat_db: ChatDB = ChatDB(connection=connection)
except Exception as e:
    log.error(f"Failed to initialize ChatDB. Error: {e}")
    st.error("Failed to initialize chat database; chat history will not be saved.")
    connection = chat_db = None


# Initialize Ollama Client connection to the specified host
try:
    ollama = OllamaClient(host=config.STREAMLIT_OLLAMA_HOST)
except Exception as e:
    log.error(f"Failed to initialize Ollama Client API for host {config.STREAMLIT_OLLAMA_HOST}. Error: {e}")
    ollama = None


# Initialize session state variables on first run
if "chat_id" not in st.session_state:
    st.session_state["chat_id"] = None

if "messages" not in st.session_state:
    st.session_state["messages"] = []


@st.dialog("Save your chat", width="medium")
def save_chat() -> None:
    """
    Dialog to save the current chat session to the database.
    """
    chat_name: str = st.text_input("Give it a unique name or description:")
    if st.button("Save", width="stretch", type="primary"):
        try:
            chat_id: int = chat_db.save_chat(name=chat_name, 
                                             model=st.session_state["selected_model"], 
                                             messages=st.session_state["messages"])
            st.session_state["chat_id"] = chat_id
            st.success("Chat saved!")
        except ChatExistsError as e:
            st.error(str(e))
        except Exception as e:
            log.exception("Unexpected error saving chat")
            st.error("Unexpected error saving chat — check logs.")
        st.rerun()


@st.dialog("Are you sure you want to delete this chat?", width="medium")
def delete_chat(chat_id: int) -> None:
    """
    Dialog to ensure you want to delete the saved chat.
    """
    if st.button("Delete", width="stretch", type="primary"):
        chat_db.delete_chat(chat_id=chat_id)
        st.session_state["messages"] = []
        st.session_state["chat_id"] = None
        st.rerun()


def update_chat_model() -> None:
    """
    Update the model used for the current chat in the database.
    Is called when the model selection changes in the sidebar.
    """
    if st.session_state["chat_id"]:
        chat_db.update_chat_model(chat_id=st.session_state["chat_id"],
                                  model=st.session_state["selected_model"])


with st.sidebar:
    st.image(config.STREAMLIT_OLLAMA_LOGO)
    st.title('Streamlit-Ollama')

    # New Chat button
    # Clears current messages and chat ID. Made available only if there is a chat in progress.
    if len(st.session_state["messages"]) > 0:
        if st.button('New Chat', width="stretch"):
            st.session_state["messages"] = []
            st.session_state["chat_id"] = None
            st.rerun()

    # Fetch available models from Ollama server
    if ollama is None:
        st.error("Ollama client unavailable; model list unavailable.")
        models = []
    else:
        list_models = ollama.list()
        models = sorted([m.model for m in list_models.models])
    
    # Determine default model selection
    # Check for last used model from chat history
    if st.session_state.get("selected_model", None) is None:
        last_used_model: str = chat_db.last_used_model()

        if last_used_model and last_used_model in models:
            st.session_state['selected_model_index'] = models.index(last_used_model)
        else:
            st.session_state['selected_model_index'] = 0  # Fallback to the first model in the list
    else:
        if st.session_state["selected_model"] in models:
            st.session_state['selected_model_index'] = models.index(st.session_state["selected_model"])
        else:
            st.session_state['selected_model_index'] = 0  # Fallback to the first model in the list

    # Model selection dropdown
    st.session_state["selected_model"] = st.selectbox('Select a model', 
                                                      options=models, 
                                                      index=st.session_state['selected_model_index'],
                                                      on_change=update_chat_model)
    st.session_state['selected_model_index'] = models.index(st.session_state["selected_model"])
    log.debug(f'Current model selected: {st.session_state["selected_model"]}, index: {st.session_state["selected_model_index"]}')

    # Save Chat / Delete Chat buttons
    if st.session_state["chat_id"] is None and len(st.session_state["messages"]) > 0:
        if st.button("Save Chat", width="stretch"):
            save_chat()
    elif st.session_state["chat_id"] and len(st.session_state["messages"]) > 1:
        if st.button("Delete Chat", width="stretch", type="primary"):
            delete_chat(chat_id=st.session_state["chat_id"])

    # Display saved chats as buttons
    # Clicking a button loads that chat's messages into the main chat area
    with st.container():
        st.markdown("### Saved Chats")
        saved_chats = chat_db.list_chats()

        if not saved_chats:
            st.info("You have no saved chats.")
        else:
            for chat in saved_chats:
                chat_id, chat_name, chat_model, chat_timestamp = chat
                if st.button(f"{chat_name}\n ({chat_model})", key=f"chat_{chat_id}", width="stretch"):
                    # Load chat messages from the database
                    st.session_state["messages"] = chat_db.get_chat_messages(chat_id=chat_id)
                    st.session_state["selected_model"] = chat_model
                    st.session_state["chat_id"] = chat_id
                    st.rerun()


# Initialize chat messages in session state with a greeting (if configured)
if len(st.session_state["messages"]) == 0:
    if config.STREAMLIT_OLLAMA_ASSISTANT_GREETING:
        st.session_state["messages"] = [{"role": "assistant", "content": config.STREAMLIT_OLLAMA_ASSISTANT_GREETING}]
    else:
        st.session_state["messages"] = []


# Write out the chat messages to the screen
for msg in st.session_state["messages"]:
    avatar = config.STREAMLIT_OLLAMA_ASSISTANT_AVATAR if msg["role"] == "assistant" else config.STREAMLIT_OLLAMA_USER_AVATAR
    st.chat_message(msg["role"], width="stretch", avatar=avatar).write(msg["content"])


# Chat input box
# The app will wait here for user input
if prompt := st.chat_input(placeholder=st.session_state["selected_model"]):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.chat_message("user", avatar=config.STREAMLIT_OLLAMA_USER_AVATAR, width="stretch").write(prompt)

    # Save the user message to the database if chat is saved
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
                                                    messages = st.session_state["messages"],
                                                    stream=True,
                                                    keep_alive=config.STREAMLIT_OLLAMA_CLIENT_KEEPALIVE)

        # Within the chat message context, stream the response
        with st.chat_message("assistant", avatar=config.STREAMLIT_OLLAMA_ASSISTANT_AVATAR, width="stretch"):
            def response_streamer():
                 """Generator function to stream response chunks."""
                 for chunk in response_stream:
                     yield chunk.message.content
            
            # Stream the response and capture the full content for the session state
            # Save the full response to the database if chat is saved
            full_response: str = st.write_stream(response_streamer)  # Dynamically update the assistant's message
            st.session_state["messages"].append({"role": "assistant", "content": full_response})
            if st.session_state["chat_id"]:
                chat_db.save_chat_message(chat_id=st.session_state["chat_id"],
                                          model=st.session_state["selected_model"],
                                          role="assistant",
                                          content=full_response)
