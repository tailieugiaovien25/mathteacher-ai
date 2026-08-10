from __future__ import annotations

from collections import defaultdict

from src.orchestrator_v2.contracts.recognition_evidence import (
    RecognitionEvidence,
)
from src.orchestrator_v2.contracts.recognition_result import (
    RecognitionCandidate,
    RecognitionResult,
    RecognitionStatus,
)
from src.orchestrator_v2.recognition.recognition_resolution_config import (
    RecognitionResolutionConfig,
)
from src.orchestrator_v2.recognition.recognition_resolution_policy import (
    RecognitionResolutionPolicy,
)


class DeterministicRecognitionResolutionPolicy(
    RecognitionResolutionPolicy
):
    """
    Deterministic Recognition Resolution Policy.

    Resolution rules:
    - Ignore evidence below minimum_authority.
    - Group evidence by candidate_data_type_id.
    - Candidate confidence is the maximum accepted confidence
      for that data_type_id.
    - Confidence and authority remain independent.
    - No valid candidate -> UNRESOLVED.
    - Best candidate below recognized threshold -> UNRESOLVED.
    - Two strongest candidates within ambiguity margin
      -> AMBIGUOUS.
    - Otherwise -> RECOGNIZED.

    This policy MUST NOT:
    - call RecognitionProvider;
    - access RecognitionProviderRegistry;
    - dispatch processors;
    - mutate input evidence;
    - create Data Types.
    """

    def __init__(
        self,
        config: RecognitionResolutionConfig,
    ) -> None:
        if config is None:
            raise ValueError(
                "config is required"
            )

        self._config = config

    def resolve(
        self,
        evidence: tuple[RecognitionEvidence, ...],
    ) -> RecognitionResult:
        """
        Resolve RecognitionEvidence into RecognitionResult.
        """

        candidate_confidences = (
            self._aggregate_candidates(
                evidence
            )
        )

        if not candidate_confidences:
            return self._unresolved_result()

        candidates = tuple(
            RecognitionCandidate(
                data_type_id=data_type_id,
                confidence=confidence,
            )
            for data_type_id, confidence
            in sorted(
                candidate_confidences.items(),
                key=lambda item: (
                    -item[1],
                    item[0],
                ),
            )
        )

        best_candidate = candidates[0]

        if (
            best_candidate.confidence
            < self._config
            .recognized_confidence_threshold
        ):
            return self._unresolved_result(
                candidates=candidates
            )

        if len(candidates) >= 2:
            second_candidate = candidates[1]

            difference = (
                best_candidate.confidence
                - second_candidate.confidence
            )

            if (
                second_candidate.confidence
                >= self._config
                .recognized_confidence_threshold
                and difference
                <= self._config.ambiguity_margin
            ):
                return RecognitionResult(
                    data_type_id=None,
                    confidence=(
                        best_candidate.confidence
                    ),
                    status=(
                        RecognitionStatus.AMBIGUOUS
                    ),
                    candidates=candidates,
                    metadata={
                        "policy": (
                            "deterministic"
                        ),
                        "reason": (
                            "candidate_conflict"
                        ),
                    },
                )

        return RecognitionResult(
            data_type_id=(
                best_candidate.data_type_id
            ),
            confidence=(
                best_candidate.confidence
            ),
            status=(
                RecognitionStatus.RECOGNIZED
            ),
            candidates=candidates,
            metadata={
                "policy": "deterministic",
                "reason": "clear_winner",
            },
        )

    def _aggregate_candidates(
        self,
        evidence: tuple[RecognitionEvidence, ...],
    ) -> dict[str, float]:
        """
        Aggregate accepted evidence by data type.

        Deterministic V1 rule:
        use the maximum confidence for each candidate.
        """

        grouped: dict[
            str,
            list[float],
        ] = defaultdict(list)

        for item in evidence:
            if (
                item.authority
                < self._config.minimum_authority
            ):
                continue

            grouped[
                item.candidate_data_type_id
            ].append(
                item.confidence
            )

        return {
            data_type_id: max(confidences)
            for data_type_id, confidences
            in grouped.items()
            if confidences
        }

    @staticmethod
    def _unresolved_result(
        *,
        candidates: tuple[
            RecognitionCandidate,
            ...
        ] = (),
    ) -> RecognitionResult:
        return RecognitionResult(
            data_type_id=None,
            confidence=0.0,
            status=RecognitionStatus.UNRESOLVED,
            candidates=candidates,
            metadata={
                "policy": "deterministic",
                "reason": "no_recognized_candidate",
            },
        )