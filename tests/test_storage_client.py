# -*- coding: utf-8 -*-
"""
Tests for StorageClient.
"""

import unittest
from unittest.mock import MagicMock, patch

from src.data.storage.storage_client import StorageClient


class TestStorageClient(unittest.TestCase):
    """Tests for StorageClient."""

    @patch("src.data.storage.storage_client.supabase_client")
    def test_upload_html(self, mock_supabase_client):
        """Test upload_html."""
        mock_supabase = MagicMock()
        mock_supabase_client.return_value = mock_supabase
        
        client = StorageClient()
        
        # Mock storage().from_().upload()
        mock_storage = mock_supabase.storage.from_.return_value
        
        client.upload_html("<html></html>", "test/path.html")
        
        mock_storage.upload.assert_called_once()
        args, kwargs = mock_storage.upload.call_args
        self.assertEqual(kwargs["path"], "test/path.html")
        self.assertEqual(kwargs["file"], b"<html></html>")
        self.assertEqual(kwargs["file_options"]["content-type"], "text/html")

    @patch("src.data.storage.storage_client.supabase_client")
    def test_download_html(self, mock_supabase_client):
        """Test download_html."""
        mock_supabase = MagicMock()
        mock_supabase_client.return_value = mock_supabase
        
        client = StorageClient()
        
        mock_storage = mock_supabase.storage.from_.return_value
        mock_storage.download.return_value = b"<html></html>"
        
        content = client.download_html("test/path.html")
        
        self.assertEqual(content, "<html></html>")
        mock_storage.download.assert_called_with("test/path.html")

    @patch("src.data.storage.storage_client.supabase_client")
    def test_list_files(self, mock_supabase_client):
        """Test list_files."""
        mock_supabase = MagicMock()
        mock_supabase_client.return_value = mock_supabase
        
        client = StorageClient()
        
        mock_storage = mock_supabase.storage.from_.return_value
        mock_storage.list.return_value = [{"name": "file.html"}]
        
        files = client.list_files("prefix")
        
        self.assertEqual(files, [{"name": "file.html"}])
        mock_storage.list.assert_called_with(path="prefix")

