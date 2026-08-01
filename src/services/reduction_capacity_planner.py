"""Exact preflight capacity planning for reduction frames."""

from src.models.reduction_capacity import (
    ReductionCapacityAssessment,
    ReductionCapacityPolicy,
)
from src.models.reduction_frame import ReductionFrame


class ReductionCapacityPlanner:
    """Creates exact capacity assessments before row materialization."""

    def __init__(
        self,
        policy: ReductionCapacityPolicy | None = None,
    ) -> None:
        """Store one reusable capacity policy."""

        if (
            policy is not None
            and not isinstance(
                policy,
                ReductionCapacityPolicy,
            )
        ):
            raise TypeError(
                "policy must be a ReductionCapacityPolicy or None."
            )

        self._policy = (
            policy
            if policy is not None
            else ReductionCapacityPolicy()
        )

    @property
    def policy(self) -> ReductionCapacityPolicy:
        """Return the active capacity policy."""

        return self._policy

    def assess(
        self,
        frame: ReductionFrame,
    ) -> ReductionCapacityAssessment:
        """Return one exact frame-capacity assessment."""

        if not isinstance(
            frame,
            ReductionFrame,
        ):
            raise TypeError(
                "ReductionCapacityPlanner requires "
                "a ReductionFrame."
            )

        return ReductionCapacityAssessment(
            frame=frame,
            policy=self._policy,
        )

    def require_materializable(
        self,
        frame: ReductionFrame,
    ) -> ReductionCapacityAssessment:
        """Return the assessment or raise when the frame is blocked."""

        assessment = self.assess(
            frame
        )
        assessment.require_materializable()

        return assessment