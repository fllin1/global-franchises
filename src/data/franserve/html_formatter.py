# -*- coding: utf-8 -*-
"""
This module contains the functions to parse the HTML of a FranServe
franchise page and extract the data.
"""

import json
import re
from typing import Any, Dict

from bs4 import BeautifulSoup, Tag

# --- Helper Functions ---


def slugify(text: str) -> str:
    """Converts a string into a URL-friendly slug."""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[\s/()]+", "_", text)
    text = re.sub(r"[^a-z0-9_]", "", text)
    text = text.strip("_")
    return text


def get_text_or_none(element: Tag) -> str | None:
    """Extracts stripped text from a BeautifulSoup Tag, returning None if the tag is None."""
    return element.get_text(strip=True) if element else None


def clean_financial_value(text: str) -> int | None:
    """Removes currency symbols and commas, then converts to an integer."""
    if not text:
        return None
    cleaned_text = re.sub(r"[$,]", "", text)
    try:
        return int(float(cleaned_text))
    except (ValueError, TypeError):
        return None


# --- Step 1: Parsing HTML to a Structured Dictionary ---


def parse_key_value_lines(text_block: str) -> Dict[str, str]:
    """
    Parses a multi-line block of text where each line is expected to be a
    'Key: Value' pair. This is more robust against formatting variations.

    Args:
        text_block: A single string containing key-value pairs separated by newlines.

    Returns:
        A dictionary of the parsed key-value pairs.
    """
    data = {}
    for line in text_block.split("\n"):
        line = line.strip()
        if ":" in line:
            # Split only on the first colon to handle values that contain colons
            parts = [p.strip() for p in line.split(":", 1)]
            if len(parts) == 2 and parts[0]:  # Ensure there's a key
                key = slugify(parts[0])
                data[key] = parts[1]
    return data


