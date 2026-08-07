"""Scoring schemes and SM-2 scheduling.

These are pure functions with no I/O, so every case is asserted against an
exact expected value rather than a range.
"""

from __future__ import annotations

import pytest

from japanese_practice.scoring import (
    BASE_AWARD,
    MAX_REPS_BONUS,
    MAX_STREAK_MULTIPLIER,
    MIN_EASE,
    SPEED_MAX,
    SPEED_MIN,
    SPEED_MS_PER_POINT,
    next_review,
    score_attempt,
    validate_scheme,
)

SCHEMES = ("accuracy", "speed", "streak", "srs")


# -- validation ------------------------------------------------------------


def test_validate_scheme_accepts_known_schemes():
    for scheme in SCHEMES:
        assert validate_scheme(scheme) == scheme


def test_validate_scheme_rejects_unknown():
    with pytest.raises(ValueError, match="unknown scoring scheme"):
        validate_scheme("vibes")


@pytest.mark.parametrize("scheme", SCHEMES)
def test_wrong_answer_scores_zero_under_every_scheme(scheme):
    """The one rule shared by all four schemes."""
    assert score_attempt(scheme, correct=False, latency_ms=500, streak=9) == 0


def test_unknown_scheme_raises_even_when_correct():
    with pytest.raises(ValueError):
        score_attempt("telepathy", correct=True, latency_ms=100, streak=1)


# -- accuracy --------------------------------------------------------------


def test_accuracy_is_flat_regardless_of_speed_or_streak():
    fast = score_attempt("accuracy", correct=True, latency_ms=1, streak=0)
    slow = score_attempt("accuracy", correct=True, latency_ms=99_999, streak=50)
    assert fast == slow == BASE_AWARD


# -- speed -----------------------------------------------------------------


@pytest.mark.parametrize(
    "latency_ms,expected",
    [
        (0, SPEED_MAX),  # instant answer, full marks
        (250, SPEED_MAX - 1),  # one bucket lost
        (1000, SPEED_MAX - 4),
        (2500, SPEED_MAX - 10),
        (100_000, SPEED_MIN),  # floored, never negative
    ],
)
def test_speed_award_decays_with_latency(latency_ms, expected):
    assert score_attempt("speed", correct=True, latency_ms=latency_ms, streak=0) == expected


def test_speed_falls_back_to_base_when_untimed():
    """A client that did not time the card must not be punished."""
    assert score_attempt("speed", correct=True, latency_ms=None, streak=0) == BASE_AWARD


def test_speed_never_drops_below_floor():
    for latency in (10_000, 50_000, 10**9):
        assert score_attempt("speed", correct=True, latency_ms=latency, streak=0) == SPEED_MIN


def test_speed_treats_negative_latency_as_instant():
    assert score_attempt("speed", correct=True, latency_ms=-500, streak=0) == SPEED_MAX


# -- streak ----------------------------------------------------------------


@pytest.mark.parametrize("streak,multiplier", [(1, 1), (5, 5), (10, 10), (99, 10)])
def test_streak_multiplies_then_caps(streak, multiplier):
    assert score_attempt("streak", correct=True, latency_ms=0, streak=streak) == (
        BASE_AWARD * multiplier
    )


def test_streak_cap_is_the_documented_constant():
    huge = score_attempt("streak", correct=True, latency_ms=0, streak=10_000)
    assert huge == BASE_AWARD * MAX_STREAK_MULTIPLIER


# -- srs -------------------------------------------------------------------


@pytest.mark.parametrize("reps,bonus", [(0, 0), (1, 1), (5, 5), (50, MAX_REPS_BONUS)])
def test_srs_award_grows_with_maturity_then_caps(reps, bonus):
    assert score_attempt("srs", correct=True, latency_ms=0, streak=0, reps=reps) == (
        BASE_AWARD + 2 * bonus
    )


def test_srs_falls_back_to_streak_when_reps_absent():
    """The four-argument call must keep working."""
    with_reps = score_attempt("srs", correct=True, latency_ms=0, streak=3, reps=3)
    without = score_attempt("srs", correct=True, latency_ms=0, streak=3)
    assert with_reps == without


# -- next_review: the correct path -----------------------------------------


def test_first_correct_review_schedules_one_day():
    ease, interval, reps = next_review(2.5, 0.0, 0, correct=True)
    assert (ease, interval, reps) == (2.5, 1.0, 1)


def test_second_correct_review_schedules_six_days():
    ease, interval, reps = next_review(2.5, 1.0, 1, correct=True)
    assert (ease, interval, reps) == (2.5, 6.0, 2)


def test_third_and_later_reviews_multiply_by_ease():
    ease, interval, reps = next_review(2.5, 6.0, 2, correct=True)
    assert reps == 3
    assert interval == pytest.approx(15.0)  # 6 * 2.5
    assert ease == 2.5  # a correct answer never moves ease


def test_intervals_compound_across_successive_reviews():
    ease, interval, reps = 2.5, 6.0, 2
    ease, interval, reps = next_review(ease, interval, reps, correct=True)  # 15
    ease, interval, reps = next_review(ease, interval, reps, correct=True)  # 37.5
    assert reps == 4
    assert interval == pytest.approx(37.5)


# -- next_review: the lapse path -------------------------------------------


def test_wrong_answer_resets_interval_and_reps():
    ease, interval, reps = next_review(2.5, 30.0, 7, correct=False)
    assert interval == 0.0
    assert reps == 0
    assert ease == pytest.approx(2.3)  # 2.5 - 0.2


def test_ease_floors_at_the_documented_minimum():
    ease = 1.4
    for _ in range(10):
        ease, _, _ = next_review(ease, 5.0, 3, correct=False)
    assert ease == pytest.approx(MIN_EASE)
    assert ease >= MIN_EASE


def test_lapse_then_recovery_restarts_the_ladder():
    """A lapsed card must re-earn its interval from one day, not resume at 30."""
    ease, interval, reps = next_review(2.5, 30.0, 7, correct=False)
    ease, interval, reps = next_review(ease, interval, reps, correct=True)
    assert (interval, reps) == (1.0, 1)


def test_negative_inputs_are_clamped_not_propagated():
    ease, interval, reps = next_review(2.5, -10.0, -3, correct=True)
    assert interval == 1.0
    assert reps == 1


def test_speed_bucket_constant_is_honoured():
    """Guards the documented 250ms-per-point relationship."""
    a = score_attempt("speed", correct=True, latency_ms=0, streak=0)
    b = score_attempt("speed", correct=True, latency_ms=SPEED_MS_PER_POINT, streak=0)
    assert a - b == 1
