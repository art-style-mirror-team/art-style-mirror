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


@pytest.mark.parametrize("gray_input", [True, False])
def test_analyze_drops_color_features_only_for_sketch(gray_input):
    import app
    from modules import features

    rng = np.random.default_rng(3)
    if gray_input:
        g = rng.integers(150, 256, size=(600, 400), dtype=np.uint8)
        img = np.stack([g, g, g], axis=-1)
    else:
        img = rng.integers(0, 256, size=(600, 400, 3), dtype=np.uint8)
    result = app.analyze(img)
    assert result["gray"] is gray_input
    used = set(result["comparison"]["z"])
    if gray_input:
        assert used and used <= set(features.LINE_FEATURES)
    else:
        assert used & set(features.COLOR_FEATURES)
    # 화면용 features는 그대로 11개 키를 유지한다
    assert "saturation" in result["features"]


def test_empty_features():
    out = explain.compare({}, PROFILES, "A", "B")
    assert out == {"why_top1": [], "toward_top2": [], "z": {}}


# --- build_view(): G안 화면용 데이터 (#37) ------------------------------------------------


def _result(gray: bool = False) -> dict:
    """app.analyze()로 만든 실제 형식의 result. 모델 함수는 conftest가 가짜로 바꿔 끼운다."""
    import app

    rng = np.random.default_rng(7)
    if gray:
        g = rng.integers(150, 256, size=(600, 400), dtype=np.uint8)
        img = np.stack([g, g, g], axis=-1)
    else:
        img = rng.integers(0, 256, size=(600, 400, 3), dtype=np.uint8)
    return app.analyze(img)


def _with_level(result: dict, level: str) -> dict:
    out = dict(result)
    out["confidence"] = {**result["confidence"], "level": level}
    return out


def test_build_view_mid_level_has_all_fields_and_is_json():
    import json

    result = _with_level(_result(), "보통")
    view = explain.build_view(result)
    assert set(view) == {
        "head", "level", "top3", "views", "low", "radar", "styles",
        "keywords", "metrics", "gray", "disclaimer", "source",
        "compare", "kind", "history_name",
    }  # fmt: skip
    json.dumps(view)  # 그대로 화면(JSON)으로 보낼 수 있어야 한다
    assert view["level"] == {"label": "보통", "bars": 2, "note": explain.LEVEL_NOTE["보통"]}
    assert view["low"] is None
    assert [t["rank"] for t in view["top3"]] == [1, 2, 3]
    assert [t["name_orig"] for t in view["top3"]] == [a for a, _ in result["top3"]]
    assert view["head"]["pct"] == round(result["top3"][0][1] * 100)
    assert view["head"]["intro"] == explain.TYPE_INTRO[result["input_type"]]
    assert len(view["radar"]["axes"]) == len(explain.FEATURE_KO)
    assert len(view["styles"]) == 3 and len(view["metrics"]) == 4
    assert view["disclaimer"] == explain.DISCLAIMER


def test_build_view_low_level_shows_both_views_separately():
    result = _with_level(_result(), "낮음")
    view = explain.build_view(result)
    assert view["level"]["bars"] == 1
    assert [x["name_orig"] for x in view["low"]["clip"]] == [a for a, _ in result["p_clip_top"]]
    assert [x["name_orig"] for x in view["low"]["cv"]] == [a for a, _ in result["p_cv_top"]]
    assert view["head"]["title"] == explain.LEVEL_NOTE["낮음"].rstrip(".")


def test_build_view_sketch_radar_uses_five_line_features():
    result = _result(gray=True)
    assert result["gray"] is True
    view = explain.build_view(result)
    keys = [a["key"] for a in view["radar"]["axes"]]
    assert keys == list(explain.LINE_FEATURES_FOR_RADAR)
    assert view["gray"] is True


def test_line_features_for_radar_match_features_module():
    from modules import features

    assert list(explain.LINE_FEATURES_FOR_RADAR) == list(features.LINE_FEATURES)


@pytest.mark.parametrize("same", [True, False])
def test_build_view_views_same_flag(same):
    result = dict(_result())
    first = result["p_clip_top"][0]
    other = ("Claude Monet", 0.5) if first[0] != "Claude Monet" else ("Raphael", 0.5)
    result["p_cv_top"] = [first if same else other, *result["p_cv_top"][1:]]
    view = explain.build_view(result)
    assert view["views"]["same"] is same
    assert view["views"]["clip"] == explain.ARTIST_KO[first[0]][1]


def test_build_view_unknown_artist_keeps_original_name():
    result = dict(_result())
    result["top3"] = [("Mystery Painter", 0.5), *result["top3"][1:]]
    view = explain.build_view(result)
    assert view["head"]["name"] == "Mystery Painter"
    assert view["top3"][0]["name"] == "Mystery Painter"
    assert all(a in explain.ARTIST_KO for a, _ in result["top3"][1:])
    assert view["top3"][1]["name"] == explain.ARTIST_KO[result["top3"][1][0]][1]


def test_build_view_radar_values_are_clipped():
    result = dict(_result())
    result["features"] = {**result["features"], "brightness": 1.7, "contrast": -0.4}
    profile = dict(result["top1_profile"])
    profile["saturation"] = (2.5, 0.1)
    result["top1_profile"] = profile
    axes = {a["key"]: a for a in explain.build_view(result)["radar"]["axes"]}
    assert axes["brightness"]["mine"] == 1.0
    assert axes["contrast"]["mine"] == 0.0
    assert axes["saturation"]["avg"] == 1.0
    assert all(0.0 <= a[k] <= 1.0 for a in axes.values() for k in ("mine", "avg"))


