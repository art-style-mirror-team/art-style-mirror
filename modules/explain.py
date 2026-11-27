"""D — 신뢰도·UI·통합 (담당: 김현승).

1일차 스텁: contracts/interfaces.md와 똑같은 모양의 결과를 돌려준다.
지표(1·2위 차이, 정규화 엔트로피, JSD)는 plan.md 6.3 식대로 계산하고,
등급 경계값만 임시값을 쓴다(#24에서 검증셋으로 확정).
"""

from __future__ import annotations

import math
import numbers
import re
from functools import lru_cache

import numpy as np
from matplotlib import font_manager
from matplotlib.figure import Figure
from scipy.spatial.distance import jensenshannon

EPS = 0.01
GAP_TOL = 1e-9  # compare(): |z| 차이가 이보다 작으면 1·2위 어느 쪽에도 넣지 않는다(부동소수 잡음)

# 임시 등급 경계값 — #24에서 "높음 등급 정확도 80% 이상"이 되도록 검증셋으로 다시 정한다.
HIGH_MARGIN, HIGH_JSD_MAX, HIGH_SIM_MIN = 0.15, 0.30, 0.75
LOW_MARGIN, LOW_JSD_MIN, LOW_SIM_MAX = 0.05, 0.50, 0.50

FEATURE_KO = {
    "brightness": "밝기",
    "contrast": "대비",
    "saturation": "채도",
    "warmth": "색온도",
    "color_diversity": "색 다양성",
    "edge_density": "선 밀도",
    "direction": "선 방향",
    "straight_ratio": "직선 비율",
    "roughness": "거칠기",
    "stroke_length": "윤곽선 길이",
}
TYPE_INTRO = {
    "photo": "사진을 그림처럼 놓고 보면",
    "painting": "이 그림은",
    "sketch": "이 스케치의 선을 보면",
}
LEVEL_NOTE = {
    "높음": "",
    "보통": "애매한 부분이 있어요.",
    "낮음": "뚜렷하게 닮은 화가가 없어요.",
}
DISCLAIMER = "픽셀 수치 기반의 통계적 해석이며 미술사적 평가가 아닙니다."

