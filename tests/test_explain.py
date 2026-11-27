"""explain 동작 테스트: compare()(#21), 레이더 차트(#45), 해석 문장 render_card()(#22).
가짜 프로필과 직접 만든 result dict만 쓴다(실제 모델 없음)."""

from __future__ import annotations

import math

import numpy as np
import pytest
from matplotlib.figure import Figure

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


# --- 레이더 차트 (#45: direction은 0~1 방향 일관성) ---------------------------


def _radar_series(features: dict, profile: dict) -> tuple[list[str], list[float], list[float]]:
    fig = explain._radar(features, profile, "A")
    ax = fig.axes[0]
    labels = [t.get_text() for t in ax.get_xticklabels()]
    mine, theirs = (list(line.get_ydata())[:-1] for line in ax.lines[:2])  # 마지막 점은 닫기용
    return labels, mine, theirs


def test_radar_uses_direction_as_is():
    labels, mine, theirs = _radar_series(
        {"direction": 0.7, "edge_density": 0.3},
        {"direction": (0.25, 0.1), "edge_density": (0.5, 0.1)},
    )
    assert labels == ["선 밀도", "선 방향 일관성"]
    assert mine == pytest.approx([0.3, 0.7])
    assert theirs == pytest.approx([0.5, 0.25])


def test_radar_clips_out_of_range_values():
    _, mine, theirs = _radar_series(
        {"direction": 1.4, "edge_density": -0.2},
        {"direction": (-0.1, 0.1), "edge_density": (2.0, 0.1)},
    )
    assert mine == pytest.approx([0.0, 1.0])
    assert theirs == pytest.approx([1.0, 0.0])


def test_radar_skips_non_numeric_and_missing_features():
    labels, mine, _ = _radar_series(
        {"direction": 0.6, "palette": [[0, 0, 0]] * 5, "roughness": "x"},
        {"direction": (0.5, 0.1), "roughness": (0.5, 0.1), "contrast": (0.5, 0.1)},
    )
    assert labels == ["선 방향 일관성"]
    assert mine == pytest.approx([0.6])


# --- 해석 문장 (#22) -----------------------------------------------------------

TYPES = ["photo", "painting", "sketch"]
LEVELS = ["높음", "보통", "낮음"]
GOGH, MONET, PICASSO = "Vincent van Gogh", "Claude Monet", "Pablo Picasso"
KEYWORDS = [("두꺼운 붓 자국", 0.71), ("소용돌이치는 하늘", 0.64), ("선명한 원색", 0.58)]
TITLES = {
    "photo": "### 사진을 그림처럼 놓고 보면 이런 화가와 닮았어요",
    "painting": "### 이 그림은 이런 화가와 닮았어요",
    "sketch": "### 이 스케치의 선을 보면 이런 화가와 닮았어요",
}


def _card_result(
    input_type: str = "painting",
    level: str = "보통",
    gray: bool = False,
    keywords: list | None = None,
    clip_first: str = GOGH,
    cv_first: str = GOGH,
    why_top1: list | None = None,
) -> dict:
    """contracts/interfaces.md 형식의 render_card() 입력."""
    others = [a for a in (GOGH, MONET, PICASSO) if a not in (clip_first, cv_first)]
    profile = {f: (0.5, 0.1) for f in explain.FEATURE_KO}
    features = {f: 0.4 for f in explain.FEATURE_KO}
    features["palette"] = [[200, 120, 40]] * 5
    return {
        "input_type": input_type,
        "gray": gray,
        "top3": [(GOGH, 0.52), (MONET, 0.31), (PICASSO, 0.17)],
        "styles_top3": [("Post-Impressionism", 0.6), ("Impressionism", 0.3), ("Cubism", 0.1)],
        "p_clip_top": [(clip_first, 0.55)] + [(a, 0.2) for a in others][:2],
        "p_cv_top": [(cv_first, 0.47)] + [(a, 0.25) for a in others][:2],
        "confidence": {
            "level": level,
            "margin": 0.21,
            "entropy": 0.62,
            "jsd": 0.18,
            "max_sim": 0.83,
        },
        "keywords": KEYWORDS if keywords is None else keywords,
        "similar": [
            {"id": 101, "artist": GOGH, "style": "Post-Impressionism", "path": "x", "score": 0.83}
        ],
        "features": features,
        "top1_profile": profile,
        "comparison": {
            "why_top1": ["brightness", "contrast"] if why_top1 is None else why_top1,
            "toward_top2": ["edge_density"],
            "z": {"brightness": 0.3},
        },
    }


