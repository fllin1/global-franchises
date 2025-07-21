# -*- coding: utf-8 -*-
"""
This module contains the tests for the supabase module.
"""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from dotenv import load_dotenv
import pytest
from supabase import Client, create_client

from src.data.upsert_supabase import RAW_DATA_DIR, upload_data_to_supabase


@pytest.fixture
def mock_env():
    """Mock the environment variables."""
    with patch("os.environ.get") as mock_get:
        mock_get.side_effect = lambda k: {"SUPABASE_URL": "url", "SUPABASE_KEY": "key"}.get(k)
        yield


@pytest.fixture
def mock_supabase():
    """Mock the supabase client."""
    with patch("src.data.supabase.create_client") as mock_create:
        mock_client = MagicMock(spec=Client)
        mock_create.return_value = mock_client
        yield mock_client


def test_upload_data_to_supabase_no_files(mock_env, mock_supabase, capsys):
    """Test the upload_data_to_supabase function when no files are found."""
    with patch("pathlib.Path.glob") as mock_glob:
        mock_glob.return_value = []
        upload_data_to_supabase()
        captured = capsys.readouterr()
        assert "No JSON files found" in captured.out


def test_upload_data_to_supabase_success(mock_env, mock_supabase):
    """Test the upload_data_to_supabase function when files are found."""
    sample_data = {
        "franchise_data": {"source_id": 1, "franchise_name": "Test Franchise"},
        "contacts_data": [{"name": "Contact"}],
    }
    mock_file = MagicMock()
    mock_file.read.return_value = json.dumps(sample_data)
    mock_file.name = "test.json"
    with patch("pathlib.Path.glob") as mock_glob, patch("builtins.open") as mock_open:
        mock_glob.return_value = [mock_file]
        mock_open.return_value.__enter__.return_value = mock_file

        mock_table = MagicMock()
        mock_supabase.table.return_value = mock_table
        mock_upsert = MagicMock()
        mock_upsert.execute.return_value = MagicMock(data=[{"id": 123}])
        mock_table.upsert.return_value = mock_upsert

        mock_delete = MagicMock()
        mock_delete.eq.return_value.execute.return_value = MagicMock()
        mock_table.delete.return_value = mock_delete

        mock_insert = MagicMock()
        mock_insert.execute.return_value = MagicMock()
        mock_table.insert.return_value = mock_insert

        upload_data_to_supabase()
        mock_table.upsert.assert_called()
        mock_table.delete.assert_called()
        mock_table.insert.assert_called()
