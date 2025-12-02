# -*- coding: utf-8 -*-
"""
Scraper for Family of Brands pages on FranServe.

Family of Brands are parent brand entities that contain multiple franchise brands.
For example, "Driven Brands" contains "1-800 Radiator & AC", "Maaco", "Meineke", etc.

This scraper:
- Scrapes the Family of Brands listing page to get all family brand URLs
- Scrapes individual family brand detail pages
- Extracts family brand information and representing franchise brands
- Stores data in the family_of_brands table and links franchises
"""

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup
import dotenv
import requests
from loguru import logger

from src.data.storage.storage_client import StorageClient
from src.data.franserve.scrapper import session_login, ScrapeConfig

dotenv.load_dotenv()


@dataclass
class FamilyBrandData:
    """Data structure for a family brand."""
    
    name: str
    source_id: int
    website_url: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    logo_url: Optional[str] = None
    last_updated_from_source: Optional[str] = None
    representing_brand_ids: List[int] = field(default_factory=list)
    representing_brand_names: List[str] = field(default_factory=list)


class FamilyBrandsConfig:
    """Configuration for the Family of Brands scraper."""
    
    BASE_URL = ScrapeConfig.BASE_URL
    FAMILY_BRANDS_LIST_URL = BASE_URL + "family-of-brands.asp"
    # The actual list is loaded via AJAX from this endpoint
    FAMILY_BRANDS_AJAX_URL = BASE_URL + "devco_list.asp"
    FAMILY_BRAND_DETAIL_URL = BASE_URL + "frandevcompany_details.asp?FranID="
    
    # Storage bucket path prefix for family brands HTML
    STORAGE_PREFIX = "family-brands"


