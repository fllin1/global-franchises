"""
This module contains the functions to clean the body of a message.
"""

import re
import unicodedata

from bs4 import BeautifulSoup, Comment, Tag
from loguru import logger

# --- Heuristics tuned for EN-only threads ---
REPLY_MARKERS = [
    r"^On .+ wrote:\s*$",
    r"^On .+ at .+ wrote:\s*$",
    r"^On .+,\s*.+ wrote:\s*$",
    r"^-----Original Message-----$",
    r"^Begin forwarded message:$",
    r"^Forwarded message:$",
    r"^From:\s?.+$",
    r"^To:\s?.+$",
    r"^Sent:\s?.+$",
    r"^Subject:\s?.+$",
    r"^Reply above this line$",
]
SIG_MARKERS = [
    r"^\s*--\s*$",  # standard sig delimiter
    r"^Thanks,?$",
    r"^Thank you,?$",
    r"^Best( regards)?,?$",
    r"^Kind regards,?$",
    r"^Regards,?$",
    r"^Sincerely,?$",
    r"^Cheers,?$",
    r"^Sent from my iPhone",
    r"^Sent from my Android",
]

FOOTER_NOISE_RE = re.compile(
    r"(unsubscribe|manage preferences|update your preferences|privacy"
    r"|terms|confidentiality|do not reply|view this email in your browser)",
    re.I,
)
ZERO_WIDTH_RE = re.compile(r"\u200b|\u200c|\u200d|\ufeff")
MULTISPACE_RE = re.compile(r"[ \t]+")
EXTRA_NEWLINES_RE = re.compile(r"\n{3,}")


def _is_hidden(el) -> bool:
    # Guard against None and non-Tag objects
    if el is None or not isinstance(el, Tag):
        return False
    try:
        attrs = el.attrs or {}

        style = str(attrs.get("style", "")).lower()
        if any(k in style for k in ("display:none", "visibility:hidden", "opacity:0")):
            return True

        aria_hidden = str(attrs.get("aria-hidden", "")).lower()
        if aria_hidden == "true":
            return True

        # handle width/height not being strings
        w = str(attrs.get("width", "")).lower()
        h = str(attrs.get("height", "")).lower()
        if w in {"1", "1px"} and h in {"1", "1px"}:
            return True

        return False
    except ValueError as e:
        # Failsafe: never raise from here
        logger.error(f"_is_hidden failed on <{getattr(el, 'name', '?')}>: {e}")
        return False


def _strip_reply_and_signature(lines):
    reply_rx = [re.compile(p, re.I) for p in REPLY_MARKERS]
    sig_rx = [re.compile(p, re.I) for p in SIG_MARKERS]
    kept = []
    for line in lines:
        if line.startswith(">"):  # quoted block
            break
        if any(rx.search(line) for rx in reply_rx):
            break
        if any(rx.search(line) for rx in sig_rx):
            break
        kept.append(line)
    return kept


def _replace_links(soup: BeautifulSoup, keep_links: bool):
    for a in soup.find_all("a"):
        text = (a.get_text(strip=True) or "").strip()
        href = (a.get("href") or "").strip()
        if not href or not keep_links or href.lower().startswith("javascript:"):
            a.replace_with(text)
        else:
            a.replace_with(f"{text} ({href})" if text else href)


def _prepare_lists(soup: BeautifulSoup):
    # Turn list items into bullet lines to preserve structure
    for li in soup.find_all("li"):
        li.insert_before("\n- ")
        li.insert_after("\n")


def clean_email_html(html: str, *, keep_links: bool = True) -> str:
    """
    Convert messy email HTML to clean plaintext.
      - remove scripts/styles/hidden nodes/trackers
      - drop common footer boilerplate (unsubscribe/legal)
      - preserve bullets and (optionally) links
      - strip quoted reply history and signatures
    """
    # 1) Parse
    soup = BeautifulSoup(html or "", "lxml")

    # Remove comments early
    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        c.extract()

    # Remove noisy tags entirely
    for tag in soup(["script", "style", "noscript", "svg", "form", "iframe", "head"]):
        tag.decompose()

    # Remove hidden/tracking elements (iterate only over Tag objects)
    for el in list(soup.find_all(True)):
        if not isinstance(el, Tag):
            continue
        if _is_hidden(el):
            el.decompose()

    # Drop footer/legal/unsubscribe blocks
    for node in list(soup.find_all(string=FOOTER_NOISE_RE)):
        # node may be a NavigableString; prefer operating on its parent Tag
        container = getattr(node, "parent", None)
        target = None
        if container and isinstance(container, Tag):
            # Try to remove the enclosing structural block; fall back to the container itself
            target = container.find_parent(["footer", "table", "div", "section", "p"]) or container
        if target and isinstance(target, Tag):
            target.decompose()
        else:
            # As a last resort, remove just the matching text node
            try:
                node.extract()
            except Exception:
                pass

    # 2) Light structural normalization
    for br in soup.find_all("br"):
        br.replace_with("\n")
    _prepare_lists(soup)
    _replace_links(soup, keep_links=keep_links)

    # Add newlines around blocks so words don’t jam together
    for blk in soup.find_all(
        [
            "p",
            "div",
            "section",
            "tr",
            "ul",
            "ol",
            "table",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
        ]
    ):
        blk.insert_before("\n")
        blk.insert_after("\n")

    # 3) Extract text
    text = soup.get_text(separator=" ", strip=True)

    # 4) Normalize whitespace and unicode
    text = unicodedata.normalize("NFKC", text)
    text = ZERO_WIDTH_RE.sub("", text)
    text = MULTISPACE_RE.sub(" ", text)
    text = EXTRA_NEWLINES_RE.sub("\n\n", text)

    # 5) Strip quoted replies and signatures
    lines = [ln.rstrip() for ln in text.splitlines()]
    lines = _strip_reply_and_signature(lines)

    out = "\n".join(lines).strip()
    out = EXTRA_NEWLINES_RE.sub("\n\n", out)

    # Remove Franchise Consultant Franchises Global footer
    out = out.replace(
        " Franchise Consultant Franchises Global 1224 N Broadway, "
        "Santa Ana, CA 92701 p:(310)999-1670 e: (mailto:e%3Amanojsoans@franchisesglobal.com) "
        "manojsoans@franchisesglobal.com (mailto:manojsoans@franchisesglobal.com) "
        "w: www.franchisesglobal.com (http://www.franchisesglobal.com)",
        "",
    )
    return out
