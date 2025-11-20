# -*- coding: utf-8 -*-
"""
Tests for Extractor with Storage.
"""

import unittest
from unittest.mock import MagicMock, patch

from src.data.functions.extract import Extractor


class TestExtractorStorage(unittest.TestCase):
    """Tests for Extractor using Storage."""

    @patch("src.data.functions.extract.StorageClient")
    @patch("src.data.functions.extract.supabase_client")
    @patch("src.data.functions.extract.session_login")
    @patch("src.data.functions.extract.get_all_pages_franchise_urls")
    @patch("src.data.functions.extract.get_franchise_data")
    @patch("src.data.functions.extract.upload_franchise_html")
    def test_scrape(
        self,
        mock_upload,
        mock_get_data,
        mock_get_urls,
        mock_login,
        mock_supabase_client,
        mock_storage_client_cls,
    ):
        """Test scrape method uploads to storage and tracks run."""
        extractor = Extractor()
        
        # Mocks
        mock_get_urls.return_value = ["http://test.com/f1"]
        mock_get_data.return_value = MagicMock()
        
        mock_storage_client = MagicMock()
        mock_storage_client_cls.return_value = mock_storage_client
        
        mock_supabase = MagicMock()
        mock_supabase_client.return_value = mock_supabase
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [{"id": 123}]
        
        extractor.scrape()
        
        # Verify Storage Upload
        mock_upload.assert_called_once()
        args, _ = mock_upload.call_args
        self.assertEqual(args[1], f"{extractor.today_str}/f1.html")
        
        # Verify Run Tracking
        mock_supabase.table.assert_any_call("scraping_runs")
        mock_supabase.table.return_value.insert.assert_called()
        mock_supabase.table.return_value.update.assert_called()

    @patch("src.data.functions.extract.StorageClient")
    @patch("src.data.functions.extract.process_franchise_html")
    def test_rule_based_parsing(self, mock_process, mock_storage_client_cls):
        """Test rule_based_parsing reads from storage."""
        extractor = Extractor()
        
        mock_storage_client = MagicMock()
        mock_storage_client_cls.return_value = mock_storage_client
        
        # Mock list files
        mock_storage_client.list_files.return_value = [{"name": "f1.html"}]
        # Mock download
        mock_storage_client.download_html.return_value = "<html></html>"
        
        mock_process.return_value = {"data": "test"}
        
        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
             with patch("json.dump") as mock_json_dump:
                extractor.rule_based_parsing()
                
                mock_storage_client.list_files.assert_called_with(extractor.today_str)
                mock_storage_client.download_html.assert_called_with(f"{extractor.today_str}/f1.html")
                mock_process.assert_called_with("<html></html>")
                mock_json_dump.assert_called()


