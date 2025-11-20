import asyncio
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional

from loguru import logger
from supabase import Client

from src.api.config.supabase_config import supabase_client
from src.ghl.utils.template_matcher import is_template_message
from src.ghl.utils.message_classifier import classify_message
from src.ghl.utils.territory_extractor import extract_territories

BATCH_SIZE = 50

async def fetch_unprocessed_messages(supabase: Client, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch messages that haven't been processed yet.
    Joins with conversations to get company_name.
    """
    # Supabase-py doesn't support complex joins easily in one go for generic queries without views
    # So we fetch messages first, then their conversations
    
    # 1. Fetch unprocessed messages
    # filtering for inbound messages only as we care about replies
    # but user said "mainly the ones that are being sent by someone else"
    # so we filter by direction='inbound' or check if it's NOT our template
    # We'll fetch pending messages regardless of direction for now, but optimize for inbound in logic
    
    response = (
        supabase.table("ghl_messages")
        .select("*")
        .eq("processed", False)
        # .eq("direction", "inbound") # Optional optimization if direction is reliable
        .limit(limit)
        .execute()
    )
    messages = response.data
    
    if not messages:
        return []
        
    # 2. Enrich with conversation details (company_name)
    enriched_messages = []
    
    # Get all conversation IDs
    conv_ids = list(set(msg["conversation_id"] for msg in messages))
    
    # Fetch conversations
    # Batch fetch conversations
    conversations_map = {}
    for i in range(0, len(conv_ids), 100):
        batch_ids = conv_ids[i:i+100]
        conv_response = (
            supabase.table("ghl_conversations")
            .select("id, company_name")
            .in_("id", batch_ids)
            .execute()
        )
        for conv in conv_response.data:
            conversations_map[conv["id"]] = conv
            
    # Match franchises
    # We need to map company_name -> franchise_id
    # Get all unique company names
    company_names = list(set(
        conv.get("company_name") 
        for conv in conversations_map.values() 
        if conv.get("company_name")
    ))
    
    franchise_map = {} # name -> id
    if company_names:
        # Fetch franchises matching names
        # This might need chunking if too many names
        # For now assume manageable batch
        fran_response = (
            supabase.table("franchises")
            .select("id, franchise_name")
            .in_("franchise_name", company_names)
            .execute()
        )
        for f in fran_response.data:
            franchise_map[f["franchise_name"]] = f["id"]
            
    # Join everything
    for msg in messages:
        conv = conversations_map.get(msg["conversation_id"])
        if not conv:
            logger.warning(f"Message {msg['id']} has no conversation found")
            continue
            
        company_name = conv.get("company_name")
        franchise_id = franchise_map.get(company_name)
        
        # We process even if franchise_id is missing, to mark it as processed (and maybe log it)
        # Or skip? Better to mark processed so we don't retry forever
        
        enriched_messages.append({
            "message": msg,
            "company_name": company_name,
            "franchise_id": franchise_id
        })
        
    return enriched_messages

async def process_message_batch(batch: List[Dict[str, Any]], supabase: Client):
    """
    Process a batch of messages.
    """
    updates = []
    territory_inserts = []
    
    for item in batch:
        msg = item["message"]
        franchise_id = item["franchise_id"]
        body = msg.get("body_clean") or ""
        msg_id = msg["id"]
        
        # Initialize flags
        is_template = False
        is_ooo = False
        has_attachment = False
        
        # 1. Check Template
        if is_template_message(body):
            logger.info(f"Message {msg_id} is a template message. Skipping extraction.")
            is_template = True
        else:
            # 2. Classify
            # Only classify if not template
            classification = await classify_message(body)
            is_ooo = classification["is_out_of_office"]
            has_attachment = classification["has_attachment_mention"]
            
            # 3. Extract Territories
            # Only extract if it's a valid reply (not OOO) and we have a franchise matched
            if not is_ooo and franchise_id:
                territories = await extract_territories(body)
                if territories:
                    logger.info(f"Extracted {len(territories)} territories from message {msg_id}")
                    for t in territories:
                        territory_inserts.append({
                            "franchise_id": franchise_id,
                            "location_raw": t["location_raw"],
                            "state_code": t.get("state_code"),
                            "availability_status": t["availability_status"],
                            "check_date": t.get("check_date") or datetime.now().isoformat()
                        })
            elif not franchise_id and not is_ooo:
                logger.warning(f"Message {msg_id} has no matching franchise for company '{item['company_name']}'")

        # Prepare update for message
        updates.append({
            "id": msg_id,
            "processed": True,
            "is_out_of_office": is_ooo,
            "has_attachment_mention": has_attachment
        })

    # Execute Database Operations
    
    # 1. Insert Territories
    if territory_inserts:
        try:
            # Bulk insert
            # Chunk inserts if necessary
            for i in range(0, len(territory_inserts), 100):
                chunk = territory_inserts[i:i+100]
                supabase.table("territory_checks").insert(chunk).execute()
            logger.success(f"Inserted {len(territory_inserts)} territory checks")
        except Exception as e:
            logger.error(f"Failed to insert territory checks: {e}")
            
    # 2. Update Messages
    # Bulk update is tricky with different values per row in Supabase/PostgREST usually
    # Upsert works if we provide all keys.
    # We need to make sure we don't overwrite other fields.
    # Best approach: Update one by one or use upsert with all fields?
    # Updating one by one is safer but slower.
    # Or constructing a big upsert if we have the full row data.
    # Let's try updating one by one for safety first, optimize later if too slow.
    # Actually, for 50 items, parallel asyncio gather is good.
    
    update_tasks = []
    for update in updates:
        task = supabase.table("ghl_messages").update({
            "processed": True,
            "is_out_of_office": update["is_out_of_office"],
            "has_attachment_mention": update["has_attachment_mention"]
        }).eq("id", update["id"]).execute()
        # We don't await here if we want parallel, but supabase client is sync by default unless async client used?
        # The project uses sync supabase client in `src/api/config/supabase_config.py`.
        # So we just run it.
        
    logger.info(f"Updated {len(updates)} messages as processed")


async def main():
    parser = argparse.ArgumentParser(description="Process GHL messages for territory extraction")
    parser.add_argument("--limit", type=int, default=100, help="Number of messages to process")
    parser.add_argument("--loop", action="store_true", help="Run in a continuous loop")
    args = parser.parse_args()
    
    supabase = supabase_client()
    
    logger.info("Starting territory reply processing...")
    
    while True:
        try:
            # Fetch batch
            batch = await fetch_unprocessed_messages(supabase, args.limit)
            
            if not batch:
                logger.info("No unprocessed messages found.")
                if not args.loop:
                    break
                await asyncio.sleep(60) # Wait before polling again
                continue
                
            logger.info(f"Processing batch of {len(batch)} messages...")
            
            # Process batch
            await process_message_batch(batch, supabase)
            
            if not args.loop:
                break
                
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            if not args.loop:
                raise e
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())

