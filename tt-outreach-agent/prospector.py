"""
Search and fetch prospects from Apollo.io API
"""
import os
import logging
import requests
from dotenv import load_dotenv
from config import ICP_SHIELDAI, ICP_TWOLAPS, APOLLO_API_BASE, DAILY_LIMITS
from db import (
    insert_prospect, check_prospect_exists, get_config, set_config
)

load_dotenv()

logger = logging.getLogger(__name__)

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")


def get_icp_config(product):
    """Get ICP configuration for product"""
    if product == "shieldai":
        return ICP_SHIELDAI
    elif product == "twolaps":
        return ICP_TWOLAPS
    else:
        raise ValueError(f"Unknown product: {product}")


def search_apollo(product, page=1, per_page=50):
    """
    Search prospects in Apollo.io using People Search API (v2 endpoint)
    Returns list of prospects from API
    """
    if not APOLLO_API_KEY:
        logger.error("APOLLO_API_KEY not set")
        return []

    icp = get_icp_config(product)

    url = f"{APOLLO_API_BASE}/mixed_people/api_search"
    headers = {"x-api-key": APOLLO_API_KEY}

    # Build employee count filter from ranges (e.g., "25-50" → {min: 25, max: 50})
    employee_count_filters = []
    for range_str in icp.get("employee_ranges", []):
        try:
            min_val, max_val = map(int, range_str.split("-"))
            employee_count_filters.append({"min": min_val, "max": max_val})
        except Exception as e:
            logger.warning(f"Invalid employee range format: {range_str}")

    # Build filter object
    filter_obj = {
        "person_titles": icp["person_titles"],
        "locations": icp["person_locations"],
    }

    if employee_count_filters:
        filter_obj["employee_count"] = employee_count_filters

    payload = {
        "filter": filter_obj,
        "page": page,
        "per_page": per_page,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Apollo search returned {len(data.get('people', []))} prospects")
        return data.get("people", [])
    except requests.exceptions.RequestException as e:
        logger.error(f"Apollo API error: {e}")
        return []


def enrich_prospect_by_id(apollo_id):
    """
    Enrich prospect by Apollo ID using /people/match endpoint
    Uses Professional plan credits to reveal email and full details
    Returns enriched prospect data with email
    """
    if not APOLLO_API_KEY:
        return None

    url = f"{APOLLO_API_BASE}/people/match"
    headers = {"x-api-key": APOLLO_API_KEY}

    # Use apollo_id to match the prospect (doesn't need name or company)
    payload = {
        "id": apollo_id,
        "reveal_personal_emails": False,
        "reveal_phone_number": False,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        person = data.get("person", {})
        if person.get("email"):
            logger.debug(f"Enriched ID {apollo_id} with email: {person.get('email')}")
            return data

        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"Apollo enrichment error for {apollo_id}: {e}")
        return None


def find_new_prospects(product, limit=None):
    """
    Find new prospects from Apollo for specified product
    Respects daily limits and deduplication
    Returns count of new prospects added
    """
    if limit is None:
        limit = DAILY_LIMITS["new_prospects"]

    limit = min(limit, DAILY_LIMITS["new_prospects"])

    # Get current page from config
    page_key = f"apollo_page_{product}"
    current_page = int(get_config(page_key) or 1)

    logger.info(f"Searching prospects for {product} (page {current_page})")

    # Search Apollo
    prospects = search_apollo(product, page=current_page, per_page=50)

    if not prospects:
        logger.warning("No prospects found from Apollo")
        return 0

    new_count = 0
    for prospect in prospects[:limit]:
        try:
            apollo_id = prospect.get("id", "")

            # Skip if no ID
            if not apollo_id:
                continue

            # Check if already exists
            if check_prospect_exists(apollo_id=apollo_id):
                logger.info(f"Prospect {apollo_id} already exists, skipping")
                continue

            # Enrich by ID to get full details including email
            logger.debug(f"Enriching prospect {apollo_id}...")
            enriched = enrich_prospect_by_id(apollo_id)

            if not enriched:
                logger.warning(f"Failed to enrich {apollo_id}")
                continue

            person = enriched.get("person", {})
            email = person.get("email")

            # Email is required
            if not email:
                logger.warning(f"No email for prospect {apollo_id}")
                continue

            # Extract all data from enriched response
            first_name = person.get("first_name", "")
            last_name = person.get("last_name", "")
            job_title = person.get("title", "")
            linkedin_url = person.get("linkedin_url", "")

            # Company data from organization in original search result
            company_name = prospect.get("organization", {}).get("name", "")
            company_domain = prospect.get("organization", {}).get("domain", "")
            country = prospect.get("country", "")
            city = prospect.get("city", "")

            # Fallback to enriched organization data if available
            if not company_name and person.get("organization_name"):
                company_name = person["organization_name"]

            # Insert prospect
            prospect_id = insert_prospect(
                apollo_id=apollo_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                linkedin_url=linkedin_url,
                job_title=job_title,
                company_name=company_name,
                company_domain=company_domain,
                country=country,
                city=city,
                product_target=product,
            )

            if prospect_id:
                new_count += 1
                logger.info(f"✓ New prospect: {first_name} {last_name} ({email}) - {job_title}")

        except Exception as e:
            logger.error(f"Error processing prospect {apollo_id}: {e}")
            continue

    # Update page for next run
    next_page = current_page + 1
    set_config(page_key, str(next_page))
    logger.info(f"Updated page tracker to {next_page}")

    logger.info(f"Found {new_count} new prospects for {product}")
    return new_count


if __name__ == "__main__":
    import sys
    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--product", default="shieldai")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    if args.test:
        print(f"Testing prospector for {args.product} (limit: {args.limit})")
        count = find_new_prospects(args.product, limit=args.limit)
        print(f"Result: {count} new prospects")
