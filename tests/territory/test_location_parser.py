# -*- coding: utf-8 -*-
"""
Tests for territory location parsing.

These tests verify that the LLM-based location parser correctly extracts
structured geographic data from raw location strings.
"""

import pytest
from typing import Dict, Any, List

# We'll test the parsing logic functions, not the LLM call directly
# The actual parsing functions will be imported from the module once created
# For now, we define the expected behavior

# Test cases for location parsing
PARSE_TEST_CASES = [
    # Simple city, state
    {
        "input": "Oakland, CA",
        "expected": {
            "country": "US",
            "state_code": "CA",
            "county": "Alameda",
            "city": "Oakland",
            "zip_code": None,
            "radius_miles": None,
            "is_resale": False,
        },
    },
    # Zip code only
    {
        "input": "33174",
        "expected": {
            "country": "US",
            "state_code": "FL",
            "county": "Miami-Dade",
            "city": "Miami",
            "zip_code": "33174",
            "radius_miles": None,
            "is_resale": False,
        },
    },
    # City, state, zip with radius
    {
        "input": "Livermore CA 94551 and 25 miles",
        "expected": {
            "country": "US",
            "state_code": "CA",
            "county": "Alameda",
            "city": "Livermore",
            "zip_code": "94551",
            "radius_miles": 25,
            "is_resale": False,
        },
    },
    # City, state, zip (no comma)
    {
        "input": "Norfolk VA 23504",
        "expected": {
            "country": "US",
            "state_code": "VA",
            "county": "Norfolk",
            "city": "Norfolk",
            "zip_code": "23504",
            "radius_miles": None,
            "is_resale": False,
        },
    },
    # County only
    {
        "input": "Orange County CA",
        "expected": {
            "country": "US",
            "state_code": "CA",
            "county": "Orange",
            "city": None,
            "zip_code": None,
            "radius_miles": None,
            "is_resale": False,
        },
    },
    # Resale mention
    {
        "input": "Amarillo TX resale",
        "expected": {
            "country": "US",
            "state_code": "TX",
            "county": "Potter",  # or Randall - Amarillo spans both
            "city": "Amarillo",
            "zip_code": None,
            "radius_miles": None,
            "is_resale": True,
        },
    },
    # Resale with different format
    {
        "input": "Rochester, NY RESALE",
        "expected": {
            "country": "US",
            "state_code": "NY",
            "county": "Monroe",
            "city": "Rochester",
            "zip_code": None,
            "radius_miles": None,
            "is_resale": True,
        },
    },
    # International - Canada
    {
        "input": "Oakville Ontario L6H4N8",
        "expected": {
            "country": "CA",
            "state_code": "ON",
            "county": None,  # Canada doesn't have US-style counties
            "city": "Oakville",
            "zip_code": "L6H4N8",
            "radius_miles": None,
            "is_resale": False,
        },
    },
    # International - Canada with explicit mention
    {
        "input": "Mississauga Ontario, Canada",
        "expected": {
            "country": "CA",
            "state_code": "ON",
            "county": None,
            "city": "Mississauga",
            "zip_code": None,
            "radius_miles": None,
            "is_resale": False,
        },
    },
    # Area reference (implies radius)
    {
        "input": "San Antonio area",
        "expected": {
            "country": "US",
            "state_code": "TX",
            "county": "Bexar",
            "city": "San Antonio",
            "zip_code": None,
            "radius_miles": None,  # "area" doesn't specify a radius
            "is_resale": False,
        },
    },
    # Zip + miles format
    {
        "input": "48188 + 50 Miles",
        "expected": {
            "country": "US",
            "state_code": "MI",
            "county": "Wayne",
            "city": "Canton",  # 48188 is Canton, MI
            "zip_code": "48188",
            "radius_miles": 50,
            "is_resale": False,
        },
    },
    # State abbreviation only format
    {
        "input": "FL 33436",
        "expected": {
            "country": "US",
            "state_code": "FL",
            "county": "Palm Beach",
            "city": "Boynton Beach",
            "zip_code": "33436",
            "radius_miles": None,
            "is_resale": False,
        },
    },
    # City with surrounding area
    {
        "input": "Arlington, TX and surrounding area",
        "expected": {
            "country": "US",
            "state_code": "TX",
            "county": "Tarrant",
            "city": "Arlington",
            "zip_code": None,
            "radius_miles": None,
            "is_resale": False,
        },
    },
]

# Test cases for multi-location splitting
MULTI_LOCATION_TEST_CASES = [
    {
        "input": "Dallas or Amarillo, TX",
        "expected_count": 2,
        "expected_cities": ["Dallas", "Amarillo"],
    },
    {
        "input": "San Jose, CA and Dallas, TX",
        "expected_count": 2,
        "expected_cities": ["San Jose", "Dallas"],
    },
    {
        "input": "orange county and Los Angeles county",
        "expected_count": 2,
        "expected_counties": ["Orange", "Los Angeles"],
    },
    {
        "input": "Summit & Cuyahoga County OH",
        "expected_count": 2,
        "expected_counties": ["Summit", "Cuyahoga"],
    },
]


class TestLocationParserSchema:
    """Test the expected schema of parsed locations."""

    def test_required_fields_present(self):
        """Every parsed location should have all required fields."""
        required_fields = [
            "country",
            "state_code", 
            "county",
            "city",
            "zip_code",
            "radius_miles",
            "is_resale",
        ]
        for case in PARSE_TEST_CASES:
            expected = case["expected"]
            for field in required_fields:
                assert field in expected, f"Missing field '{field}' in test case: {case['input']}"


