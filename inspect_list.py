
import inspect
from google import genai
import os

try:
    client = genai.Client(api_key="test")
    print("CLIENT.batches.list signature:")
    print(inspect.signature(client.batches.list))
except Exception as e:
    print(f"Error: {e}")

