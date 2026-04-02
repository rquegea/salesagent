"""
Send emails and LinkedIn requests via Unipile API
"""
import os
import logging
import time
import random
import json
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta
from config import DAILY_LIMITS, CADENCE
from db import (
    get_prospects_by_status, update_prospect_sent
)

load_dotenv()

logger = logging.getLogger(__name__)

UNIPILE_API_KEY = os.getenv("UNIPILE_API_KEY")
UNIPILE_DSN = os.getenv("UNIPILE_DSN")
UNIPILE_EMAIL_ACCOUNT_ID = os.getenv("UNIPILE_EMAIL_ACCOUNT_ID")
UNIPILE_LINKEDIN_ACCOUNT_ID = os.getenv("UNIPILE_LINKEDIN_ACCOUNT_ID")


def is_weekend():
    """Check if today is weekend"""
    return datetime.now().weekday() >= 5


def send_email_unipile(to_email, to_name, subject, body):
    """Send email via Unipile API using multipart/form-data"""
    if not (UNIPILE_API_KEY and UNIPILE_DSN and UNIPILE_EMAIL_ACCOUNT_ID):
        logger.error("Unipile credentials not configured")
        return False

    # DSN format: "host:port" (e.g., "api19.unipile.com:14942")
    url = f"https://{UNIPILE_DSN}/api/v1/emails"
    headers = {"X-API-KEY": UNIPILE_API_KEY}

    # Unipile API requires multipart/form-data, not JSON
    files = {
        "account_id": (None, UNIPILE_EMAIL_ACCOUNT_ID),
        "subject": (None, subject),
        "body": (None, body),
        "to": (None, json.dumps([{"identifier": to_email, "display_name": to_name}])),
    }

    try:
        response = requests.post(url, files=files, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Check for success response
        if data.get("object") == "EmailSent":
            logger.info(f"✓ Email sent to {to_email} (tracking_id: {data.get('tracking_id')})")
            return True
        else:
            logger.error(f"Unexpected response: {data}")
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


def send_linkedin_request(profile_id, first_name, message=None):
    """Send LinkedIn connection request via Unipile API"""
    if not (UNIPILE_API_KEY and UNIPILE_DSN and UNIPILE_LINKEDIN_ACCOUNT_ID):
        logger.error("Unipile credentials not configured")
        return False

    # DSN format: "host:port" (e.g., "api19.unipile.com:14942")
    url = f"https://{UNIPILE_DSN}/api/v1/users/invite"
    headers = {"X-API-KEY": UNIPILE_API_KEY}

    payload = {
        "account_id": UNIPILE_LINKEDIN_ACCOUNT_ID,
        "provider_id": profile_id,
    }

    if message:
        payload["message"] = message

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        logger.info(f"LinkedIn request sent to {profile_id}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send LinkedIn request to {profile_id}: {e}")
        return False


def send_emails(limit=None, dry_run=False):
    """Send all drafted emails"""
    if is_weekend():
        logger.info("Weekend — skipping email sends")
        return 0

    if limit is None:
        limit = DAILY_LIMITS["emails_sent"]

    limit = min(limit, DAILY_LIMITS["emails_sent"])

    logger.info(f"Sending emails (limit: {limit}, dry_run: {dry_run})")

    # Get drafted prospects
    prospects = get_prospects_by_status("drafted", limit=limit)

    if not prospects:
        logger.info("No drafted emails to send")
        return 0

    sent_count = 0
    for prospect in prospects:
        email = prospect.get("email")
        first_name = prospect.get("first_name")
        subject = prospect.get("draft_subject")
        body = prospect.get("draft_body")

        if not (email and subject and body):
            logger.warning(f"Incomplete prospect data: {prospect['id']}")
            continue

        logger.info(f"Sending to {email}...")

        if not dry_run:
            # Add unsubscribe footer (GDPR compliance)
            footer = "\n\n---\nSi prefieres no recibir más emails, responde 'baja' y te elimino inmediatamente."
            full_body = body + footer

            if send_email_unipile(email, first_name, subject, full_body):
                # Mark as sent
                update_prospect_sent(prospect["id"], next_contact_days=CADENCE["follow_up_1"])
                sent_count += 1

                # Spacing to avoid spam filter
                delay = random.uniform(60, 180)
                logger.info(f"Waiting {delay:.0f}s before next email...")
                time.sleep(delay)
        else:
            logger.info(f"[DRY RUN] Would send: {subject} to {email}")
            sent_count += 1

    logger.info(f"Sent {sent_count}/{len(prospects)} emails")
    return sent_count


def send_linkedin_requests(limit=None, dry_run=False):
    """Send LinkedIn connection requests"""
    if not UNIPILE_LINKEDIN_ACCOUNT_ID:
        logger.info("LinkedIn not configured, skipping")
        return 0

    if is_weekend():
        logger.info("Weekend — skipping LinkedIn sends")
        return 0

    if limit is None:
        limit = DAILY_LIMITS["linkedin_requests"]

    limit = min(limit, DAILY_LIMITS["linkedin_requests"])

    logger.info(f"Sending LinkedIn requests (limit: {limit}, dry_run: {dry_run})")

    # Get sent prospects with LinkedIn profiles
    prospects = get_prospects_by_status("sent", limit=limit)
    prospects = [p for p in prospects if p.get("linkedin_url")]

    if not prospects:
        logger.info("No LinkedIn profiles to connect with")
        return 0

    sent_count = 0
    for prospect in prospects:
        linkedin_url = prospect.get("linkedin_url")
        first_name = prospect.get("first_name")

        # Extract profile ID from URL (simple extraction)
        try:
            profile_id = linkedin_url.rstrip("/").split("/")[-1]
        except Exception as e:
            logger.warning(f"Failed to extract profile ID from {linkedin_url}: {e}")
            continue

        message = f"Hola {first_name}, encontré algo que podría servirte. Conectamos?"

        logger.info(f"Sending LinkedIn request to {profile_id}...")

        if not dry_run:
            if send_linkedin_request(profile_id, first_name, message):
                sent_count += 1

                delay = random.uniform(60, 120)
                logger.info(f"Waiting {delay:.0f}s before next request...")
                time.sleep(delay)
        else:
            logger.info(f"[DRY RUN] Would send LinkedIn request to {profile_id}")
            sent_count += 1

    logger.info(f"Sent {sent_count} LinkedIn requests")
    return sent_count


if __name__ == "__main__":
    import sys
    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--to", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.test:
        print("Testing sender (dry run mode)")
        email_count = send_emails(limit=2, dry_run=True)
        li_count = send_linkedin_requests(limit=2, dry_run=True)
        print(f"Result: {email_count} emails, {li_count} LinkedIn requests (dry run)")
