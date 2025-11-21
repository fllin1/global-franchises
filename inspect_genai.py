
import inspect
from google import genai
import os

try:
    client = genai.Client(api_key="test")
    print("CLIENT.batches.create signature:")
    print(inspect.signature(client.batches.create))
    
    # Check if there are type hints or docstrings
    print("\nDocstring:")
    print(client.batches.create.__doc__)
except Exception as e:
    print(f"Error: {e}")

