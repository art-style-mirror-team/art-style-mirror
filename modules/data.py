"""A — 데이터·CLIP (담당: 홍승민).

1일차 스텁: contracts/interfaces.md와 똑같은 모양의 가짜 결과를 돌려준다.
값은 입력에서 결정적으로 만들어지므로 같은 입력에는 항상 같은 결과가 나온다.
실제 구현(#3~#7)에서 함수 이름·입출력 형식은 그대로 두고 내용만 바꾼다.
"""
from __future__ import annotations

import hashlib
from functools import lru_cache

import numpy as np
import pandas as pd

EMB_DIM = 512

# 스텁용 화가 24명과 대표 화풍. 실제 목록은 #3에서 확정한다.
ARTIST_STYLE = {
    "Vincent van Gogh": "Post-Impressionism",
    "Claude Monet": "Impressionism",
    "Pierre-Auguste Renoir": "Impressionism",
    "Paul Cezanne": "Post-Impressionism",
    "Paul Gauguin": "Post-Impressionism",
    "Edgar Degas": "Impressionism",
    "Camille Pissarro": "Impressionism",
    "Pablo Picasso": "Cubism",
    "Henri Matisse": "Fauvism",
    "Wassily Kandinsky": "Abstract Expressionism",
    "Piet Mondrian": "Minimalism",
    "Salvador Dali": "Surrealism",
    "Rene Magritte": "Surrealism",
    "Gustav Klimt": "Art Nouveau",
    "Edvard Munch": "Expressionism",
    "Rembrandt": "Baroque",
    "Caravaggio": "Baroque",
    "Albrecht Durer": "Northern Renaissance",
    "Sandro Botticelli": "Early Renaissance",
    "Raphael": "High Renaissance",
    "Katsushika Hokusai": "Ukiyo-e",
    "Andy Warhol": "Pop Art",
    "Ivan Aivazovsky": "Romanticism",
    "Ivan Shishkin": "Realism",
}
ARTISTS = list(ARTIST_STYLE)
STYLES = sorted(set(ARTIST_STYLE.values()))
GENRES = ["landscape", "portrait", "still_life", "religious_painting", "sketch_and_study", "genre_painting"]

WORKS_PER_ARTIST = 20  # 14 train / 3 val / 3 test → 70/15/15

# clip_keywords()가 고르는 소재·분위기·양식 표현 (실제 구현은 반대 문장쌍 비교, #7)
KEYWORDS = [
    "두꺼운 붓 자국", "소용돌이치는 하늘", "선명한 원색", "차분한 색조", "부드러운 빛",
    "강한 명암 대비", "단순한 기하학 형태", "꿈같은 분위기", "섬세한 윤곽선", "평면적인 색면",
    "야외 풍경", "인물 초상", "정물", "어두운 배경", "밝은 햇살",
]


def _seed(*parts: bytes | str) -> int:
    h = hashlib.sha1()
    for p in parts:
        h.update(p.encode("utf-8") if isinstance(p, str) else p)
    return int.from_bytes(h.digest()[:8], "little")


def _unit(v: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(v, axis=-1, keepdims=True)
    return (v / np.maximum(norm, 1e-12)).astype(np.float32)


def _check_image(img: np.ndarray) -> None:
    if not isinstance(img, np.ndarray) or img.dtype != np.uint8 or img.ndim != 3 or img.shape[2] != 3:
        raise ValueError("이미지는 RGB np.ndarray(uint8), shape (H, W, 3)이어야 합니다.")


@lru_cache(maxsize=1)
def _artist_directions() -> np.ndarray:
    """화가별 가짜 '중심 방향'. 같은 화가 작품끼리 임베딩이 모이도록 쓴다."""
    rng = np.random.default_rng(_seed("artist-directions"))
    return _unit(rng.normal(size=(len(ARTISTS), EMB_DIM)))


def embed_image(img: np.ndarray) -> np.ndarray:
    """CLIP 이미지 임베딩. shape (512,), L2 정규화. (스텁: 이미지 바이트로 만든 가짜 벡터)"""
    _check_image(img)
    rng = np.random.default_rng(_seed(img.tobytes(), str(img.shape)))
    # 입력도 어느 한 화가 쪽으로 약간 기울게 해서 Top 3가 뚜렷하게 보이게 한다.
    direction = _artist_directions()[rng.integers(len(ARTISTS))]
    return _unit(0.6 * direction + 0.8 * _unit(rng.normal(size=EMB_DIM)))


def embed_text(texts: list[str]) -> np.ndarray:
    """문장 임베딩. shape (n, 512), 각 행 L2 정규화. (스텁: 문장으로 만든 가짜 벡터)"""
    if isinstance(texts, str):
        texts = [texts]
    rows = [np.random.default_rng(_seed("text", t)).normal(size=EMB_DIM) for t in texts]
    return _unit(np.array(rows, dtype=np.float64).reshape(len(texts), EMB_DIM))


@lru_cache(maxsize=1)
def _build_index() -> tuple[np.ndarray, pd.DataFrame]:
    rng = np.random.default_rng(_seed("index"))
    splits = ["train"] * 14 + ["val"] * 3 + ["test"] * 3
    embs, rows = [], []
    for a_idx, artist in enumerate(ARTISTS):
        center = _artist_directions()[a_idx]
        for w in range(WORKS_PER_ARTIST):
            embs.append(center + 0.7 * _unit(rng.normal(size=EMB_DIM)))
            work_id = f"{a_idx:02d}{w:03d}"
            rows.append({
                "id": work_id,
                "artist": artist,
                "style": ARTIST_STYLE[artist],
                "genre": GENRES[w % len(GENRES)],
                "path": f"data/wikiart/{artist.lower().replace(' ', '-')}_{work_id}.jpg",
                "split": splits[w],
            })
    emb = _unit(np.array(embs))
    emb.setflags(write=False)
    return emb, pd.DataFrame(rows, columns=["id", "artist", "style", "genre", "path", "split"])


def load_index() -> dict:
    """{"emb": (N, 512), "meta": DataFrame[id, artist, style, genre, path, split]}. (스텁: 화가 24명 × 20점)"""
    emb, meta = _build_index()
    return {"emb": emb, "meta": meta.copy()}


def clip_keywords(emb: np.ndarray, k: int = 3) -> list[tuple]:
    """CLIP 키워드 설명. [("두꺼운 붓 자국", 0.71), ...] 점수 내림차순. (스텁: 임베딩으로 고른 가짜 키워드)"""
    emb = np.asarray(emb, dtype=np.float32)
    rng = np.random.default_rng(_seed(emb.tobytes()))
    picks = rng.choice(len(KEYWORDS), size=min(k, len(KEYWORDS)), replace=False)
    scores = np.sort(rng.uniform(0.55, 0.85, size=len(picks)))[::-1]
    return [(KEYWORDS[i], round(float(s), 2)) for i, s in zip(picks, scores)]
