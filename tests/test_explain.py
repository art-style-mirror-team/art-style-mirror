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
    note = explain.LEVEL_TEXT[(result["input_type"], "보통")]
    assert view["level"] == {"label": "보통", "bars": 2, "note": note}
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
    assert view["head"]["title"] == explain.LEVEL_TEXT[(result["input_type"], "낮음")].rstrip(".")
    assert view["level"]["note"] == ""  # 제목과 같은 문구를 배지에 되풀이하지 않는다


@pytest.mark.parametrize("input_type", ["photo", "painting", "sketch"])
@pytest.mark.parametrize("level", ["높음", "보통"])
def test_build_view_level_note_matches_card_text(input_type, level):
    """화면 배지 문구는 결과 카드(#22)의 9칸 문구와 같다."""
    result = _with_level(_result(), level)
    result["input_type"] = input_type
    view = explain.build_view(result)
    assert view["level"]["note"] == explain.LEVEL_TEXT[(input_type, level)]
    card, _ = explain.render_card(result)
    assert view["level"]["note"] in card


def test_build_view_level_note_uses_default_for_unknown_type():
    result = _with_level(_result(), "높음")
    result["input_type"] = "webtoon"
    view = explain.build_view(result)
    assert view["level"]["note"] == explain.LEVEL_TEXT[(explain.DEFAULT_TYPE, "높음")]


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
    feats["palette"] = [[255, 0, 16], [0, 0, 0], [12, 34, 56], [255, 255, 255], [1, 2, 3]]
    w = explain.build_view(result, [_work(result, "Claude Monet", feats=feats)])["compare"]
    w = w["works"][0]
    # 어두운 색 → 밝은 색 순으로 정렬된다
    assert w["palette"] == ["#000000", "#010203", "#0c2238", "#ff0010", "#ffffff"]
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


# PR #58 실제 색인(화가 23명, "Post_Impressionism"처럼 밑줄 쓴 화풍 16종)에 맞춘 화면 이름 (#37)
REAL_ARTISTS_23 = [
    "Albrecht Durer",
    "Boris Kustodiev",
    "Camille Pissarro",
    "Childe Hassam",
    "Claude Monet",
    "Edgar Degas",
    "Eugene Boudin",
    "Gustave Dore",
    "Ilya Repin",
    "Ivan Aivazovsky",
    "Ivan Shishkin",
    "John Singer Sargent",
    "Marc Chagall",
    "Martiros Saryan",
    "Nicholas Roerich",
    "Pablo Picasso",
    "Paul Cezanne",
    "Pierre-Auguste Renoir",
    "Pyotr Konchalovsky",
    "Raphael Kirchner",
    "Rembrandt",
    "Salvador Dali",
    "Vincent van Gogh",
]
REAL_STYLES_16 = [
    "Abstract_Expressionism",
    "Analytical_Cubism",
    "Art_Nouveau",
    "Baroque",
    "Cubism",
    "Expressionism",
    "Fauvism",
    "Impressionism",
    "Naive_Art_Primitivism",
    "Northern_Renaissance",
    "Pointillism",
    "Post_Impressionism",
    "Realism",
    "Romanticism",
    "Symbolism",
    "Synthetic_Cubism",
]


def test_artist_ko_covers_real_index_artists():
    missing = [a for a in REAL_ARTISTS_23 if a not in explain.ARTIST_KO]
    assert missing == []
    assert explain._artist_names("Pyotr Konchalovsky") == ("표트르 콘찰롭스키", "콘찰롭스키")


def test_style_name_covers_real_index_styles():
    names = {s: explain._style_name(s) for s in REAL_STYLES_16}
    untranslated = [s for s, ko in names.items() if not any("가" <= ch <= "힣" for ch in ko)]
    assert untranslated == []
    assert names["Post_Impressionism"] == "후기 인상주의"
    assert names["Art_Nouveau"] == "아르누보"


@pytest.mark.parametrize(
    "style",
    ["Post_Impressionism", "Post-Impressionism", "post impressionism", " POST_impressionism "],
)
def test_style_name_ignores_separators_and_case(style):
    assert explain._style_name(style) == "후기 인상주의"


@pytest.mark.parametrize(
    ("style", "shown"), [("Color_Field_Painting", "Color Field Painting"), ("", ""), (None, "")]
)
def test_style_name_unknown_replaces_underscores(style, shown):
    assert explain._style_name(style) == shown


def test_build_view_shows_korean_style_for_underscore_styles():
    result = dict(_result())
    result["styles_top3"] = [("Post_Impressionism", 0.5), ("Art_Nouveau", 0.3), ("Realism", 0.2)]
    result["similar"] = []
    view = explain.build_view(result)
    assert [s["name"] for s in view["styles"]] == ["후기 인상주의", "아르누보", "사실주의"]
    assert view["styles"][0]["name_orig"] == "Post_Impressionism"
    assert view["head"]["style"] == "후기 인상주의"


def test_palette_sorted_by_perceived_brightness_not_rgb_sum():
    # 파랑(0,0,255)은 RGB 합이 회색(64,64,64)보다 크지만 눈에는 더 어둡다.
    # 자홍(255,0,255)은 초록(0,255,0)보다 합이 크지만 더 어둡다.
    feats = {"palette": [[0, 255, 0], [255, 0, 255], [0, 0, 255], [64, 64, 64], [255, 255, 255]]}
    assert explain._palette_hex(feats) == ["#404040", "#0000ff", "#ff00ff", "#00ff00", "#ffffff"]


def test_mine_palette_is_sorted_dark_to_light():
    result = dict(_result())
    result["features"] = dict(result["features"])
    result["features"]["palette"] = [
        [250, 250, 250],
        [10, 10, 10],
        [128, 128, 128],
        [200, 200, 200],
        [60, 60, 60],
    ]
    work = {
        "id": "1",
        "artist": result["top3"][0][0],
        "style": "Impressionism",
        "score": 0.8,
        "image": None,
        "features": None,
        "top1_work": True,
    }
    view = explain.build_view(result, [work])
    lum = [explain._luminance(c) for c in view["compare"]["mine_palette"]]
    assert lum == sorted(lum)


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
