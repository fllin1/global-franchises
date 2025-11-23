
import os
import sys
import asyncio
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.api.config.genai_gemini_config import CLIENT

def list_batches():
    print("Fetching batch jobs...")
    try:
        # List batch jobs. valid arguments depend on the SDK version.
        # Based on google-genai SDK inspection earlier, likely list() method exists.
        batches = CLIENT.batches.list()
        
        active_batches = []
        all_batches = []
        
        # Iterate if it returns an iterator/pager
        count = 0
        for job in batches:
            all_batches.append(job)
            # state might be a string or enum
            state = str(job.state)
            if state in ["STATE_ACTIVE", "STATE_CREATING", "STATE_PROCESSING", "ACTIVE", "CREATING", "PROCESSING"]: 
                active_batches.append(job)
            count += 1
            # Limit to last 20 for display
            if count >= 20:
                break
        
        print(f"\nTotal visible batches (limit 20): {len(all_batches)}")
        print(f"Active/Processing batches: {len(active_batches)}")
        
        print("\n--- Recent Batches ---")
        for job in all_batches:
            created_time = "Unknown"
            if hasattr(job, "create_time"):
                created_time = job.create_time
            
            print(f"ID: {job.name.split('/')[-1] if hasattr(job, 'name') else 'N/A'}")
            print(f"  State: {job.state}")
            print(f"  Created: {created_time}")
            if hasattr(job, "error") and job.error:
                print(f"  Error: {job.error}")
            print("-" * 30)

        return active_batches

    except Exception as e:
        print(f"Error listing batches: {e}")
        import traceback
        traceback.print_exc()
        return []

def cancel_batch(batch_name):
    try:
        print(f"Cancelling batch {batch_name}...")
        CLIENT.batches.delete(name=batch_name)
        print("Cancelled/Deleted.")
    except Exception as e:
        print(f"Error cancelling batch: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_batches()
    elif len(sys.argv) > 2 and sys.argv[1] == "cancel":
        cancel_batch(sys.argv[2])
    else:
        print("Usage:")
        print("  python manage_batches.py list")
        print("  python manage_batches.py cancel <batch_name>")
        
        # Default run list
        print("\nRunning list...")
        list_batches()