# 화면용 화가 한글 이름: 원래 이름 → (전체 이름, 짧은 이름). #3(PR #58)에서 확정한 화가 23명과
# 1일차 스텁의 24명을 모두 담는다. 표에 없는 화가는 원래 이름을 그대로 쓴다.
ARTIST_KO = {
    "Boris Kustodiev": ("보리스 쿠스토디예프", "쿠스토디예프"),
    "Childe Hassam": ("차일드 하삼", "하삼"),
    "Eugene Boudin": ("외젠 부댕", "부댕"),
    "Gustave Dore": ("귀스타브 도레", "도레"),
    "Ilya Repin": ("일리야 레핀", "레핀"),
    "John Singer Sargent": ("존 싱어 사전트", "사전트"),
    "Marc Chagall": ("마르크 샤갈", "샤갈"),
    "Martiros Saryan": ("마르티로스 사리안", "사리안"),
    "Nicholas Roerich": ("니콜라스 레리흐", "레리흐"),
    "Pyotr Konchalovsky": ("표트르 콘찰롭스키", "콘찰롭스키"),
    "Raphael Kirchner": ("라파엘 키르히너", "키르히너"),
    "Vincent van Gogh": ("빈센트 반 고흐", "반 고흐"),
    "Claude Monet": ("클로드 모네", "모네"),
    "Pierre-Auguste Renoir": ("피에르오귀스트 르누아르", "르누아르"),
    "Paul Cezanne": ("폴 세잔", "세잔"),
    "Paul Gauguin": ("폴 고갱", "고갱"),
    "Edgar Degas": ("에드가 드가", "드가"),
    "Camille Pissarro": ("카미유 피사로", "피사로"),
    "Pablo Picasso": ("파블로 피카소", "피카소"),
    "Henri Matisse": ("앙리 마티스", "마티스"),
    "Wassily Kandinsky": ("바실리 칸딘스키", "칸딘스키"),
    "Piet Mondrian": ("피트 몬드리안", "몬드리안"),
    "Salvador Dali": ("살바도르 달리", "달리"),
    "Rene Magritte": ("르네 마그리트", "마그리트"),
    "Gustav Klimt": ("구스타프 클림트", "클림트"),
    "Edvard Munch": ("에드바르 뭉크", "뭉크"),
    "Rembrandt": ("렘브란트", "렘브란트"),
    "Caravaggio": ("카라바조", "카라바조"),
    "Albrecht Durer": ("알브레히트 뒤러", "뒤러"),
    "Sandro Botticelli": ("산드로 보티첼리", "보티첼리"),
    "Raphael": ("라파엘로", "라파엘로"),
    "Katsushika Hokusai": ("가쓰시카 호쿠사이", "호쿠사이"),
    "Andy Warhol": ("앤디 워홀", "워홀"),
    "Ivan Aivazovsky": ("이반 아이바좁스키", "아이바좁스키"),
    "Ivan Shishkin": ("이반 시시킨", "시시킨"),
}
# 화면용 화풍 한글 이름. 실제 색인(meta.csv)은 "Post_Impressionism"처럼 밑줄을 쓰므로 찾을 때는
# _style_name()이 공백·하이픈·밑줄·대소문자 차이를 무시한다. 표에 없으면 밑줄을 공백으로 바꿔 쓴다.
STYLE_KO = {
    "Symbolism": "상징주의",
    "Pointillism": "점묘주의",
    "Naive Art Primitivism": "나이브 아트",
    "Analytical Cubism": "분석적 입체주의",
    "Synthetic Cubism": "종합적 입체주의",
    "Post-Impressionism": "후기 인상주의",
    "Impressionism": "인상주의",
    "Cubism": "입체주의",
    "Fauvism": "야수주의",
    "Abstract Expressionism": "추상 표현주의",
    "Minimalism": "미니멀리즘",
    "Surrealism": "초현실주의",
    "Art Nouveau": "아르누보",
    "Expressionism": "표현주의",
    "Baroque": "바로크",
    "Northern Renaissance": "북유럽 르네상스",
    "Early Renaissance": "초기 르네상스",
    "High Renaissance": "전성기 르네상스",
    "Ukiyo-e": "우키요에",
    "Pop Art": "팝 아트",
    "Romanticism": "낭만주의",
    "Realism": "사실주의",
}
# 스케치 레이더에 쓰는 선 특징 5개. features.LINE_FEATURES와 같아야 한다(explain은 다른 모듈을
# import하지 않으므로 여기에 따로 둔다. app.analyze도 스케치에서 이 5개만 대조한다).
LINE_FEATURES_FOR_RADAR = (
    "edge_density",
    "direction",
    "straight_ratio",
    "roughness",
    "stroke_length",
)
LEVEL_BARS = {"높음": 3, "보통": 2, "낮음": 1}
SOURCE_NOTE = "명화 데이터는 WikiArt(비상업 연구용)예요."
# 기록·명화 페이지에 보이는 입력 종류(흑백이면 스케치). 값은 기록 화면의 종류 칩과 같다.
KIND_KO = {"photo": "사진", "painting": "그림", "sketch": "스케치"}
KIND_NOTE = {"사진": "사진으로 인식", "그림": "그림으로 인식", "스케치": "스케치로 인식"}
NO_MATCH_NAME = "닮은 화가 없음"
PALETTE_LEN = 5
_KO_FONT_CANDIDATES = [
    "Malgun Gothic",
    "AppleGothic",
    "NanumGothic",
    "Noto Sans CJK KR",
    "Noto Sans KR",
]


def _ranked(p) -> list[tuple]:
    items = p.items() if isinstance(p, dict) else p
    return sorted(((str(a), float(v)) for a, v in items), key=lambda x: -x[1])


def _normalized_entropy(ranked: list[tuple], K: int) -> float:
    """H = −Σ p log p / log K. fuse()가 Top 3만 주므로 나머지 확률은 남은 화가에 고르게 나눈다고 본다."""
    if K <= 1:
        return 0.0
    probs = [p for _, p in ranked if p > 0]
    h = -sum(p * math.log(p) for p in probs)
    rest, n_rest = max(0.0, 1.0 - sum(probs)), K - len(probs)
    if rest > 1e-12 and n_rest > 0:
        h -= rest * math.log(rest / n_rest)
    return float(min(1.0, max(0.0, h / math.log(K))))