def get_family_brands_list(session: requests.Session) -> List[Tuple[str, str, int]]:
    """
    Scrape the Family of Brands listing page to get all family brand URLs.
    
    The family brands list is loaded via AJAX from devco_list.asp endpoint.
    
    Args:
        session: Authenticated requests session
        
    Returns:
        List of tuples: (family_brand_name, url, source_id)
    """
    logger.info(f"Fetching family brands list from {FamilyBrandsConfig.FAMILY_BRANDS_AJAX_URL}")
    
    # The list is loaded via POST to devco_list.asp with empty filter
    # This returns all family brands
    resp = session.post(
        FamilyBrandsConfig.FAMILY_BRANDS_AJAX_URL,
        data={
            "devconame": "",  # Empty to get all
            "ClientID": "",
            "filter": "10"  # This appears to be a pagination/limit parameter
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )
    resp.raise_for_status()
    
    soup = BeautifulSoup(resp.text, "html.parser")
    
    family_brands = []
    
    # Find all links to family brand detail pages
    # Pattern: frandevcompany_details.asp?FranID=XXXX
    for link in soup.find_all("a", href=re.compile(r"frandevcompany_details\.asp\?FranID=\d+")):
        href = link.get("href", "")
        
        # Extract FranID from URL
        parsed = urlparse(href)
        params = parse_qs(parsed.query)
        fran_id = params.get("FranID", [None])[0]
        
        if fran_id:
            # Get the family brand name from the link text or image alt
            name = link.get_text(strip=True)
            if not name:
                img = link.find("img")
                if img:
                    name = img.get("alt", "").strip()
            
            if not name:
                name = f"Family Brand {fran_id}"
            
            full_url = FamilyBrandsConfig.BASE_URL + href if not href.startswith("http") else href
            family_brands.append((name, full_url, int(fran_id)))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_brands = []
    for brand in family_brands:
        if brand[2] not in seen:  # Check source_id
            seen.add(brand[2])
            unique_brands.append(brand)
    
    logger.info(f"Found {len(unique_brands)} unique family brands")
    return unique_brands


def scrape_family_brand_page(session: requests.Session, url: str) -> BeautifulSoup:
    """
    Scrape an individual family brand detail page.
    
    Args:
        session: Authenticated requests session
        url: URL of the family brand detail page
        
    Returns:
        BeautifulSoup object of the page content
    """
    logger.debug(f"Scraping family brand page: {url}")
    
    resp = session.get(url)
    resp.raise_for_status()
    
    soup = BeautifulSoup(resp.text, "html.parser")
    return soup


def parse_family_brand_html(soup: BeautifulSoup, source_id: int) -> FamilyBrandData:
    """
    Parse a family brand detail page HTML into structured data.
    
    Args:
        soup: BeautifulSoup object of the page
        source_id: The FranID from the URL
        
    Returns:
        FamilyBrandData object with extracted information
    """
    data = FamilyBrandData(
        name="",
        source_id=source_id
    )
    
    # Extract family brand name from page title or header
    # The name is typically in a bold font tag near the top
    title_tag = soup.find("title")
    if title_tag:
        title_text = title_tag.get_text(strip=True)
        # Remove " Franchise Details" suffix if present
        if "Franchise Details" in title_text:
            data.name = title_text.replace("Franchise Details", "").strip()
    
    # Try to find the name in the main content area
    if not data.name:
        # Look for bold text that might be the name
        for b_tag in soup.find_all("b"):
            font_tag = b_tag.find("font", size="+1")
            if font_tag:
                data.name = font_tag.get_text(strip=True)
                break
    
    # Extract contact information
    # Look for patterns like "Contact:", "Phone:", "Email:", "Website:"
    text_content = soup.get_text()
    
    # Website URL
    website_link = soup.find("a", href=re.compile(r"^https?://(?!franserve)"))
    if not website_link:
        website_link = soup.find("a", href=re.compile(r"^www\."))
    if website_link:
        href = website_link.get("href", "")
        if href and not "franserve" in href.lower():
            data.website_url = href if href.startswith("http") else f"http://{href}"
    
    # Contact name - look for "Contact:" label
    contact_match = re.search(r"Contact:\s*([A-Za-z\s]+?)(?:\s*Phone:|$)", text_content)
    if contact_match:
        data.contact_name = contact_match.group(1).strip()
    
    # Phone number
    phone_match = re.search(r"Phone:\s*([\d\-\(\)\s]+)", text_content)
    if phone_match:
        data.contact_phone = phone_match.group(1).strip()
    
    # Email - find mailto links
    email_link = soup.find("a", href=re.compile(r"^mailto:"))
    if email_link:
        email = email_link.get("href", "").replace("mailto:", "")
        data.contact_email = email
    
    # Logo URL
    # Look for logo images in the right column
    logo_patterns = [
        re.compile(r"images/logos/"),
        re.compile(r"logo", re.IGNORECASE)
    ]
    for pattern in logo_patterns:
        logo_img = soup.find("img", src=pattern)
        if logo_img:
            src = logo_img.get("src", "")
            if src:
                data.logo_url = FamilyBrandsConfig.BASE_URL + src if not src.startswith("http") else src
                break
    
    # Last updated date
    last_updated_tag = soup.find("i", string=re.compile(r"Last updated:"))
    if not last_updated_tag:
        last_updated_tag = soup.find(string=re.compile(r"Last updated:"))
    if last_updated_tag:
        date_text = str(last_updated_tag)
        date_match = re.search(r"Last updated:\s*(\d{1,2}/\d{1,2}/\d{4})", date_text)
        if date_match:
            data.last_updated_from_source = date_match.group(1)
    
    # Extract representing brands
    representing_brands = extract_representing_brands(soup)
    data.representing_brand_ids = [b[1] for b in representing_brands]
    data.representing_brand_names = [b[0] for b in representing_brands]
    
    logger.debug(f"Parsed family brand: {data.name} with {len(data.representing_brand_ids)} representing brands")
    
    return data


def extract_representing_brands(soup: BeautifulSoup) -> List[Tuple[str, int]]:
    """
    Extract the list of representing franchise brands from a family brand page.
    
    Args:
        soup: BeautifulSoup object of the family brand page
        
    Returns:
        List of tuples: (brand_name, fran_id)
    """
    brands = []
    
    # Look for "Representing Brands" section
    # The representing brands are typically links to franchisedetails.asp?FranID=XXXX
    
    # Find links to franchise detail pages
    for link in soup.find_all("a", href=re.compile(r"franchisedetails\.asp\?FranID=\d+")):
        href = link.get("href", "")
        
        # Extract FranID from URL
        parsed = urlparse(href)
        params = parse_qs(parsed.query)
        fran_id = params.get("FranID", [None])[0]
        
        if fran_id:
            # Get the brand name from link text
            name = link.get_text(strip=True)
            if name:
                brands.append((name, int(fran_id)))
    
    # Remove duplicates
    seen = set()
    unique_brands = []
    for brand in brands:
        if brand[1] not in seen:
            seen.add(brand[1])
            unique_brands.append(brand)
    
    return unique_brands


def upload_family_brand_html(
    soup: BeautifulSoup, 
    file_path: str, 
    storage_client: StorageClient
) -> str:
    """
    Upload family brand HTML data to Supabase Storage.
    
    Args:
        soup: BeautifulSoup object to upload
        file_path: The path within the bucket
        storage_client: The storage client instance
        
    Returns:
        The path of the uploaded file
    """
    html_content = soup.prettify(formatter="html")
    return storage_client.upload_html(html_content, file_path)


def save_family_brand_to_db(
    data: FamilyBrandData,
    supabase_client
) -> Optional[int]:
    """
    Insert or update a family brand in the database.
    
    Args:
        data: FamilyBrandData object with the family brand information
        supabase_client: Supabase client instance
        
    Returns:
        The database ID of the inserted/updated record, or None on failure
    """
    try:
        # Prepare the record
        record = {
            "name": data.name,
            "source_id": data.source_id,
            "website_url": data.website_url,
            "contact_name": data.contact_name,
            "contact_phone": data.contact_phone,
            "contact_email": data.contact_email,
            "logo_url": data.logo_url,
        }
        
        # Parse date if present
        if data.last_updated_from_source:
            try:
                from datetime import datetime
                parsed_date = datetime.strptime(data.last_updated_from_source, "%m/%d/%Y")
                record["last_updated_from_source"] = parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                logger.warning(f"Could not parse date: {data.last_updated_from_source}")
        
        # Upsert based on source_id
        result = supabase_client.table("family_of_brands").upsert(
            record,
            on_conflict="source_id"
        ).execute()
        
        if result.data:
            db_id = result.data[0].get("id")
            logger.info(f"Saved family brand '{data.name}' (source_id={data.source_id}) with db_id={db_id}")
            return db_id
        
        return None
        
    except Exception as e:
        logger.error(f"Error saving family brand {data.name}: {e}")
        return None


def link_franchises_to_family_brand(
    family_brand_db_id: int,
    representing_brand_source_ids: List[int],
    supabase_client
) -> int:
    """
    Update franchises to link them to their parent family brand.
    
    Args:
        family_brand_db_id: The database ID of the family brand
        representing_brand_source_ids: List of franchise source_ids (FranIDs)
        supabase_client: Supabase client instance
        
    Returns:
        Number of franchises updated
    """
    if not representing_brand_source_ids:
        return 0
    
    try:
        # Update franchises where source_id matches
        result = supabase_client.table("franchises").update({
            "parent_family_brand_id": family_brand_db_id
        }).in_("source_id", representing_brand_source_ids).execute()
        
        updated_count = len(result.data) if result.data else 0
        logger.info(f"Linked {updated_count} franchises to family brand (db_id={family_brand_db_id})")
        
        return updated_count
        
    except Exception as e:
        logger.error(f"Error linking franchises to family brand: {e}")
        return 0


def scrape_all_family_brands(
    session: requests.Session,
    storage_client: StorageClient,
    supabase_client,
    date_prefix: str
) -> Dict[str, int]:
    """
    Scrape all family brands and store them in the database.
    
    Args:
        session: Authenticated requests session
        storage_client: Storage client for HTML files
        supabase_client: Supabase client for database operations
        date_prefix: Date prefix for storage path (e.g., "2025-12-02")
        
    Returns:
        Dictionary with scraping statistics
    """
    stats = {
        "total_found": 0,
        "scraped_success": 0,
        "scraped_failed": 0,
        "saved_to_db": 0,
        "franchises_linked": 0
    }
    
    # Get list of all family brands
    family_brands = get_family_brands_list(session)
    stats["total_found"] = len(family_brands)
    
    logger.info(f"Starting to scrape {len(family_brands)} family brands...")
    
    for idx, (name, url, source_id) in enumerate(family_brands, 1):
        try:
            logger.info(f"Processing family brand {idx}/{len(family_brands)}: {name} (FranID={source_id})")
            
            # Scrape the page
            soup = scrape_family_brand_page(session, url)
            
            # Save HTML to storage
            file_path = f"{FamilyBrandsConfig.STORAGE_PREFIX}/{date_prefix}/FranID_{source_id}.html"
            upload_family_brand_html(soup, file_path, storage_client)
            
            # Parse the HTML
            data = parse_family_brand_html(soup, source_id)
            
            # If name wasn't found in HTML, use the name from the list
            if not data.name:
                data.name = name
            
            # Save to database
            db_id = save_family_brand_to_db(data, supabase_client)
            
            if db_id:
                stats["saved_to_db"] += 1
                
                # Link franchises to this family brand
                linked = link_franchises_to_family_brand(
                    db_id, 
                    data.representing_brand_ids, 
                    supabase_client
                )
                stats["franchises_linked"] += linked
            
            stats["scraped_success"] += 1
            
        except Exception as e:
            logger.error(f"Error processing family brand {name} (FranID={source_id}): {e}")
            stats["scraped_failed"] += 1
    
    logger.info(f"Family brands scraping complete: {stats}")
    return stats


# Convenience function to get an authenticated session
def get_authenticated_session() -> requests.Session:
    """
    Get an authenticated session for scraping.
    
    Returns:
        Authenticated requests.Session object
    """
    return session_login(
        ScrapeConfig.LOGIN_ACTION,
        ScrapeConfig.USERNAME,
        ScrapeConfig.PASSWORD
    )

