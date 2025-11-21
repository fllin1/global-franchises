
import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.api.config.genai_gemini_config import CLIENT, MODEL_FLASH

try:
    from google.genai import types
    
    print(f"Testing with model: {MODEL_FLASH}")
    # using a dummy file name that looks like a resource name
    CLIENT.batches.create(
        model=MODEL_FLASH, 
        src="files/dummy-file-name",
        config=types.CreateBatchJobConfig(display_name="test_job")
    )
except Exception as e:
    print(f"Caught error: {e}")