def _jsd(p: dict, q: dict) -> float:
    """JSD(p, q), 밑 2, 0~1. SciPy는 제곱근을 돌려주므로 제곱한다."""
    names = sorted(set(p) | set(q))
    a = np.array([p.get(n, 0.0) for n in names], dtype=float)
    b = np.array([q.get(n, 0.0) for n in names], dtype=float)
    if a.sum() <= 0 or b.sum() <= 0:
        return 1.0
    return float(jensenshannon(a, b, base=2) ** 2)


def assess_confidence(p_fused, p_clip: dict, p_cv: dict, max_sim: float) -> dict:
    """결과 신뢰 등급. {"level": "높음|보통|낮음", "margin", "entropy", "jsd", "max_sim"}.
    p_fused = fuse() 결과, p_clip = predict_clip()["artists"], p_cv = predict_cv() 결과,
    max_sim = 가장 비슷한 명화와의 코사인 유사도."""
    ranked = _ranked(p_fused)
    margin = ranked[0][1] - ranked[1][1] if len(ranked) > 1 else (ranked[0][1] if ranked else 0.0)
    K = max(len(p_clip), len(p_cv), len(ranked))
    entropy = _normalized_entropy(ranked, K)
    jsd = _jsd(p_clip, p_cv)
    max_sim = float(max_sim)

    if (margin < LOW_MARGIN and jsd > LOW_JSD_MIN) or max_sim < LOW_SIM_MAX:
        level = "낮음"
    elif margin >= HIGH_MARGIN and jsd <= HIGH_JSD_MAX and max_sim >= HIGH_SIM_MIN:
        level = "높음"
    else:
        level = "보통"
    return {
        "level": level,
        "margin": float(margin),
        "entropy": entropy,
        "jsd": jsd,
        "max_sim": max_sim,
    }


def _finite_number(v) -> bool:
    """bool이 아닌 유한한 실수인지. numpy 실수(np.float32 등)도 받는다."""
    return isinstance(v, numbers.Real) and not isinstance(v, bool) and math.isfinite(float(v))


def _usable_stat(stat) -> bool:
    """프로필 값 (mean, std)가 쓸 수 있는 모양인지."""
    return (
        isinstance(stat, (tuple, list))
        and len(stat) == 2
        and _finite_number(stat[0])
        and _finite_number(stat[1])
    )


def compare(features: dict, profiles: dict, top1: str, top2: str) -> dict:
    """1·2위 대조. {"why_top1": [특징 이름 ≤2], "toward_top2": [특징 이름 ≤2], "z": {feature: 1위 기준 z값}}.
    why_top1 = 1위 평균에 더 가까운 특징, toward_top2 = 2위 평균에 더 가까운 특징 (차이가 큰 순).

    - 비교 대상은 features와 두 화가 프로필에 모두 있고 유한한 수인 특징뿐이다. palette처럼 수가 아닌
      값, NaN·inf, 모양이 틀린 프로필 값은 건너뛴다. 스케치일 때 색 특징을 빼는 일은 호출하는 쪽
      (app.analyze)이 features에서 미리 빼서 한다.
    - top1 == top2이면 대조할 상대가 없으므로 두 목록은 비우고 z만 채운다.
    - 차이가 같으면(동점) 특징 이름 순으로 정해 결과가 매번 같게 한다.
    - 프로필에 없는 화가가 오면 KeyError를 낸다(조용히 빈 설명을 내지 않는다).
    """
    missing = [a for a in (top1, top2) if a not in profiles]
    if missing:
        raise KeyError(f"compare(): 프로필에 없는 화가 {missing}")
    p1, p2 = profiles[top1], profiles[top2]
    usable = [
        f
        for f in p1
        if f in p2
        and _finite_number(features.get(f))
        and _usable_stat(p1[f])
        and _usable_stat(p2[f])
    ]
    x = {f: float(features[f]) for f in usable}
    z1 = {f: (x[f] - float(p1[f][0])) / max(float(p1[f][1]), EPS) for f in usable}
    if top1 == top2:
        return {"why_top1": [], "toward_top2": [], "z": z1}
    z2 = {f: (x[f] - float(p2[f][0])) / max(float(p2[f][1]), EPS) for f in usable}
    gap = {f: abs(z2[f]) - abs(z1[f]) for f in usable}  # 양수 = 1위 쪽이 더 가까움
    why_top1 = [f for f in sorted(usable, key=lambda f: (-gap[f], f)) if gap[f] > GAP_TOL][:2]
    toward_top2 = [f for f in sorted(usable, key=lambda f: (gap[f], f)) if gap[f] < -GAP_TOL][:2]
    return {
        "why_top1": why_top1,
        "toward_top2": toward_top2,
        "z": z1,
    }


