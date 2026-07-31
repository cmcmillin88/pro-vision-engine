"""Validation rules for football pool coupons."""

from src.models.coupon import Coupon
from src.models.game_type import GameType


class CouponValidationError(ValueError):
    """Raised when a coupon fails validation."""


class CouponValidator:
    """Validates coupon structure and match numbering."""

    def validate(self, coupon: Coupon) -> None:
        """Validate a coupon and raise an error if it is invalid."""

        self._validate_coupon_type(coupon)
        self._validate_game_type(coupon)

        expected_match_count = coupon.expected_match_count

        if expected_match_count is None:
            raise CouponValidationError(
                "Expected match count could not be determined."
            )

        self._validate_match_count(
            coupon,
            expected_match_count,
        )
        self._validate_match_numbers(
            coupon,
            expected_match_count,
        )

    @staticmethod
    def _validate_coupon_type(coupon: Coupon) -> None:
        """Ensure that the supplied object is a Coupon."""

        if not isinstance(coupon, Coupon):
            raise TypeError("CouponValidator requires a Coupon object.")

    @staticmethod
    def _validate_game_type(coupon: Coupon) -> None:
        """Ensure that the coupon has a supported game type."""

        if coupon.game_type is GameType.UNKNOWN:
            raise CouponValidationError(
                "Coupon game type must be specified."
            )

    @staticmethod
    def _validate_match_count(
        coupon: Coupon,
        expected_match_count: int,
    ) -> None:
        """Ensure that the coupon contains the correct number of matches."""

        actual_match_count = len(coupon)

        if actual_match_count != expected_match_count:
            raise CouponValidationError(
                f"{coupon.game_type.display_name} requires exactly "
                f"{expected_match_count} matches, but the coupon "
                f"contains {actual_match_count}."
            )

    @staticmethod
    def _validate_match_numbers(
        coupon: Coupon,
        expected_match_count: int,
    ) -> None:
        """Ensure that match numbers are unique and correctly ordered."""

        match_numbers = [
            match.match_number
            for match in coupon.matches
        ]

        if len(match_numbers) != len(set(match_numbers)):
            raise CouponValidationError(
                "Match numbers must be unique."
            )

        expected_match_numbers = list(
            range(1, expected_match_count + 1)
        )

        if match_numbers != expected_match_numbers:
            raise CouponValidationError(
                "Match numbers must be sequential and ordered from "
                f"1 to {expected_match_count}."
            )