def _text(**kw) -> str:
    text, _ = explain.render_card(_card_result(**kw))
    return text


def _disagree_line(text: str) -> str:
    return next(line for line in text.splitlines() if line.startswith("분위기는"))


def test_level_text_has_nine_distinct_cells():
    assert set(explain.LEVEL_TEXT) == {(t, lv) for t in TYPES for lv in LEVELS}
    values = list(explain.LEVEL_TEXT.values())
    assert all(v.strip() for v in values)
    assert len(set(values)) == 9


@pytest.mark.parametrize("input_type", TYPES)
@pytest.mark.parametrize("level", LEVELS)
def test_card_uses_cell_text_and_type_title(input_type, level):
    text = _text(input_type=input_type, level=level)
    assert text.splitlines()[0] == TITLES[input_type]
    assert f"**신뢰 등급: {level}** — {explain.LEVEL_TEXT[(input_type, level)]}" in text


def test_nine_cards_differ_and_high_has_note():
    texts = {_text(input_type=t, level=lv) for t in TYPES for lv in LEVELS}
    assert len(texts) == 9
    for t in TYPES:
        high = _text(input_type=t, level="높음")
        assert f"**신뢰 등급: 높음** — {explain.LEVEL_TEXT[(t, '높음')]}" in high


@pytest.mark.parametrize("gray", [True, False])
def test_low_shows_two_views_instead_of_top3(gray):
    text = _text(input_type="sketch", level="낮음", gray=gray, cv_first=MONET)
    lines = text.splitlines()
    assert not any(line.startswith(("1. ", "2. ", "3. ")) for line in lines)
    assert explain.LOW_TAIL.strip() in text
    assert any(line.startswith("- 소재·분위기·양식(CLIP): ") for line in lines)
    if gray:
        assert any(line.startswith("- 선(OpenCV): ") for line in lines)
        assert "색·선(OpenCV)" not in text
    else:
        assert any(line.startswith("- 색·선(OpenCV): ") for line in lines)


def test_out_of_contract_values_use_defaults():
    text, fig = explain.render_card(_card_result(input_type="unknown", level="?"))
    assert isinstance(text, str) and isinstance(fig, Figure)
    assert text.splitlines()[0] == "### 이 이미지는 이런 화가와 닮았어요"
    assert f"**신뢰 등급: ?** — {explain.LEVEL_TEXT[('painting', '보통')]}" in text
    assert f"1. **{GOGH}** — 52%" in text  # 보통처럼 Top 3를 보여준다


@pytest.mark.parametrize("input_type", TYPES)
@pytest.mark.parametrize("level", LEVELS)
def test_gray_disagreement_has_no_color(input_type, level):
    text = _text(input_type=input_type, level=level, gray=True, clip_first=GOGH, cv_first=MONET)
    line = _disagree_line(text)
    assert "색" not in line
    assert line == f"분위기는 **{GOGH}**, 선은 **{MONET}** 쪽에 가까워요."
    assert text.splitlines()[0] == TITLES[input_type]  # 제목은 gray와 상관없이 input_type


def test_color_disagreement_mentions_color_and_line():
    line = _disagree_line(_text(gray=False, clip_first=GOGH, cv_first=MONET))
    assert line == f"분위기는 **{GOGH}**, 색감·선은 **{MONET}** 쪽에 가까워요."


