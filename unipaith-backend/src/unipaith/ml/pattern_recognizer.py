"""Pattern recognition via HDBSCAN clustering + association rules.

Discovers admission archetypes ("high-GPA research STEM applicant") and
maps profile patterns to program success. Uses HDBSCAN for density-based
clustering on student feature vectors, and mlxtend for association rule
mining on successful student-program pairings.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from uuid import UUID

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.matching import StudentFeature
from unipaith.models.ml_loop import OutcomeRecord

logger = logging.getLogger("unipaith.ml.pattern_recognizer")

POSITIVE_OUTCOMES = {"admitted", "enrolled"}
FEATURE_KEYS = [
    "normalized_gpa",
    "work_experience_years",
    "research_count",
    "leadership_count",
    "publication_count",
    "total_activities",
    "test_score_avg",
    "highest_degree_level",
]


class PatternRecognizer:
    """Discovers admission archetypes and pattern-to-program success mappings."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._cluster_labels: dict[UUID, int] = {}
        self._cluster_centers: dict[int, np.ndarray] = {}
        self._cluster_program_affinities: dict[int, dict[UUID, float]] = {}
        self._association_rules: list[dict] = []

    async def train(self, min_cluster_size: int = 5) -> dict:
        """Train clustering + association rules on student features and outcomes."""
        features, student_ids = await self._load_student_features()
        if len(features) < min_cluster_size * 2:
            return {"status": "skipped", "reason": "insufficient_data", "count": len(features)}

        cluster_result = self._run_clustering(features, student_ids, min_cluster_size)
        await self._mine_association_rules(student_ids)

        return {
            "status": "trained",
            "students": len(student_ids),
            "clusters": cluster_result.get("n_clusters", 0),
            "noise_points": cluster_result.get("noise", 0),
            "rules_found": len(self._association_rules),
        }

    def get_pattern_score(self, student_id: UUID, program_id: UUID) -> float:
        """Get pattern-affinity score for a student-program pair."""
        cluster = self._cluster_labels.get(student_id)
        if cluster is None or cluster == -1:
            return 0.5

        affinities = self._cluster_program_affinities.get(cluster, {})
        return affinities.get(program_id, 0.5)

    def get_pattern_scores_batch(
        self,
        student_id: UUID,
        program_ids: list[UUID],
    ) -> dict[UUID, float]:
        """Get pattern scores for multiple programs."""
        return {pid: self.get_pattern_score(student_id, pid) for pid in program_ids}

    def get_student_archetype(self, student_id: UUID) -> dict | None:
        """Get the archetype label and center for a student."""
        cluster = self._cluster_labels.get(student_id)
        if cluster is None or cluster == -1:
            return None
        center = self._cluster_centers.get(cluster)
        return {
            "cluster_id": cluster,
            "center": center.tolist() if center is not None else None,
            "top_programs": sorted(
                self._cluster_program_affinities.get(cluster, {}).items(),
                key=lambda x: x[1],
                reverse=True,
            )[:10],
        }

    def _run_clustering(
        self,
        features: np.ndarray,
        student_ids: list[UUID],
        min_cluster_size: int,
    ) -> dict:
        """Run HDBSCAN clustering on student features."""
        try:
            from hdbscan import HDBSCAN
            from sklearn.preprocessing import StandardScaler

            scaled = StandardScaler().fit_transform(features)
            clusterer = HDBSCAN(
                min_cluster_size=min_cluster_size,
                min_samples=max(2, min_cluster_size // 2),
                metric="euclidean",
            )
            labels = clusterer.fit_predict(scaled)

            for sid, label in zip(student_ids, labels):
                self._cluster_labels[sid] = int(label)

            unique_labels = set(labels) - {-1}
            for label in unique_labels:
                mask = labels == label
                self._cluster_centers[int(label)] = features[mask].mean(axis=0)

            noise = int(np.sum(labels == -1))
            logger.info(
                "HDBSCAN: %d clusters, %d noise points from %d students",
                len(unique_labels),
                noise,
                len(student_ids),
            )
            return {"n_clusters": len(unique_labels), "noise": noise}
        except Exception:
            logger.exception("Clustering failed")
            return {"n_clusters": 0, "noise": len(student_ids)}

    async def _mine_association_rules(self, student_ids: list[UUID]) -> dict:
        """Mine association rules: what clusters succeed at which programs."""
        outcomes_result = await self.db.execute(
            select(OutcomeRecord).where(
                OutcomeRecord.actual_outcome.in_(list(POSITIVE_OUTCOMES)),
            )
        )
        outcomes = outcomes_result.scalars().all()

        cluster_program_counts: dict[int, dict[UUID, int]] = defaultdict(lambda: defaultdict(int))
        cluster_total: dict[int, int] = defaultdict(int)

        for outcome in outcomes:
            cluster = self._cluster_labels.get(outcome.student_id)
            if cluster is None or cluster == -1:
                continue
            cluster_program_counts[cluster][outcome.program_id] += 1
            cluster_total[cluster] += 1

        for cluster, program_counts in cluster_program_counts.items():
            total = max(cluster_total[cluster], 1)
            affinities: dict[UUID, float] = {}
            for pid, count in program_counts.items():
                affinities[pid] = min(1.0, count / total + 0.3)
            self._cluster_program_affinities[cluster] = affinities

        try:
            self._build_mlxtend_rules(outcomes)
        except Exception:
            logger.debug("mlxtend rules skipped (insufficient data or import)")

        return {"rules": len(self._association_rules)}

    def _build_mlxtend_rules(self, outcomes: list) -> None:
        """Build association rules using mlxtend for deeper pattern mining."""
        import pandas as pd
        from mlxtend.frequent_patterns import apriori, association_rules

        transactions: list[dict[str, bool]] = []
        for outcome in outcomes:
            cluster = self._cluster_labels.get(outcome.student_id, -1)
            if cluster == -1:
                continue
            item = {
                f"cluster_{cluster}": True,
                f"program_{outcome.program_id}": True,
                f"outcome_{outcome.actual_outcome}": True,
            }
            transactions.append(item)

        if len(transactions) < 10:
            return

        df = pd.DataFrame(transactions).fillna(False)
        frequent = apriori(df, min_support=0.05, use_colnames=True)
        if frequent.empty:
            return

        rules = association_rules(frequent, metric="confidence", min_threshold=0.3)
        self._association_rules = rules.to_dict("records")

    async def _load_student_features(self) -> tuple[np.ndarray, list[UUID]]:
        """Load student feature vectors for clustering."""
        result = await self.db.execute(select(StudentFeature))
        features_list = []
        student_ids = []

        for sf in result.scalars().all():
            data = sf.feature_data or {}
            structured = data.get("structured", {})
            vec = [float(structured.get(k, 0) or 0) for k in FEATURE_KEYS]
            features_list.append(vec)
            student_ids.append(sf.student_id)

        if not features_list:
            return np.array([]), []

        return np.array(features_list), student_ids
