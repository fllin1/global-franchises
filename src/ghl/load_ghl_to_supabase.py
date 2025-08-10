"""
Script to load GHL CSV data into Supabase tables.
"""

from datetime import datetime
from typing import Optional

from loguru import logger
import pandas as pd

from src.api.config.supabase_config import supabase_client
from src.config import PROCESSED_DATA_DIR

# CSV file paths
CONV_CSV = PROCESSED_DATA_DIR / "ghl_conversations.csv"
MSG_CSV = PROCESSED_DATA_DIR / "ghl_messages.csv"


def parse_iso_timestamp(timestamp_str: Optional[str]) -> Optional[str]:
    """
    Parse ISO timestamp string to PostgreSQL compatible format.
    """
    if not timestamp_str:
        return None

    try:
        # Handle different timestamp formats
        if timestamp_str.endswith("Z"):
            # Already in ISO format
            return timestamp_str
        elif "." in timestamp_str:
            # Has milliseconds
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            return dt.isoformat()
        else:
            # Basic ISO format
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            return dt.isoformat()
    except (ValueError, TypeError):
        logger.warning(f"Could not parse timestamp: {timestamp_str}")
        return None


def load_conversations_to_supabase():
    """
    Load conversations from CSV to Supabase.
    """
    if not CONV_CSV.exists():
        logger.error(f"Conversations CSV file not found: {CONV_CSV}")
        return

    supabase = supabase_client()

    # Read CSV with pandas for better handling
    df = pd.read_csv(CONV_CSV)
    logger.info(f"Loaded {len(df)} conversations from CSV")

    # Transform data to match table schema
    conversations_data = []
    for _, row in df.iterrows():
        conversation = {
            "id": row["id"],
            "location_id": row["locationId"],
            "contact_id": row["contactId"],
            "full_name": row["fullName"] if pd.notna(row["fullName"]) else None,
            "company_name": (
                row["companyName"] if pd.notna(row["companyName"]) else None
            ),
            "email": row["email"] if pd.notna(row["email"]) else None,
            "phone": row["phone"] if pd.notna(row["phone"]) else None,
            "date_added": parse_iso_timestamp(row["dateAdded"]),
            "date_updated": parse_iso_timestamp(row["dateUpdated"]),
            "last_message_date": parse_iso_timestamp(row["lastMessageDate"]),
            "last_message_type": (
                row["lastMessageType"] if pd.notna(row["lastMessageType"]) else None
            ),
            "last_message_direction": (
                row["lastMessageDirection"]
                if pd.notna(row["lastMessageDirection"])
                else None
            ),
            "unread_count": (
                int(row["unreadCount"]) if pd.notna(row["unreadCount"]) else 0
            ),
            "tags": row["tags"] if pd.notna(row["tags"]) else None,
            "type": row["type"] if pd.notna(row["type"]) else None,
        }
        conversations_data.append(conversation)

    # Insert data in batches
    batch_size = 100
    total_inserted = 0

    for i in range(0, len(conversations_data), batch_size):
        batch = conversations_data[i : i + batch_size]
        try:
            result = (
                supabase.table("ghl_conversations")
                .upsert(batch, on_conflict="id")
                .execute()
            )
            total_inserted += len(batch)
            logger.info(
                f"Inserted batch {i//batch_size + 1}: {len(batch)} conversations"
            )
        except ValueError as e:
            logger.error(f"Error inserting batch {i//batch_size + 1}: {e}")
            # Try inserting one by one to identify problematic records
            for conv in batch:
                try:
                    supabase.table("ghl_conversations").upsert(
                        [conv], on_conflict="id"
                    ).execute()
                    total_inserted += 1
                except ValueError as e2:
                    logger.error(f"Error inserting conversation {conv['id']}: {e2}")

    logger.success(f"Successfully loaded {total_inserted} conversations to Supabase")


