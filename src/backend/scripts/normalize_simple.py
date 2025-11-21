
import asyncio
import re
from loguru import logger
import pgeocode
from src.api.config.supabase_config import supabase_client

# Initialize pgeocode for US
nomi = pgeocode.Nominatim('us')

async def fetch_all_unprocessed_territories(batch_size: int = 1000):
    """Fetch ALL territory checks that haven't been normalized using pagination."""
    all_data = []
    offset = 0
    
    logger.info("Fetching unprocessed territories...")
    
    while True:
        # Note: offset approach works but might be slow for very deep pagination.
        # For 12k records it is fine.
        response = supabase_client().table("territory_checks") \
            .select("id, location_raw, state_code") \
            .is_("zip_code", "null") \
            .is_("city", "null") \
            .range(offset, offset + batch_size - 1) \
            .execute()
            
        data = response.data
        if not data:
            break
            
        all_data.extend(data)
        offset += len(data)
        logger.info(f"Fetched {len(all_data)} records so far...")
        
        # If we got fewer than batch_size, we're done
        if len(data) < batch_size:
            break
            
    return all_data

def extract_simple_location(text: str, state_ctx: str):
    """
    Attempt to extract structured data using regex for simple patterns.
    Returns dict if confident, None otherwise.
    """
    if not text: return None
    text = text.strip()
    
    # Pattern 1: Simple Zip Code (e.g., "75019", "TX 75019")
    # 5 digit number, possibly surrounded by state
    zip_match = re.search(r'\b(\d{5})\b', text)
    if zip_match:
        zip_code = zip_match.group(1)
        # Verify it's a valid US zip via pgeocode
        geo = nomi.query_postal_code(zip_code)
        if not geo.empty and str(geo.latitude) != 'nan':
             # If state context matches (if provided), it's a strong match
             if not state_ctx or (geo.state_code and state_ctx.upper() == geo.state_code):
                 return {
                     "city": geo.place_name,
                     "state_code": geo.state_code,
                     "zip_code": zip_code,
                     "latitude": float(geo.latitude),
                     "longitude": float(geo.longitude),
                     "radius_miles": None
                 }
    
    # Pattern 2: "City, State" strictly (e.g., "Austin, TX")
    # Must be at start of string or strictly the whole string to be safe
    city_state_match = re.match(r'^([A-Za-z\s\.]+),\s*([A-Z]{2})$', text)
    if city_state_match:
        city = city_state_match.group(1).strip()
        state = city_state_match.group(2).upper()
        
        # Validate state matches context or is valid US state
        if state_ctx and state != state_ctx.upper():
            return None # ambiguous
            
        # We can try to get a "central" zip for this city using pgeocode? 
        # pgeocode is zip-first. Hard to do City->LatLon without API.
        # But we can save City/State and leave Lat/Lon/Zip null for now, 
        # or use a lightweight local city DB. 
        # For now, let's skip City-only matches in this fast pass to avoid bad data,
        # and let LLM handle them or use a better geocoder in batch.
        return {
             "city": city,
             "state_code": state,
             "zip_code": None,
             "latitude": None, 
             "longitude": None,
             "radius_miles": None
        }

    return None

async def process_regex_batch():
    items = await fetch_all_unprocessed_territories()
    if not items:
        logger.info("No unprocessed items found.")
        return

    logger.info(f"Scanning {len(items)} items for simple patterns...")
    
    updates = []
    
    for item in items:
        raw = item.get('location_raw')
        ctx_state = item.get('state_code')
        
        result = extract_simple_location(raw, ctx_state)
        
        if result:
            updates.append({
                "id": item['id'],
                **result
            })

    logger.info(f"Found {len(updates)} simple matches via Regex/Zip lookup.")
    
    # Batch update (Supabase doesn't support massive bulk update easily in one HTTP call without RPC,
    # so we loop or chunk it. Looping is fine for this script if not too huge, or chunk 50.)
    
    # Chunk updates
    chunk_size = 50
    for i in range(0, len(updates), chunk_size):
        chunk = updates[i:i+chunk_size]
        # We have to update one by one or use upsert. 
        # Upsert requires all columns? No, just PK.
        # But we want to update specific columns. 
        # Supabase upsert works if we provide ID.
        
        try:
            # We can upsert data. But wait, territory_checks has other cols?
            # Upsert will overwrite other cols if we don't include them? 
            # No, Postgres ON CONFLICT DO UPDATE SET ... usually merges if mapped correctly,
            # but Supabase client `upsert` usually replaces the row or merges if configured.
            # Safer to just loop update for now or create a custom RPC for batch update.
            # Given 12k records, creating an RPC is better, but let's do simple loop with concurrency for now.
            
            for update in chunk:
                supabase_client().table("territory_checks").update(update).eq("id", update['id']).execute()
                
            logger.info(f"Processed chunk {i}-{i+len(chunk)}")
            
        except Exception as e:
            logger.error(f"Error in chunk {i}: {e}")

if __name__ == "__main__":
    asyncio.run(process_regex_batch())
