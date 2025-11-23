
import inspect
from google import genai
from google.genai import types
import os

try:
    print("types.CreateBatchJobConfig signature/fields:")
    # It might be a Pydantic model or TypedDict or similar class
    if hasattr(types, 'CreateBatchJobConfig'):
        cls = types.CreateBatchJobConfig
        print(cls)
        print(dir(cls))
        if hasattr(cls, '__annotations__'):
            print(cls.__annotations__)
    
    print("\ntypes.CreateBatchJobConfigDict:")
    if hasattr(types, 'CreateBatchJobConfigDict'):
        print(types.CreateBatchJobConfigDict.__annotations__)

except Exception as e:
    print(f"Error: {e}")


