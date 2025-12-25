import config
import os
import streamlit as st

from ollama import ChatResponse, Client as OllamaClient, ListResponse
from sqlalchemy import text


# Ensure data directory exists for storing the SQLite database and other files
if os.path.exists("data") is False:
    os.mkdir("data")


# Configure logging
# Streamlit's logging doesn't seem to work as expected; a custom one will be established for now.
log = config.logger()


class ChatDB:
    """
    Database Connection class for simplified database interactions.
    """
    def __init__(self, connection_name: str):
        try:
            self.connection = st.connection(name=connection_name, type="sql")

            # Enable forign key constraints for SQLite
            with self.connection.session as db_session:
                db_session.execute(text("PRAGMA foreign_keys = ON;"))
        
            # Initialize database tables if they do not exist
            # Create chats table for storing the high-level chat metadata
            with self.connection.session as db_session:
                create_chats_table_sql = """
                    CREATE TABLE IF NOT EXISTS chats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE,
                        model TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                """
                db_session.execute(text(create_chats_table_sql))

                # Create messages table for storing individual messages in each chat
                create_messages_table_sql = """
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id INTEGER NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
                    );
                """
                db_session.execute(text(create_messages_table_sql))
                db_session.commit()
        except Exception as e:
            log.error(f"Failed to connect to database with connection name '{connection_name}'. Error: {e}")
            self.connection = None
    
    def save(self, name: str, model: str, messages: list[dict]):
        """
        Save a chat conversation to the database.
        """
        if self.connection is None:
            log.error("No database connection available. Cannot save chat.")
            return

        try:
            with self.connection.session as db_session:
                # Create the chat entry
                insert_query = "INSERT INTO chats (name, model) VALUES (:name, :model);"
                db_session.execute(text(insert_query), {"name": name, "model": model})
                db_session.commit()

                # Get the chat ID of the newly created chat
                chat_id_query = "SELECT id FROM chats WHERE name = :name;"
                result = db_session.execute(text(chat_id_query), {"name": name})
                chat_id_row = result.fetchone()
                if chat_id_row is None:
                    log.error(f"Failed to retrieve chat ID for chat name '{name}'.")
                    return
                
                chat_id: int = chat_id_row[0]

                # Insert messages into the messages table
                for msg in messages:
                    insert_message_query = "INSERT INTO messages (chat_id, role, content) VALUES (:chat_id, :role, :content);"
                    db_session.execute(text(insert_message_query), {"chat_id": chat_id, "role": msg["role"], "content": msg["content"]})
                db_session.commit()

                st.session_state["chat_id"] = chat_id
                log.info("Chat history saved to database.")
        except Exception as e:
            log.error(f"Failed to save chat history to database. Error: {e}")

    def list(self):
        """
        List saved chats from the SQLite database.
        """
        if self.connection is None:
            log.error("No database connection available. Cannot list chats.")
            return []

        try:
            with self.connection.session as db_session:
                list_chats_sql = "SELECT id, name, model, timestamp FROM chats ORDER BY timestamp DESC;"
                result = db_session.execute(text(list_chats_sql))
                chats = result.fetchall()
                log.info("Fetched saved chats from database.")
                return chats
        except Exception as e:
            log.error(f"Failed to fetch saved chats from database. Error: {e}")
            return []
    
    def save_message(self, chat_id: int, role: str, content: str):
        """
        Add a message to a specific chat.
        """
        if self.connection is None:
            log.error("No database connection available. Cannot add message.")
            return

        try:
            with self.connection.session as db_session:
                insert_message_query = "INSERT INTO messages (chat_id, role, content) VALUES (:chat_id, :role, :content);"
                db_session.execute(text(insert_message_query), {"chat_id": chat_id, "role": role, "content": content})
                db_session.commit()
                log.info(f"Added message to chat ID {chat_id} in database.")
        except Exception as e:
            log.error(f"Failed to add message to chat ID {chat_id} in database. Error: {e}")
    
    def last_model(self):
        """
        Retrieve the last used model from saved chats.
        """
        if self.connection is None:
            log.error("No database connection available. Cannot retrieve last used model.")
            return None

        try:
            with self.connection.session as db_session:
                last_model_sql = "SELECT model FROM chats ORDER BY timestamp DESC LIMIT 1;"
                result = db_session.execute(text(last_model_sql))
                row = result.fetchone()
                if row:
                    log.info("Retrieved last used model from database.")
                    return row[0]
                else:
                    log.info("No saved chats found to retrieve last used model.")
                    return None
        except Exception as e:
            log.error(f"Failed to retrieve last used model from database. Error: {e}")
            return None
    
    def get_messages(self, chat_id: int):
        """
        Retrieve messages for a specific chat ID.
        """
        if self.connection is None:
            log.error("No database connection available. Cannot retrieve messages.")
            return []

        try:
            with self.connection.session as db_session:
                get_messages_sql = "SELECT role, content FROM messages WHERE chat_id = :chat_id ORDER BY id ASC;"
                result = db_session.execute(text(get_messages_sql), {"chat_id": chat_id})
                messages = [{"role": row[0], "content": row[1]} for row in result.fetchall()]
                log.info(f"Retrieved messages for chat ID {chat_id} from database.")
                return messages
        except Exception as e:
            log.error(f"Failed to retrieve messages for chat ID {chat_id} from database. Error: {e}")
            return []

    def delete(self, chat_id: int):
        """
        Delete a chat and its messages from the database.
        """
        if self.connection is None:
            log.error("No database connection available. Cannot delete chat.")
            return

        try:
            with self.connection.session as db_session:
                delete_chat_sql = "DELETE FROM chats WHERE id = :chat_id;"
                db_session.execute(text(delete_chat_sql), {"chat_id": chat_id})
                db_session.commit()
                log.info(f"Deleted chat ID {chat_id} and its messages from database.")
        except Exception as e:
            log.error(f"Failed to delete chat ID {chat_id} from database. Error: {e}")