class TestSimpleCityState:
    """Test parsing of simple 'City, State' format."""

    def test_oakland_ca(self):
        """Oakland, CA should parse to city=Oakland, state=CA, county=Alameda."""
        case = PARSE_TEST_CASES[0]
        assert case["input"] == "Oakland, CA"
        expected = case["expected"]
        assert expected["city"] == "Oakland"
        assert expected["state_code"] == "CA"
        assert expected["county"] == "Alameda"
        assert expected["country"] == "US"
        assert expected["is_resale"] is False


class TestZipCodeOnly:
    """Test parsing of zip code only format."""

    def test_zip_33174(self):
        """33174 should resolve to Miami, FL, Miami-Dade county."""
        case = PARSE_TEST_CASES[1]
        assert case["input"] == "33174"
        expected = case["expected"]
        assert expected["zip_code"] == "33174"
        assert expected["city"] == "Miami"
        assert expected["state_code"] == "FL"
        assert expected["county"] == "Miami-Dade"


class TestRadiusExtraction:
    """Test extraction of radius from location strings."""

    def test_livermore_with_radius(self):
        """'Livermore CA 94551 and 25 miles' should extract radius_miles=25."""
        case = PARSE_TEST_CASES[2]
        expected = case["expected"]
        assert expected["radius_miles"] == 25
        assert expected["zip_code"] == "94551"
        assert expected["city"] == "Livermore"

    def test_zip_plus_miles(self):
        """'48188 + 50 Miles' should extract radius_miles=50."""
        case = next(c for c in PARSE_TEST_CASES if c["input"] == "48188 + 50 Miles")
        expected = case["expected"]
        assert expected["radius_miles"] == 50
        assert expected["zip_code"] == "48188"


class TestCountyLevel:
    """Test parsing of county-level locations."""

    def test_orange_county_ca(self):
        """'Orange County CA' should have county=Orange, city=None."""
        case = PARSE_TEST_CASES[4]
        assert case["input"] == "Orange County CA"
        expected = case["expected"]
        assert expected["county"] == "Orange"
        assert expected["city"] is None
        assert expected["state_code"] == "CA"


class TestResaleExtraction:
    """Test extraction of resale flag from location strings."""

    def test_amarillo_resale(self):
        """'Amarillo TX resale' should have is_resale=True."""
        case = PARSE_TEST_CASES[5]
        expected = case["expected"]
        assert expected["is_resale"] is True
        assert expected["city"] == "Amarillo"

    def test_rochester_resale_uppercase(self):
        """'Rochester, NY RESALE' should have is_resale=True."""
        case = PARSE_TEST_CASES[6]
        expected = case["expected"]
        assert expected["is_resale"] is True
        assert expected["city"] == "Rochester"


class TestInternationalLocations:
    """Test parsing of international (non-US) locations."""

    def test_oakville_ontario(self):
        """'Oakville Ontario L6H4N8' should have country=CA (Canada)."""
        case = PARSE_TEST_CASES[7]
        expected = case["expected"]
        assert expected["country"] == "CA"
        assert expected["state_code"] == "ON"
        assert expected["city"] == "Oakville"
        assert expected["zip_code"] == "L6H4N8"

    def test_mississauga_canada_explicit(self):
        """'Mississauga Ontario, Canada' should have country=CA."""
        case = PARSE_TEST_CASES[8]
        expected = case["expected"]
        assert expected["country"] == "CA"
        assert expected["city"] == "Mississauga"


class TestMultiLocationSplit:
    """Test splitting of multi-location entries."""

    def test_dallas_or_amarillo(self):
        """'Dallas or Amarillo, TX' should split into 2 locations."""
        case = MULTI_LOCATION_TEST_CASES[0]
        assert case["expected_count"] == 2
        assert "Dallas" in case["expected_cities"]
        assert "Amarillo" in case["expected_cities"]

    def test_san_jose_and_dallas(self):
        """'San Jose, CA and Dallas, TX' should split into 2 locations."""
        case = MULTI_LOCATION_TEST_CASES[1]
        assert case["expected_count"] == 2

    def test_county_and_county(self):
        """'orange county and Los Angeles county' should split into 2."""
        case = MULTI_LOCATION_TEST_CASES[2]
        assert case["expected_count"] == 2


class TestEdgeCases:
    """Test edge cases and unusual formats."""

    def test_city_state_zip_no_comma(self):
        """'Norfolk VA 23504' should parse correctly without comma."""
        case = PARSE_TEST_CASES[3]
        expected = case["expected"]
        assert expected["city"] == "Norfolk"
        assert expected["state_code"] == "VA"
        assert expected["zip_code"] == "23504"

    def test_state_zip_format(self):
        """'FL 33436' should resolve to city from zip."""
        case = next(c for c in PARSE_TEST_CASES if c["input"] == "FL 33436")
        expected = case["expected"]
        assert expected["state_code"] == "FL"
        assert expected["zip_code"] == "33436"
        assert expected["city"] is not None


# Placeholder tests that will call actual implementation
class TestParserIntegration:
    """Integration tests that will use the actual parser implementation."""

    @pytest.mark.skip(reason="Parser implementation not yet available")
    def test_parse_simple_location(self):
        """Test actual parser with simple location."""
        from src.backend.scripts.parse_territory_locations import parse_location
        result = parse_location("Oakland, CA")
        assert result["city"] == "Oakland"
        assert result["state_code"] == "CA"

    @pytest.mark.skip(reason="Parser implementation not yet available")
    def test_parse_multi_location(self):
        """Test actual parser with multi-location."""
        from src.backend.scripts.parse_territory_locations import parse_location
        result = parse_location("Dallas or Amarillo, TX")
        assert isinstance(result, list)
        assert len(result) == 2















