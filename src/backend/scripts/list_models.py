
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from src.api.config.genai_gemini_config import CLIENT

def list_models():
    print("Listing models...")
    try:
        models = CLIENT.models.list()
        for m in models:
            if "gemini" in m.name:
                print(f"Model: {m.name}")
                print(f"  Supported Actions: {m.supported_actions}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_models()
