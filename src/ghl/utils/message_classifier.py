import json
import asyncio
from typing import Dict, Optional
from loguru import logger
from google.genai import types

from src.api.config.genai_gemini_config import CLIENT, MODEL_PRO
from src.api.genai_gemini import generate

async def classify_message(body_clean: str) -> Dict[str, bool]:
    """
    Classifies a message to determine if it is an out-of-office reply
    or if it mentions attachments/PDFs.
    
    Args:
        body_clean: The cleaned message body text
        
    Returns:
        Dict with keys:
            - is_out_of_office: bool
            - has_attachment_mention: bool
    """
    if not body_clean or len(body_clean.strip()) < 5:
        return {"is_out_of_office": False, "has_attachment_mention": False}

    prompt = f"""
    You are a message classification assistant. Analyze the following email reply to a franchise territory inquiry.
    
    Determine two things:
    1. is_out_of_office: Is this an automated "out of office", "vacation", or "auto-reply" message?
       (Look for phrases like "I am out of the office", "automatic reply", "I will have limited access to email")
       
    2. has_attachment_mention: Does the sender explicitly mention that they have attached a file, PDF, map, or image?
       (Look for "attached is", "see attachment", "attached map", "included a PDF", "check the files below")
       Note: Simply saying "here is the info" without implying an attachment does not count.
    
    Message Body:
    "{body_clean}"
    
    Output JSON only.
    """
    
    schema = {
        "type": "OBJECT",
        "properties": {
            "is_out_of_office": {"type": "BOOLEAN"},
            "has_attachment_mention": {"type": "BOOLEAN"}
        },
        "required": ["is_out_of_office", "has_attachment_mention"]
    }
    
    generate_content_config = types.GenerateContentConfig(
        temperature=0.1,
        top_p=0.95,
        response_mime_type="application/json",
        response_schema=schema,
    )
    
    retries = 3
    for attempt in range(retries):
        try:
            response = generate(
                client=CLIENT,
                model=MODEL_PRO,
                parts=[types.Part(text=prompt)],
                generate_content_config=generate_content_config
            )
            
            if not response.text:
                logger.warning("Empty response from Gemini classifier")
                # If empty, it might be a glitch, retry
                raise ValueError("Empty response")
                
            result = json.loads(response.text)
            return result
            
        except Exception as e:
            logger.warning(f"Error classifying message (Attempt {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                await asyncio.sleep(1 * (attempt + 1))
            else:
                logger.error(f"Failed to classify message after {retries} attempts")
                # Fail safe defaults
                return {"is_out_of_office": False, "has_attachment_mention": False}
