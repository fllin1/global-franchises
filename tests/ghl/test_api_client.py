# tests/ghl/test_api_client.py
"""
Tests for the GHL API Client.

Uses mocking to avoid making real API calls.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

# Set environment variables before importing the module
os.environ["GHL_TOKEN"] = "test-token"
os.environ["GHL_LOCATION_ID"] = "test-location-id"

from src.ghl.api_client import (
    search_contacts,
    find_contact_by_email_or_phone,
    create_contact,
    update_contact,
    list_pipelines,
    get_or_create_lead_nurturing_pipeline,
    create_opportunity,
    update_opportunity,
    get_stage_id_for_workflow_status,
    get_workflow_status_for_stage,
    list_custom_fields,
    create_custom_field,
    get_or_create_custom_field,
    clear_custom_field_cache,
    WORKFLOW_TO_STAGE,
    STAGE_TO_WORKFLOW,
)


class TestWorkflowStatusMapping:
    """Test workflow status to stage mapping for Lead Nurturing pipeline."""

    def test_workflow_to_stage_mapping(self):
        """All workflow statuses should have a stage mapping matching GHL Lead Nurturing pipeline."""
        expected_mappings = {
            "new_lead": "New Lead",
            "initial_sms_sent": "Initial SMS Sent",
            "sms_engaged_scheduling": "SMS Engaged - Scheduling",
            "deeper_dive_scheduled": "Deeper Dive Scheduled",
            "needs_manual_followup": "Needs Manual Follow-up",
            "qualified_post_deeper_dive": "Qualified - Post Deeper Dive",
            "franchises_presented": "Franchise(s) Presented",
            "funding_intro_made": "Funding Intro Made",
            "franchisor_intro_made": "Franchisor Intro Made",
            "closed_won": "Closed - Won",
            "disqualified": "Disqualified",
            "nurturing_long_term": "Nurturing - Long Term",
        }
        
        assert WORKFLOW_TO_STAGE == expected_mappings

    def test_stage_to_workflow_mapping(self):
        """All stages should map back to workflow statuses."""
        expected_mappings = {
            "New Lead": "new_lead",
            "Initial SMS Sent": "initial_sms_sent",
            "SMS Engaged - Scheduling": "sms_engaged_scheduling",
            "Deeper Dive Scheduled": "deeper_dive_scheduled",
            "Needs Manual Follow-up": "needs_manual_followup",
            "Qualified - Post Deeper Dive": "qualified_post_deeper_dive",
            "Franchise(s) Presented": "franchises_presented",
            "Funding Intro Made": "funding_intro_made",
            "Franchisor Intro Made": "franchisor_intro_made",
            "Closed - Won": "closed_won",
            "Disqualified": "disqualified",
            "Nurturing - Long Term": "nurturing_long_term",
        }
        
        assert STAGE_TO_WORKFLOW == expected_mappings

    def test_get_stage_id_for_workflow_status(self):
        """Should return correct stage ID for workflow status."""
        pipeline = {
            "id": "pipeline-123",
            "stages": [
                {"id": "stage-1", "name": "New Lead"},
                {"id": "stage-2", "name": "Initial SMS Sent"},
                {"id": "stage-3", "name": "Qualified - Post Deeper Dive"},
                {"id": "stage-4", "name": "Closed - Won"},
            ]
        }
        
        assert get_stage_id_for_workflow_status(pipeline, "new_lead") == "stage-1"
        assert get_stage_id_for_workflow_status(pipeline, "initial_sms_sent") == "stage-2"
        assert get_stage_id_for_workflow_status(pipeline, "qualified_post_deeper_dive") == "stage-3"
        assert get_stage_id_for_workflow_status(pipeline, "closed_won") == "stage-4"
        assert get_stage_id_for_workflow_status(pipeline, "unknown") is None

    def test_get_workflow_status_for_stage(self):
        """Should return correct workflow status for stage ID."""
        pipeline = {
            "id": "pipeline-123",
            "stages": [
                {"id": "stage-1", "name": "New Lead"},
                {"id": "stage-2", "name": "Initial SMS Sent"},
                {"id": "stage-3", "name": "Disqualified"},
            ]
        }
        
        assert get_workflow_status_for_stage(pipeline, "stage-1") == "new_lead"
        assert get_workflow_status_for_stage(pipeline, "stage-2") == "initial_sms_sent"
        assert get_workflow_status_for_stage(pipeline, "stage-3") == "disqualified"
        assert get_workflow_status_for_stage(pipeline, "stage-unknown") is None


class TestContactOperations:
    """Test contact API operations."""

    @patch("src.ghl.api_client._api_request")
    def test_search_contacts_by_email(self, mock_request):
        """Should search contacts by email."""
        mock_request.return_value = {
            "contacts": [
                {"id": "contact-1", "email": "test@example.com", "firstName": "John"}
            ]
        }
        
        result = search_contacts(email="test@example.com")
        
        assert len(result) == 1
        assert result[0]["email"] == "test@example.com"
        mock_request.assert_called_once()

    @patch("src.ghl.api_client._api_request")
    def test_search_contacts_by_phone(self, mock_request):
        """Should search contacts by phone."""
        mock_request.return_value = {
            "contacts": [
                {"id": "contact-2", "phone": "+1234567890", "firstName": "Jane"}
            ]
        }
        
        result = search_contacts(phone="+1234567890")
        
        assert len(result) == 1
        assert result[0]["phone"] == "+1234567890"

    @patch("src.ghl.api_client._api_request")
    def test_find_contact_by_email_first(self, mock_request):
        """Should find contact by email first, then phone."""
        mock_request.return_value = {
            "contacts": [
                {"id": "contact-1", "email": "test@example.com"}
            ]
        }
        
        result = find_contact_by_email_or_phone(email="test@example.com", phone="+1234567890")
        
        assert result["id"] == "contact-1"
        # Should only call once (email search succeeds)
        assert mock_request.call_count == 1

    @patch("src.ghl.api_client._api_request")
    def test_find_contact_falls_back_to_phone(self, mock_request):
        """Should fall back to phone if email not found."""
        # First call (email) returns empty, second call (phone) returns contact
        mock_request.side_effect = [
            {"contacts": []},
            {"contacts": [{"id": "contact-2", "phone": "+1234567890"}]}
        ]
        
        result = find_contact_by_email_or_phone(email="notfound@example.com", phone="+1234567890")
        
        assert result["id"] == "contact-2"
        assert mock_request.call_count == 2

    @patch("src.ghl.api_client._api_request")
    def test_create_contact(self, mock_request):
        """Should create a new contact."""
        mock_request.return_value = {
            "contact": {
                "id": "new-contact-1",
                "firstName": "John",
                "lastName": "Doe",
                "email": "john@example.com"
            }
        }
        
        result = create_contact(
            name="John Doe",
            email="john@example.com",
            city="Austin",
            state="TX"
        )
        
        assert result["id"] == "new-contact-1"
        mock_request.assert_called_once()
        
        # Check the call arguments
        call_args = mock_request.call_args
        assert call_args[0][0] == "POST"
        assert "firstName" in call_args[1]["json_body"]

    @patch("src.ghl.api_client._api_request")
    def test_update_contact(self, mock_request):
        """Should update an existing contact."""
        mock_request.return_value = {
            "contact": {
                "id": "contact-1",
                "firstName": "John",
                "lastName": "Updated"
            }
        }
        
        result = update_contact(
            contact_id="contact-1",
            last_name="Updated"
        )
        
        assert result["id"] == "contact-1"
        mock_request.assert_called_once()


class TestPipelineOperations:
    """Test pipeline API operations."""

    @patch("src.ghl.api_client._api_request")
    def test_list_pipelines(self, mock_request):
        """Should list all pipelines."""
        mock_request.return_value = {
            "pipelines": [
                {"id": "pipeline-1", "name": "Sales Pipeline"},
                {"id": "pipeline-2", "name": "Lead Nurturing"}
            ]
        }
        
        result = list_pipelines()
        
        assert len(result) == 2
        assert result[0]["name"] == "Sales Pipeline"

    @patch("src.ghl.api_client._api_request")
    def test_get_or_create_lead_nurturing_pipeline_existing(self, mock_request):
        """Should return existing Lead Nurturing pipeline."""
        mock_request.return_value = {
            "pipelines": [
                {"id": "pipeline-1", "name": "Lead Nurturing", "stages": []}
            ]
        }
        
        result = get_or_create_lead_nurturing_pipeline()
        
        assert result["id"] == "pipeline-1"
        assert result["name"] == "Lead Nurturing"
        # Should only call list_pipelines, not create
        assert mock_request.call_count == 1

    @patch("src.ghl.api_client._api_request")
    def test_get_or_create_lead_nurturing_pipeline_not_found_raises(self, mock_request):
        """Should raise error if Lead Nurturing pipeline not found."""
        mock_request.return_value = {"pipelines": []}
        
        with pytest.raises(RuntimeError, match="Lead Nurturing pipeline not found"):
            get_or_create_lead_nurturing_pipeline()


class TestOpportunityOperations:
    """Test opportunity API operations."""

    @patch("src.ghl.api_client._api_request")
    def test_create_opportunity(self, mock_request):
        """Should create a new opportunity."""
        mock_request.return_value = {
            "opportunity": {
                "id": "opp-1",
                "name": "Franchise Lead: John Doe",
                "pipelineId": "pipeline-1",
                "pipelineStageId": "stage-1",
                "status": "open"
            }
        }
        
        result = create_opportunity(
            contact_id="contact-1",
            pipeline_id="pipeline-1",
            stage_id="stage-1",
            name="Franchise Lead: John Doe",
            monetary_value=500000
        )
        
        assert result["id"] == "opp-1"
        assert result["status"] == "open"
        mock_request.assert_called_once()

    @patch("src.ghl.api_client._api_request")
    def test_update_opportunity(self, mock_request):
        """Should update an existing opportunity."""
        mock_request.return_value = {
            "opportunity": {
                "id": "opp-1",
                "pipelineStageId": "stage-2",
                "status": "open"
            }
        }
        
        result = update_opportunity(
            opportunity_id="opp-1",
            stage_id="stage-2"
        )
        
        assert result["id"] == "opp-1"
        assert result["pipelineStageId"] == "stage-2"


class TestCustomFieldOperations:
    """Test custom field API operations."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Clear custom field cache before each test."""
        clear_custom_field_cache()

    @patch("src.ghl.api_client._api_request")
    def test_list_custom_fields(self, mock_request):
        """Should list all custom fields for contacts."""
        mock_request.return_value = {
            "customFields": [
                {"id": "cf-1", "name": "FG Liquidity", "dataType": "MONETARY"},
                {"id": "cf-2", "name": "FG Location", "dataType": "SINGLE_LINE_TEXT"},
            ]
        }
        
        result = list_custom_fields(model="contact")
        
        assert len(result) == 2
        assert result[0]["name"] == "FG Liquidity"
        mock_request.assert_called_once()

    @patch("src.ghl.api_client._api_request")
    def test_create_custom_field(self, mock_request):
        """Should create a new custom field."""
        mock_request.return_value = {
            "customField": {
                "id": "cf-new",
                "name": "FG Net Worth",
                "dataType": "MONETARY",
            }
        }
        
        result = create_custom_field(
            name="FG Net Worth",
            data_type="MONETARY",
            model="contact"
        )
        
        assert result["id"] == "cf-new"
        assert result["name"] == "FG Net Worth"
        mock_request.assert_called_once()

    @patch("src.ghl.api_client._api_request")
    def test_get_or_create_custom_field_exists(self, mock_request):
        """Should return existing custom field ID if already exists."""
        mock_request.return_value = {
            "customFields": [
                {"id": "cf-existing", "name": "FG Liquidity", "dataType": "MONETARY"},
            ]
        }
        
        result = get_or_create_custom_field(
            name="FG Liquidity",
            data_type="MONETARY",
            model="contact"
        )
        
        assert result == "cf-existing"
        # Should only call list, not create
        assert mock_request.call_count == 1

    @patch("src.ghl.api_client._api_request")
    def test_get_or_create_custom_field_creates_new(self, mock_request):
        """Should create custom field if not exists."""
        # First call returns empty list, second call creates field
        mock_request.side_effect = [
            {"customFields": []},
            {"customField": {"id": "cf-new", "name": "FG Liquidity", "dataType": "MONETARY"}}
        ]
        
        result = get_or_create_custom_field(
            name="FG Liquidity",
            data_type="MONETARY",
            model="contact"
        )
        
        assert result == "cf-new"
        assert mock_request.call_count == 2

