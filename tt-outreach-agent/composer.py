"""
Generate email drafts using Claude API
"""
import os
import logging
import requests
from dotenv import load_dotenv
from config import PRODUCT_DESCRIPTIONS, DAILY_LIMITS, ANTHROPIC_API_BASE
from db import (
    get_prospects_by_status, update_prospect_draft, get_prospects_needing_followup
)

load_dotenv()

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CALENDLY_URL = os.getenv("CALENDLY_URL", "https://calendly.com/rodrigo/30min")


def load_template(product, template_type="cold"):
    """Load prompt template"""
    template_path = f"templates/{product}_{template_type}.txt"
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"Template not found: {template_path}")
        return None


def render_template(template, prospect):
    """Render template with prospect data"""
    if not template:
        return None

    product_desc = PRODUCT_DESCRIPTIONS.get(
        prospect.get("product_target"), "Nuestro producto"
    )

    context = {
        "first_name": prospect.get("first_name", ""),
        "last_name": prospect.get("last_name", ""),
        "email": prospect.get("email", ""),
        "job_title": prospect.get("job_title", ""),
        "company_name": prospect.get("company_name", ""),
        "company_domain": prospect.get("company_domain", ""),
        "country": prospect.get("country", ""),
        "city": prospect.get("city", ""),
        "product_description": product_desc,
        "calendly_url": CALENDLY_URL,
    }

    rendered = template
    for key, value in context.items():
        rendered = rendered.replace(f"{{{key}}}", value)

    return rendered


def call_claude(prompt):
    """Call Claude API to generate email"""
    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not set")
        return None

    url = f"{ANTHROPIC_API_BASE}/messages"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    payload = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 500,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        content = data.get("content", [{}])[0].get("text", "")
        logger.info("Claude API call successful")
        return content
    except requests.exceptions.RequestException as e:
        logger.error(f"Claude API error: {e}")
        return None


def parse_email(response_text):
    """Parse Claude response to extract SUBJECT and BODY"""
    if not response_text:
        return None, None

    lines = response_text.strip().split("\n")
    subject = None
    body_lines = []
    parsing_body = False

    for line in lines:
        if line.startswith("SUBJECT:"):
            subject = line.replace("SUBJECT:", "").strip()
        elif line.startswith("BODY:"):
            parsing_body = True
            body_lines.append(line.replace("BODY:", "").strip())
        elif parsing_body:
            body_lines.append(line)

    body = "\n".join(body_lines).strip()

    return subject, body


def generate_draft_for_prospect(prospect):
    """Generate email draft for single prospect"""
    product = prospect.get("product_target", "shieldai")
    touchpoints = prospect.get("touchpoints", 0)

    # Determine template type
    if touchpoints == 0:
        template_type = "cold"
    elif touchpoints == 1:
        template_type = "fu1"
    else:
        template_type = "fu2"

    logger.info(
        f"Generating {template_type} for {prospect['first_name']} "
        f"({product}, touchpoint {touchpoints})"
    )

    # Load and render template
    template = load_template(product, template_type)
    if not template:
        logger.error(f"No template found for {product} {template_type}")
        return False

    prompt = render_template(template, prospect)
    if not prompt:
        logger.error("Failed to render template")
        return False

    # Call Claude
    response = call_claude(prompt)
    if not response:
        logger.error("Claude API failed")
        return False

    # Parse response
    subject, body = parse_email(response)
    if not subject or not body:
        logger.error("Failed to parse Claude response")
        logger.debug(f"Response: {response}")
        return False

    # Update prospect with draft
    update_prospect_draft(prospect["id"], subject, body, channel="email")
    logger.info(f"Draft generated for prospect {prospect['id']}")
    return True


def generate_drafts(limit=None):
    """Generate drafts for all new prospects"""
    if limit is None:
        limit = DAILY_LIMITS["claude_calls"]

    limit = min(limit, DAILY_LIMITS["claude_calls"])

    logger.info(f"Generating drafts (limit: {limit})")

    # Get new prospects
    prospects = get_prospects_by_status("new", limit=limit)

    if not prospects:
        logger.info("No new prospects to draft")
        return 0

    success_count = 0
    for prospect in prospects:
        if generate_draft_for_prospect(prospect):
            success_count += 1

    logger.info(f"Generated {success_count}/{len(prospects)} drafts")
    return success_count


def generate_followup_drafts():
    """Generate follow-up drafts for prospects that need follow-up"""
    logger.info("Generating follow-up drafts")

    prospects = get_prospects_needing_followup()

    if not prospects:
        logger.info("No prospects needing follow-up")
        return 0

    success_count = 0
    for prospect in prospects:
        if generate_draft_for_prospect(prospect):
            success_count += 1

    logger.info(f"Generated {success_count} follow-up drafts")
    return success_count


if __name__ == "__main__":
    import sys
    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()

    if args.test:
        print(f"Testing composer (limit: {args.limit})")
        count = generate_drafts(limit=args.limit)
        print(f"Result: {count} drafts generated")