@lru_cache(maxsize=1)
def _korean_font() -> str | None:
    available = {f.name for f in font_manager.fontManager.ttflist}
    return next((n for n in _KO_FONT_CANDIDATES if n in available), None)


def _radar_value(feature: str, value: float) -> float:
    if feature == "direction":  # 각도(0~180)를 0~1로
        value = value / 180.0
    return float(min(1.0, max(0.0, value)))


def _radar(features: dict, profile: dict, artist: str) -> Figure:
    names = [f for f in FEATURE_KO if f in profile and isinstance(features.get(f), (int, float))]
    mine = [_radar_value(f, features[f]) for f in names]
    theirs = [_radar_value(f, profile[f][0]) for f in names]
    angles = np.linspace(0, 2 * np.pi, len(names), endpoint=False).tolist()
    font = _korean_font()

    fig = Figure(figsize=(5, 5), dpi=100)
    ax = fig.add_subplot(projection="polar")
    for vals, label, color, style in (
        (mine, "내 그림", "#d9480f", "-"),
        (theirs, f"{artist} 평균", "#1c7ed6", "--"),
    ):
        ax.plot(angles + angles[:1], vals + vals[:1], style, color=color, linewidth=2, label=label)
        ax.fill(angles + angles[:1], vals + vals[:1], color=color, alpha=0.15)
    ax.set_xticks(angles)
    ax.set_xticklabels([FEATURE_KO[f] for f in names], fontfamily=font)
    ax.set_ylim(0, 1)
    ax.set_yticklabels([])
    ax.legend(
        loc="upper right", bbox_to_anchor=(1.25, 1.12), prop={"family": font} if font else None
    )
    fig.tight_layout()
    return fig


def _pct(p: float) -> str:
    return f"{p * 100:.0f}%"


def _ko_list(features: list[str]) -> str:
    return ", ".join(FEATURE_KO.get(f, f) for f in features)


