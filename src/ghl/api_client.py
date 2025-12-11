# src/ghl/api_client.py
"""
GoHighLevel API Client for Contacts and Opportunities.

Implements GHL API v2 calls for two-way sync with leads.
"""

import os
import time
from typing import Dict, List, Optional, Any

from dotenv import load_dotenv
from loguru import logger
import requests

# ---------- Config ----------
load_dotenv()

TOKEN = os.environ.get("GHL_TOKEN")
LOCATION_ID = os.environ.get("GHL_LOCATION_ID")

BASE_URL = "https://services.leadconnectorhq.com"
API_VERSION = "2021-07-28"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Version": API_VERSION,
    "Authorization": f"Bearer {TOKEN}",
}

# Retry configuration
MAX_RETRIES = 5
BASE_SLEEP = 1.0


# ---------- Helpers ----------

def ensure_token():
    """Ensure the token is set in the environment."""
    if not TOKEN:
        raise RuntimeError("GHL_TOKEN is missing. Set it in your environment (.env).")
    if not LOCATION_ID:
        raise RuntimeError("GHL_LOCATION_ID is missing. Set it in your environment (.env).")


def _api_request(
    method: str,
    endpoint: str,
    params: Optional[Dict] = None,
    json_body: Optional[Dict] = None,
) -> Dict:
    """
    Make an API request with retry/backoff on 429 and 5xx errors.
    """
    ensure_token()
    
    url = f"{BASE_URL}{endpoint}"
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=HEADERS,
                params=params,
                json=json_body,
                timeout=60,
            )
            
            if response.status_code in (200, 201):
                return response.json()
            
            if response.status_code == 429:
                # Rate limited - honor Retry-After if present
                retry_after = response.headers.get("Retry-After")
                sleep_s = float(retry_after) if retry_after else BASE_SLEEP * (2 ** (attempt - 1))
                logger.warning(f"Rate limited. Retrying in {sleep_s}s...")
                time.sleep(min(sleep_s, 60))
                continue
            
            if 500 <= response.status_code < 600:
                # Server error - retry with backoff
                sleep_s = BASE_SLEEP * (2 ** (attempt - 1))
                logger.warning(f"Server error {response.status_code}. Retrying in {sleep_s}s...")
                time.sleep(sleep_s)
                continue
            
            # Client error - don't retry
            logger.error(f"{method} {url} failed: {response.status_code} {response.text}")
            raise RuntimeError(f"GHL API error {response.status_code}: {response.text}")
            
        except requests.RequestException as e:
            if attempt == MAX_RETRIES:
                raise RuntimeError(f"GHL API request failed after {MAX_RETRIES} retries: {e}")
            sleep_s = BASE_SLEEP * (2 ** (attempt - 1))
            logger.warning(f"Request error: {e}. Retrying in {sleep_s}s...")
            time.sleep(sleep_s)
    
    raise RuntimeError(f"GHL API request failed after {MAX_RETRIES} retries")


# ---------- Contact Operations ----------

def search_contacts(
    email: Optional[str] = None,
    phone: Optional[str] = None,
    limit: int = 20,
) -> List[Dict]:
    """
    Search for contacts by email or phone.
    
    Returns list of matching contacts.
    """
    params = {
        "locationId": LOCATION_ID,
        "limit": limit,
    }
    
    if email:
        params["email"] = email
    if phone:
        params["phone"] = phone
    
    result = _api_request("GET", "/contacts/", params=params)
    return result.get("contacts", [])


def find_contact_by_email_or_phone(
    email: Optional[str] = None,
    phone: Optional[str] = None,
) -> Optional[Dict]:
    """
    Find a single contact by email OR phone.
    
    First tries email, then phone if email doesn't match.
    Returns the first matching contact or None.
    """
    if email:
        contacts = search_contacts(email=email)
        if contacts:
            return contacts[0]
    
    if phone:
        contacts = search_contacts(phone=phone)
        if contacts:
            return contacts[0]
    
    return None


def get_contact(contact_id: str) -> Optional[Dict]:
    """Get a contact by ID."""
    try:
        result = _api_request("GET", f"/contacts/{contact_id}")
        return result.get("contact")
    except RuntimeError:
        return None


def create_contact(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    address: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    postal_code: Optional[str] = None,
    tags: Optional[List[str]] = None,
    custom_fields: Optional[List[Dict]] = None,
    source: str = "FranchisesGlobal Lead",
) -> Dict:
    """
    Create a new contact in GHL.
    
    Returns the created contact data.
    """
    body = {
        "locationId": LOCATION_ID,
        "source": source,
    }
    
    # Handle name - either first/last or full name
    if first_name:
        body["firstName"] = first_name
    if last_name:
        body["lastName"] = last_name
    if name and not (first_name or last_name):
        # Split full name into first/last
        parts = name.strip().split(" ", 1)
        body["firstName"] = parts[0]
        if len(parts) > 1:
            body["lastName"] = parts[1]
    
    if email:
        body["email"] = email
    if phone:
        body["phone"] = phone
    if address:
        body["address1"] = address
    if city:
        body["city"] = city
    if state:
        body["state"] = state
    if postal_code:
        body["postalCode"] = postal_code
    if tags:
        body["tags"] = tags
    if custom_fields:
        body["customFields"] = custom_fields
    
    result = _api_request("POST", "/contacts/", json_body=body)
    return result.get("contact", result)


