# -*- coding: utf-8 -*-
"""
Supabase Storage Client Wrapper.

This module handles interactions with Supabase Storage for the Data Lake implementation.
"""

import io
from pathlib import Path
from typing import List, Optional, Union

from loguru import logger
from storage3.utils import StorageException

from src.api.config.supabase_config import RAW_FRANCHISE_BUCKET, supabase_client


class StorageClient:
    """
    Wrapper around Supabase Storage client for managing franchise HTML files.
    """

    def __init__(self):
        """Initialize the Supabase Storage client."""
        self.supabase = supabase_client()
        self.bucket_name = RAW_FRANCHISE_BUCKET
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """
        Ensure the storage bucket exists.
        Note: Creating buckets via API might require specific permissions.
        """
        try:
            buckets = self.supabase.storage.list_buckets()
            bucket_names = [b.name for b in buckets]
            if self.bucket_name not in bucket_names:
                logger.info(f"Creating storage bucket: {self.bucket_name}")
                self.supabase.storage.create_bucket(
                    self.bucket_name, options={"public": False}
                )
        except Exception as e:
            logger.warning(f"Could not verify/create bucket '{self.bucket_name}': {e}")

    def upload_html(
        self, content: str, file_path: str, content_type: str = "text/html"
    ) -> str:
        """
        Upload HTML content to Supabase Storage.

        Args:
            content (str): The HTML content to upload.
            file_path (str): The path within the bucket (e.g., '2025-01-20/123.html').
            content_type (str): The MIME type of the content.

        Returns:
            str: The path of the uploaded file.
        """
        try:
            # Convert string to bytes
            file_bytes = content.encode("utf-8")
            
            # Check if file exists (optional, but good for idempotency if we want to avoid overwrite or just overwrite)
            # upsert=True is the standard way to handle overwrites
            
            self.supabase.storage.from_(self.bucket_name).upload(
                path=file_path,
                file=file_bytes,
                file_options={"content-type": content_type, "upsert": "true"},
            )
            logger.info(f"Uploaded {file_path} to {self.bucket_name}")
            return file_path
        except StorageException as e:
            logger.error(f"Failed to upload {file_path}: {e}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error uploading {file_path}: {e}")
            raise e

    def download_html(self, file_path: str) -> str:
        """
        Download HTML content from Supabase Storage.

        Args:
            file_path (str): The path within the bucket.

        Returns:
            str: The HTML content.
        """
        try:
            response = self.supabase.storage.from_(self.bucket_name).download(file_path)
            return response.decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to download {file_path}: {e}")
            raise e

    def list_files(self, prefix: str = "") -> List[dict]:
        """
        List files in the storage bucket with a given prefix.

        Args:
            prefix (str): The folder path to list (e.g., '2025-01-20').

        Returns:
            List[dict]: List of file objects.
        """
        try:
            # list() expects a folder path, if prefix is empty it lists root
            return self.supabase.storage.from_(self.bucket_name).list(path=prefix)
        except Exception as e:
            logger.error(f"Failed to list files with prefix {prefix}: {e}")
            raise e

    def exists(self, file_path: str) -> bool:
        """
        Check if a file exists in storage.
        
        Args:
            file_path (str): Path to check.
            
        Returns:
            bool: True if exists, False otherwise.
        """
        try:
            # Split path into folder and filename
            path_obj = Path(file_path)
            folder = str(path_obj.parent)
            filename = path_obj.name
            
            # If folder is '.', it means root
            if folder == ".":
                folder = ""
                
            files = self.list_files(folder)
            return any(f.get("name") == filename for f in files)
        except Exception:
            return False