def render_card(result: dict) -> tuple[str, Figure]:
    """결과 카드. (해석 문장 Markdown, 레이더 차트 Figure). result 형식은 contracts/interfaces.md 참고."""
    top3 = result["top3"]
    conf = result["confidence"]
    level = conf["level"]
    top1 = top3[0][0]
    top2 = top3[1][0] if len(top3) > 1 else None
    lines = [f"### {TYPE_INTRO.get(result['input_type'], '이 이미지는')} 이런 화가와 닮았어요", ""]

    if level == "낮음":
        lines.append(
            f"**신뢰 등급: {level}** — {LEVEL_NOTE[level]} 두 관점의 결과를 따로 보여드릴게요."
        )
        lines.append("")
        lines.append(
            "- 소재·분위기·양식(CLIP): "
            + ", ".join(f"{a} {_pct(p)}" for a, p in result["p_clip_top"])
        )
        lines.append(
            "- 색·선(OpenCV): " + ", ".join(f"{a} {_pct(p)}" for a, p in result["p_cv_top"])
        )
    else:
        for i, (artist, p) in enumerate(top3, 1):
            lines.append(f"{i}. **{artist}** — {_pct(p)}")
        lines.append("")
        note = f" — {LEVEL_NOTE[level]}" if LEVEL_NOTE[level] else ""
        lines.append(f"**신뢰 등급: {level}**{note}")

    clip_first, cv_first = result["p_clip_top"][0][0], result["p_cv_top"][0][0]
    if clip_first != cv_first:
        lines.append(f"\n분위기는 **{clip_first}**, 색감·선은 **{cv_first}** 쪽에 가까워요.")

    lines.append("")
    lines.append("**닮은 화풍**: " + ", ".join(f"{s} {_pct(p)}" for s, p in result["styles_top3"]))
    lines.append("**CLIP 키워드**: " + ", ".join(f"{k}({s:.2f})" for k, s in result["keywords"]))

    comp = result["comparison"]
    if comp["why_top1"]:
        lines.append(
            f"**{top1}인 이유**: {_ko_list(comp['why_top1'])}이(가) {top1} 평균에 더 가까워요."
        )
    if top2 and comp["toward_top2"]:
        lines.append(f"**{top2} 느낌이 나는 부분**: {_ko_list(comp['toward_top2'])}")

    if result["similar"]:
        lines.append(
            "**비슷한 명화**: "
            + ", ".join(f"{w['artist']} #{w['id']} ({w['score']:.2f})" for w in result["similar"])
        )

    lines.append(
        f"\n<sub>1·2위 차이 {conf['margin']:.2f} · 엔트로피 {conf['entropy']:.2f} · "
        f"관점 차이(JSD) {conf['jsd']:.2f} · 데이터셋 유사도 {conf['max_sim']:.2f}</sub>"
    )
    lines.append(f"\n> {DISCLAIMER}")
    return "\n".join(lines), _radar(result["features"], result["top1_profile"], top1)


# --- 화면(G안)용 데이터 — 계약 밖 보조 함수 (#37) ---------------------------------------


def _artist_names(artist: str) -> tuple[str, str]:
    """화가의 (한글 전체 이름, 한글 짧은 이름). 한글 이름표에 없으면 원래 이름을 그대로 쓴다."""
    return ARTIST_KO.get(artist, (artist, artist))


def _style_key(style: str) -> str:
    return re.sub(r"[\s_\-]+", " ", style).strip().casefold()


_STYLE_KO_BY_KEY = {_style_key(k): v for k, v in STYLE_KO.items()}


def _style_name(style) -> str:
    """화풍의 한글 이름. "Post_Impressionism"·"Post-Impressionism" 모두 "후기 인상주의".
    표에 없으면 밑줄을 공백으로 바꾼 원래 이름을 쓴다."""
    raw = str(style or "")
    return _STYLE_KO_BY_KEY.get(_style_key(raw), raw.replace("_", " ").strip())


def _pct_int(p) -> int:
    """확률(0~1)을 정수 %로. 수가 아니면 0."""
    return round(float(p) * 100) if _finite_number(p) else 0


def _named_pcts(ranked) -> list[dict]:
    """[(화가, 확률), ...] → [{"name": 짧은 한글 이름, "name_orig": 원래 이름, "pct": 정수 %}]."""
    return [
        {"name": _artist_names(str(a))[1], "name_orig": str(a), "pct": _pct_int(p)}
        for a, p in ranked
    ]


def _top1_style(result: dict, top1: str) -> str:
    """1위 화가의 대표 화풍. 1위 화가의 비슷한 명화에 붙은 화풍을 먼저 쓰고, 없으면 CLIP 화풍 1위."""
    for work in result.get("similar") or []:
        if work.get("artist") == top1 and work.get("style"):
            return str(work["style"])
    styles = result.get("styles_top3") or []
    return str(styles[0][0]) if styles else ""