def update_contact(
    contact_id: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    address: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    postal_code: Optional[str] = None,
    tags: Optional[List[str]] = None,
    custom_fields: Optional[List[Dict]] = None,
) -> Dict:
    """
    Update an existing contact.
    
    Only provided fields will be updated.
    """
    body = {}
    
    if first_name is not None:
        body["firstName"] = first_name
    if last_name is not None:
        body["lastName"] = last_name
    if email is not None:
        body["email"] = email
    if phone is not None:
        body["phone"] = phone
    if address is not None:
        body["address1"] = address
    if city is not None:
        body["city"] = city
    if state is not None:
        body["state"] = state
    if postal_code is not None:
        body["postalCode"] = postal_code
    if tags is not None:
        body["tags"] = tags
    if custom_fields is not None:
        body["customFields"] = custom_fields
    
    result = _api_request("PUT", f"/contacts/{contact_id}", json_body=body)
    return result.get("contact", result)


# ---------- Custom Field Operations ----------

# Cache for custom field IDs to avoid repeated API calls
_custom_field_cache: Dict[str, str] = {}  # name -> id


def list_custom_fields(model: str = "contact") -> List[Dict]:
    """
    List all custom fields for a given model (contact or opportunity).
    
    Returns list of custom field objects with id, name, dataType, etc.
    """
    params = {"model": model}
    result = _api_request("GET", f"/locations/{LOCATION_ID}/customFields", params=params)
    return result.get("customFields", [])


def create_custom_field(
    name: str,
    data_type: str,
    model: str = "contact",
) -> Dict:
    """
    Create a new custom field.
    
    Args:
        name: Display name of the custom field (e.g., "FG Liquidity")
        data_type: Field type - SINGLE_LINE_TEXT, MULTI_LINE_TEXT, MONETARY, NUMBER, etc.
        model: Object type - "contact" or "opportunity"
    
    Returns the created custom field object.
    """
    body = {
        "name": name,
        "dataType": data_type,
        "model": model,
    }
    
    result = _api_request("POST", f"/locations/{LOCATION_ID}/customFields", json_body=body)
    return result.get("customField", result)


def get_or_create_custom_field(
    name: str,
    data_type: str,
    model: str = "contact",
) -> str:
    """
    Get custom field ID by name, creating it if it doesn't exist.
    
    Uses caching to avoid repeated API calls.
    
    Returns the custom field ID.
    """
    cache_key = f"{model}:{name}"
    
    # Check cache first
    if cache_key in _custom_field_cache:
        return _custom_field_cache[cache_key]
    
    # List existing fields and look for match
    fields = list_custom_fields(model=model)
    for field in fields:
        if field.get("name") == name:
            field_id = field.get("id")
            _custom_field_cache[cache_key] = field_id
            return field_id
    
    # Create new field
    new_field = create_custom_field(name=name, data_type=data_type, model=model)
    field_id = new_field.get("id")
    _custom_field_cache[cache_key] = field_id
    logger.info(f"Created custom field '{name}' ({data_type}): {field_id}")
    return field_id


def clear_custom_field_cache():
    """Clear the custom field cache (useful for testing)."""
    global _custom_field_cache
    _custom_field_cache = {}


# ---------- Pipeline Operations ----------

def list_pipelines() -> List[Dict]:
    """List all pipelines in the location."""
    result = _api_request("GET", "/opportunities/pipelines", params={"locationId": LOCATION_ID})
    return result.get("pipelines", [])


def get_pipeline(pipeline_id: str) -> Optional[Dict]:
    """Get a pipeline by ID."""
    try:
        result = _api_request("GET", f"/opportunities/pipelines/{pipeline_id}")
        return result.get("pipeline")
    except RuntimeError:
        return None


def create_pipeline(
    name: str,
    stages: List[Dict[str, str]],
) -> Dict:
    """
    Create a new pipeline with stages.
    
    stages format: [{"name": "Stage Name"}, ...]
    """
    body = {
        "locationId": LOCATION_ID,
        "name": name,
        "stages": stages,
    }
    
    result = _api_request("POST", "/opportunities/pipelines", json_body=body)
    return result.get("pipeline", result)


