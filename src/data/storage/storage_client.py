# -*- coding: utf-8 -*-
"""
Supabase Storage Client Wrapper.

This module handles interactions with Supabase Storage for the Data Lake implementation.
"""

import io
from pathlib import Path
from typing import List, Optional, Union
from urllib.parse import quote, unquote

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
            file_path (str): The path within the bucket (e.g., '2025-11-24/file.html').
                            Can be a full path or just filename. If filename contains
                            special characters like ? or &, they will be URL-encoded.

        Returns:
            str: The HTML content.
        """
        try:
            # URL-encode the file path to handle special characters like ? and &
            # Files are uploaded with quote(filename, safe=""), so we need to encode the filename part
            # Split path into directory and filename parts
            path_parts = file_path.split("/")
            if len(path_parts) > 1:
                # Encode the filename part but keep directory structure
                directory = "/".join(path_parts[:-1])
                filename = path_parts[-1]
                # Encode special characters in filename (same as upload uses: quote(..., safe=""))
                # This handles ? -> %3F, & -> %26, etc.
                encoded_filename = quote(filename, safe="")
                encoded_path = f"{directory}/{encoded_filename}"
            else:
                # Just a filename, encode it
                encoded_path = quote(file_path, safe="")
            
            logger.debug(f"Downloading file: {file_path} (encoded: {encoded_path}) from bucket: {self.bucket_name}")
            response = self.supabase.storage.from_(self.bucket_name).download(encoded_path)
            
            if response is None:
                raise ValueError(f"Download returned None for path: {file_path}")
            
            # Handle different response types
            if isinstance(response, bytes):
                content = response.decode("utf-8")
            elif isinstance(response, str):
                content = response
            elif hasattr(response, 'read'):
                # If it's a file-like object
                content = response.read()
                if isinstance(content, bytes):
                    content = content.decode("utf-8")
            else:
                # Try to convert to string
                try:
                    content = str(response)
                except Exception as e:
                    raise TypeError(f"Unexpected response type: {type(response)}, cannot convert to string: {e}")
            
            logger.debug(f"Successfully downloaded {file_path}, content length: {len(content)}")
            return content
        except StorageException as e:
            logger.error(f"Storage error downloading {file_path}: {e}")
            raise e
        except Exception as e:
            logger.error(f"Failed to download {file_path}: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            raise e

    def upload_json(
        self, content: str, file_path: str, content_type: str = "application/json"
    ) -> str:
        """
        Upload JSON content to Supabase Storage.

        Args:
            content (str): The JSON content to upload (as string).
            file_path (str): The path within the bucket (e.g., '2025-01-20/123.json').
            content_type (str): The MIME type of the content.

        Returns:
            str: The path of the uploaded file.
        """
        try:
            # Convert string to bytes
            file_bytes = content.encode("utf-8")

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

    def upload_markdown(
        self, content: str, file_path: str, content_type: str = "text/markdown"
    ) -> str:
        """
        Upload Markdown content to Supabase Storage.

        Args:
            content (str): The Markdown content to upload.
            file_path (str): The path within the bucket (e.g., '2025-01-20/123.md').
            content_type (str): The MIME type of the content.

        Returns:
            str: The path of the uploaded file.
        """
        try:
            # Convert string to bytes
            file_bytes = content.encode("utf-8")

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

    def download_markdown(self, file_path: str) -> str:
        """
        Download Markdown content from Supabase Storage.

        Args:
            file_path (str): The path within the bucket (e.g., '2025-11-24/file.md').

        Returns:
            str: The Markdown content.
        """
        try:
            # URL-encode the file path (same as download_html)
            path_parts = file_path.split("/")
            if len(path_parts) > 1:
                directory = "/".join(path_parts[:-1])
                filename = path_parts[-1]
                encoded_filename = quote(filename, safe="")
                encoded_path = f"{directory}/{encoded_filename}"
            else:
                encoded_path = quote(file_path, safe="")
            
            logger.debug(f"Downloading markdown file: {file_path} (encoded: {encoded_path}) from bucket: {self.bucket_name}")
            response = self.supabase.storage.from_(self.bucket_name).download(encoded_path)
            
            if response is None:
                raise ValueError(f"Download returned None for path: {file_path}")
            
            # Handle different response types (same as download_html)
            if isinstance(response, bytes):
                content = response.decode("utf-8")
            elif isinstance(response, str):
                content = response
            elif hasattr(response, 'read'):
                content = response.read()
                if isinstance(content, bytes):
                    content = content.decode("utf-8")
            else:
                try:
                    content = str(response)
                except Exception as e:
                    raise TypeError(f"Unexpected response type: {type(response)}, cannot convert to string: {e}")
            
            logger.debug(f"Successfully downloaded {file_path}, content length: {len(content)}")
            return content
        except StorageException as e:
            logger.error(f"Storage error downloading {file_path}: {e}")
            raise e
        except Exception as e:
            logger.error(f"Failed to download {file_path}: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            raise e

    def list_files(self, prefix: str = "") -> List[dict]:
        """
        List files in the storage bucket with a given prefix.
        Handles pagination to retrieve all files.

        Args:
            prefix (str): The folder path to list (e.g., '2025-01-20').

        Returns:
            List[dict]: List of file objects (all pages combined).
        """
        try:
            all_files = []
            # Try to get all files - Supabase Storage list() may paginate
            # First attempt: try without options to see if it returns all files
            try:
                page_files = self.supabase.storage.from_(self.bucket_name).list(path=prefix)
                if page_files:
                    all_files.extend(page_files)
                    logger.debug(f"Initial list returned {len(page_files)} files")
                    
                    # If we got exactly 100 files, it might be paginated (common default limit)
                    # Try to fetch more pages
                    if len(page_files) == 100:
                        logger.info(f"Got exactly 100 files, checking for more pages...")
                        # Try with limit parameter if supported
                        try:
                            # Some Supabase clients support limit directly
                            for offset in range(100, 10000, 100):  # Check up to 10k files
                                try:
                                    next_page = self.supabase.storage.from_(self.bucket_name).list(
                                        path=prefix,
                                        options={"limit": 100, "offset": offset}
                                    )
                                    if not next_page or len(next_page) == 0:
                                        break
                                    all_files.extend(next_page)
                                    logger.debug(f"Fetched page at offset {offset}: {len(next_page)} files")
                                    if len(next_page) < 100:
                                        break
                                except (TypeError, AttributeError) as e:
                                    # Options parameter not supported, try alternative
                                    logger.debug(f"Options parameter not supported, trying alternative method")
                                    break
                        except Exception as e:
                            logger.debug(f"Pagination attempt failed: {e}, using initial results")
            except Exception as e:
                logger.warning(f"Error listing files: {e}, attempting fallback")
                # Fallback: try with options parameter
                try:
                    page_files = self.supabase.storage.from_(self.bucket_name).list(
                        path=prefix,
                        options={"limit": 1000}
                    )
                    if page_files:
                        all_files.extend(page_files)
                except Exception:
                    raise e
            
            logger.info(f"Retrieved {len(all_files)} total files from storage prefix '{prefix}'")
            return all_files
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

