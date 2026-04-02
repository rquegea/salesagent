"""
Main orchestrator for T&T Outreach Agent
Executed daily via cron (8 AM Madrid time)
"""
import logging
from datetime import datetime
from dotenv import load_dotenv

from db import init_db, get_stats
from follower import check_replies, generate_followups, cleanup_exhausted
from prospector import find_new_prospects
from composer import generate_drafts
from sender import send_emails, send_linkedin_requests

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/outreach.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


def log_stats():
    """Log current statistics"""
    stats = get_stats()
    if stats:
        logger.info(
            f"Stats: Total={stats['total']}, New={stats['new_count']}, "
            f"Drafted={stats['drafted_count']}, Sent={stats['sent_count']}, "
            f"Replied={stats['replied_count']}"
        )


def run():
    """Main execution flow"""
    today = datetime.now()

    # Skip weekends
    if today.weekday() >= 5:
        logger.info(f"Weekend ({today.strftime('%A')}) — skipping execution")
        return

    logger.info(f"=== Outreach run: {today.isoformat()} ===")

    try:
        # Initialize DB
        init_db()

        # 1. Check replies and mark them
        logger.info("Step 1: Checking replies...")
        replies = check_replies()
        logger.info(f"Replies found: {replies}")

        # 2. Generate follow-ups for due prospects
        logger.info("Step 2: Generating follow-ups...")
        followups = generate_followups()
        logger.info(f"Follow-ups queued: {followups}")

        # 3. Search for new prospects
        logger.info("Step 3: Searching new prospects...")
        shieldai_new = find_new_prospects(product="shieldai", limit=25)
        twolaps_new = find_new_prospects(product="twolaps", limit=25)
        total_new = shieldai_new + twolaps_new
        logger.info(f"New prospects: ShieldAI={shieldai_new}, 2laps={twolaps_new}, Total={total_new}")

        # 4. Generate drafts for new prospects
        logger.info("Step 4: Generating drafts...")
        drafts = generate_drafts()
        logger.info(f"Drafts generated: {drafts}")

        # 5. Send emails
        logger.info("Step 5: Sending emails...")
        sent_email = send_emails()
        logger.info(f"Emails sent: {sent_email}")

        # 6. Send LinkedIn requests
        logger.info("Step 6: Sending LinkedIn requests...")
        sent_li = send_linkedin_requests()
        logger.info(f"LinkedIn requests sent: {sent_li}")

        # 7. Cleanup exhausted prospects
        logger.info("Step 7: Cleaning up exhausted prospects...")
        exhausted = cleanup_exhausted()
        logger.info(f"Exhausted prospects: {exhausted}")

        # Log final stats
        logger.info("Final statistics:")
        log_stats()

        logger.info("=== Outreach run completed successfully ===")

    except Exception as e:
        logger.error(f"Outreach run failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run()
