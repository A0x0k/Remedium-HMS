"""
OpenFDA API integration service.

Provides drug information from the FDA's public API.
Results are cached to avoid repeated API calls.
"""

"""
OpenFDA API integration service.

Provides drug information from the FDA's public API.
Results are cached to avoid repeated API calls.

NOTE: These calls are synchronous and block the request thread. For production
deployments at scale, consider migrating to an async task queue (Celery/django-q)
to prevent worker threads from being blocked during OpenFDA API calls.
"""

import logging
from django.core.cache import cache
import requests

logger = logging.getLogger(__name__)

OPENFDA_BASE_URL = "https://api.fda.gov"
CACHE_TIMEOUT = 60 * 60 * 24  # 24 hours
REQUEST_TIMEOUT = 5  # seconds — reduced from 10s to minimize request thread blocking


def search_drug_label(drug_name: str, skip_cache: bool = False) -> dict:
    """
    Search OpenFDA drug label database for a medication.

    Returns structured drug information including:
    - Brand names
    - Generic name
    - Manufacturer
    - Route (oral, topical, etc.)
    - Warnings and precautions
    - Adverse reactions
    - Dosage information

    Args:
        drug_name: Name of the drug to search for
        skip_cache: If True, bypass cache and fetch fresh data

    Returns:
        dict with drug information or error dict if not found
    """
    cache_key = f"openfda_drug_label_{drug_name.lower().strip()}"

    if not skip_cache:
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

    try:
        response = requests.get(
            f"{OPENFDA_BASE_URL}/drug/label.json",
            params={
                "search": f'openfda.generic_name:"{drug_name}"',
                "limit": 1,
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        if not data.get("results"):
            # Fallback: search by brand name
            response = requests.get(
                f"{OPENFDA_BASE_URL}/drug/label.json",
                params={
                    "search": f'openfda.brand_name:"{drug_name}"',
                    "limit": 1,
                },
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()

        if not data.get("results"):
            return {"error": f"No information found for '{drug_name}'"}

        result = _parse_label_result(data["results"][0])
        cache.set(cache_key, result, CACHE_TIMEOUT)
        return result

    except requests.RequestException as e:
        logger.warning(f"OpenFDA API error for '{drug_name}': {e}")
        return {"error": "Unable to fetch drug information. Please try again later."}
    except Exception as e:
        logger.error(f"Unexpected error fetching OpenFDA data for '{drug_name}': {e}")
        return {"error": "An unexpected error occurred."}


def search_adverse_events(drug_name: str, skip_cache: bool = False) -> dict:
    """
    Search OpenFDA adverse event reports for a medication.

    Returns summary of reported side effects and adverse reactions.

    Args:
        drug_name: Name of the drug to search for
        skip_cache: If True, bypass cache and fetch fresh data

    Returns:
        dict with adverse event summary
    """
    cache_key = f"openfda_adverse_{drug_name.lower().strip()}"

    if not skip_cache:
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

    try:
        response = requests.get(
            f"{OPENFDA_BASE_URL}/drug/event.json",
            params={
                "search": f'patient.drug.openfda.generic_name:"{drug_name}"',
                "count": "patient.reaction.reactionmeddrapt.exact",
                "limit": 10,
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("results", []):
            results.append(
                {
                    "reaction": item.get("term", ""),
                    "count": item.get("count", 0),
                }
            )

        result = {
            "drug_name": drug_name,
            "top_adverse_reactions": results[:10],
            "total_reports": sum(r["count"] for r in results),
        }
        cache.set(cache_key, result, CACHE_TIMEOUT)
        return result

    except requests.RequestException as e:
        logger.warning(f"OpenFDA adverse events error for '{drug_name}': {e}")
        return {"error": "Unable to fetch adverse event data."}
    except Exception as e:
        logger.error(f"Unexpected error fetching adverse events for '{drug_name}': {e}")
        return {"error": "An unexpected error occurred."}


def _parse_label_result(result: dict) -> dict:
    """Parse a single OpenFDA label result into a clean structure."""
    openfda = result.get("openfda", {})

    return {
        "generic_name": _first(openfda.get("generic_name")),
        "brand_name": _first(openfda.get("brand_name")),
        "manufacturer": _first(openfda.get("manufacturer_name")),
        "route": openfda.get("route", []),
        "substance_name": openfda.get("substance_name", []),
        "product_type": openfda.get("product_type", []),
        "warnings": _first(result.get("warnings_and_cautions")),
        "adverse_reactions": _first(result.get("adverse_reactions")),
        "dosage_administration": _first(result.get("dosage_and_administration")),
        "drug_interactions": _first(result.get("drug_interactions")),
        "indications": _first(result.get("indications_and_usage")),
        "set_id": _first(openfda.get("set_id")),
    }


def _first(items: list) -> str:
    """Safely return the first item from a list, or empty string."""
    if items:
        return items[0]
    return ""
