# src/ghl/get_messages.py
"""
This script exports all conversations and messages from the GHL API to CSV files.
"""

import csv
import os
import signal
import time
from typing import Dict, Iterable, List, Optional
import unicodedata

from dotenv import load_dotenv
from loguru import logger
import requests

from src.config import PROCESSED_DATA_DIR
from src.ghl.utils.clean_messages_body import clean_email_html

# ---------- Config ----------
load_dotenv()

TOKEN = os.environ.get("GHL_TOKEN")
LOCATION_ID = os.environ.get("GHL_LOCATION_ID", "JMKW7uSiXL63XD0a2duU")

BASE = "https://services.leadconnectorhq.com"
HEADERS = {
    "Accept": "application/json",
    "Version": "2021-04-15",
    "Authorization": f"Bearer {TOKEN}",
}

# CSV files
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

CONV_CSV = PROCESSED_DATA_DIR / "ghl_conversations.csv"
MSG_CSV = PROCESSED_DATA_DIR / "ghl_messages.csv"

# Cursor file to resume conversations
CONV_CURSOR = PROCESSED_DATA_DIR / "ghl_conversations.cursor"
CONV_SEEN = PROCESSED_DATA_DIR / "ghl_conversations.seen"
# Resume/seen files for messages
MSG_SEEN = PROCESSED_DATA_DIR / "ghl_messages.seen"

# Page sizes
CONV_PAGE_LIMIT = 20
MSG_PAGE_LIMIT = 100

# Safety: max retries and base sleep (for 429, 5xx)
MAX_RETRIES = 6
BASE_SLEEP = 1.0


# ---------- Helpers ----------
def ensure_token():
    """
    Ensure the token is set in the environment.
    """
    if not TOKEN:
        raise RuntimeError("GHL_TOKEN is missing. Set it in your environment (.env).")


def iso_from_epoch_ms(ms: Optional[int]) -> Optional[str]:
    """
    Convert epoch milliseconds to ISO-8601 string (UTC).
    """
    if ms is None:
        return None
    try:
        # Some fields might already be ISO strings; if so, return as-is
        if isinstance(ms, str) and ms.endswith("Z"):
            return ms
        # Accept both stringified numbers and integers
        ms_int = int(ms)
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ms_int / 1000.0))
    except ValueError:
        return None


def api_get(
    url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None
) -> Dict:
    """
    GET with retry/backoff on 429 and 5xx.
    """
    h = headers or HEADERS
    params = params or {}
    for attempt in range(1, MAX_RETRIES + 1):
        resp = requests.get(url, headers=h, params=params, timeout=60)
        if resp.status_code == 200:
            try:
                return resp.json()
            except ValueError:
                # Fallback if not JSON
                return {"_raw": resp.text}
        if resp.status_code == 429:
            # honor Retry-After if present
            retry_after = resp.headers.get("Retry-After")
            sleep_s = (
                float(retry_after) if retry_after else BASE_SLEEP * (2 ** (attempt - 1))
            )
            time.sleep(min(sleep_s, 60))
            continue
        if 500 <= resp.status_code < 600:
            time.sleep(BASE_SLEEP * (2 ** (attempt - 1)))
            continue
        # Other non-retryable errors
        raise RuntimeError(f"GET {url} failed: {resp.status_code} {resp.text}")
    raise RuntimeError(f"GET {url} failed after {MAX_RETRIES} retries.")


def load_conv_cursor() -> Optional[str]:
    """Return last saved startAfterDate (epoch ms) if any."""
    try:
        if CONV_CURSOR.exists():
            v = CONV_CURSOR.read_text(encoding="utf-8").strip()
            return v if v else None
    except ValueError:
        pass
    return None


def save_conv_cursor(ms_str: str) -> None:
    """Save last saved startAfterDate (epoch ms) if any."""
    try:
        CONV_CURSOR.write_text(str(ms_str), encoding="utf-8")
    except ValueError as e:
        logger.warning(f"Could not write cursor file: {e}")


def load_seen(path: str) -> set:
    """
    Load seen items from a file.
    """
    s = set()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                s.add(line.strip())
    return s


def append_seen(path: str, _id: str):
    """
    Append an item to the seen file.
    """
    with open(path, "a", encoding="utf-8") as f:
        f.write(_id + "\n")


