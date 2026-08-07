"""Scoring schemes and the spaced-repetition schedule (BUILD-SPEC section 6).

Four schemes are supported, named exactly as they are stored in
``sessions.scoring``:

``accuracy``
    Flat award — 10 for a correct answer, 0 for a wrong one.
``speed``
    Rewards fast recall: ``max(2, 20 - latency_ms // 250)``.
``streak``
    Rewards unbroken runs: ``10 * min(streak, 10)``.
``srs``
    Rewards maturity: ``10 + 2 * reps_bonus``, and the character's review
    schedule is advanced by :func:`next_review`.

Both functions here are pure: they never touch the database. ``session.py``
owns the persistence side.
"""

from __future__ import annotations

__all__ = [
    "BASE_AWARD",
    "MAX_REPS_BONUS",
    "MAX_STREAK_MULTIPLIER",
    "MIN_EASE",
    "SCHEMES",
    "SPEED_MAX",
    "SPEED_MIN",
    "SPEED_MS_PER_POINT",
    "STARTING_EASE",
    "next_review",
    "score_attempt",
    "validate_scheme",
]

#: The only valid values for ``sessions.scoring``.
SCHEMES: tuple[str, ...] = ("accuracy", "speed", "streak", "srs")

#: Award for a correct answer under ``accuracy``; also the neutral award used
#: by ``speed`` when latency was not measured (it equals a 2.5 s answer).
BASE_AWARD = 10

#: A skip is not neutral. Passing on a card is an admission of not knowing it,
#: and costing a point stops skipping from being a free way to protect a score.
SKIP_PENALTY = -1

SPEED_MAX = 20
SPEED_MIN = 2
SPEED_MS_PER_POINT = 250

#: ``streak`` stops compounding past ten in a row.
MAX_STREAK_MULTIPLIER = 10

#: ``srs`` stops compounding past five repetitions, capping the award at 20 —
#: the same ceiling ``speed`` has.
MAX_REPS_BONUS = 5

STARTING_EASE = 2.5
MIN_EASE = 1.3
_EASE_PENALTY = 0.2
_FIRST_INTERVAL_DAYS = 1.0
_SECOND_INTERVAL_DAYS = 6.0


def validate_scheme(scheme: str) -> str:
    """Return ``scheme`` unchanged, raising ``ValueError`` if it is not known."""
    if scheme not in SCHEMES:
        raise ValueError(
            f"unknown scoring scheme: {scheme!r} (expected one of {', '.join(SCHEMES)})"
        )
    return scheme


def score_attempt(
    scheme: str,
    *,
    correct: bool,
    latency_ms: int | None,
    streak: int,
    reps: int | None = None,
    skipped: bool = False,
) -> int:
    """Points awarded for a single answered card.

    Args:
        scheme: One of :data:`SCHEMES`.
        correct: Whether the learner got the card right. Every scheme awards 0
            for a wrong answer.
        latency_ms: Time taken to answer, in milliseconds. ``None`` means the
            client did not time the card; ``speed`` then falls back to
            :data:`BASE_AWARD`.
        streak: The learner's run of correct answers *including* this one.
        reps: The character's repetition count under ``srs`` after this
            review. Defaults to ``streak`` when the caller has no review state
            to hand, which keeps the documented four-argument call working.

    Returns:
        A non-negative point award.

    Raises:
        ValueError: If ``scheme`` is not one of :data:`SCHEMES`.
    """
    validate_scheme(scheme)
    if skipped:
        return SKIP_PENALTY
    if not correct:
        return 0

    if scheme == "accuracy":
        return BASE_AWARD

    if scheme == "speed":
        if latency_ms is None:
            return BASE_AWARD
        elapsed = max(0, int(latency_ms))
        return max(SPEED_MIN, SPEED_MAX - elapsed // SPEED_MS_PER_POINT)

    if scheme == "streak":
        run = max(0, int(streak))
        return BASE_AWARD * min(run, MAX_STREAK_MULTIPLIER)

    # srs
    maturity = streak if reps is None else reps
    reps_bonus = min(max(0, int(maturity)), MAX_REPS_BONUS)
    return BASE_AWARD + 2 * reps_bonus


def next_review(
    ease: float, interval_days: float, reps: int, correct: bool
) -> tuple[float, float, int]:
    """Advance an SM-2 style schedule by one review.

    Args:
        ease: The current ease factor (starts at :data:`STARTING_EASE`).
        interval_days: The interval that has just elapsed, in days.
        reps: Successful repetitions *before* this review.
        correct: Whether this review was answered correctly.

    Returns:
        ``(ease, interval_days, reps)`` after the review. A wrong answer resets
        the interval to 0 and the repetition count to 0, and drops the ease by
        0.2 with a floor of :data:`MIN_EASE`. A correct answer leaves the ease
        alone and schedules 1 day for the first repetition, 6 days for the
        second, and ``interval * ease`` thereafter.
    """
    current_ease = float(ease)
    current_interval = max(0.0, float(interval_days))
    current_reps = max(0, int(reps))

    if not correct:
        return max(MIN_EASE, current_ease - _EASE_PENALTY), 0.0, 0

    new_reps = current_reps + 1
    if new_reps == 1:
        new_interval = _FIRST_INTERVAL_DAYS
    elif new_reps == 2:
        new_interval = _SECOND_INTERVAL_DAYS
    else:
        new_interval = current_interval * current_ease
    return current_ease, new_interval, new_reps
