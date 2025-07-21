# -*- coding: utf-8 -*-
"""
Scrapper for the FranServe website.

The website is protected by a login.

The scrapper will:
- Login to the website
- Get the list of franchise URLs
- Get the data for each franchise
- Save the data to a JSON file
"""

import os
from typing import List
from urllib.parse import quote

from bs4 import BeautifulSoup
import dotenv
import requests
from tqdm import tqdm

from src.config import EXTERNAL_DATA_DIR

dotenv.load_dotenv()

USERNAME = os.getenv("FRANSERVE_EMAIL")
PASSWORD = os.getenv("FRANSERVE_PASSWORD")

LOGIN_URL = "https://franservesupport.com/Default.asp"
LOGIN_ACTION = "https://franservesupport.com/process_login.asp"

BASE_URL = "https://franservesupport.com/"
CATALOGUE_BASE_URL = BASE_URL + "directory.asp?ClientID="


def session_login(login_action: str, username: str, password: str) -> requests.Session:
    """
    Login to the FranServe website and return a session object.

    Args:
        login_action (str): The URL to login to.
        username (str): The username to login with.
        password (str): The password to login with.

    Returns:
        requests.Session: A session object with the login credentials.
    """

    session = requests.Session()

    payload = {
        "email": username,
        "password": password,
        "Submit": "Login",
    }
    login_resp = session.post(login_action, data=payload)
    login_resp.raise_for_status()  # ensure login succeeded

    return session


def get_page_franchise_urls(
    session: requests.Session, base_url: str, catalogue_url: str
) -> List[str]:
    """
    Get a list of URLs to scrape.

    Args:
        session (requests.Session): The session object to use.
        base_url (str): The base URL to scrape.
        catalogue_url (str): The URL to scrape.

    Returns:
        List[str]: A list of URLs to scrape.
    """
    resp = session.get(catalogue_url)
    soup = BeautifulSoup(resp.text, "html.parser")

    matching_links = [
        base_url + a["href"]
        for a in soup.find_all("a", href=True)
        if a["href"].startswith("franchisedetails")
    ]

    # We ignore the first link as it belongs to the ad at the top of the page
    return matching_links[1:]


def get_all_pages_franchise_urls(
    session: requests.Session,
    base_url: str,
    catalogue_base_url: str,
    offset_max: int = 800,
    offset_step: int = 50,
) -> list[str]:
    """
    Get a list of URLs to scrape.

    Args:
        session (requests.Session): The session object to use.
        base_url (str): The base URL to scrape.
        catalogue_base_url (str): The base URL to scrape.
        offset_max (int): The maximum offset to scrape.
        offset_step (int): The step size for the offset.

    Returns:
        list[str]: A list of URLs to scrape.
    """
    catalogue_urls = [
        f"{catalogue_base_url}&offset={i}" for i in range(0, offset_max, offset_step)
    ]
    franchise_urls = []
    for catalogue_url in catalogue_urls:
        franchise_urls.extend(get_page_franchise_urls(session, base_url, catalogue_url))

    return franchise_urls


def get_franchise_data(session: requests.Session, url: str) -> BeautifulSoup:
    """
    Get the data for a franchise.

    Args:
        session (requests.Session): The session object to use.
        url (str): The URL to scrape.

    Returns:
        BeautifulSoup: A BeautifulSoup tag of the franchise data.
    """
    resp = session.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    td = soup.find_all("td", attrs={"colspan": "2"})[1]

    return td


def save_franchise_data(data: BeautifulSoup, file_name: str):
    """
    Save the data for a franchise to a JSON file.

    Args:
        data (BeautifulSoup): The data to save.
        file_name (str): The name of the file to save the data to.
    """
    with open(os.path.join(EXTERNAL_DATA_DIR, file_name), "w", encoding="utf-8") as f:
        f.write(data.prettify())


def main():
    """
    Main function to run the scrapper.
    """
    session = session_login(LOGIN_ACTION, USERNAME, PASSWORD)
    franchise_urls = get_all_pages_franchise_urls(session, BASE_URL, CATALOGUE_BASE_URL)
    for url in tqdm(franchise_urls, total=len(franchise_urls), desc="Scraping franchise data"):
        data = get_franchise_data(session, url)
        file_name = quote(url.split("/")[-1], safe="") + ".html"
        save_franchise_data(data, file_name)


if __name__ == "__main__":
    main()
