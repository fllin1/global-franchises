#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to check if territory checks are being captured during scraping.

This script:
1. Scrapes just 1-2 franchise pages
2. Saves the HTML fragments that would normally be saved to storage
3. Compares with full page HTML to detect missing territory checks
4. Checks for "Show more" buttons or hidden content
"""

from pathlib import Path
from bs4 import BeautifulSoup

from src.data.franserve.scrapper import (
    ScrapeConfig,
    session_login,
    get_page_franchise_urls,
    get_franchise_data,
)


def test_scrape_limited():
    """Scrape just 1-2 pages and inspect the HTML for territory checks."""
    
    print("=" * 80)
    print("Testing Scraper Territory Checks Capture")
    print("=" * 80)
    
    # Login
    print("\n[1/4] Logging in to FranServe...")
    session = session_login(
        ScrapeConfig.LOGIN_ACTION, 
        ScrapeConfig.USERNAME, 
        ScrapeConfig.PASSWORD
    )
    print("✓ Login successful")
    
    # Get URLs from just the first catalogue page (offset=0)
    print("\n[2/4] Fetching franchise URLs from first catalogue page...")
    franchise_urls = get_page_franchise_urls(
        session, 
        ScrapeConfig.BASE_URL, 
        f"{ScrapeConfig.CATALOGUE_BASE_URL}&offset=0"
    )
    
    # Limit to just first 2 franchises for testing
    test_urls = franchise_urls[:2]
    
    print(f"✓ Found {len(franchise_urls)} franchises on first page")
    print(f"  Testing with first {len(test_urls)} franchises:")
    for i, url in enumerate(test_urls, 1):
        print(f"    {i}. {url}")
    
    # Create test output directory
    test_dir = Path("test_scrape_output")
    test_dir.mkdir(exist_ok=True)
    print(f"\n[3/4] Saving test output to: {test_dir}")
    
    results = []
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n{'='*80}")
        print(f"[{i}/{len(test_urls)}] Processing: {url}")
        print(f"{'='*80}")
        
        # Get the HTML fragment that gets saved (what scrapper.py returns)
        print("\n  → Fetching HTML fragment (what gets saved to storage)...")
        try:
            data = get_franchise_data(session, url)
            html_fragment = data.prettify(formatter="html")
            
            # Save fragment for inspection
            file_name = url.split("/")[-1].split("?")[0] + ".html"
            fragment_path = test_dir / f"{file_name}.fragment.html"
            with open(fragment_path, "w", encoding="utf-8") as f:
                f.write(html_fragment)
            print(f"  ✓ Saved fragment to: {fragment_path}")
        except Exception as e:
            print(f"  ✗ Error fetching fragment: {e}")
            continue
        
        # Parse fragment and check for territory checks
        print("\n  → Analyzing fragment for territory checks...")
        fragment_soup = BeautifulSoup(html_fragment, "html.parser")
        fragment_tchecks = fragment_soup.find("div", id="tchecks")
        
        fragment_checks = []
        if fragment_tchecks:
            fragment_checks = [li.get_text(strip=True) for li in fragment_tchecks.find_all("li")]
            print(f"  ✓ Found territory checks div with {len(fragment_checks)} items")
            if fragment_checks:
                print(f"  Sample checks:")
                for j, check in enumerate(fragment_checks[:3], 1):
                    print(f"    {j}. {check[:80]}...")
        else:
            print(f"  ✗ No territory checks div found in fragment!")
        
        # Check for "Show more" button or hidden content in fragment
        show_more_in_fragment = fragment_soup.find(
            string=lambda text: text and "show more" in text.lower()
        ) or fragment_soup.find("button", string=lambda text: text and "show" in text.lower() if text else False)
        
        if show_more_in_fragment:
            print(f"  ⚠️  Found 'Show more' button/text in fragment")
        
        # Now get the FULL page HTML for comparison
        print("\n  → Fetching full page HTML for comparison...")
        try:
            resp = session.get(url)
            full_html = resp.text
            full_soup = BeautifulSoup(full_html, "html.parser")
            
            # Save full page for inspection
            full_path = test_dir / f"{file_name}.full_page.html"
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(full_html)
            print(f"  ✓ Saved full page to: {full_path}")
        except Exception as e:
            print(f"  ✗ Error fetching full page: {e}")
            continue
        
        # Check full page for territory checks
        print("\n  → Analyzing full page for territory checks...")
        full_tchecks = full_soup.find("div", id="tchecks")
        
        full_checks = []
        if full_tchecks:
            full_checks = [li.get_text(strip=True) for li in full_tchecks.find_all("li")]
            print(f"  ✓ Full page has {len(full_checks)} territory checks")
            
            # Check for hidden/collapsed content
            hidden_items = full_tchecks.find_all("li", style=lambda x: x and "display:none" in x.lower())
            if hidden_items:
                print(f"  ⚠️  Found {len(hidden_items)} hidden list items (display:none)")
            
            # Check for "Show more" button
            show_more_btn = full_soup.find(
                string=lambda text: text and "show more" in text.lower()
            ) or full_soup.find("button", string=lambda text: text and "show" in text.lower() if text else False)
            
            if show_more_btn:
                print(f"  ⚠️  Found 'Show more' button/text in full page")
                # Try to find the button element
                btn = full_soup.find("button", string=lambda text: text and "show" in text.lower() if text else False)
                if btn:
                    print(f"      Button HTML: {str(btn)[:100]}...")
        else:
            print(f"  ✗ No territory checks div found in full page!")
        
        # Compare results
        print("\n  → Comparison Results:")
        print(f"    Fragment checks: {len(fragment_checks)}")
        print(f"    Full page checks: {len(full_checks)}")
        
        if len(fragment_checks) == len(full_checks):
            print(f"    ✓ Match! All checks captured")
        elif len(fragment_checks) < len(full_checks):
            missing = len(full_checks) - len(fragment_checks)
            print(f"    ⚠️  WARNING: Missing {missing} territory checks!")
            print(f"    Missing checks:")
            for j, check in enumerate(full_checks[len(fragment_checks):], 1):
                print(f"      {j}. {check[:80]}...")
        else:
            print(f"    ⚠️  Fragment has more checks than full page (unexpected)")
        
        # Store results
        results.append({
            "url": url,
            "fragment_checks_count": len(fragment_checks),
            "full_page_checks_count": len(full_checks),
            "missing_count": max(0, len(full_checks) - len(fragment_checks)),
            "has_show_more": bool(show_more_btn),
        })
    
    # Summary
    print(f"\n{'='*80}")
    print("[4/4] Test Summary")
    print(f"{'='*80}")
    
    total_missing = sum(r["missing_count"] for r in results)
    total_show_more = sum(1 for r in results if r["has_show_more"])
    
    for i, result in enumerate(results, 1):
        print(f"\nFranchise {i}:")
        print(f"  URL: {result['url']}")
        print(f"  Fragment checks: {result['fragment_checks_count']}")
        print(f"  Full page checks: {result['full_page_checks_count']}")
        print(f"  Missing: {result['missing_count']}")
        print(f"  Has 'Show more': {result['has_show_more']}")
    
    print(f"\n{'='*80}")
    print("Overall Results:")
    print(f"  Total missing checks: {total_missing}")
    print(f"  Pages with 'Show more': {total_show_more}/{len(results)}")
    
    if total_missing > 0:
        print(f"\n  ⚠️  ISSUE DETECTED: Territory checks are being missed!")
        print(f"     The scraper needs to handle 'Show more' button clicks.")
    else:
        print(f"\n  ✓ All territory checks captured successfully!")
    
    print(f"\n  Check HTML files in: {test_dir}")
    print(f"{'='*80}")


if __name__ == "__main__":
    test_scrape_limited()
























