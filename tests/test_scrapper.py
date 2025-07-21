# -*- coding: utf-8 -*-
"""
This module contains the tests for the scrapper module.
"""

from unittest.mock import patch

import pytest

from src.data.franserve.scrapper import get_franchise_data, get_page_franchise_urls, session_login


@pytest.fixture
def mock_session():
    """Mock the session."""
    with patch("requests.Session") as mock_session:
        yield mock_session.return_value


def test_session_login(mock_session):
    """Test the session_login function."""
    session_login("login_url", "user", "pass")
    mock_session.post.assert_called_with(
        "login_url", data={"email": "user", "password": "pass", "Submit": "Login"}
    )


def test_get_page_franchise_urls(requests_mock):
    """Test the get_page_franchise_urls function."""
    requests_mock.get("catalogue_url", text='<a href="franchisedetails/1">Link</a>')
    session = requests_mock.Session()
    urls = get_page_franchise_urls(session, "base/", "catalogue_url")
    assert urls == ["base/franchisedetails/1"]


def test_get_franchise_data(requests_mock):
    """Test the get_franchise_data function."""
    requests_mock.get("franchise_url", text='<td colspan="2">Data</td>')
    session = requests_mock.Session()
    data = get_franchise_data(session, "franchise_url")
    assert data.get_text(strip=True) == "Data"