def test_no_disagreement_line_when_views_agree():
    assert not any(line.startswith("분위기는") for line in _text().splitlines())


@pytest.mark.parametrize(
    ("keywords", "expected"),
    [
        (KEYWORDS, "두꺼운 붓 자국, 소용돌이치는 하늘, 선명한 원색이 두드러져요."),
        ([("부드러운 빛", 0.7), ("정물", 0.5)], "부드러운 빛, 정물이 두드러져요."),
        ([("소용돌이치는 하늘", 0.9)], "소용돌이치는 하늘이 두드러져요."),
        ([("두꺼운 붓 자국", 0.9), ("밝은 색조", 0.4)], "두꺼운 붓 자국, 밝은 색조가 두드러져요."),
    ],
)
def test_keywords_as_sentence_without_scores(keywords, expected):
    text = _text(keywords=keywords)
    assert f"**CLIP이 본 특징**: {expected}" in text
    for _, score in keywords:
        assert f"{score:.2f}" not in text


def test_empty_keywords_drop_line():
    text, fig = explain.render_card(_card_result(keywords=[]))
    assert "CLIP이 본 특징" not in text and "두드러져요" not in text
    assert isinstance(fig, Figure)


@pytest.mark.parametrize(
    ("word", "pair", "expected"),
    [
        ("밝기", "이/가", "밝기가"),
        ("선 방향 일관성", "이/가", "선 방향 일관성이"),
        ("정물", "이/가", "정물이"),
        ("부드러운 빛", "이/가", "부드러운 빛이"),
        ("대비", "은/는", "대비는"),
        ("채도", "과/와", "채도와"),
        ("색온도", "을/를", "색온도를"),
        ("직선 비율", "은/는", "직선 비율은"),
        ("거칠기", "을/를", "거칠기를"),
        ("윤곽선 길이", "과/와", "윤곽선 길이와"),
        ("선 밀도", "을/를", "선 밀도를"),
        ("색 다양성", "과/와", "색 다양성과"),
        ("Monet", "이/가", "Monet가"),
        ("Picasso", "은/는", "Picasso는"),
        ("3", "을/를", "3를"),
        ("", "이/가", "가"),
    ],
)
def test_josa(word, pair, expected):
    assert explain._josa(word, pair) == expected


@pytest.mark.parametrize(
    ("why", "expected"),
    [
        (["brightness", "contrast"], "밝기, 대비가"),
        (["direction"], "선 방향 일관성이"),
        (["edge_density", "color_diversity"], "선 밀도, 색 다양성이"),
    ],
)
def test_contrast_sentence_uses_josa(why, expected):
    text = _text(why_top1=why)
    assert "이(가)" not in text and "(가)" not in text
    assert f"**{GOGH}인 이유**: {expected} {GOGH} 평균에 더 가까워요." in text


def test_existing_parts_kept_and_deterministic():
    result = _card_result(level="보통", clip_first=GOGH, cv_first=MONET)
    text, fig = explain.render_card(result)
    again, _ = explain.render_card(result)
    assert text == again
    assert isinstance(fig, Figure)
    assert f"1. **{GOGH}** — 52%" in text
    assert f"2. **{MONET}** — 31%" in text
    assert f"3. **{PICASSO}** — 17%" in text
    assert "**닮은 화풍**: Post-Impressionism 60%, Impressionism 30%, Cubism 10%" in text
    assert f"**비슷한 명화**: {GOGH} #101 (0.83)" in text
    assert f"**{MONET} 느낌이 나는 부분**: 선 밀도" in text
    assert "1·2위 차이 0.21 · 엔트로피 0.62 · 관점 차이(JSD) 0.18 · 데이터셋 유사도 0.83" in text
    assert explain.DISCLAIMER in text
