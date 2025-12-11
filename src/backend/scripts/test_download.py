#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to debug download issues from Supabase Storage.
"""

from loguru import logger
import traceback
from src.data.storage.storage_client import StorageClient
from src.data.functions.extract import Extractor


def main():
    logger.info("Testing download functionality from Supabase Storage...")
    
    extractor = Extractor()
    prefix = extractor.today_str
    
    try:
        storage_client = StorageClient()
        
        # List files first
        logger.info(f"Listing files in prefix: {prefix}")
        files = storage_client.list_files(prefix)
        html_files = [f for f in files if f.get("name", "").endswith(".html")]
        
        if not html_files:
            logger.error("No HTML files found to test download")
            return
        
        logger.info(f"Found {len(html_files)} HTML files")
        
        # Test with first file
        test_file = html_files[0]
        file_name = test_file.get("name")
        file_path = f"{prefix}/{file_name}"
        
        logger.info(f"\n=== Testing Download ===")
        logger.info(f"File name: {file_name}")
        logger.info(f"Full path: {file_path}")
        logger.info(f"File metadata: {test_file}")
        
        # Try different path formats
        test_paths = [
            file_path,  # Full path with prefix
            file_name,  # Just filename
            f"/{file_path}",  # With leading slash
        ]
        
        for test_path in test_paths:
            logger.info(f"\n--- Trying path: '{test_path}' ---")
            try:
                # Try direct Supabase call to see raw response
                logger.info("Calling supabase.storage.from_().download()...")
                response = storage_client.supabase.storage.from_(storage_client.bucket_name).download(test_path)
                
                logger.info(f"Response type: {type(response)}")
                logger.info(f"Response length: {len(response) if hasattr(response, '__len__') else 'N/A'}")
                
                if isinstance(response, bytes):
                    logger.success("✓ Response is bytes")
                    content = response.decode("utf-8")
                    logger.success(f"✓ Successfully decoded! Content length: {len(content)} chars")
                    logger.info(f"First 200 chars: {content[:200]}...")
                    break
                elif isinstance(response, str):
                    logger.success("✓ Response is already a string")
                    logger.info(f"Content length: {len(response)} chars")
                    logger.info(f"First 200 chars: {response[:200]}...")
                    break
                else:
                    logger.warning(f"Unexpected response type: {type(response)}")
                    logger.info(f"Response: {response}")
                    
            except Exception as e:
                logger.error(f"✗ Failed with path '{test_path}': {e}")
                logger.error(f"Error type: {type(e).__name__}")
                logger.error(f"Traceback:\n{traceback.format_exc()}")
        
        # Also test the wrapper method
        logger.info(f"\n--- Testing download_html() wrapper method ---")
        try:
            content = storage_client.download_html(file_path)
            logger.success(f"✓ download_html() succeeded! Content length: {len(content)} chars")
        except Exception as e:
            logger.error(f"✗ download_html() failed: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            
    except Exception as e:
        logger.error(f"Failed to test download: {e}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        raise


if __name__ == "__main__":
    main()
























