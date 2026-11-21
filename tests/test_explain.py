"""explain.compare() 동작 테스트 (#21). 가짜 프로필만 쓴다."""

from __future__ import annotations

import math

import numpy as np
import pytest

from modules import explain

PROFILES = {
    "A": {
        "brightness": (0.8, 0.1),
        "contrast": (0.2, 0.1),
        "warmth": (0.5, 0.1),
        "edge_density": (0.3, 0.1),
    },
    "B": {
        "brightness": (0.2, 0.1),
        "contrast": (0.8, 0.1),
        "warmth": (0.5, 0.1),
        "edge_density": (0.7, 0.1),
    },
}


def test_why_and_toward_sorted_by_gap():
    feats = {"brightness": 0.75, "contrast": 0.7, "warmth": 0.5, "edge_density": 0.35}
    out = explain.compare(feats, PROFILES, "A", "B")
    # brightness: |z2|=5.5 - |z1|=0.5 → 5.0, edge_density: 3.5 - 0.5 → 3.0
    assert out["why_top1"] == ["brightness", "edge_density"]
    assert out["toward_top2"] == ["contrast"]
    assert out["z"]["brightness"] == pytest.approx(-0.5)
    assert out["z"]["contrast"] == pytest.approx(5.0)


def test_at_most_two_each():
    feats = {"brightness": 0.8, "contrast": 0.2, "warmth": 0.5, "edge_density": 0.3}
    out = explain.compare(feats, PROFILES, "A", "B")
    assert len(out["why_top1"]) <= 2 and len(out["toward_top2"]) <= 2
    assert out["why_top1"] == ["brightness", "contrast"]  # 동점(6.0)은 이름 순
    assert not set(out["why_top1"]) & set(out["toward_top2"])


def test_equal_distance_feature_goes_nowhere():
    out = explain.compare({"warmth": 0.9}, PROFILES, "A", "B")
    assert out["why_top1"] == [] and out["toward_top2"] == []
    assert out["z"] == {"warmth": pytest.approx(4.0)}


def test_same_artist_has_no_contrast():
    feats = {"brightness": 0.5, "contrast": 0.5}
    out = explain.compare(feats, PROFILES, "A", "A")
    assert out["why_top1"] == [] and out["toward_top2"] == []
    assert set(out["z"]) == {"brightness", "contrast"}


def test_skips_non_numeric_nan_and_missing():
    feats = {
        "brightness": float("nan"),
        "contrast": math.inf,
        "warmth": True,  # bool은 수로 보지 않는다
        "edge_density": 0.35,
        "palette": [[1, 2, 3]],
    }
    out = explain.compare(feats, PROFILES, "A", "B")
    assert set(out["z"]) == {"edge_density"}
    assert out["why_top1"] == ["edge_density"]


def test_accepts_numpy_numbers():
    feats = {"brightness": np.float32(0.75), "contrast": np.float64(0.7), "warmth": np.int64(1)}
    out = explain.compare(feats, PROFILES, "A", "B")
    assert set(out["z"]) == {"brightness", "contrast", "warmth"}
    assert all(type(v) is float for v in out["z"].values())


def test_zero_std_uses_eps():
    profiles = {"A": {"brightness": (0.5, 0.0)}, "B": {"brightness": (0.9, 0.0)}}
    out = explain.compare({"brightness": 0.51}, profiles, "A", "B")
    assert out["z"]["brightness"] == pytest.approx(0.01 / explain.EPS)
    assert out["why_top1"] == ["brightness"]


def test_skips_malformed_profile_values():
    profiles = {
        "A": {"brightness": (0.8, 0.1), "contrast": (0.2,), "warmth": (float("nan"), 0.1)},
        "B": {"brightness": (0.2, 0.1), "contrast": (0.8, 0.1), "warmth": (0.5, 0.1)},
    }
    out = explain.compare({"brightness": 0.7, "contrast": 0.5, "warmth": 0.5}, profiles, "A", "B")
    assert set(out["z"]) == {"brightness"}


def test_only_features_in_both_profiles():
    profiles = {"A": {"brightness": (0.8, 0.1), "contrast": (0.2, 0.1)}, "B": PROFILES["B"]}
    out = explain.compare({"brightness": 0.7, "contrast": 0.3, "warmth": 0.5}, profiles, "A", "B")
    assert set(out["z"]) == {"brightness", "contrast"}


def test_line_only_features_for_sketch():
    """app.analyze가 스케치에서 색 특징을 빼고 넘기면 선 특징만 대조한다."""
    feats = {"edge_density": 0.65}
    out = explain.compare(feats, PROFILES, "A", "B")
    assert set(out["z"]) == {"edge_density"}
    assert out["toward_top2"] == ["edge_density"]


def test_unknown_artist_raises():
    with pytest.raises(KeyError, match="Z"):
        explain.compare({"brightness": 0.5}, PROFILES, "A", "Z")


def test_empty_features():
    out = explain.compare({}, PROFILES, "A", "B")
    assert out == {"why_top1": [], "toward_top2": [], "z": {}}
