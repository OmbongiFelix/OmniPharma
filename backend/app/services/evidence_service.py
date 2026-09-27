"""Retrieves supporting drug information from configured external
sources and records provenance for every item returned.

Imports/dependencies: httpx.AsyncClient, external API adapters (e.g.
openFDA), app.core.config.

Public outputs: `get_evidence()`.
"""

import logging
from datetime import datetime, timezone

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_OPENFDA_BASE = "https://api.fda.gov/drug/label.json"


async def get_evidence(drug_name: str) -> list[dict]:
    """Retrieve supporting (non-authoritative) evidence for a drug.

    Args:
        drug_name: Canonical drug name to look up.

    Returns:
        A list of `EvidenceItem`, each with `source_name`, `source_url`,
        `retrieved_at`, and a short excerpt. Returns an empty list
        (never raises) if every configured source times out or is
        unavailable; the caller marks `evidence_unavailable=True` in
        that case.

    Notes:
        openFDA responses are treated as supporting evidence only, per
        `03_Agent_Architecture.md` Section 9 — this function must never
        be the sole basis for a finding's severity.
    """
    settings = get_settings()
    timeout = settings.evidence_timeout_seconds
    retrieved_at = datetime.now(tz=timezone.utc).isoformat()

    params: dict = {"search": f"openfda.generic_name:{drug_name}", "limit": 1}
    if settings.openfda_api_key:
        params["api_key"] = settings.openfda_api_key

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(_OPENFDA_BASE, params=params)
            response.raise_for_status()
            data = response.json()

        results = data.get("results", [])
        if not results:
            return []

        label = results[0]
        excerpts: list[str] = []
        for field in ("warnings", "drug_interactions", "contraindications", "precautions"):
            texts = label.get(field, [])
            if texts:
                excerpts.append(texts[0][:400])

        excerpt = " | ".join(excerpts) if excerpts else "No structured label text available."
        source_url = (
            f"https://api.fda.gov/drug/label.json?search=openfda.generic_name:{drug_name}&limit=1"
        )
        return [
            {
                "source_name": "openFDA drug label",
                "source_url": source_url,
                "retrieved_at": retrieved_at,
                "excerpt": excerpt,
            }
        ]

    except httpx.TimeoutException:
        logger.warning("openFDA request timed out for drug '%s'", drug_name)
        return []
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "openFDA returned HTTP %s for drug '%s'", exc.response.status_code, drug_name
        )
        return []
    except Exception as exc:  # noqa: BLE001
        logger.warning("Evidence retrieval failed for '%s': %s", drug_name, exc)
        return []
