
import asyncio
import json
import os
from loguru import logger
from src.api.config.supabase_config import supabase_client
import pgeocode

nomi = pgeocode.Nominatim('us')

async def process_batch_results(result_file_path: str):
    """Read Gemini Batch result file and update DB."""
    
    if not os.path.exists(result_file_path):
        logger.error(f"File not found: {result_file_path}")
        return

    logger.info(f"Processing results from {result_file_path}...")
    
    updates = []
    
    with open(result_file_path, 'r') as f:
        for line in f:
            try:
                result = json.loads(line)
                custom_id = result.get('custom_id') # This is our DB ID
                
                # Extract LLM response
                # Note: structure depends on Gemini Batch Output format, usually:
                # { response: { candidates: [ { content: { parts: [ { text: ... } ] } } ] } }
                # But if we get error, it might be different.
                
                if 'error' in result:
                    logger.error(f"Item {custom_id} failed: {result['error']}")
                    continue
                    
                candidate = result['response']['candidates'][0]['content']['parts'][0]['text']
                clean_json = candidate.replace('```json', '').replace('```', '').strip()
                data = json.loads(clean_json)
                
                # Geocode if needed
                zip_code = data.get('zip_code')
                city = data.get('city')
                lat, lon = None, None
                
                if zip_code:
                    geo = nomi.query_postal_code(zip_code)
                    if not geo.empty and str(geo.latitude) != 'nan':
                        lat = float(geo.latitude)
                        lon = float(geo.longitude)
                        if not city: city = geo.place_name

                updates.append({
                    "id": int(custom_id),
                    "city": city,
                    "state_code": data.get('state_code'),
                    "zip_code": zip_code,
                    "radius_miles": data.get('radius_miles'),
                    "latitude": lat,
                    "longitude": lon
                })
                
            except Exception as e:
                logger.error(f"Failed to parse line: {e}")

    logger.info(f"Prepared {len(updates)} updates.")
    
    # Batch Update Loop
    chunk_size = 50
    for i in range(0, len(updates), chunk_size):
        chunk = updates[i:i+chunk_size]
        try:
            for up in chunk:
                 await supabase_client().table("territory_checks").update(up).eq("id", up['id']).execute()
            logger.info(f"Updated chunk {i}-{i+len(chunk)}")
        except Exception as e:
             logger.error(f"Error updating chunk {i}: {e}")

if __name__ == "__main__":
    # Usage: poetry run python -m src.backend.scripts.process_batch_results path/to/results.jsonl
    import sys
    if len(sys.argv) > 1:
        asyncio.run(process_batch_results(sys.argv[1]))
    else:
        print("Please provide the result .jsonl file path")