def parse_html_to_structured_dict(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Parses the BeautifulSoup object of a franchise page into an organized,
    nested dictionary that reflects the semantic sections of the page.
    This version is enhanced to correctly separate adjacent text elements
    and parse all sections of the page.
    """
    structured_data = {
        "franchise_name": None,
        "source_id": None,
        "page_layout": {},
        "sections": {},
    }

    # --- Basic Information ---
    franchise_name_tag = soup.find("b")
    if franchise_name_tag and franchise_name_tag.find("font", size="+1"):
        structured_data["franchise_name"] = get_text_or_none(franchise_name_tag.font)

    fran_id_tag = soup.find("input", {"name": "ZorID"})
    if fran_id_tag and fran_id_tag.get("value"):
        structured_data["source_id"] = int(fran_id_tag["value"])

    # --- NEW: Parse Top Columns Layout ---
    page_layout = {}
    # Left column with contact info and website
    left_col_div = soup.select_one('div.col-left > div[style*="border-right"]')
    if left_col_div:
        # Extract text, ensuring <br> tags create newlines
        left_col_text = left_col_div.get_text(separator="\n", strip=True)
        page_layout["left_col"] = parse_key_value_lines(left_col_text)
        # Extract website URL separately as it's in an <a> tag
        website_tag = left_col_div.find("a", href=re.compile(r"www\..*"))
        if website_tag:
            page_layout["left_col"]["website"] = website_tag["href"]

    # Middle column with top-level financials and booleans
    middle_col_div = soup.select_one('div.col-left > div:not([style*="border-right"])')
    if middle_col_div:
        middle_col_text = middle_col_div.get_text(separator="\n", strip=True)
        page_layout["middle_col"] = parse_key_value_lines(middle_col_text)

    # Right column with territory checks
    tchecks_div = soup.find("div", id="tchecks")
    if tchecks_div:
        checks = [li.get_text(strip=True) for li in tchecks_div.find_all("li")]
        page_layout["right_col"] = {"recent_territory_checks": checks}

    structured_data["page_layout"] = page_layout

    # --- Main Content Sections (Existing Logic) ---
    main_content_area = soup.find("div", class_="col-left") or soup
    section_keywords = {
        "introduction": re.compile(r"\bAdditional Details\b", re.IGNORECASE),
        "why_franchise": re.compile(r"^WHY .*", re.IGNORECASE),
        "ideal_franchisee": re.compile(r"IDEAL FRANCHISEE", re.IGNORECASE),
        "available_markets": re.compile(r"AVAILABLE MARKETS", re.IGNORECASE),
        "background": re.compile(r"BACKGROUND", re.IGNORECASE),
        "financial_details": re.compile(r"FINANCIAL DETAILS", re.IGNORECASE),
        "support_and_training": re.compile(r"SUPPORT & TRAINING", re.IGNORECASE),
    }

    # This part of the logic remains the same as before
    intro_header = main_content_area.find("h2", string=section_keywords["introduction"])
    intro_paragraphs = []
    if intro_header:
        for sibling in intro_header.find_next_siblings():
            if sibling.name in ["table", "h2"] or (sibling.find and sibling.find(["b", "strong"])):
                break
            if sibling.name == "p":
                text = sibling.get_text(strip=True)
                if text:
                    intro_paragraphs.append(text)
    structured_data["sections"]["introduction"] = "\n".join(intro_paragraphs)

    for section_name, pattern in section_keywords.items():
        header_tag = main_content_area.find(
            lambda tag: tag.name in ["strong", "b"] and pattern.search(get_text_or_none(tag) or "")
        )
        if not header_tag:
            continue
        parent_container = header_tag.find_parent(["p", "td"])
        if not parent_container:
            continue

        content_elements = []
        next_elem = parent_container.find_next_sibling()
        while next_elem and (not next_elem.find or not next_elem.find(["b", "strong", "h2"])):
            content_elements.append(next_elem)
            next_elem = next_elem.find_next_sibling()

        if section_name in ["why_franchise", "ideal_franchisee"]:
            for elem in [parent_container] + content_elements:
                ul = elem.find("ul")
                if ul:
                    structured_data["sections"][section_name] = [
                        li.get_text(strip=True) for li in ul.find_all("li")
                    ]
                    break
        elif section_name in [
            "available_markets",
            "background",
            "financial_details",
            "support_and_training",
        ]:
            all_section_tags = [parent_container] + content_elements
            section_text_parts = [
                tag.get_text(separator="\n", strip=True) for tag in all_section_tags
            ]
            full_text_block = "\n".join(section_text_parts)
            structured_data["sections"][section_name] = parse_key_value_lines(full_text_block)

    # --- Last Updated ---
    last_updated_tag = soup.find("i", string=re.compile(r"Last updated:"))
    if last_updated_tag:
        structured_data["last_updated_from_source"] = (
            get_text_or_none(last_updated_tag).replace("Last updated:", "").strip()
        )

    return structured_data


# The rest of the file (`format_structured_dict_for_db`, `process_franchise_html`, `main`) remains unchanged.

# --- Step 2: Formatting the Structured Dictionary for the Database ---


def format_structured_dict_for_db(structured_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Takes the structured, nested dictionary and formats it into the flat
    structure required by the 'Franchises' and 'Contacts' database tables.

    Args:
        structured_data: The nested dictionary from `parse_html_to_structured_dict`.

    Returns:
        A dictionary containing 'franchise_data' and 'contacts_data' lists.
    """
    franchise_data = {}
    contacts_data = []

    # --- Basic Info ---
    franchise_data["franchise_name"] = structured_data.get("franchise_name")
    source_id = structured_data.get("source_id")
    franchise_data["source_id"] = source_id
    franchise_data["source_url"] = (
        f"https://franservesupport.com/franchisedetails.asp?FranID={source_id}&ClientID="
        if source_id
        else None
    )

    # --- Map Data from Top Layout Columns ---
    layout = structured_data.get("page_layout", {})
    left_col = layout.get("left_col", {})
    middle_col = layout.get("middle_col", {})
    right_col = layout.get("right_col", {})

    # Extract Corporate Address
    # It might be split across multiple lines, so we reassemble it.
    address_lines = []
    if "corporate_office" in left_col:
        # Find the line with the key and collect subsequent lines without a key
        lines = left_col.get("_raw_text", "").split("\n")  # Assuming _raw_text would be stored
        try:
            start_index = next(i for i, line in enumerate(lines) if "Corporate Office:" in line)
            address_lines.append(lines[start_index].split(":", 1)[1].strip())
            for line in lines[start_index + 1 :]:
                if ":" in line:
                    break
                address_lines.append(line.strip())
            franchise_data["corporate_address"] = " ".join(address_lines)
        except (StopIteration, IndexError):
            franchise_data["corporate_address"] = left_col.get("corporate_office")  # Fallback
    else:
        franchise_data["corporate_address"] = None

    franchise_data["website_url"] = left_col.get("website")

    # Extract boolean flags from middle column
    franchise_data["sba_approved"] = "yes" in middle_col.get("sba_approved", "no").lower()
    franchise_data["vetfran_member"] = "yes" in middle_col.get("vetfran", "no").lower()
    franchise_data["master_franchise_opportunity"] = (
        "yes" in middle_col.get("master_franchise_area_developer_opportunity", "no").lower()
    )

    # Extract Territory Checks
    checks = right_col.get("recent_territory_checks")
    franchise_data["recent_territory_checks"] = json.dumps(checks) if checks else None

    # Extract Contacts
    if "contact" in left_col:
        contacts_data.append(
            {
                "name": left_col.get("contact"),
                "phone": left_col.get("phone"),
                "email": left_col.get("email"),
                "is_primary": True,
            }
        )
    if "alternative_contact" in left_col:
        contacts_data.append(
            {
                "name": left_col.get("alternative_contact"),
                "phone": left_col.get("phone"),  # Note: HTML structure might reuse the 'phone' key
                "email": left_col.get(
                    "email"
                ),  # Same for email, may need refinement if HTML varies
                "is_primary": False,
            }
        )

    # --- Map Main Sections (Existing and New Logic) ---
    sections = structured_data.get("sections", {})
    financials = sections.get("financial_details", {}) or {}
    background = sections.get("background", {}) or {}
    markets = sections.get("available_markets", {}) or {}

    # Extract Unavailable States
    unavailable_text = markets.get("not_available")
    if unavailable_text and unavailable_text.lower() != "none":
        franchise_data["unavailable_states"] = json.dumps(
            [state.strip() for state in unavailable_text.split(",")]
        )
    else:
        franchise_data["unavailable_states"] = None

    # Map Financial Details
    fee_text = financials.get("franchise_fee") or middle_col.get("franchise_fee")
    investment_text = financials.get("total_investment_range") or middle_col.get(
        "total_investment"
    )

    # Use the first part of the franchise fee string for the value
    franchise_data["franchise_fee_usd"] = clean_financial_value(
        fee_text.split("-")[0] if fee_text else None
    )

    if investment_text and "-" in investment_text:
        min_inv, max_inv = (part.strip() for part in investment_text.split("-", 1))
        franchise_data["total_investment_min_usd"] = clean_financial_value(min_inv)
        franchise_data["total_investment_max_usd"] = clean_financial_value(max_inv)
    else:
        franchise_data["total_investment_min_usd"] = clean_financial_value(investment_text)
        franchise_data["total_investment_max_usd"] = clean_financial_value(investment_text)

    franchise_data["required_net_worth_usd"] = clean_financial_value(
        financials.get("net_worth_requirement") or middle_col.get("networth")
    )
    franchise_data["required_cash_investment_usd"] = clean_financial_value(
        middle_col.get("cash_investment")
    )
    franchise_data["royalty_details_text"] = financials.get("royalty") or middle_col.get(
        "royalties"
    )

    # Map Background & Other Details
    franchise_data["founded_year"] = clean_financial_value(
        background.get("year_founded") or middle_col.get("founded")
    )
    franchise_data["franchised_year"] = clean_financial_value(
        background.get("year_franchised") or middle_col.get("franchised")
    )

    franchise_data["is_home_based"] = "yes" in background.get("home_based", "no").lower()
    franchise_data["allows_semi_absentee"] = (
        "yes" in background.get("semiabsentee_ownership_available", "no").lower()
    )
    franchise_data["allows_absentee"] = (
        "yes" in background.get("absentee_ownership_available", "no").lower()
    )
    franchise_data["e2_visa_friendly"] = "yes" in background.get("e2_visa_friendly", "no").lower()

    # Serialize complex fields to JSON
    franchise_data["description_text"] = (
        json.dumps(sections.get("introduction")) if sections.get("introduction") else None
    )
    franchise_data["why_franchise_summary"] = (
        json.dumps(sections.get("why_franchise")) if sections.get("why_franchise") else None
    )
    franchise_data["ideal_candidate_profile_text"] = (
        json.dumps(sections.get("ideal_franchisee")) if sections.get("ideal_franchisee") else None
    )

    franchise_data["franchises_data"] = json.dumps(
        {
            "background": background,
            "available_markets": markets,
            "support_and_training": sections.get("support_and_training", {}),
            "financials_unmapped": financials,
        }
    )

    franchise_data["last_updated_from_source"] = structured_data.get("last_updated_from_source")

    return {"franchise_data": franchise_data, "contacts_data": contacts_data}


def process_franchise_html(franchise_html_content: str) -> Dict[str, Any]:
    """
    Process the HTML content of a franchise page and return a structured dictionary.
    """
    soup = BeautifulSoup(franchise_html_content, "html.parser")
    structured_data = parse_html_to_structured_dict(soup)
    final_data = format_structured_dict_for_db(structured_data)
    return final_data