# --- build_view(result, works): 명화 비교·기록용 값 (#37 범위 추가) ---------------------------


def _work(result: dict, artist: str, wid: str = "7", score: float = 0.81, feats=None, **kw):
    return {
        "id": wid,
        "artist": artist,
        "style": "Post-Impressionism",
        "score": score,
        "top1_work": kw.get("top1_work", artist == result["top3"][0][0]),
        "image": kw.get("image"),
        "features": feats,
    }


def test_build_view_without_works_has_no_compare():
    result = _with_level(_result(), "보통")
    assert explain.build_view(result)["compare"] is None
    assert explain.build_view(result, [])["compare"] is None


def test_build_view_top1_work_title_and_fields():
    import json

    result = _with_level(_result(), "보통")
    top1 = result["top3"][0][0]
    short = explain.ARTIST_KO[top1][1]
    works = [
        _work(result, top1, "12", 0.814, image="data:image/jpeg;base64,AAAA"),
        _work(result, "Mystery Painter", "3", 0.7),
    ]
    cmp = explain.build_view(result, works)["compare"]
    json.dumps(cmp)
    assert cmp["eyebrow"] == f"1위 화가 {short}의 작품 중에서"
    assert cmp["title"] == "가장 닮은 명화예요"
    first, second = cmp["works"]
    assert first["label"] == f"{short} #12" and first["pct"] == 81
    assert first["style"] == "후기 인상주의" and first["image"].startswith("data:image/")
    # 1위 화가 작품이 아닌 명화는 "비슷한" 문구, 한글 이름표 밖 화가는 원래 이름
    assert second["title"] == "가장 비슷한 명화예요" and second["eyebrow"] == "화가와 상관없이 고른"
    assert second["short"] == "Mystery Painter" and second["image"] is None


def test_build_view_low_level_compare_title_is_similar():
    result = _with_level(_result(), "낮음")
    top1 = result["top3"][0][0]
    cmp = explain.build_view(result, [_work(result, top1, top1_work=True)])["compare"]
    assert cmp["title"] == "가장 비슷한 명화예요"
    assert cmp["works"][0]["top1_work"] is False


def test_build_view_work_without_features_hides_palette_and_radar():
    result = _with_level(_result(), "보통")
    work = _work(result, "Claude Monet", image="file:///etc/passwd")
    w = explain.build_view(result, [work])["compare"]["works"][0]
    assert w["palette"] is None and w["radar"] is None
    assert w["near"] == [] and w["far"] == []
    assert w["image"] is None  # data URL이 아니면 화면에 보내지 않는다


def test_build_view_palette_hex_and_near_far_by_difference():
    result = _with_level(_result(), "보통")
    view0 = explain.build_view(result)
    mine = {a["key"]: a["mine"] for a in view0["radar"]["axes"]}
    keys = list(mine)
    # 앞 두 축은 내 값과 같게(차이 0), 다음 두 축은 가장 멀게, 나머지는 조금 다르게
    feats = {k: min(1.0, mine[k] + 0.05) if mine[k] < 0.5 else mine[k] - 0.05 for k in keys}
    feats[keys[0]], feats[keys[1]] = mine[keys[0]], mine[keys[1]]
    feats[keys[2]] = 1.0 if mine[keys[2]] < 0.5 else 0.0
    feats[keys[3]] = 1.0 if mine[keys[3]] < 0.5 else 0.0
    if "direction" in feats:
        feats["direction"] = feats["direction"] * 180.0  # direction은 각도(0~180)로 넘어온다
    feats["palette"] = [[255, 0, 16], [0, 0, 0], [12, 34, 56], [255, 255, 255], [1, 2, 3]]
    w = explain.build_view(result, [_work(result, "Claude Monet", feats=feats)])["compare"]
    w = w["works"][0]
    assert w["palette"] == ["#ff0010", "#000000", "#0c2238", "#ffffff", "#010203"]
    assert set(w["near_keys"]) == {keys[0], keys[1]}
    assert set(w["far_keys"]) == {keys[2], keys[3]}
    assert w["near"] == [explain.FEATURE_KO[k] for k in w["near_keys"]]
    assert set(w["radar"]) == set(keys) and all(0.0 <= v <= 1.0 for v in w["radar"].values())
    cmp = explain.build_view(result, [_work(result, "Claude Monet", feats=feats)])["compare"]
    assert len(cmp["mine_palette"]) == 5
    assert all(c.startswith("#") and len(c) == 7 for c in cmp["mine_palette"])


@pytest.mark.parametrize(
    ("level", "gray", "input_type", "kind"),
    [
        ("보통", False, "photo", "사진"),
        ("높음", False, "painting", "그림"),
        ("낮음", True, "photo", "스케치"),
    ],
)
def test_build_view_kind_and_history_name(level, gray, input_type, kind):
    result = _with_level(_result(gray=gray), level)
    result["input_type"] = input_type
    view = explain.build_view(result)
    assert view["kind"] == kind
    if level == "낮음":
        assert view["history_name"] == "닮은 화가 없음"
    else:
        assert view["history_name"] == explain.ARTIST_KO[result["top3"][0][0]][0]
