import re
import unicodedata
from dataclasses import dataclass
from statistics import median
from uuid import UUID

import numpy as np
from numpy.typing import NDArray
from scipy.sparse import hstack
from sklearn.cluster import AgglomerativeClustering
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import (
    Cluster,
    ClusterKeyword,
    DiscoveryRun,
    KeywordAnalysis,
    KeywordObservation,
)

CLUSTERING_VERSION = "tfidf-agglomerative-v1"
_NON_WORD = re.compile(r"[^\w]+", flags=re.UNICODE)
_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class TextClusteringResult:
    labels: tuple[int, ...]
    similarities: NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class ClusteringRunResult:
    run_id: UUID
    cluster_count: int
    keyword_count: int
    similarity_threshold: float
    algorithm_version: str = CLUSTERING_VERSION


def normalize_cluster_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return _WHITESPACE.sub(" ", _NON_WORD.sub(" ", normalized)).strip()


def cluster_texts(texts: list[str], similarity_threshold: float) -> TextClusteringResult:
    if not 0 <= similarity_threshold <= 1:
        raise ValueError("Similarity threshold must be between 0 and 1.")
    normalized = [normalize_cluster_text(text) for text in texts]
    if not normalized:
        return TextClusteringResult((), np.empty((0, 0), dtype=np.float64))
    if len(normalized) == 1:
        return TextClusteringResult((0,), np.ones((1, 1), dtype=np.float64))

    word_features = TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 2),
        token_pattern=r"(?u)\b\w+\b",
        sublinear_tf=True,
    ).fit_transform(normalized)
    char_features = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        sublinear_tf=True,
    ).fit_transform(normalized)
    features = hstack((word_features * 0.65, char_features * 0.35), format="csr")
    similarities = np.asarray(cosine_similarity(features), dtype=np.float64)
    distances = np.clip(1.0 - similarities, 0.0, 1.0)
    np.fill_diagonal(distances, 0.0)
    labels = AgglomerativeClustering(
        n_clusters=None,
        metric="precomputed",
        linkage="average",
        distance_threshold=1.0 - similarity_threshold,
    ).fit_predict(distances)
    return TextClusteringResult(tuple(int(label) for label in labels), similarities)


def _midpoint(observation: KeywordObservation) -> float | None:
    bids = [
        float(value)
        for value in (observation.low_top_page_bid, observation.high_top_page_bid)
        if value is not None
    ]
    return sum(bids) / len(bids) if bids else None


def _representative(
    indices: list[int],
    texts: list[str],
    similarities: NDArray[np.float64],
) -> int:
    return sorted(
        indices,
        key=lambda index: (
            -float(np.mean(similarities[index, indices])),
            normalize_cluster_text(texts[index]),
        ),
    )[0]


def cluster_discovery_run(
    session: Session,
    run_id: UUID,
    *,
    similarity_threshold: float,
) -> ClusteringRunResult:
    run = session.get(DiscoveryRun, run_id)
    if run is None:
        raise LookupError(f"Discovery run {run_id} was not found.")

    observations = session.scalars(
        select(KeywordObservation)
        .options(joinedload(KeywordObservation.keyword))
        .where(KeywordObservation.discovery_run_id == run_id)
        .order_by(KeywordObservation.keyword_id)
    ).unique().all()
    texts = [observation.keyword.display_text for observation in observations]
    clustering = cluster_texts(texts, similarity_threshold)
    analyses = {
        analysis.keyword_id: analysis
        for analysis in session.scalars(
            select(KeywordAnalysis).where(KeywordAnalysis.discovery_run_id == run_id)
        ).all()
    }

    for cluster in session.scalars(
        select(Cluster).where(Cluster.discovery_run_id == run_id)
    ).all():
        session.delete(cluster)
    session.flush()

    indices_by_label: dict[int, list[int]] = {}
    for index, label in enumerate(clustering.labels):
        indices_by_label.setdefault(label, []).append(index)

    for indices in sorted(indices_by_label.values(), key=lambda group: min(group)):
        representative = _representative(indices, texts, clustering.similarities)
        member_observations = [observations[index] for index in indices]
        volumes = [
            observation.avg_monthly_searches
            for observation in member_observations
            if observation.avg_monthly_searches is not None
        ]
        competitions = [
            float(observation.competition_index)
            for observation in member_observations
            if observation.competition_index is not None
        ]
        bids = [
            bid
            for observation in member_observations
            if (bid := _midpoint(observation)) is not None
        ]
        growth_with_weight = [
            (analysis.growth_3m, max(observation.avg_monthly_searches or 0, 1))
            for observation in member_observations
            if (analysis := analyses.get(observation.keyword_id)) is not None
            and analysis.growth_3m is not None
        ]
        growth_weight = sum(weight for _, weight in growth_with_weight)
        weighted_growth = (
            sum(growth * weight for growth, weight in growth_with_weight) / growth_weight
            if growth_weight
            else None
        )
        cluster = Cluster(
            discovery_run_id=run_id,
            name=texts[representative],
            description=(
                f"{len(indices)} semantically related keyword"
                f"{'s' if len(indices) != 1 else ''} grouped by TF-IDF similarity."
            ),
            algorithm_version=CLUSTERING_VERSION,
            similarity_threshold=similarity_threshold,
            total_volume=sum(volumes),
            median_volume=median(volumes) if volumes else None,
            weighted_growth=weighted_growth,
            median_competition=median(competitions) if competitions else None,
            median_bid=median(bids) if bids else None,
            keyword_count=len(indices),
            keyword_links=[
                ClusterKeyword(
                    keyword_id=observations[index].keyword_id,
                    similarity=float(
                        np.clip(clustering.similarities[index, representative], 0.0, 1.0)
                    ),
                )
                for index in indices
            ],
        )
        session.add(cluster)

    session.flush()
    return ClusteringRunResult(
        run_id=run_id,
        cluster_count=len(indices_by_label),
        keyword_count=len(observations),
        similarity_threshold=similarity_threshold,
    )