def _radar_view(result: dict, top1: str, top2: str | None) -> dict:
    """레이더 좌표. 내 값과 1위 화가 평균을 0~1로 자른다(_radar_value 규칙). 스케치면 선 특징 5개만."""
    feats = result.get("features") or {}
    profile = result.get("top1_profile") or {}
    comp = result.get("comparison") or {}
    keys = LINE_FEATURES_FOR_RADAR if result.get("gray") else tuple(FEATURE_KO)
    names = [f for f in keys if _finite_number(feats.get(f)) and _usable_stat(profile.get(f))]
    near = [f for f in comp.get("why_top1", []) if f in names]
    far = [f for f in comp.get("toward_top2", []) if f in names]
    axes = [
        {
            "key": f,
            "label": FEATURE_KO.get(f, f),
            "mine": _radar_value(f, float(feats[f])),
            "avg": _radar_value(f, float(profile[f][0])),
            "near": f in near,
            "far": f in far,
        }
        for f in names
    ]
    return {
        "axes": axes,
        "artist": _artist_names(top1)[1],
        "artist2": _artist_names(top2)[1] if top2 else "",
        "near": [FEATURE_KO.get(f, f) for f in near],
        "far": [FEATURE_KO.get(f, f) for f in far],
    }


def _hex(color) -> str | None:
    """[r, g, b](0~255) → "#rrggbb". 모양이 틀리면 None."""
    if not isinstance(color, (list, tuple)) or len(color) != 3:
        return None
    if not all(_finite_number(c) for c in color):
        return None
    r, g, b = (min(255, max(0, round(float(c)))) for c in color)
    return f"#{r:02x}{g:02x}{b:02x}"


def _palette_hex(feats) -> list[str] | None:
    """특징의 palette를 hex 5개로. 없거나 모양이 틀린 색이 있으면 None(화면이 그 칸을 숨긴다)."""
    palette = feats.get("palette") if isinstance(feats, dict) else None
    if not isinstance(palette, (list, tuple)) or not palette:
        return None
    out = [_hex(c) for c in list(palette)[:PALETTE_LEN]]
    return out if all(out) else None


def _kind(result: dict) -> str:
    """기록·명화 페이지의 종류. 흑백이면 스케치, 아니면 input_type(모르면 사진)."""
    if result.get("gray"):
        return KIND_KO["sketch"]
    return KIND_KO.get(result.get("input_type"), KIND_KO["photo"])


def _work_view(work: dict, axes: list[dict], top1_short: str, low: bool) -> dict:
    """명화 한 점의 화면용 값. 특징이 있으면 대표색 hex 5개와 레이더 값(색·선 페이지 축과 같은
    축, 0~1)을 넣고, 내 값과 차이가 가장 작은 축 2개를 near, 가장 큰 축 2개를 far로 고른다."""
    artist = str(work.get("artist") or "")
    full, short = _artist_names(artist)
    style = str(work.get("style") or "")
    wid = str(work.get("id") or "")
    top1_work = bool(work.get("top1_work")) and not low
    feats = work.get("features") if isinstance(work.get("features"), dict) else None
    image = work.get("image")
    image = image if isinstance(image, str) and image.startswith("data:image/") else None

    radar = None
    near: list[str] = []
    far: list[str] = []
    if feats is not None and axes and all(_finite_number(feats.get(a["key"])) for a in axes):
        radar = {a["key"]: _radar_value(a["key"], float(feats[a["key"]])) for a in axes}
        gaps = sorted(axes, key=lambda a: (abs(a["mine"] - radar[a["key"]]), a["key"]))
        near = [a["key"] for a in gaps[:2]]
        far = [a["key"] for a in reversed(gaps) if a["key"] not in near][:2]

    return {
        "id": wid,
        "artist": full,
        "short": short,
        "artist_orig": artist,
        "label": f"{short} #{wid}" if wid else short,
        "style": _style_name(style),
        "style_orig": style,
        "pct": max(0, min(100, _pct_int(work.get("score")))),
        "top1_work": top1_work,
        "eyebrow": f"1위 화가 {top1_short}의 작품 중에서" if top1_work else "화가와 상관없이 고른",
        "title": "가장 닮은 명화예요" if top1_work else "가장 비슷한 명화예요",
        "image": image,
        "palette": _palette_hex(feats),
        "radar": radar,
        "near_keys": near,
        "far_keys": far,
        "near": [FEATURE_KO.get(k, k) for k in near],
        "far": [FEATURE_KO.get(k, k) for k in far],
    }