# Initialize ChatDB instance
# This will manage chat history persistence
chat_db: ChatDB = ChatDB(connection_name="streamlit_ollama_db")


@st.dialog("Save your chat")
def save_chat():
    """
    Dialog to save the current chat session to the database.
    """
    chat_name: str = st.text_input("Give it a unique name or description:")
    if st.button("Save", width="stretch", type="primary"):
        chat_db.save(name=chat_name, 
                     model=st.session_state["selected_model"], 
                     messages=st.session_state["messages"])
        st.rerun()


# Initialize session state variables on first run
if "chat_id" not in st.session_state:
    st.session_state["chat_id"] = None

if "messages" not in st.session_state:
    st.session_state["messages"] = []


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
        last_model: str = chat_db.last_model()

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
                                                      index=st.session_state['selected_model_index'])
    st.session_state['selected_model_index'] = models.index(st.session_state["selected_model"])
    log.debug(f'Current model selected: {st.session_state["selected_model"]}, index: {st.session_state["selected_model_index"]}')

    if st.session_state["chat_id"] is None and len(st.session_state["messages"]) > 0:
        if st.button("Save Chat", width="stretch"):
            save_chat()
    elif st.session_state["chat_id"] and len(st.session_state["messages"]) > 1:
        if st.button("Delete Chat", width="stretch", type="primary"):
            chat_db.delete(chat_id=st.session_state["chat_id"])
            st.session_state["messages"] = []
            st.session_state["chat_id"] = None
            st.rerun()

    with st.container():
        st.markdown("### Saved Chats")
        saved_chats = chat_db.list()
        if not saved_chats:
            st.info("You have no saved chats.")
        else:
            for chat in saved_chats:
                chat_id, chat_name, chat_model, chat_timestamp = chat
                if st.button(f"{chat_name}\r\n ({chat_model})", key=f"chat_{chat_id}"):
                    # Load chat messages from the database
                    st.session_state["messages"] = chat_db.get_messages(chat_id=chat_id)
                    st.session_state["selected_model"] = chat_model
                    st.session_state["chat_id"] = chat_id
                    st.rerun()


# Main app loop
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
