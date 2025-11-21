
import asyncio
import json
import os
from typing import List, Dict, Any
from loguru import logger
from google import genai
from google.genai import types
from src.api.config.supabase_config import supabase_client
from src.api.config.genai_gemini_config import CLIENT, MODEL_FLASH

# Directory for batch files
BATCH_DIR = "data/processed/batch_results"
os.makedirs(BATCH_DIR, exist_ok=True)

async def fetch_all_complex_territories(batch_size: int = 1000):
    """Fetch ALL remaining unprocessed territories using pagination."""
    all_data = []
    offset = 0
    
    logger.info("Fetching all unprocessed territories for batch processing...")
    
    while True:
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
        
        if len(data) < batch_size:
            break
            
    return all_data

def create_batch_request_file(items: List[Dict], output_path: str):
    """Create JSONL file for Gemini Batch API."""
    
    with open(output_path, 'w') as f:
        for item in items:
            location_raw = item['location_raw']
            state_context = item['state_code']
            request_id = str(item['id'])
            
            prompt = f"""
            Extract structured geographic data.
            Input: "{location_raw}"
            Context State: "{state_context}"
            
            Output JSON: {{ "city": string, "state_code": string, "zip_code": string, "radius_miles": number, "is_entire_state": boolean }}
            """
            
            # Construct Batch Request Object
            # Ref: https://ai.google.dev/gemini-api/docs/batch
            request = {
                "custom_id": request_id,
                "request": {
                    "model": f"models/{MODEL_FLASH}",
                    "contents": [
                        {"role": "user", "parts": [{"text": prompt}]}
                    ],
                    "generationConfig": {
                        "responseMimeType": "application/json"
                    }
                }
            }
            
            f.write(json.dumps(request) + "\n")
            
    logger.info(f"Created batch file with {len(items)} requests at {output_path}")

async def submit_batch_job(file_path: str):
    """Upload file and start batch job."""
    
    # 1. Upload File
    logger.info("Uploading batch file...")
    batch_file = CLIENT.files.upload(file=file_path, config={'mime_type': 'application/json'})
    logger.info(f"File uploaded: {batch_file.name}")
    
    # 2. Create Batch Job
    logger.info("Creating batch job...")
    # config expects a dict or CreateBatchJobConfig
    # Using types.CreateBatchJobConfig to ensure correct parameter handling
    batch_job = CLIENT.batches.create(
        model=MODEL_FLASH,
        src=batch_file.name,
        config=types.CreateBatchJobConfig(
            display_name=f"batch_job_{batch_file.name}"
        )
    )
    
    logger.info(f"Batch job started: {batch_job.name}")
    logger.info(f"State: {batch_job.state}")
    return batch_job

async def main():
    # 1. Fetch Data
    items = await fetch_all_complex_territories()
    if not items:
        logger.info("No items to process.")
        return
        
    logger.info(f"Found {len(items)} complex items to process via Batch API.")
    
    # 2. Generate JSONL
    timestamp = int(time.time())
    jsonl_path = f"{BATCH_DIR}/batch_request_{timestamp}.jsonl"
    create_batch_request_file(items, jsonl_path)
    
    # 3. Submit
    job = await submit_batch_job(jsonl_path)
    print(f"Job ID: {job.name}")
    print("Run 'check_batch_status.py' later to check progress.")

if __name__ == "__main__":
    import time
    asyncio.run(main())

