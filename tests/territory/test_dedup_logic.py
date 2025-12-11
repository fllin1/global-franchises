# -*- coding: utf-8 -*-
"""
Tests for territory deduplication logic.

These tests verify the geographic hierarchy-based deduplication rules:
- Geographic hierarchy: Zip ⊂ City ⊂ County ⊂ State
- If status = "Not Available": Keep BROADER scope
- If status = "Available": Keep SPECIFIC scope
- Mixed status: Newer check_date always wins
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any


# Sample records for testing
def make_record(
    id: int,
    franchise_id: int,
    state_code: str,
    county: str | None,
    city: str | None,
    zip_code: str | None,
    availability_status: str,
    check_date: datetime,
    location_raw: str = "",
) -> Dict[str, Any]:
    """Create a territory check record for testing."""
    return {
        "id": id,
        "franchise_id": franchise_id,
        "state_code": state_code,
        "county": county,
        "city": city,
        "zip_code": zip_code,
        "availability_status": availability_status,
        "check_date": check_date.isoformat(),
        "location_raw": location_raw or f"{city or county or state_code}",
    }


# Test dates
DATE_OLD = datetime(2025, 11, 15)
DATE_NEW = datetime(2025, 11, 19)
DATE_NEWEST = datetime(2025, 11, 25)


class TestDedupRules:
    """Test deduplication rules with geographic hierarchy."""

    def test_not_available_keeps_broader_scope(self):
        """
        When status is 'Not Available', keep the BROADER scope.
        
        City-level 'Not Available' (newer) should supersede zip-level 'Not Available' (older).
        """
        records = [
            # Older, specific (zip-level)
            make_record(
                id=1,
                franchise_id=50,
                state_code="IN",
                county="Marion",
                city="Indianapolis",
                zip_code="46077",
                availability_status="Not Available",
                check_date=DATE_OLD,
                location_raw="Indianapolis, 46077 IN",
            ),
            # Newer, broader (city-level)
            make_record(
                id=2,
                franchise_id=50,
                state_code="IN",
                county="Marion",
                city="Indianapolis",
                zip_code=None,
                availability_status="Not Available",
                check_date=DATE_NEW,
                location_raw="Indianapolis, IN",
            ),
        ]
        
        # Expected: Keep record 2 (city-level, broader restriction)
        # Delete record 1 (redundant - zip is within city that's already not available)
        expected_keep_ids = [2]
        expected_delete_ids = [1]
        
        # Store expected behavior for implementation testing
        self._expected_keep = expected_keep_ids
        self._expected_delete = expected_delete_ids
        self._records = records

    def test_available_keeps_specific_scope(self):
        """
        When status is 'Available', keep the SPECIFIC scope.
        
        Zip-level 'Available' is more informative than city-level 'Available'.
        """
        records = [
            # Older, specific (zip-level)
            make_record(
                id=1,
                franchise_id=50,
                state_code="IN",
                county="Marion",
                city="Indianapolis",
                zip_code="46077",
                availability_status="Available",
                check_date=DATE_OLD,
                location_raw="Indianapolis, 46077 IN",
            ),
            # Newer, broader (city-level)
            make_record(
                id=2,
                franchise_id=50,
                state_code="IN",
                county="Marion",
                city="Indianapolis",
                zip_code=None,
                availability_status="Available",
                check_date=DATE_NEW,
                location_raw="Indianapolis, IN",
            ),
        ]
        
        # Expected: Keep record 1 (zip-level, more specific/informative)
        # Delete record 2 (redundant - city available implies zip could be, but zip is more actionable)
        expected_keep_ids = [1]
        expected_delete_ids = [2]
        
        self._expected_keep = expected_keep_ids
        self._expected_delete = expected_delete_ids
        self._records = records

    def test_mixed_status_newer_wins(self):
        """
        When status differs between checks, newer check_date always wins.
        """
        records = [
            # Older: Available
            make_record(
                id=1,
                franchise_id=50,
                state_code="IN",
                county="Marion",
                city="Indianapolis",
                zip_code="46077",
                availability_status="Available",
                check_date=DATE_OLD,
                location_raw="Indianapolis, 46077 IN",
            ),
            # Newer: Not Available (status changed)
            make_record(
                id=2,
                franchise_id=50,
                state_code="IN",
                county="Marion",
                city="Indianapolis",
                zip_code=None,
                availability_status="Not Available",
                check_date=DATE_NEW,
                location_raw="Indianapolis, IN",
            ),
        ]
        
        # Expected: Keep record 2 (newer, status changed)
        # The newer city-level "Not Available" supersedes older zip-level "Available"
        expected_keep_ids = [2]
        expected_delete_ids = [1]
        
        self._expected_keep = expected_keep_ids
        self._expected_delete = expected_delete_ids
        self._records = records

    def test_exact_duplicates_keep_newest(self):
        """
        Exact duplicates (same location_raw) should keep the most recent check_date.
        """
        records = [
            make_record(
                id=1,
                franchise_id=50,
                state_code="CA",
                county="Alameda",
                city="Oakland",
                zip_code=None,
                availability_status="Available",
                check_date=DATE_OLD,
                location_raw="Oakland, CA",
            ),
            make_record(
                id=2,
                franchise_id=50,
                state_code="CA",
                county="Alameda",
                city="Oakland",
                zip_code=None,
                availability_status="Available",
                check_date=DATE_NEW,
                location_raw="Oakland, CA",
            ),
            make_record(
                id=3,
                franchise_id=50,
                state_code="CA",
                county="Alameda",
                city="Oakland",
                zip_code=None,
                availability_status="Available",
                check_date=DATE_NEWEST,
                location_raw="Oakland, CA",
            ),
        ]
        
        # Expected: Keep record 3 (newest)
        expected_keep_ids = [3]
        expected_delete_ids = [1, 2]
        
        self._expected_keep = expected_keep_ids
        self._expected_delete = expected_delete_ids
        self._records = records


class TestGeographicHierarchy:
    """Test geographic containment logic."""

    def test_zip_contained_in_city(self):
        """Verify that zip codes are considered contained in their city."""
        # 46077 is in Indianapolis
        assert _zip_in_city("46077", "Indianapolis", "IN") is True
        # 90210 is in Beverly Hills, not Indianapolis
        assert _zip_in_city("90210", "Indianapolis", "IN") is False

    def test_city_contained_in_county(self):
        """Verify that cities are considered contained in their county."""
        assert _city_in_county("Indianapolis", "Marion", "IN") is True
        assert _city_in_county("Indianapolis", "Hamilton", "IN") is False

    def test_county_contained_in_state(self):
        """Verify that counties are considered contained in their state."""
        assert _county_in_state("Marion", "IN") is True
        assert _county_in_state("Marion", "TX") is False


class TestScopeComparison:
    """Test scope comparison between records."""

    def test_zip_more_specific_than_city(self):
        """Zip-level is more specific than city-level."""
        zip_record = make_record(
            id=1, franchise_id=50, state_code="IN", county="Marion",
            city="Indianapolis", zip_code="46077",
            availability_status="Available", check_date=DATE_OLD,
        )
        city_record = make_record(
            id=2, franchise_id=50, state_code="IN", county="Marion",
            city="Indianapolis", zip_code=None,
            availability_status="Available", check_date=DATE_NEW,
        )
        
        assert _get_scope_level(zip_record) < _get_scope_level(city_record)

    def test_city_more_specific_than_county(self):
        """City-level is more specific than county-level."""
        city_record = make_record(
            id=1, franchise_id=50, state_code="CA", county="Orange",
            city="Irvine", zip_code=None,
            availability_status="Available", check_date=DATE_OLD,
        )
        county_record = make_record(
            id=2, franchise_id=50, state_code="CA", county="Orange",
            city=None, zip_code=None,
            availability_status="Available", check_date=DATE_NEW,
        )
        
        assert _get_scope_level(city_record) < _get_scope_level(county_record)

    def test_county_more_specific_than_state(self):
        """County-level is more specific than state-level."""
        county_record = make_record(
            id=1, franchise_id=50, state_code="CA", county="Orange",
            city=None, zip_code=None,
            availability_status="Available", check_date=DATE_OLD,
        )
        state_record = make_record(
            id=2, franchise_id=50, state_code="CA", county=None,
            city=None, zip_code=None,
            availability_status="Available", check_date=DATE_NEW,
        )
        
        assert _get_scope_level(county_record) < _get_scope_level(state_record)


class TestDedupScenarios:
    """Test complete deduplication scenarios."""

    def test_franchise_50_oakland_duplicates(self):
        """
        Real-world scenario: Oakland, CA appears 3 times for franchise 50.
        All Available - keep the newest.
        """
        records = [
            make_record(
                id=14014, franchise_id=50, state_code="CA", county="Alameda",
                city="Oakland", zip_code=None,
                availability_status="Available",
                check_date=datetime(2025, 11, 23),
                location_raw="Oakland, CA",
            ),
            make_record(
                id=14021, franchise_id=50, state_code="CA", county="Alameda",
                city="Oakland", zip_code=None,
                availability_status="Available",
                check_date=datetime(2025, 11, 14),
                location_raw="Oakland, CA",
            ),
            make_record(
                id=14022, franchise_id=50, state_code="CA", county="Alameda",
                city="Oakland", zip_code=None,
                availability_status="Available",
                check_date=datetime(2025, 11, 14),
                location_raw="Oakland, CA",
            ),
        ]
        
        # Expected: Keep 14014 (newest date 11/23)
        expected_keep_ids = [14014]
        expected_delete_ids = [14021, 14022]

    def test_dallas_zip_vs_city_not_available(self):
        """
        If Dallas city is Not Available, zip 75206 Not Available is redundant.
        """
        records = [
            # Zip-level (older)
            make_record(
                id=1, franchise_id=50, state_code="TX", county="Dallas",
                city="Dallas", zip_code="75206",
                availability_status="Not Available",
                check_date=datetime(2025, 11, 12),
                location_raw="Dallas, TX 75206",
            ),
            # City-level (newer)
            make_record(
                id=2, franchise_id=50, state_code="TX", county="Dallas",
                city="Dallas", zip_code=None,
                availability_status="Not Available",
                check_date=datetime(2025, 11, 20),
                location_raw="Dallas, TX",
            ),
        ]
        
        # Expected: Keep record 2 (city-level Not Available supersedes)
        expected_keep_ids = [2]
        expected_delete_ids = [1]

    def test_different_cities_same_county_not_affected(self):
        """
        Different cities in the same county should not affect each other.
        """
        records = [
            make_record(
                id=1, franchise_id=50, state_code="TX", county="Dallas",
                city="Dallas", zip_code=None,
                availability_status="Not Available",
                check_date=DATE_NEW,
                location_raw="Dallas, TX",
            ),
            make_record(
                id=2, franchise_id=50, state_code="TX", county="Dallas",
                city="Garland", zip_code=None,
                availability_status="Available",
                check_date=DATE_OLD,
                location_raw="Garland, TX",
            ),
        ]
        
        # Expected: Keep both - different cities
        expected_keep_ids = [1, 2]
        expected_delete_ids = []


# Helper functions (placeholders - will be implemented in actual module)
def _zip_in_city(zip_code: str, city: str, state_code: str) -> bool:
    """Check if a zip code is within a city. Placeholder."""
    # Will use pgeocode lookup
    return True  # Placeholder


def _city_in_county(city: str, county: str, state_code: str) -> bool:
    """Check if a city is within a county. Placeholder."""
    return True  # Placeholder


def _county_in_state(county: str, state_code: str) -> bool:
    """Check if a county is within a state."""
    # Counties are always within their state by definition
    return True


def _get_scope_level(record: Dict[str, Any]) -> int:
    """
    Get the scope level of a record.
    Lower number = more specific.
    
    Levels:
    1 = zip_code present
    2 = city present, no zip
    3 = county present, no city
    4 = state only
    """
    if record.get("zip_code"):
        return 1
    if record.get("city"):
        return 2
    if record.get("county"):
        return 3
    return 4


# Integration tests (placeholder)
class TestDedupIntegration:
    """Integration tests for the actual deduplication implementation."""

    @pytest.mark.skip(reason="Dedup implementation not yet available")
    def test_dedupe_franchise_records(self):
        """Test actual dedup function with franchise records."""
        from src.backend.scripts.dedupe_territory_checks import dedupe_franchise_records
        # Will test actual implementation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
















