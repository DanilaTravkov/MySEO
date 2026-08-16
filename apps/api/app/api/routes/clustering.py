from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.analytics.service import latest_completed_run
from app.clustering.service import ClusteringRunResult, cluster_discovery_run
from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.models import Cluster, ClusterKeyword, DiscoveryRun

router = APIRouter(tags=["clustering"])


class ClusteringRunResponse(BaseModel):
    run_id: UUID
    cluster_count: int
    keyword_count: int
    similarity_threshold: float
    algorithm_version: str


class ClusterKeywordResponse(BaseModel):
    id: UUID
    keyword: str
    similarity: float | None


class ClusterResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    total_volume: int
    median_volume: float | None
    weighted_growth: float | None
    median_competition: float | None
    median_bid: float | None
    keyword_count: int
    similarity_threshold: float
    algorithm_version: str
    demand_label: str = "Aggregated search-demand signal"
    keywords: list[ClusterKeywordResponse]


def _run_response(result: ClusteringRunResult) -> ClusteringRunResponse:
    return ClusteringRunResponse(
        run_id=result.run_id,
        cluster_count=result.cluster_count,
        keyword_count=result.keyword_count,
        similarity_threshold=result.similarity_threshold,
        algorithm_version=result.algorithm_version,
    )


@router.post("/clustering/runs/{run_id}", response_model=ClusteringRunResponse)
def cluster_run(
    run_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    similarity_threshold: Annotated[float | None, Query(ge=0, le=1)] = None,
) -> ClusteringRunResponse:
    try:
        result = cluster_discovery_run(
            session,
            run_id,
            similarity_threshold=(
                similarity_threshold
                if similarity_threshold is not None
                else settings.clustering_similarity_threshold
            ),
        )
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    session.commit()
    return _run_response(result)


@router.get("/clusters", response_model=list[ClusterResponse])
def list_clusters(
    session: Annotated[Session, Depends(get_session)],
    run_id: Annotated[UUID | None, Query()] = None,
) -> list[ClusterResponse]:
    run = session.get(DiscoveryRun, run_id) if run_id else latest_completed_run(session)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No completed discovery run is available.",
        )
    clusters = session.scalars(
        select(Cluster)
        .options(selectinload(Cluster.keyword_links).joinedload(ClusterKeyword.keyword))
        .where(Cluster.discovery_run_id == run.id)
        .order_by(Cluster.total_volume.desc(), Cluster.name)
    ).unique().all()
    return [
        ClusterResponse(
            id=cluster.id,
            name=cluster.name,
            description=cluster.description,
            total_volume=cluster.total_volume,
            median_volume=cluster.median_volume,
            weighted_growth=cluster.weighted_growth,
            median_competition=cluster.median_competition,
            median_bid=cluster.median_bid,
            keyword_count=cluster.keyword_count,
            similarity_threshold=cluster.similarity_threshold,
            algorithm_version=cluster.algorithm_version,
            keywords=[
                ClusterKeywordResponse(
                    id=link.keyword_id,
                    keyword=link.keyword.display_text,
                    similarity=link.similarity,
                )
                for link in sorted(
                    cluster.keyword_links,
                    key=lambda item: (-(item.similarity or 0), item.keyword.display_text),
                )
            ],
        )
        for cluster in clusters
    ]
