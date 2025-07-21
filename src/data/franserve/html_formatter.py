# -*- coding: utf-8 -*-
"""
This module contains the functions to parse the HTML of a FranServe
franchise page and extract the data.
"""

import json
import re

from bs4 import BeautifulSoup
from tqdm import tqdm

from src.config import EXTERNAL_DATA_DIR, RAW_DATA_DIR


def slugify(text: str) -> str:
    """Converts a string into a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[\s/()]+", "_", text)
    text = re.sub(r"[^a-z0-9_]", "", text)
    text = text.strip("_")
    return text


def parse_franchise_html(franchise_html_tag: BeautifulSoup) -> dict:
    """
    Parses the BeautifulSoup Tag of a FranServe franchise page and extracts the data.
    This version is updated to be more robust against HTML variations.

    Args:
        franchise_html_tag: A BeautifulSoup Tag object containing the franchise details.

    Returns:
        A dictionary containing the extracted franchise and contact information.
    """
    soup = franchise_html_tag

    def get_text_or_none(element: BeautifulSoup) -> str:
        return element.get_text(strip=True) if element else None

    def clean_financial_value(text: str) -> int:
        if not text:
            return None
        cleaned_text = re.sub(r"[$,]", "", text)
        try:
            return int(cleaned_text)
        except (ValueError, TypeError):
            return None

    # --- Franchise Information ---
    franchise_data = {}

    franchise_name_tag = soup.find("b").find("font", size="+1")
    franchise_data["franchise_name"] = get_text_or_none(franchise_name_tag)

    fran_id_tag = soup.find("input", {"name": "ZorID"})
    franchise_data["source_id"] = (
        int(fran_id_tag["value"]) if fran_id_tag and fran_id_tag.get("value") else None
    )
    franchise_data["source_url"] = (
        f"https://franservesupport.com/franchisedetails.asp?FranID={franchise_data['source_id']}&ClientID="
        if franchise_data.get("source_id")
        else None
    )

    # Using more robust find methods instead of CSS selectors with non-standard pseudo-classes

    def get_successive_a_siblings(start_tag):
        siblings = []
        next_tag = start_tag.find_next_sibling()
        while next_tag and next_tag.name == "a":
            siblings.append(next_tag)
            next_tag = next_tag.find_next_sibling()
        return siblings

    # --- CATEGORY ---
    category_header = soup.find(
        lambda tag: tag.name == "b" and "Category:" in tag.get_text(strip=True)
    )
    if category_header:
        category_links = get_successive_a_siblings(category_header)
        franchise_data["primary_category"] = (
            json.dumps([get_text_or_none(link) for link in category_links])
            if category_links
            else None
        )
    else:
        franchise_data["primary_category"] = None

    # --- SUBCATEGORY ---
    subcategory_header = soup.find(
        lambda tag: tag.name == "b" and "Subcategory:" in tag.get_text(strip=True)
    )
    if subcategory_header:
        sub_category_links = get_successive_a_siblings(subcategory_header)
        franchise_data["sub_categories"] = (
            json.dumps([get_text_or_none(link) for link in sub_category_links])
            if sub_category_links
            else None
        )
    else:
        franchise_data["sub_categories"] = None

    left_col_div = soup.select_one('div.col-left > div[style*="border-right"]')
    left_col_text = left_col_div.get_text(separator="\n", strip=True) if left_col_div else ""

    corporate_address_match = re.search(
        r"Corporate Office:\s*(.*?)(?=\s*Contact:)", left_col_text, re.DOTALL
    )
    franchise_data["corporate_address"] = (
        corporate_address_match.group(1).replace("\n", " ").strip()
        if corporate_address_match
        else None
    )

    website_tag = soup.find("a", href=re.compile(r"www\..*"))
    franchise_data["website_url"] = website_tag["href"] if website_tag else None

    right_col_top_div = soup.select_one("div.col-left > div:nth-of-type(2)")
    if right_col_top_div:
        right_col_top_text = right_col_top_div.get_text(separator="\n", strip=True)
        fee_match = re.search(r"Franchise Fee:\s*([$\d,]+)", right_col_top_text)
        franchise_data["franchise_fee_usd"] = (
            clean_financial_value(fee_match.group(1)) if fee_match else None
        )
        cash_match = re.search(r"Cash Investment:\s*([$\d,]+)", right_col_top_text)
        franchise_data["required_cash_investment_usd"] = (
            clean_financial_value(cash_match.group(1)) if cash_match else None
        )
        investment_match = re.search(
            r"Total Investment:\s*([$\d,]+)\s*-\s*([$\d,]+)", right_col_top_text
        )
        if investment_match:
            franchise_data["total_investment_min_usd"] = clean_financial_value(
                investment_match.group(1)
            )
            franchise_data["total_investment_max_usd"] = clean_financial_value(
                investment_match.group(2)
            )
        else:
            franchise_data["total_investment_min_usd"] = None
            franchise_data["total_investment_max_usd"] = None
        networth_match = re.search(r"NetWorth:\s*([$\d,]+)", right_col_top_text)
        franchise_data["required_net_worth_usd"] = (
            clean_financial_value(networth_match.group(1)) if networth_match else None
        )
        royalty_match = re.search(r"Royalties:\s*(.+)", right_col_top_text)
        franchise_data["royalty_details_text"] = (
            royalty_match.group(1).strip() if royalty_match else None
        )
        sba_match = re.search(r"SBA approved:\s*(.*)", right_col_top_text)
        franchise_data["sba_approved"] = (
            "Yes" in sba_match.group(1) if sba_match and sba_match.group(1) else False
        )
        vetfran_match = re.search(r"VetFran:\s*(.*)", right_col_top_text)
        franchise_data["vetfran_member"] = (
            "Yes" in vetfran_match.group(1) if vetfran_match and vetfran_match.group(1) else False
        )
        master_match = re.search(
            r"Master Franchise / Area Developer Opportunity:\s*(.*)", right_col_top_text
        )
        franchise_data["master_franchise_opportunity"] = (
            "Yes" in master_match.group(1) if master_match and master_match.group(1) else False
        )
        founded_match = re.search(r"Founded:\s*(\d{4})", right_col_top_text)
        franchise_data["founded_year"] = int(founded_match.group(1)) if founded_match else None
        franchised_match = re.search(r"Franchised:\s*(\d{4})", right_col_top_text)
        franchise_data["franchised_year"] = (
            int(franchised_match.group(1)) if franchised_match else None
        )

    additional_details_heading = soup.find("h2", string="Additional Details")
    description_paragraphs = []
    if additional_details_heading:
        for sibling in additional_details_heading.find_next_siblings():
            if sibling.name == "table":
                break
            # Use get_text() on the sibling <p> tag. This captures all text within it,
            # even from nested tags, solving the missing description issue.
            if sibling.name == "p":
                text = sibling.get_text(separator=" ", strip=True)
                if text:
                    description_paragraphs.append(text)
    franchise_data["description_text"] = "\n".join(description_paragraphs)

    # Using re.compile for more robust searching
    why_franchise_header = soup.find(["strong", "b"], string=re.compile(r"WHY .*"))
    if why_franchise_header:
        why_franchise_list = why_franchise_header.find_parent("p").find_next_sibling("ul")
        franchise_data["why_franchise_summary"] = (
            json.dumps([get_text_or_none(li) for li in why_franchise_list.find_all("li")])
            if why_franchise_list
            else None
        )
    else:
        franchise_data["why_franchise_summary"] = None

    ideal_candidate_header = soup.find(["strong", "b"], string=re.compile(r"IDEAL FRANCHISEE"))
    if ideal_candidate_header:
        ideal_candidate_list = ideal_candidate_header.find_parent("p").find_next_sibling("ul")
        franchise_data["ideal_candidate_profile_text"] = (
            json.dumps([get_text_or_none(li) for li in ideal_candidate_list.find_all("li")])
            if ideal_candidate_list
            else None
        )
    else:
        franchise_data["ideal_candidate_profile_text"] = None

    background_data = {}
    background_section_text = ""
    # Find the header tag (b or strong) instead of a <p> with a direct string.
    background_header = soup.find(
        lambda tag: tag.name in ["b", "strong"] and tag.get_text(strip=True) == "BACKGROUND"
    )
    if background_header:
        # Start from the container of the header (a <p> tag)
        current_element = background_header.find_parent("p")
        # Iterate through the FOLLOWING sibling elements
        while current_element := current_element.find_next_sibling():
            # Stop if we hit the next major section to avoid grabbing too much.
            if current_element.find(["b", "strong"], string=re.compile(r"FINANCIAL DETAILS")):
                break

            # Aggregate the text from all relevant paragraphs
            if current_element.name == "p":
                background_section_text += current_element.get_text(separator="\n") + "\n"

        # Now parse the aggregated text
        for line in background_section_text.split("\n"):
            if ":" in line:
                parts = [p.strip() for p in line.split(":", 1)]
                if len(parts) == 2 and parts[0]:
                    key = slugify(parts[0])
                    background_data[key] = parts[1]

    # This logic remains the same but now has data to work with
    franchise_data["is_home_based"] = background_data.get("home_based", "No").lower() == "yes"
    franchise_data["allows_semi_absentee"] = (
        background_data.get("semiabsentee_ownership_available", "No").lower() == "yes"
    )
    franchise_data["allows_absentee"] = (
        background_data.get("absentee_ownership_available", "No").lower() == "yes"
    )
    franchise_data["e2_visa_friendly"] = (
        background_data.get("e2_visa_friendly", "No").lower() == "yes"
    )
    franchise_data["franchises_data"] = json.dumps(background_data) if background_data else None

    territory_checks = []
    tchecks_div = soup.find("div", id="tchecks")
    if tchecks_div:
        for li in tchecks_div.find_all("li"):
            # Improved parsing for territory checks to handle complex strings
            text_parts = [part.strip() for part in get_text_or_none(li).split(" - ", 2)]
            if len(text_parts) >= 2:  # Must have at least timestamp and something else
                check_data = {"check_timestamp": text_parts[0]}
                if len(text_parts) == 2:
                    check_data["location"] = text_parts[1]
                    check_data["status"] = "Unknown"
                else:  # len == 3
                    check_data["location"] = text_parts[1]
                    check_data["status"] = text_parts[2]
                territory_checks.append(check_data)

    franchise_data["recent_territory_checks"] = (
        json.dumps(territory_checks) if territory_checks else None
    )

    # Use the reliably fetched background_section_text
    unavailable_states_match = re.search(
        r"NOT available:\s*(.+)", background_section_text, re.MULTILINE
    )
    if unavailable_states_match:
        states_text = unavailable_states_match.group(1).strip()
        unavailable_states = [state.strip() for state in states_text.split(", ")]
        franchise_data["unavailable_states"] = json.dumps(unavailable_states)
    else:
        franchise_data["unavailable_states"] = None

    last_updated_tag = soup.find("i", string=re.compile(r"Last updated:"))
    franchise_data["last_updated_from_source"] = (
        last_updated_tag.get_text(strip=True).replace("Last updated:", "").strip()
        if last_updated_tag
        else None
    )

    # --- Contacts Information ---
    contacts_data = []

    if left_col_div:
        contact_tag = left_col_div.find(
            lambda tag: tag.name == "b" and "Contact:" in tag.get_text(strip=True)
        )
        if contact_tag:
            name_text = contact_tag.next_sibling
            phone_tag = contact_tag.find_next(
                lambda tag: tag.name == "b" and "Phone:" in tag.get_text(strip=True)
            )
            email_tag = contact_tag.find_next("a", href=lambda href: href and "mailto:" in href)
            contacts_data.append(
                {
                    "name": name_text.strip() if name_text else None,
                    "phone": phone_tag.next_sibling.strip()
                    if phone_tag and phone_tag.next_sibling
                    else None,
                    "email": get_text_or_none(email_tag),
                    "is_primary": True,
                }
            )

        alt_contact_tag = left_col_div.find(
            lambda tag: tag.name == "b" and "Alternative Contact:" in tag.get_text(strip=True)
        )
        if alt_contact_tag:
            name_text = alt_contact_tag.next_sibling
            phone_tag = alt_contact_tag.find_next(
                lambda tag: tag.name == "b" and "Phone:" in tag.get_text(strip=True)
            )
            email_tag = alt_contact_tag.find_next_sibling(
                "a", href=lambda href: href and "mailto:" in href
            )
            contacts_data.append(
                {
                    "name": name_text.strip() if name_text else None,
                    "phone": phone_tag.next_sibling.strip()
                    if phone_tag and phone_tag.next_sibling
                    else None,
                    "email": get_text_or_none(email_tag),
                    "is_primary": False,
                }
            )

    return {"franchise_data": franchise_data, "contacts_data": contacts_data}


def main():
    """
    Main function to run the scrapper.
    """
    html_data = list(EXTERNAL_DATA_DIR.glob("*.html"))
    for file in tqdm(html_data, total=len(html_data), desc="Parsing HTML data"):
        with open(file, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        data = parse_franchise_html(soup)
        file_name = file.name.replace(".html", ".json")
        with open(RAW_DATA_DIR / file_name, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)


if __name__ == "__main__":
    main()