def load_messages_to_supabase():
    """
    Load messages from CSV to Supabase.
    """
    if not MSG_CSV.exists():
        logger.error(f"Messages CSV file not found: {MSG_CSV}")
        return

    supabase = supabase_client()

    # Read CSV with pandas for better handling
    df = pd.read_csv(MSG_CSV)
    logger.info(f"Loaded {len(df)} messages from CSV")

    # Transform data to match table schema
    messages_data = []
    for _, row in df.iterrows():
        message = {
            "id": row["id"],
            "conversation_id": row["conversationId"],
            "contact_id": row["contactId"],
            "location_id": row["locationId"],
            "date_added": parse_iso_timestamp(row["dateAdded"]),
            "message_type": (
                row["messageType"] if pd.notna(row["messageType"]) else None
            ),
            "source": row["source"] if pd.notna(row["source"]) else None,
            "type": row["type"] if pd.notna(row["type"]) else None,
            "direction": (
                row.get("direction") if pd.notna(row.get("direction")) else None
            ),
            "subject": row.get("subject") if pd.notna(row.get("subject")) else None,
            "body_length": (
                int(row["body_length"]) if pd.notna(row["body_length"]) else 0
            ),
            "body_clean_length": (
                int(row["body_clean_length"])
                if pd.notna(row["body_clean_length"])
                else 0
            ),
            "body_clean": row["body_clean"] if pd.notna(row["body_clean"]) else None,
        }
        messages_data.append(message)

    # Insert data in batches
    batch_size = 100
    total_inserted = 0

    for i in range(0, len(messages_data), batch_size):
        batch = messages_data[i : i + batch_size]
        try:
            result = (
                supabase.table("ghl_messages").upsert(batch, on_conflict="id").execute()
            )
            total_inserted += len(batch)
            logger.info(f"Inserted batch {i//batch_size + 1}: {len(batch)} messages")
        except ValueError as e:
            logger.error(f"Error inserting batch {i//batch_size + 1}: {e}")
            # Try inserting one by one to identify problematic records
            for msg in batch:
                try:
                    supabase.table("ghl_messages").upsert(
                        [msg], on_conflict="id"
                    ).execute()
                    total_inserted += 1
                except ValueError as e2:
                    logger.error(f"Error inserting message {msg['id']}: {e2}")

    logger.success(f"Successfully loaded {total_inserted} messages to Supabase")


def verify_data_loaded():
    """
    Verify that data was loaded correctly.
    """
    supabase = supabase_client()

    # Check conversations count
    conv_result = (
        supabase.table("ghl_conversations").select("id", count="exact").execute()
    )
    conv_count = (
        conv_result.count if hasattr(conv_result, "count") else len(conv_result.data)
    )

    # Check messages count
    msg_result = supabase.table("ghl_messages").select("id", count="exact").execute()
    msg_count = (
        msg_result.count if hasattr(msg_result, "count") else len(msg_result.data)
    )

    logger.info(f"Verification - Conversations: {conv_count}, Messages: {msg_count}")

    # Check a few sample records
    sample_conv = supabase.table("ghl_conversations").select("*").limit(1).execute()
    if sample_conv.data:
        logger.info(f"Sample conversation: {sample_conv.data[0]['id']}")

    sample_msg = supabase.table("ghl_messages").select("*").limit(1).execute()
    if sample_msg.data:
        logger.info(f"Sample message: {sample_msg.data[0]['id']}")


def main():
    """
    Main function to load GHL data to Supabase.
    """
    logger.info("Starting GHL data load to Supabase...")

    # Load conversations first (messages depend on conversations)
    logger.info("Loading conversations...")
    load_conversations_to_supabase()

    # Load messages
    logger.info("Loading messages...")
    load_messages_to_supabase()

    # Verify data
    logger.info("Verifying loaded data...")
    verify_data_loaded()

    logger.success("GHL data load completed!")


if __name__ == "__main__":
    main()
