import config

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from streamlit.connections import SQLConnection

# Configure logging
# Streamlit's logging doesn't seem to work as expected; a custom one will be established for now.
log = config.logger()


class ChatExistsError(Exception):
    """Raised when attempting to create a chat with a name that already exists."""
    pass


class ChatDB:
    """
    Database Connection class for simplified database interactions.
    """
    def __init__(self, connection: SQLConnection):
        try:
            self.connection = connection

            # Enable foreign key constraints for SQLite
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
                        model TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
                    );
                """
                db_session.execute(text(create_messages_table_sql))
                db_session.commit()
        except Exception as e:
            log.error(f"Failed to initialize DB connection. Error: {e}")
            self.connection = None
    
    def save_chat(self, name: str, model: str, messages: list[dict]) -> int:
        """
        Save a chat conversation to the database.
        """
        if self.connection is None:
            raise RuntimeError("DB connection not available")

        with self.connection.session as db_session:
            try:
                # Insert chat metadata (unique constraint enforced by DB)
                db_session.execute(
                    text("INSERT INTO chats (name, model) VALUES (:name, :model);"),
                    {"name": name, "model": model}
                )
                db_session.commit()

                # Obtain new chat id
                chat_id = db_session.execute(
                    text("SELECT id FROM chats WHERE name = :name;"),
                    {"name": name}
                ).scalar()

                # Insert messages
                for msg in messages:
                    db_session.execute(
                        text("INSERT INTO messages (chat_id, model, role, content) VALUES (:chat_id, :model, :role, :content);"),
                        {"chat_id": chat_id, "model": model, "role": msg["role"], "content": msg["content"]}
                    )
                db_session.commit()
                return chat_id

            except IntegrityError as ie:
                db_session.rollback()
                # re-raise a clearer, domain-specific error
                raise ChatExistsError(f"Chat with name '{name}' already exists") from ie
            except Exception:
                db_session.rollback()
                log.exception("Unexpected error saving chat")
                raise

    def save_chat_message(self, chat_id: int, model:str, role: str, content: str):
        """
        Add a message to a specific chat.
        """
        if self.connection is None:
            log.error("No database connection available. Cannot add message.")
            return

        try:
            with self.connection.session as db_session:
                insert_message_query = "INSERT INTO messages (chat_id, model, role, content) VALUES (:chat_id, :model, :role, :content);"
                db_session.execute(
                    text(insert_message_query), 
                    {"chat_id": chat_id, "model": model, "role": role, "content": content}
                )
                db_session.commit()
                log.info(f"Added message to chat ID {chat_id} in database.")
        except Exception as e:
            log.error(f"Failed to add message to chat ID {chat_id} in database. Error: {e}")

    def get_chat_messages(self, chat_id: int):
        """
        Retrieve messages for a specific chat ID.
        """
        if self.connection is None:
            log.error("No database connection available. Cannot retrieve messages.")
            return []

        try:
            with self.connection.session as db_session:
                get_messages_sql = "SELECT role, content FROM messages WHERE chat_id = :chat_id ORDER BY id ASC;"
                result = db_session.execute(
                    text(get_messages_sql), 
                    {"chat_id": chat_id}
                )
                messages = [{"role": row[0], "content": row[1]} for row in result.fetchall()]
                log.info(f"Retrieved messages for chat ID {chat_id} from database.")
                return messages
        except Exception as e:
            log.error(f"Failed to retrieve messages for chat ID {chat_id} from database. Error: {e}")
            return []

    def update_chat_model(self, chat_id: int, model: str):
        """
        Update the model used for a specific chat.
        """
        if self.connection is None:
            log.error("No database connection available. Cannot update chat model.")
            return

        try:
            with self.connection.session as db_session:
                update_model_sql = "UPDATE chats SET model = :model WHERE id = :chat_id;"
                db_session.execute(
                    text(update_model_sql), 
                    {"model": model, "chat_id": chat_id}
                )
                db_session.commit()
                log.info(f"Updated model for chat ID {chat_id} to '{model}' in database.")
        except Exception as e:
            log.error(f"Failed to update model for chat ID {chat_id} in database. Error: {e}")

    def delete_chat(self, chat_id: int):
        """
        Delete a chat and its messages from the database.
        """
        if self.connection is None:
            log.error("No database connection available. Cannot delete chat.")
            return

        try:
            with self.connection.session as db_session:
                delete_chat_sql = "DELETE FROM chats WHERE id = :chat_id;"
                db_session.execute(
                    text(delete_chat_sql), 
                    {"chat_id": chat_id}
                )
                db_session.commit()
                log.info(f"Deleted chat ID {chat_id} and its messages from database.")
        except Exception as e:
            log.error(f"Failed to delete chat ID {chat_id} from database. Error: {e}")

    def list_chats(self):
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
    
    def last_used_model(self):
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
