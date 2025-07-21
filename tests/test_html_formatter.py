# -*- coding: utf-8 -*-
"""
This module contains the tests for the html_formatter module.
"""

from bs4 import BeautifulSoup
import pytest

from src.data.franserve.html_formatter import parse_franchise_html


@pytest.fixture
def sample_html():
    """Sample HTML for testing."""
    return """
    <td colspan="2">
        <b><font size="+1">Test Franchise</font></b>
        <input name="ZorID" value="123" />
        <!-- More sample HTML structure here -->
    </td>
    """


def test_parse_franchise_html(sample_html):
    """Test the parse_franchise_html function."""
    soup = BeautifulSoup(sample_html, "html.parser")
    data = parse_franchise_html(soup)
    assert data["franchise_data"]["franchise_name"] == "Test Franchise"
    assert data["franchise_data"]["source_id"] == 123
    # Add more assertions based on expected parsing
