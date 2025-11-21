
import os
import sys
from google import genai
from google.genai import types

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from src.api.config.genai_gemini_config import CLIENT, MODEL_FLASH

def test_create_small_batch():
    print("Creating test batch...")
    
    # Create a small jsonl file
    filename = "test_small_batch.jsonl"
    with open(filename, "w") as f:
        f.write('{"custom_id": "test1", "request": {"model": "models/gemini-1.5-flash", "contents": [{"role": "user", "parts": [{"text": "Hello"}]}]}}\n')
    
    try:
        # Upload
        print("Uploading file...")
        batch_file = CLIENT.files.upload(file=filename, config={'mime_type': 'application/json'})
        print(f"Uploaded: {batch_file.name}")
        
        # Create Job
        print("Creating job with gemini-1.5-flash...")
        batch_job = CLIENT.batches.create(
            model="gemini-1.5-flash",
            src=batch_file.name,
            config=types.CreateBatchJobConfig(
                display_name="test_small_batch_1_5"
            )
        )
        print(f"Job created: {batch_job.name}")
        print(f"State: {batch_job.state}")
        
    except Exception as e:
        print(f"Error: {e}")
        if hasattr(e, 'response'):
            print(f"Response: {e.response}")
            
    finally:
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == "__main__":
    test_create_small_batch()

