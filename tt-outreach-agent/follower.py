"""
Monitor responses and generate follow-ups
"""
import os
import logging
import requests
from dotenv import load_dotenv
from config import CADENCE
from db import (
    get_prospects_needing_followup, mark_prospect_replied,
    mark_prospect_exhausted, update_prospect_status
)
from composer import generate_followup_drafts

load_dotenv()

logger = logging.getLogger(__name__)

UNIPILE_API_KEY = os.getenv("UNIPILE_API_KEY")
UNIPILE_DSN = os.getenv("UNIPILE_DSN")


def check_replies():
    """
    Check for replies to sent emails via Unipile API
    Returns count of replies found
    """
    if not (UNIPILE_API_KEY and UNIPILE_DSN):
        logger.warning("Unipile credentials not configured, skipping reply check")
        return 0

    url = f"https://{UNIPILE_DSN}.unipile.com:13443/api/v1/emails"
    headers = {"X-API-KEY": UNIPILE_API_KEY}
    params = {"folder": "inbox", "limit": 100}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        emails = data.get("results", [])
        logger.info(f"Retrieved {len(emails)} emails from inbox")

        reply_count = 0
        for email in emails:
            # Simple heuristic: if subject has "Re:" or "RE:" it's likely a reply
            subject = email.get("subject", "").lower()
            if "re:" in subject:
                # This is a simplified implementation
                # In production, would need to match to specific sent emails
                logger.info(f"Found potential reply: {subject}")
                reply_count += 1

        return reply_count

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to check replies: {e}")
        return 0


def generate_followups():
    """
    Generate follow-ups for prospects that need them
    Returns count of follow-ups generated
    """
    logger.info("Checking for prospects needing follow-ups")

    prospects = get_prospects_needing_followup()

    if not prospects:
        logger.info("No prospects needing follow-up")
        return 0

    logger.info(f"Found {len(prospects)} prospects needing follow-up")

    # Mark as needing follow-up
    followup_count = 0
    for prospect in prospects:
        touchpoints = prospect.get("touchpoints", 0)

        # Determine new status based on touchpoints
        if touchpoints == 1:
            new_status = "followed_up_1"
        elif touchpoints == 2:
            new_status = "followed_up_2"
        else:
            new_status = "followed_up_1"

        update_prospect_status(prospect["id"], new_status)
        followup_count += 1

    # Now generate drafts for follow-ups
    draft_count = generate_followup_drafts()

    logger.info(f"Marked {followup_count} prospects for follow-up, generated {draft_count} drafts")
    return followup_count


def cleanup_exhausted():
    """
    Mark prospects as exhausted if they've reached max touchpoints
    Returns count of exhausted prospects
    """
    logger.info("Cleaning up exhausted prospects")

    from db import get_db_connection

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT id FROM prospects
            WHERE touchpoints >= %s
            AND status NOT IN ('replied', 'meeting', 'closed')
            AND status != 'exhausted'
        """, (CADENCE["max_touchpoints"],))

        prospects_to_exhaust = cur.fetchall()

        for prospect_row in prospects_to_exhaust:
            prospect_id = prospect_row[0]
            mark_prospect_exhausted(prospect_id)

        conn.commit()
        logger.info(f"Marked {len(prospects_to_exhaust)} prospects as exhausted")
        return len(prospects_to_exhaust)

    except Exception as e:
        logger.error(f"Failed to cleanup exhausted: {e}")
        conn.rollback()
        return 0
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    import sys
    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    if args.test:
        print("Testing follower")
        replies = check_replies()
        followups = generate_followups()
        exhausted = cleanup_exhausted()
        print(f"Result: {replies} replies, {followups} follow-ups, {exhausted} exhausted")
