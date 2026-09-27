"""Drug catalogue lookup/search endpoints.

Imports/dependencies: fastapi, app.services.drug_catalog_service.

Public outputs: route handlers registered under `/api/v1/medications`.

    GET /api/v1/medications/search?q=... -> list[DrugSummary]
    GET /api/v1/medications/{drug_id}    -> DrugDetail
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.exceptions import DrugResolutionError
from app.db.session import get_db
from app.schemas.medication import DrugDetail, DrugSummary
from app.services import drug_catalog_service

router = APIRouter()


@router.get(
    "/medications/search",
    response_model=list[DrugSummary],
    summary="Search drug catalogue",
    description="Full-text search against canonical name, INN and trade name.",
)
def search_medications(
    q: str = Query(description="Search term; minimum 1 character"),
    db: Session = Depends(get_db),
) -> list[DrugSummary]:
    """Search the catalogue for drugs matching the query string.

    Args:
        q: Free-text search term.
        db: Injected database session.

    Returns:
        List of :class:`~app.schemas.medication.DrugSummary` ranked by
        relevance (exact canonical match first, then INN, then substring).

    Raises:
        HTTPException: 400 if the query is empty.
    """
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'q' must not be empty.")
    return drug_catalog_service.search_drugs(q, db)


@router.get(
    "/medications/{drug_id}",
    response_model=DrugDetail,
    summary="Get drug detail",
    description="Return canonical drug details including inventory status.",
)
def get_medication(
    drug_id: int,
    db: Session = Depends(get_db),
) -> DrugDetail:
    """Return full detail for a single drug by primary key.

    Args:
        drug_id: Database primary key of the medication.
        db: Injected database session.

    Returns:
        :class:`~app.schemas.medication.DrugDetail` with inventory status.

    Raises:
        HTTPException: 404 if no medication with ``drug_id`` exists.
    """
    try:
        return drug_catalog_service.get_drug_detail(drug_id, db)
    except DrugResolutionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