def csv_exists_with_header(path: str) -> bool:
    """
    Check if a CSV file exists and has a header.
    """
    return os.path.exists(path) and os.path.getsize(path) > 0


def open_csv_writer(path: str, fieldnames: List[str]):
    """
    Open a CSV file for writing.
    """
    file_exists = csv_exists_with_header(path)
    f = open(path, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(f, fieldnames=fieldnames)
    if not file_exists:
        w.writeheader()
    return f, w


def normalize_text(s: Optional[str]) -> str:
    """
    Normalize text to remove accents and whitespace.
    """
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    return s.strip()


# ---------- Fetchers ----------


def fetch_conversations(start_after: Optional[str] = None) -> Iterable[Dict]:
    """
    Cursor pagination using startAfterDate.
    We sort newest-first (last_message_date desc) and advance the cursor
    with the last item's lastMessageDate (epoch ms).
    """
    params_base = {
        "locationId": LOCATION_ID,
        "status": "all",
        "sortBy": "last_message_date",
        "sort": "desc",
        "limit": CONV_PAGE_LIMIT,  # <= 100 per API
    }

    cursor = start_after
    batch_idx = 0
    while True:
        params = dict(params_base)
        if cursor:
            params["startAfterDate"] = cursor

        url = f"{BASE}/conversations/search"
        data = api_get(url, params=params)
        convs = data.get("conversations") or data.get("items") or []
        if not convs:
            logger.debug("No more conversations to fetch.")
            break

        logger.debug(
            f"Batch {batch_idx}: {len(convs)} conversations (cursor={cursor or 'None'})"
        )
        yield from convs

        # Advance the cursor to the last item's lastMessageDate (epoch ms)
        last = convs[-1]
        last_ms = last.get("lastMessageDate") or (last.get("sort") or [None])[-1]
        if last_ms is None:
            logger.warning(
                "Missing lastMessageDate on last item; stopping to avoid loop."
            )
            break
        cursor = str(last_ms)
        save_conv_cursor(cursor)

        if len(convs) < CONV_PAGE_LIMIT:
            logger.info("Reached final (short) batch.")
            break

        batch_idx += 1


def fetch_messages_for_conversation(conversation_id: str) -> Iterable[Dict]:
    """
    Page through messages using lastMessageId + nextPage=True.
    """
    last_id = None
    while True:
        params = {"limit": MSG_PAGE_LIMIT}
        if last_id:
            params["lastMessageId"] = last_id
        url = f"{BASE}/conversations/{conversation_id}/messages"
        data = api_get(url, params=params)
        # API shape: { "messages": { "lastMessageId": "...",
        # "nextPage": bool, "messages": [ ... ] } }
        msgs_container = data.get("messages") or {}
        batch = msgs_container.get("messages") or []
        if not batch:
            break
        yield from batch
        last_id = msgs_container.get("lastMessageId")
        next_page = msgs_container.get("nextPage")
        if not next_page:
            break


def fetch_message_detail(message_id: str) -> Optional[Dict]:
    """
    GET /conversations/messages/{messageId}
    """
    url = f"{BASE}/conversations/messages/{message_id}"
    data = api_get(url)
    return data.get("message")


# ---------- Main export ----------
def export_all():
    """
    Export all conversations and messages to CSV files.
    """
    ensure_token()

    # Prepare writers
    conv_fields = [
        "id",
        "locationId",
        "contactId",
        "fullName",
        "companyName",
        "email",
        "phone",
        "dateAdded",
        "dateUpdated",
        "lastMessageDate",
        "lastMessageType",
        "lastMessageDirection",
        "unreadCount",
        "tags",
        "type",
    ]
    msg_fields = [
        "id",
        "conversationId",
        "contactId",
        "locationId",
        "dateAdded",
        "messageType",
        "source",
        "type",
        "body_length",
        "body_clean_length",
        "body_clean",
    ]
    conv_f, conv_w = open_csv_writer(CONV_CSV, conv_fields)
    msg_f, msg_w = open_csv_writer(MSG_CSV, msg_fields)

    # Resume sets (fast skip)
    start_after = load_conv_cursor()  # Cursor to resume conversations
    seen_convs = load_seen(CONV_SEEN)  # Seen conversations
    # NOTE: in itself, the seen convs is not needed, it is only used to
    # assert that the "start_after" cursor logic is working.
    seen_msgs = load_seen(MSG_SEEN)  # Seen messages

    # Graceful shutdown (write files if Ctrl+C)
    def _graceful_exit(signum, frame):
        try:
            conv_f.flush()
            conv_f.close()
        except (ValueError, OSError):
            pass
        try:
            msg_f.flush()
            msg_f.close()
        except (ValueError, OSError):
            pass
        logger.info("Stopped. Files flushed.")
        raise SystemExit(0)

    signal.signal(signal.SIGINT, _graceful_exit)
    signal.signal(signal.SIGTERM, _graceful_exit)

    # 1) Conversations
    conv_count = 0
    for conv in fetch_conversations(start_after=start_after):
        conv_id = conv.get("id")
        if not conv_id:
            continue

        # Write conversation row if not seen
        if conv_id not in seen_convs:
            conv_row = {
                "id": conv_id,
                "locationId": conv.get("locationId"),
                "contactId": conv.get("contactId"),
                "fullName": normalize_text(
                    conv.get("fullName") or conv.get("contactName")
                ),
                "companyName": normalize_text(conv.get("companyName")),
                "email": normalize_text(conv.get("email")),
                "phone": normalize_text(conv.get("phone")),
                "dateAdded": iso_from_epoch_ms(conv.get("dateAdded")),
                "dateUpdated": iso_from_epoch_ms(conv.get("dateUpdated")),
                "lastMessageDate": iso_from_epoch_ms(conv.get("lastMessageDate")),
                "lastMessageType": conv.get("lastMessageType"),
                "lastMessageDirection": conv.get("lastMessageDirection"),
                "unreadCount": conv.get("unreadCount"),
                "tags": ",".join(conv.get("tags") or []),
                "type": conv.get("type"),
            }
            conv_w.writerow(conv_row)
            conv_f.flush()
            append_seen(CONV_SEEN, conv_id)
            seen_convs.add(conv_id)
            logger.info(f"Created new conversation: {conv_id} ({conv_row['email']})")
        else:
            logger.debug(f"Skipping seen conversation: {conv_id}")

        # 2) Messages for conversation
        messages = fetch_messages_for_conversation(conv_id)
        for m in messages:
            msg_id = m.get("id")
            if msg_id in seen_msgs:
                logger.debug(f"Skipping seen message: {msg_id}")
                continue

            if not msg_id:
                logger.debug(f"Skipping message without ID: {m}")
                continue

            # We call detail endpoint to get the body/subject (body is not in the list response)
            detail = fetch_message_detail(msg_id)
            if not detail:
                logger.debug(f"Skipping message without detail: {msg_id}")
                continue

            # Basic fields
            body_raw = detail.get("body") or ""
            body_len = len(body_raw)

            # Clean only if email; else leave empty (or raw if you prefer)
            message_type = detail.get("messageType")
            is_email = isinstance(message_type, str) and "EMAIL" in message_type
            body_clean = clean_email_html(body_raw) if is_email else ""
            body_clean_len = len(body_clean)

            msg_row = {
                "id": detail.get("id"),
                "conversationId": detail.get("conversationId"),
                "contactId": detail.get("contactId"),
                "locationId": detail.get("locationId"),
                "dateAdded": detail.get("dateAdded"),  # already ISO per your sample
                "messageType": message_type,
                "source": detail.get("source"),
                "type": detail.get("type"),
                "body_length": body_len,
                "body_clean_length": body_clean_len,
                "body_clean": body_clean,
            }
            msg_w.writerow(msg_row)
            msg_f.flush()
            append_seen(MSG_SEEN, msg_id)
            seen_msgs.add(msg_id)
            logger.info(f"Added message {msg_id}")

        conv_count += 1
        # Periodic flush, in case of OS buffers
        conv_f.flush()
        msg_f.flush()
        print(f"Conversations count: {conv_count}.\n")

    conv_f.close()
    msg_f.close()
    logger.success("Done. Conversations and messages exported.")


if __name__ == "__main__":
    export_all()
