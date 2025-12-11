# tests/ghl/test_sync_service.py
"""
Tests for the GHL Sync Service.

Uses mocking to avoid making real API calls and database operations.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

# Set environment variables before importing the module
os.environ["GHL_TOKEN"] = "test-token"
os.environ["GHL_LOCATION_ID"] = "test-location-id"

from src.ghl.sync_service import (
    _parse_location,
    sync_lead_to_ghl,
    sync_from_ghl,
    bulk_sync_leads_to_ghl,
    bulk_sync_from_ghl,
    two_way_sync_lead,
    _clear_pipeline_cache,
)


class TestParseLocation:
    """Test location parsing helper."""

    def test_parse_city_and_state(self):
        """Should parse 'City, State' format."""
        city, state = _parse_location("Austin, TX")
        assert city == "Austin"
        assert state == "TX"

    def test_parse_city_and_full_state(self):
        """Should parse 'City, Full State Name' format."""
        city, state = _parse_location("New York, New York")
        assert city == "New York"
        assert state == "New York"

    def test_parse_state_code_only(self):
        """Should parse 2-letter state code only."""
        city, state = _parse_location("TX")
        assert city is None
        assert state == "TX"

    def test_parse_city_only(self):
        """Should parse city only (no comma)."""
        city, state = _parse_location("Austin")
        assert city == "Austin"
        assert state is None

    def test_parse_none(self):
        """Should handle None input."""
        city, state = _parse_location(None)
        assert city is None
        assert state is None

    def test_parse_empty_string(self):
        """Should handle empty string."""
        city, state = _parse_location("")
        assert city is None
        assert state is None


class TestSyncLeadToGHL:
    """Test sync_lead_to_ghl function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Clear pipeline cache before each test."""
        _clear_pipeline_cache()

    @patch("src.ghl.sync_service.supabase_client")
    @patch("src.ghl.sync_service.get_or_create_franchise_leads_pipeline")
    @patch("src.ghl.sync_service.find_contact_by_email_or_phone")
    @patch("src.ghl.sync_service.create_contact")
    @patch("src.ghl.sync_service.create_opportunity")
    def test_sync_new_lead_creates_contact_and_opportunity(
        self,
        mock_create_opportunity,
        mock_create_contact,
        mock_find_contact,
        mock_get_pipeline,
        mock_supabase,
    ):
        """Should create contact and opportunity for new lead."""
        # Setup mocks
        mock_supabase_instance = MagicMock()
        mock_supabase.return_value = mock_supabase_instance
        
        # Lead data from database
        mock_supabase_instance.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {
                "id": 1,
                "candidate_name": "John Doe",
                "workflow_status": "new",
                "qualification_status": "tier_1",
                "profile_data": {
                    "candidate_name": "John Doe",
                    "email": "john@example.com",
                    "phone": "+1234567890",
                    "location": "Austin, TX",
                    "liquidity": 500000,
                },
                "ghl_contact_id": None,
                "ghl_opportunity_id": None,
            }
        ]
        
        mock_get_pipeline.return_value = {
            "id": "pipeline-1",
            "stages": [
                {"id": "stage-1", "name": "New Lead"},
                {"id": "stage-2", "name": "Contacted"},
            ]
        }
        
        mock_find_contact.return_value = None
        mock_create_contact.return_value = {"id": "contact-1"}
        mock_create_opportunity.return_value = {"id": "opp-1"}
        
        # Update call should succeed
        mock_supabase_instance.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()
        
        # Execute
        result = sync_lead_to_ghl(1)
        
        # Verify
        assert result["success"] is True
        assert result["lead_id"] == 1
        assert result["ghl_contact_id"] == "contact-1"
        assert result["ghl_opportunity_id"] == "opp-1"
        assert result["action"] == "created"
        
        # Verify contact was created
        mock_create_contact.assert_called_once()
        
        # Verify opportunity was created
        mock_create_opportunity.assert_called_once()

    @patch("src.ghl.sync_service.supabase_client")
    def test_sync_nonexistent_lead_returns_error(self, mock_supabase):
        """Should return error for non-existent lead."""
        mock_supabase_instance = MagicMock()
        mock_supabase.return_value = mock_supabase_instance
        mock_supabase_instance.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        result = sync_lead_to_ghl(999)
        
        assert result["success"] is False
        assert result["error"] == "Lead not found"

    @patch("src.ghl.sync_service.supabase_client")
    @patch("src.ghl.sync_service.get_or_create_franchise_leads_pipeline")
    @patch("src.ghl.sync_service.get_contact")
    @patch("src.ghl.sync_service.update_contact")
    @patch("src.ghl.sync_service.get_opportunity")
    @patch("src.ghl.sync_service.update_opportunity")
    def test_sync_existing_lead_updates_contact_and_opportunity(
        self,
        mock_update_opportunity,
        mock_get_opportunity,
        mock_update_contact,
        mock_get_contact,
        mock_get_pipeline,
        mock_supabase,
    ):
        """Should update existing contact and opportunity."""
        # Setup mocks
        mock_supabase_instance = MagicMock()
        mock_supabase.return_value = mock_supabase_instance
        
        # Lead with existing GHL IDs
        mock_supabase_instance.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {
                "id": 1,
                "candidate_name": "John Doe",
                "workflow_status": "contacted",
                "qualification_status": "tier_1",
                "profile_data": {"location": "Austin, TX"},
                "ghl_contact_id": "existing-contact-1",
                "ghl_opportunity_id": "existing-opp-1",
            }
        ]
        
        mock_get_pipeline.return_value = {
            "id": "pipeline-1",
            "stages": [
                {"id": "stage-1", "name": "New Lead"},
                {"id": "stage-2", "name": "Contacted"},
            ]
        }
        
        mock_get_contact.return_value = {"id": "existing-contact-1"}
        mock_update_contact.return_value = {"id": "existing-contact-1"}
        
        mock_get_opportunity.return_value = {
            "id": "existing-opp-1",
            "pipelineStageId": "stage-1"  # Different from current status
        }
        mock_update_opportunity.return_value = {"id": "existing-opp-1"}
        
        mock_supabase_instance.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()
        
        result = sync_lead_to_ghl(1)
        
        assert result["success"] is True
        assert result["action"] == "updated"
        mock_update_opportunity.assert_called_once()


class TestSyncFromGHL:
    """Test sync_from_ghl function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Clear pipeline cache before each test."""
        _clear_pipeline_cache()

    @patch("src.ghl.sync_service.supabase_client")
    def test_sync_from_ghl_no_opportunity_id(self, mock_supabase):
        """Should return error if lead has no opportunity ID."""
        mock_supabase_instance = MagicMock()
        mock_supabase.return_value = mock_supabase_instance
        mock_supabase_instance.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {
                "id": 1,
                "workflow_status": "new",
                "ghl_opportunity_id": None,
            }
        ]
        
        result = sync_from_ghl(1)
        
        assert result["success"] is False
        assert "not synced" in result["error"]

    @patch("src.ghl.sync_service.supabase_client")
    @patch("src.ghl.sync_service.get_opportunity")
    @patch("src.ghl.sync_service._get_pipeline")
    def test_sync_from_ghl_updates_workflow_status(
        self, mock_get_pipeline, mock_get_opportunity, mock_supabase
    ):
        """Should update workflow status from GHL opportunity stage."""
        mock_supabase_instance = MagicMock()
        mock_supabase.return_value = mock_supabase_instance
        mock_supabase_instance.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {
                "id": 1,
                "workflow_status": "new",
                "ghl_opportunity_id": "opp-1",
            }
        ]
        
        mock_get_pipeline.return_value = {
            "id": "pipeline-1",
            "stages": [
                {"id": "stage-1", "name": "New Lead"},
                {"id": "stage-2", "name": "Contacted"},
            ]
        }
        
        mock_get_opportunity.return_value = {
            "id": "opp-1",
            "pipelineStageId": "stage-2"  # "Contacted"
        }
        
        mock_supabase_instance.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()
        
        result = sync_from_ghl(1)
        
        assert result["success"] is True
        assert result["workflow_status"] == "contacted"
        assert result["changed"] is True

    @patch("src.ghl.sync_service.supabase_client")
    @patch("src.ghl.sync_service.get_opportunity")
    @patch("src.ghl.sync_service._get_pipeline")
    def test_sync_from_ghl_no_change(
        self, mock_get_pipeline, mock_get_opportunity, mock_supabase
    ):
        """Should not update if status is the same."""
        mock_supabase_instance = MagicMock()
        mock_supabase.return_value = mock_supabase_instance
        mock_supabase_instance.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {
                "id": 1,
                "workflow_status": "contacted",
                "ghl_opportunity_id": "opp-1",
            }
        ]
        
        mock_get_pipeline.return_value = {
            "id": "pipeline-1",
            "stages": [
                {"id": "stage-1", "name": "New Lead"},
                {"id": "stage-2", "name": "Contacted"},
            ]
        }
        
        mock_get_opportunity.return_value = {
            "id": "opp-1",
            "pipelineStageId": "stage-2"  # Same as current
        }
        
        result = sync_from_ghl(1)
        
        assert result["success"] is True
        assert result["workflow_status"] == "contacted"
        assert result["changed"] is False


class TestBulkSync:
    """Test bulk sync functions."""

    @patch("src.ghl.sync_service.sync_lead_to_ghl")
    def test_bulk_sync_leads_to_ghl(self, mock_sync):
        """Should sync multiple leads and return summary."""
        mock_sync.side_effect = [
            {"success": True, "lead_id": 1, "action": "created"},
            {"success": True, "lead_id": 2, "action": "updated"},
            {"success": False, "lead_id": 3, "error": "Some error"},
        ]
        
        result = bulk_sync_leads_to_ghl([1, 2, 3])
        
        assert result["total"] == 3
        assert result["success"] == 2
        assert result["failed"] == 1
        assert len(result["results"]) == 3

    @patch("src.ghl.sync_service.sync_from_ghl")
    def test_bulk_sync_from_ghl(self, mock_sync):
        """Should sync multiple leads from GHL and return summary."""
        mock_sync.side_effect = [
            {"success": True, "lead_id": 1, "changed": True},
            {"success": True, "lead_id": 2, "changed": False},
            {"success": False, "lead_id": 3, "error": "Not synced"},
        ]
        
        result = bulk_sync_from_ghl([1, 2, 3])
        
        assert result["total"] == 3
        assert result["success"] == 2
        assert result["failed"] == 1
        assert result["changed"] == 1


class TestTwoWaySync:
    """Test two-way sync function."""

    @patch("src.ghl.sync_service.sync_from_ghl")
    @patch("src.ghl.sync_service.sync_lead_to_ghl")
    def test_two_way_sync_lead(self, mock_push, mock_pull):
        """Should perform both pull and push sync."""
        mock_pull.return_value = {
            "success": True,
            "lead_id": 1,
            "workflow_status": "contacted",
            "changed": True,
        }
        mock_push.return_value = {
            "success": True,
            "lead_id": 1,
            "ghl_contact_id": "contact-1",
            "ghl_opportunity_id": "opp-1",
            "action": "synced",
        }
        
        result = two_way_sync_lead(1)
        
        assert result["lead_id"] == 1
        assert result["success"] is True
        assert result["pull"]["changed"] is True
        assert result["push"]["action"] == "synced"
        
        mock_pull.assert_called_once_with(1)
        mock_push.assert_called_once_with(1)
