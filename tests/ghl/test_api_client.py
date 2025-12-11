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
    get_or_create_franchise_leads_pipeline,
    create_opportunity,
    update_opportunity,
    get_stage_id_for_workflow_status,
    get_workflow_status_for_stage,
    WORKFLOW_TO_STAGE,
    STAGE_TO_WORKFLOW,
)


class TestWorkflowStatusMapping:
    """Test workflow status to stage mapping."""

    def test_workflow_to_stage_mapping(self):
        """All workflow statuses should have a stage mapping."""
        expected_mappings = {
            "new": "New Lead",
            "contacted": "Contacted",
            "qualified": "Qualified",
            "presented": "Presented",
            "closed_won": "Closed Won",
            "closed_lost": "Closed Lost",
        }
        
        assert WORKFLOW_TO_STAGE == expected_mappings

    def test_stage_to_workflow_mapping(self):
        """All stages should map back to workflow statuses."""
        expected_mappings = {
            "New Lead": "new",
            "Contacted": "contacted",
            "Qualified": "qualified",
            "Presented": "presented",
            "Closed Won": "closed_won",
            "Closed Lost": "closed_lost",
        }
        
        assert STAGE_TO_WORKFLOW == expected_mappings

    def test_get_stage_id_for_workflow_status(self):
        """Should return correct stage ID for workflow status."""
        pipeline = {
            "id": "pipeline-123",
            "stages": [
                {"id": "stage-1", "name": "New Lead"},
                {"id": "stage-2", "name": "Contacted"},
                {"id": "stage-3", "name": "Qualified"},
            ]
        }
        
        assert get_stage_id_for_workflow_status(pipeline, "new") == "stage-1"
        assert get_stage_id_for_workflow_status(pipeline, "contacted") == "stage-2"
        assert get_stage_id_for_workflow_status(pipeline, "qualified") == "stage-3"
        assert get_stage_id_for_workflow_status(pipeline, "unknown") is None

    def test_get_workflow_status_for_stage(self):
        """Should return correct workflow status for stage ID."""
        pipeline = {
            "id": "pipeline-123",
            "stages": [
                {"id": "stage-1", "name": "New Lead"},
                {"id": "stage-2", "name": "Contacted"},
            ]
        }
        
        assert get_workflow_status_for_stage(pipeline, "stage-1") == "new"
        assert get_workflow_status_for_stage(pipeline, "stage-2") == "contacted"
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
                {"id": "pipeline-2", "name": "Franchise Leads"}
            ]
        }
        
        result = list_pipelines()
        
        assert len(result) == 2
        assert result[0]["name"] == "Sales Pipeline"

    @patch("src.ghl.api_client._api_request")
    def test_get_or_create_franchise_leads_pipeline_existing(self, mock_request):
        """Should return existing Franchise Leads pipeline."""
        mock_request.return_value = {
            "pipelines": [
                {"id": "pipeline-1", "name": "Franchise Leads", "stages": []}
            ]
        }
        
        result = get_or_create_franchise_leads_pipeline()
        
        assert result["id"] == "pipeline-1"
        assert result["name"] == "Franchise Leads"
        # Should only call list_pipelines, not create
        assert mock_request.call_count == 1

    @patch("src.ghl.api_client._api_request")
    def test_get_or_create_franchise_leads_pipeline_creates_new(self, mock_request):
        """Should create new Franchise Leads pipeline if not exists."""
        # First call returns empty list, second call creates pipeline
        mock_request.side_effect = [
            {"pipelines": []},
            {
                "pipeline": {
                    "id": "new-pipeline-1",
                    "name": "Franchise Leads",
                    "stages": [
                        {"id": "stage-1", "name": "New Lead"},
                        {"id": "stage-2", "name": "Contacted"},
                    ]
                }
            }
        ]
        
        result = get_or_create_franchise_leads_pipeline()
        
        assert result["id"] == "new-pipeline-1"
        assert result["name"] == "Franchise Leads"
        assert mock_request.call_count == 2


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