def _compare_view(result: dict, works, axes: list[dict], top1_short: str, low: bool):
    """명화 페이지 값(FR7.4, FR8). works가 비어 있으면 None(화면이 명화 페이지를 숨긴다, FR8.9)."""
    works = [w for w in (works or []) if isinstance(w, dict)]
    if not works:
        return None
    items = [_work_view(w, axes, top1_short, low) for w in works]
    kind = _kind(result)
    return {
        "eyebrow": items[0]["eyebrow"],
        "title": items[0]["title"],
        "kind_note": KIND_NOTE.get(kind, ""),
        "mine_palette": _palette_hex(result.get("features")),
        "works": items,
    }


def build_view(result: dict, works: list[dict] | None = None) -> dict:
    """G안 화면에 필요한 값을 JSON으로 바꿀 수 있는 dict로 만든다. result와 works만 읽는다
    (추가 계산 없음).

    result 형식은 contracts/interfaces.md(app.analyze 반환)를 따른다. 화면은 result를 직접 읽지
    않고 이 dict만 쓴다. 키: head, level, top3, views, low, radar, styles, keywords, metrics,
    gray, disclaimer, source, compare, kind, history_name.

    works는 app.py가 고른 명화 비교용 목록이다:
    [{"id", "artist", "style", "score", "top1_work", "image": data URL | None,
    "features": extract_features() 결과 | None}]. 비어 있으면 compare는 None.
    """
    top3 = list(result["top3"])
    conf = result["confidence"]
    level = conf["level"]
    top1 = str(top3[0][0])
    top2 = str(top3[1][0]) if len(top3) > 1 else None
    full, short = _artist_names(top1)
    style = _top1_style(result, top1)
    low = level == "낮음"

    clip_first = str(result["p_clip_top"][0][0]) if result["p_clip_top"] else ""
    cv_first = str(result["p_cv_top"][0][0]) if result["p_cv_top"] else ""

    if low:
        title = LEVEL_NOTE["낮음"].rstrip(".")
        sub = "두 관점의 결과를 따로 보여 드려요"
    else:
        title = full
        sub = " · ".join(s for s in (top1, _style_name(style)) if s)

    radar = _radar_view(result, top1, top2)

    return {
        "head": {
            "intro": TYPE_INTRO.get(result.get("input_type"), "이 이미지는"),
            "title": title,
            "sub": sub,
            "name": full,
            "short": short,
            "name_orig": top1,
            "style": _style_name(style),
            "style_orig": style,
            "pct": _pct_int(top3[0][1]),
        },
        "level": {
            "label": level,
            "bars": LEVEL_BARS.get(level, 1),
            "note": LEVEL_NOTE.get(level) or "결과가 뚜렷해요.",
        },
        "top3": [dict(rank=i, **item) for i, item in enumerate(_named_pcts(top3), 1)],
        "views": {
            "clip": _artist_names(clip_first)[1],
            "cv": _artist_names(cv_first)[1],
            "same": clip_first == cv_first,
        },
        "low": (
            {"clip": _named_pcts(result["p_clip_top"]), "cv": _named_pcts(result["p_cv_top"])}
            if low
            else None
        ),
        "radar": radar,
        "styles": [
            {"name": _style_name(s), "name_orig": str(s), "pct": _pct_int(p)}
            for s, p in result["styles_top3"]
        ],
        "keywords": [str(k) for k, _ in result["keywords"]],
        "metrics": [
            {
                "label": "1·2위 차이",
                "value": round(float(conf["margin"]), 2),
                "note": "클수록 1위가 뚜렷해요",
            },
            {
                "label": "엔트로피",
                "value": round(float(conf["entropy"]), 2),
                "note": "작을수록 결과가 모여요",
            },
            {
                "label": "관점 차이 (JSD)",
                "value": round(float(conf["jsd"]), 2),
                "note": "작을수록 두 관점이 비슷해요",
            },
            {
                "label": "데이터셋 유사도",
                "value": round(float(conf["max_sim"]), 2),
                "note": "가장 닮은 명화 기준",
            },
        ],
        "gray": bool(result.get("gray")),
        "disclaimer": DISCLAIMER,
        "source": SOURCE_NOTE,
        "compare": _compare_view(result, works, radar["axes"], short, low),
        "kind": _kind(result),
        "history_name": NO_MATCH_NAME if low else full,
    }