def get_or_create_lead_nurturing_pipeline() -> Dict:
    """
    Get the existing "Lead Nurturing" pipeline from GHL.
    
    Stages in Lead Nurturing pipeline:
    - New Lead
    - Initial SMS Sent
    - SMS Engaged - Scheduling
    - Deeper Dive Scheduled
    - Needs Manual Follow-up
    - Qualified - Post Deeper Dive
    - Franchise(s) Presented
    - Funding Intro Made
    - Franchisor Intro Made
    - Closed - Won
    - Disqualified
    - Nurturing - Long Term
    
    Returns the pipeline with stages (including stage IDs).
    Raises RuntimeError if pipeline not found (must be created manually in GHL).
    """
    pipelines = list_pipelines()
    for pipeline in pipelines:
        if pipeline.get("name") == "Lead Nurturing":
            logger.info(f"Found 'Lead Nurturing' pipeline: {pipeline.get('id')}")
            return pipeline
    
    raise RuntimeError(
        "Lead Nurturing pipeline not found in GHL. "
        "Please create it manually in GoHighLevel with the required stages."
    )


# Keep alias for backwards compatibility
def get_or_create_franchise_leads_pipeline() -> Dict:
    """Deprecated: Use get_or_create_lead_nurturing_pipeline instead."""
    return get_or_create_lead_nurturing_pipeline()


# ---------- Opportunity Operations ----------

def list_opportunities(
    pipeline_id: Optional[str] = None,
    contact_id: Optional[str] = None,
    limit: int = 20,
) -> List[Dict]:
    """List opportunities with optional filters."""
    params = {
        "locationId": LOCATION_ID,
        "limit": limit,
    }
    
    if pipeline_id:
        params["pipelineId"] = pipeline_id
    if contact_id:
        params["contactId"] = contact_id
    
    result = _api_request("GET", "/opportunities/search", params=params)
    return result.get("opportunities", [])


def get_opportunity(opportunity_id: str) -> Optional[Dict]:
    """Get an opportunity by ID."""
    try:
        result = _api_request("GET", f"/opportunities/{opportunity_id}")
        return result.get("opportunity")
    except RuntimeError:
        return None


def create_opportunity(
    contact_id: str,
    pipeline_id: str,
    stage_id: str,
    name: str,
    monetary_value: Optional[float] = None,
    status: str = "open",
) -> Dict:
    """
    Create a new opportunity.
    
    status: "open", "won", "lost", "abandoned"
    """
    body = {
        "locationId": LOCATION_ID,
        "contactId": contact_id,
        "pipelineId": pipeline_id,
        "pipelineStageId": stage_id,
        "name": name,
        "status": status,
    }
    
    if monetary_value is not None:
        body["monetaryValue"] = monetary_value
    
    result = _api_request("POST", "/opportunities/", json_body=body)
    return result.get("opportunity", result)


def update_opportunity(
    opportunity_id: str,
    stage_id: Optional[str] = None,
    name: Optional[str] = None,
    monetary_value: Optional[float] = None,
    status: Optional[str] = None,
) -> Dict:
    """
    Update an existing opportunity.
    
    Only provided fields will be updated.
    """
    body = {}
    
    if stage_id is not None:
        body["pipelineStageId"] = stage_id
    if name is not None:
        body["name"] = name
    if monetary_value is not None:
        body["monetaryValue"] = monetary_value
    if status is not None:
        body["status"] = status
    
    result = _api_request("PUT", f"/opportunities/{opportunity_id}", json_body=body)
    return result.get("opportunity", result)


def find_opportunity_for_contact(contact_id: str, pipeline_id: str) -> Optional[Dict]:
    """Find an existing opportunity for a contact in a specific pipeline."""
    opportunities = list_opportunities(pipeline_id=pipeline_id, contact_id=contact_id)
    if opportunities:
        return opportunities[0]
    return None


# ---------- Workflow Status Mapping ----------

# Map lead workflow_status to GHL "Lead Nurturing" pipeline stage names
WORKFLOW_TO_STAGE = {
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

# Reverse mapping
STAGE_TO_WORKFLOW = {v: k for k, v in WORKFLOW_TO_STAGE.items()}


def get_stage_id_for_workflow_status(pipeline: Dict, workflow_status: str) -> Optional[str]:
    """
    Get the GHL stage ID for a given workflow status.
    
    Returns None if the workflow status is not found.
    """
    stage_name = WORKFLOW_TO_STAGE.get(workflow_status)
    if not stage_name:
        return None
    
    stages = pipeline.get("stages", [])
    for stage in stages:
        if stage.get("name") == stage_name:
            return stage.get("id")
    
    return None


def get_workflow_status_for_stage(pipeline: Dict, stage_id: str) -> Optional[str]:
    """
    Get the workflow status for a given GHL stage ID.
    
    Returns None if the stage is not found or doesn't map to a workflow status.
    """
    stages = pipeline.get("stages", [])
    for stage in stages:
        if stage.get("id") == stage_id:
            stage_name = stage.get("name")
            return STAGE_TO_WORKFLOW.get(stage_name)
    
    return None

