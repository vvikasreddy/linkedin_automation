# generate_summaries.py

import os
import json
import re
import psycopg2
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from tqdm import tqdm
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

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

def create_summary_table(cursor):
    """Creates the linkedin_summary table if it doesn't already exist."""
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS linkedin_summary (
        message_id      TEXT PRIMARY KEY,
        conversation_id TEXT,
        connection_name TEXT,
        message_sender  TEXT, 
        message_date    TIMESTAMP,
        chat_summary    TEXT,
        company         TEXT
    );
    """)
    print("TABLE 'linkedin_summary' is ready.")

def find_conversations_to_update(cursor):
    """
    Compares linkedin_messages and linkedin_summary tables to find conversations
    that are new or have been updated.
    """
    # 1. Get the latest conversation_id for each message_id in the messages table
    cursor.execute("SELECT message_id, conversation_id FROM linkedin_messages")
    latest_conv_ids = {}
    for message_id, conversation_id in cursor.fetchall():
        conv_num = int(conversation_id.replace("conv_", ""))
        if message_id not in latest_conv_ids or conv_num > latest_conv_ids[message_id][0]:
            latest_conv_ids[message_id] = (conv_num, conversation_id)

    # 2. Get the conversation_ids already present in the summary table
    cursor.execute("SELECT message_id, conversation_id FROM linkedin_summary")
    summary_conv_ids = {mid: cid for mid, cid in cursor.fetchall()}

    # 3. Find mismatches
    mismatches = {}
    for message_id, (_, latest_cid) in latest_conv_ids.items():
        
        summary_cid = summary_conv_ids.get(message_id, "not present")
        # print(summary_cid, latest_cid)
        if (latest_cid == "conv_0" and summary_cid == "not present") or summary_cid != latest_cid:
            mismatches[message_id] = {
                "latest_cid": latest_cid,
                "summary_cid": "conv_0" if summary_cid == "not present" else summary_cid
            }
    
    print(f"Found {len(mismatches)} conversations to summarize or update.")
    return mismatches

def get_conversation_text(cursor, message_id, start_conv_id):
    """Retrieve messages for a given message_id, starting from a specific conversation_id."""
    cursor.execute("""
        SELECT message_sender, message_date, message_text, connection_title, conversation_id
        FROM linkedin_messages
        WHERE message_id = %s
        ORDER BY message_date ASC
    """, (message_id,))
    
    rows = cursor.fetchall()
    conversation = ""
    title = ""
    start_conv_num = int(start_conv_id.replace("conv_", ""))

    for row in rows:
        sender, date, text, row_title, conv_id_last = row
        title = row_title or title  # Keep the last non-null title
        if int(conv_id_last.replace("conv_", "")) >= start_conv_num:
            conversation += f"{sender} ({date}): {text}\n"
            
    return conversation.strip(), title

def setup_llm_chains():
    """Initializes and returns the LangChain LLM, prompts, and chains."""
    load_dotenv()
    api_key = os.getenv("SUMMARIES_OPENAI")
    if not api_key:
        raise ValueError("SUMMARIES_OPENAI environment variable not set.")

    llm = ChatOpenAI(openai_api_key=api_key, temperature=0.3, model="gpt-3.5-turbo")

    # Prompt for generating a brand new summary
    new_summary_prompt = PromptTemplate(
        input_variables=["conversation"],
        template="""You are a helpful assistant that summarizes LinkedIn chat conversations.
        Summarize the conversation below in 3–5 sentences. Focus on:
        - Who I messaged and their role/company
        - My intent (e.g., asking for a referral, meeting, or recruiter intro)
        - Their response and any follow-up actions
        - Outcome or current status (e.g., they agreed, ignored, redirected)
        \n\n{conversation}"""
    )

    # Prompt for updating an existing summary with new messages
    update_summary_prompt = PromptTemplate(
        input_variables=["conversation", "summary"],
        template="""You are a helpful assistant that updates summaries of LinkedIn chat conversations.
        Update the existing summary based on the new conversation below. Focus on:
        - The new messages and any changes in context
        - Any new actions taken or responses received
        - Integrate new information into the previous summary seamlessly.
        \n\nPrevious Summary: {summary}
        \n\nNew Conversation: {conversation}"""
    )
    
    # Prompt for extracting the company name in JSON format
    json_prompt = PromptTemplate(
        input_variables=["conversation", "title"],
        template="""You are an assistant that extracts the company name from a LinkedIn chat.
        Based on the conversation and title, identify the company name. If it cannot be determined, return "None".
        Output only a JSON object with a single key "company_name".
        
        Example: {{"company_name": "Google"}}
        
        Conversation: {conversation}
        Title: {title}
        """
    )

    return {
        "new_summary_chain": LLMChain(llm=llm, prompt=new_summary_prompt),
        "update_summary_chain": LLMChain(llm=llm, prompt=update_summary_prompt),
        "json_chain": LLMChain(llm=llm, prompt=json_prompt)
    }

def clean_summary(text):
    """Removes boilerplate headers like 'Summary:' from the LLM output."""
    if not isinstance(text, str):
        return text
    # Use regex to remove "Summary:", "Updated Summary:", etc., case-insensitively, and trim whitespace
    return re.sub(r"^(updated summary|summary):(\s*conv_\d+\s*)?", "", text.strip(), flags=re.IGNORECASE).strip()

def get_latest_message_details(cursor, message_id, conversation_id):
    """Retrieve details from the most recent message in a thread."""
    cursor.execute("""
        SELECT message_sender, message_date, connection_name
        FROM linkedin_messages
        WHERE message_id = %s AND conversation_id = %s
    """, (message_id, conversation_id))
    return cursor.fetchone() or (None, None, None)

def process_and_save_summaries(connection, mismatches, chains):
    """Main loop to generate, update, and save summaries."""
    upsert_sql = """
        INSERT INTO linkedin_summary 
            (message_id, conversation_id, chat_summary, company, message_sender, message_date, connection_name)
        VALUES 
            (%(message_id)s, %(conversation_id)s, %(summary)s, %(company)s, %(message_sender)s, %(message_date)s, %(connection_name)s)
        ON CONFLICT (message_id) DO UPDATE SET
            conversation_id = EXCLUDED.conversation_id,
            chat_summary = EXCLUDED.chat_summary,
            company = EXCLUDED.company,
            message_sender = EXCLUDED.message_sender,
            message_date = EXCLUDED.message_date,
            connection_name = EXCLUDED.connection_name;
    """
    
    update_partial_sql = """
        UPDATE linkedin_summary
        SET 
            conversation_id = %(conversation_id)s, 
            chat_summary = %(summary)s, 
            message_sender = %(message_sender)s, 
            message_date = %(message_date)s
        WHERE 
            message_id = %(message_id)s;
    """

    cursor = connection.cursor()

    for message_id, conv_data in tqdm(mismatches.items(), desc="Processing Summaries"):
        try:
            is_new_summary = conv_data["summary_cid"] == "conv_0"
            
            conversation, title = get_conversation_text(cursor, message_id, conv_data["summary_cid"])
            if not conversation:
                continue
            
            summary_data = {"message_id": message_id, "conversation_id": conv_data["latest_cid"]}

            if is_new_summary:
                # Generate new summary and extract company
                summary_text = chains["new_summary_chain"].run(conversation=conversation)
                company_json_str = chains["json_chain"].run(conversation=conversation, title=title)
                company_data = json.loads(company_json_str)
                summary_data["company"] = company_data.get("company_name", "None")
                summary_data["summary"] = clean_summary(summary_text)
                
                # Get details for the summary record
                sender, date, name = get_latest_message_details(cursor, message_id, conv_data["latest_cid"])
                summary_data.update({"message_sender": sender, "message_date": date, "connection_name": name})

                cursor.execute(upsert_sql, summary_data)
            else:
                # Fetch old summary and generate an updated one
                cursor.execute("SELECT chat_summary FROM linkedin_summary WHERE message_id = %s", (message_id,))
                old_summary = cursor.fetchone()[0]
                updated_summary_text = chains["update_summary_chain"].run(conversation=conversation, summary=old_summary)
                summary_data["summary"] = clean_summary(updated_summary_text)

                # Get details for the summary record
                sender, date, _ = get_latest_message_details(cursor, message_id, conv_data["latest_cid"])
                summary_data.update({"message_sender": sender, "message_date": date})

                cursor.execute(update_partial_sql, summary_data)
            
            connection.commit()

        except Exception as e:
            print(f"\n❌ Error processing message_id {message_id}: {e}")
            connection.rollback()
    
    cursor.close()

def main():
    """Main execution function to generate and save summaries."""
    print("--- Starting Summary Generation Script ---")
    
    try:
        chains = setup_llm_chains()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return

    connection = connect_to_db()
    if not connection:
        return
        
    try:
        with connection.cursor() as cursor:
            create_summary_table(cursor)
            conversations_to_process = find_conversations_to_update(cursor)
        
        if conversations_to_process:
            process_and_save_summaries(connection, conversations_to_process, chains)
            print("✅ Summarization process complete.")
        else:
            print("No new summaries to generate.")
            
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
    finally:
        if connection:
            connection.close()
            print("--- Script Finished ---")

if __name__ == "__main__":
    main()