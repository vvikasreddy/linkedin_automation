# add_messages.py

import json
import psycopg2
import unicodedata
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()


DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
JSON_FILE_PATH = os.getenv("JSON_FILE_PATH")

print(os.path.exists(JSON_FILE_PATH), JSON_FILE_PATH, os.getcwd())

def connect_to_db():
    """Establishes a connection to the PostgreSQL database."""
    try:
        connection = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        print("✅ Connected to the database")
        return connection
    except psycopg2.OperationalError as e:
        print(f"❌ Could not connect to the database. Error: {e}")
        return None

def create_messages_table(cursor):
    """Creates the linkedin_messages table if it doesn't already exist."""
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS linkedin_messages (
      message_id       TEXT,
      conversation_id  TEXT,
      platform         TEXT,
      connection_name  TEXT,
      message_sender   TEXT,
      message_date     TIMESTAMP,
      message_text     TEXT,
      connection_title TEXT,
      PRIMARY KEY (message_id, conversation_id)
    );
    """)
    print("TABLE 'linkedin_messages' is ready.")

def load_json_records(file_path):
    """Loads records from the specified JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"❌ Error: JSON file not found at {file_path}")
        return []
    except json.JSONDecodeError:
        print(f"❌ Error: Could not decode JSON from {file_path}")
        return []

def filter_new_messages(cursor, records):
    """Filters out records that already exist in the database."""
    print("Filtering out messages that are already in the database...")
    new_records = []
    for record in records:
        pair = (record['message_id'], record['conversation_id'])
        cursor.execute("""
        SELECT 1 FROM linkedin_messages
        WHERE message_id = %s AND conversation_id = %s
        """, pair)
        if not cursor.fetchone():
            new_records.append(record)
    print(f"Found {len(new_records)} new messages to add.")
    return new_records

def preprocess_text(text):
    """Normalizes and cleans text to remove special characters."""
    if not text or not isinstance(text, str):
        return ""
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')

def insert_messages(cursor, records):
    """Performs a bulk insert of new messages into the database."""
    if not records:
        print("No new messages to insert.")
        return 0

    # Preprocess message text before insertion
    for record in records:
        record["message_text"] = preprocess_text(record["message_text"])

    sql = """
    INSERT INTO linkedin_messages
      (message_id, conversation_id, platform,
       connection_name, message_sender, message_date,
       message_text, connection_title)
    VALUES %s
    ON CONFLICT (message_id, conversation_id) DO NOTHING;
    """
    
    values = [
        (
          rec["message_id"],
          rec["conversation_id"],
          rec["platform"],
          rec["connection_name"],
          rec["message_sender"],
          rec["message_date"],
          rec["message_text"],
          rec.get("connection_title")
        )
        for rec in records
    ]
    
    execute_values(cursor, sql, values)
    return len(values)

def main():
    """Main execution function to load and save messages."""
    print("--- Starting Message Ingestion Script ---")
    
    # Load records from JSON
    all_records = load_json_records(JSON_FILE_PATH)
    if not all_records:
        return

    # Connect to database
    connection = connect_to_db()
    if not connection:
        return

    try:
        with connection.cursor() as cursor:
            # Ensure table exists
            create_messages_table(cursor)
            
            # Identify only new messages
            new_records = filter_new_messages(cursor, all_records)
            
            # Insert new messages
            inserted_count = insert_messages(cursor, new_records)
            
            # Commit changes
            connection.commit()
            print(f"✅ Successfully inserted {inserted_count} new messages.")
    
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        connection.rollback()
    
    finally:
        if connection:
            connection.close()
            print("--- Script Finished ---")

if __name__ == "__main__":
    main()