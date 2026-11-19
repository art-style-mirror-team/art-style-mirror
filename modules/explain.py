"""D — 신뢰도·UI·통합 (담당: 김현승).

1일차 스텁: contracts/interfaces.md와 똑같은 모양의 결과를 돌려준다.
지표(1·2위 차이, 정규화 엔트로피, JSD)는 plan.md 6.3 식대로 계산하고,
등급 경계값만 임시값을 쓴다(#24에서 검증셋으로 확정).
"""

from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
from matplotlib import font_manager
from matplotlib.figure import Figure
from scipy.spatial.distance import jensenshannon

EPS = 0.01

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


def compare(features: dict, profiles: dict, top1: str, top2: str) -> dict:
    """1·2위 대조. {"why_top1": [특징 이름 ≤2], "toward_top2": [특징 이름 ≤2], "z": {feature: 1위 기준 z값}}.
    why_top1 = 1위 평균에 더 가까운 특징, toward_top2 = 2위 평균에 더 가까운 특징 (차이가 큰 순)."""
    p1, p2 = profiles[top1], profiles[top2]
    usable = [
        f
        for f in p1
        if f in p2
        and isinstance(features.get(f), (int, float))
        and not isinstance(features.get(f), bool)
    ]
    z1 = {f: (features[f] - p1[f][0]) / max(p1[f][1], EPS) for f in usable}
    z2 = {f: (features[f] - p2[f][0]) / max(p2[f][1], EPS) for f in usable}
    gap = {f: abs(z2[f]) - abs(z1[f]) for f in usable}  # 양수 = 1위 쪽이 더 가까움
    why_top1 = [f for f in sorted(usable, key=lambda f: -gap[f]) if gap[f] > 0][:2]
    toward_top2 = [f for f in sorted(usable, key=lambda f: gap[f]) if gap[f] < 0][:2]
    return {
        "why_top1": why_top1,
        "toward_top2": toward_top2,
        "z": {f: float(z1[f]) for f in usable},
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
