"""A 모듈: 데이터 분할 + CLIP 임베딩.

contracts/interfaces.md의 시그니처를 따른다.
  embed_image(img) -> (512,)   L2 정규화
  embed_text(texts) -> (n,512) L2 정규화
  load_index() -> {"emb": (N,512), "meta": DataFrame[id, artist, style, genre, path, split]}
  clip_keywords(emb, k=3) -> [(키워드, 점수), ...]
이미지는 모두 RGB np.ndarray(uint8).
"""

from __future__ import annotations

import hashlib
import logging
import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

# 명화와 사용자 입력은 반드시 이 모델 하나로만 변환한다 (AGENTS.md 규칙).
CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"
EMB_DIM = 512

ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = ROOT / "artifacts"
SEED = 42
SPLIT_NAMES = ("train", "val", "test")  # 70 / 15 / 15

# ───────────── 팀 호환용 상수 (features.py·테스트가 import한다) ─────────────
# 확정된 화가 23명(표시용 이름). 값은 artifacts가 없을 때 쓰는 '가짜 인덱스'용 대표 화풍이며,
# 실제 화풍은 meta.csv의 style 열이다.
ARTIST_STYLE = {
    "Albrecht Durer": "Northern Renaissance",
    "Boris Kustodiev": "Realism",
    "Camille Pissarro": "Impressionism",
    "Childe Hassam": "Impressionism",
    "Claude Monet": "Impressionism",
    "Edgar Degas": "Impressionism",
    "Eugene Boudin": "Impressionism",
    "Gustave Dore": "Romanticism",
    "Ilya Repin": "Realism",
    "Ivan Aivazovsky": "Romanticism",
    "Ivan Shishkin": "Realism",
    "John Singer Sargent": "Realism",
    "Marc Chagall": "Expressionism",
    "Martiros Saryan": "Post-Impressionism",
    "Nicholas Roerich": "Symbolism",
    "Pablo Picasso": "Cubism",
    "Paul Cezanne": "Post-Impressionism",
    "Pierre-Auguste Renoir": "Impressionism",
    "Pyotr Konchalovsky": "Post-Impressionism",
    "Raphael Kirchner": "Art Nouveau",
    "Rembrandt": "Baroque",
    "Salvador Dali": "Surrealism",
    "Vincent van Gogh": "Post-Impressionism",
}
ARTISTS = list(ARTIST_STYLE)
GENRES = [
    "landscape",
    "portrait",
    "still_life",
    "religious_painting",
    "sketch_and_study",
    "genre_painting",
]
WORKS_PER_ARTIST = 20  # 가짜 인덱스: 14 train / 3 val / 3 test

# clip_keywords()가 쓰는 반대 문장쌍: (한쪽 표시어, 반대쪽 표시어, 한쪽 영어 표현들, 반대쪽 영어 표현들)
KEYWORD_PAIRS = [
    (
        "두꺼운 붓 자국",
        "매끈한 붓질",
        ["thick visible brush strokes", "heavy impasto texture"],
        ["smooth blended brushwork", "a polished surface with no visible strokes"],
    ),
    (
        "선명한 색감",
        "차분한 색감",
        ["vivid saturated colors", "bold bright colors"],
        ["muted subdued colors", "a soft desaturated palette"],
    ),
    (
        "강한 명암 대비",
        "부드러운 조명",
        ["strong contrast between light and dark", "dramatic lighting"],
        ["soft even lighting", "gentle low contrast tones"],
    ),
    (
        "따뜻한 색조",
        "차가운 색조",
        ["a warm color palette of reds and oranges", "warm golden tones"],
        ["a cool color palette of blues and greens", "cool silvery tones"],
    ),
    (
        "어두운 분위기",
        "밝은 분위기",
        ["a dark moody atmosphere", "deep shadows"],
        ["a bright cheerful atmosphere", "a luminous sunny feeling"],
    ),
    (
        "섬세한 사실 묘사",
        "단순화된 형태",
        ["fine realistic detail", "precise lifelike rendering"],
        ["simplified abstract shapes", "flat geometric forms"],
    ),
    (
        "역동적인 움직임",
        "정적인 구도",
        ["dynamic swirling movement", "energetic dramatic motion"],
        ["a calm still composition", "a quiet static scene"],
    ),
    (
        "뚜렷한 윤곽선",
        "흐릿한 윤곽",
        ["bold clear outlines", "sharp defined edges"],
        ["soft blurred edges", "hazy indistinct contours"],
    ),
    (
        "평면적인 화면",
        "깊은 원근감",
        ["a flat two-dimensional surface", "flat areas of color"],
        ["deep perspective and depth", "a strong sense of space"],
    ),
    (
        "몽환적인 분위기",
        "현실적인 분위기",
        ["a dreamlike fantastical mood", "a surreal imaginative scene"],
        ["an ordinary realistic scene", "an everyday naturalistic view"],
    ),
]
KEYWORD_TEMPLATES = ("a painting with {}", "an artwork with {}")
KEYWORDS = [w for pos, neg, _, _ in KEYWORD_PAIRS for w in (pos, neg)]  # 호환용: 가능한 모든 표시어


def _seed(*parts: bytes | str) -> int:
    h = hashlib.sha1()
    for p in parts:
        h.update(p.encode("utf-8") if isinstance(p, str) else p)
    return int.from_bytes(h.digest()[:8], "little")


def _unit(v: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(v, axis=-1, keepdims=True)
    return (v / np.maximum(norm, 1e-12)).astype(np.float32)


@lru_cache(maxsize=1)
def _fake_index() -> tuple[np.ndarray, pd.DataFrame]:
    """artifacts 파일이 없을 때만 쓰는 가짜 인덱스 (화가 23명 × 20점). 평가·결과 보고에 쓰지 않는다."""
    rng = np.random.default_rng(_seed("index"))
    dirs = _unit(
        np.random.default_rng(_seed("artist-directions")).normal(size=(len(ARTISTS), EMB_DIM))
    )
    splits = ["train"] * 14 + ["val"] * 3 + ["test"] * 3
    embs, rows = [], []
    for a_idx, artist in enumerate(ARTISTS):
        for w in range(WORKS_PER_ARTIST):
            embs.append(dirs[a_idx] + 0.7 * _unit(rng.normal(size=EMB_DIM)))
            work_id = f"{a_idx:02d}{w:03d}"
            rows.append(
                {
                    "id": work_id,
                    "artist": artist,
                    "style": ARTIST_STYLE[artist],
                    "genre": GENRES[w % len(GENRES)],
                    "path": f"data/wikiart/{artist.lower().replace(' ', '-')}_{work_id}.jpg",
                    "split": splits[w],
                }
            )
    emb = _unit(np.array(embs))
    emb.setflags(write=False)
    return emb, pd.DataFrame(rows, columns=["id", "artist", "style", "genre", "path", "split"])


# ───────────────────────── 이슈 #3: 화가 선별 · 분할 ─────────────────────────
def select_artists(
    df: pd.DataFrame,
    n: int = 23,
    min_count: int = 50,
    exclude: tuple[str, ...] = ("Unknown Artist", "Unknown"),
) -> list[str]:
    """작품 수가 많은 순으로 화가 n명을 고른다 (동률은 이름순, 항상 같은 결과)."""
    counts = df[~df["artist"].isin(exclude)]["artist"].value_counts()
    counts = counts[counts >= min_count]
    ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    if len(ordered) < n:
        raise ValueError(
            f"작품 {min_count}점 이상인 화가가 {len(ordered)}명뿐입니다 (필요 {n}명). "
            "--min-count를 낮추거나 데이터셋을 바꾸세요."
        )
    return [name for name, _ in ordered[:n]]


def cap_per_artist(df: pd.DataFrame, max_per_artist: int | None, seed: int = SEED) -> pd.DataFrame:
    """화가당 최대 작품 수 제한 (임베딩 시간 단축). None이면 그대로."""
    if not max_per_artist:
        return df
    shuffled = df.sample(frac=1.0, random_state=seed)  # 무작위 순서 (재현 가능)
    return shuffled.groupby("artist", sort=False).head(max_per_artist).sort_index()


def split_dataframe(df: pd.DataFrame, seed: int = SEED) -> pd.DataFrame:
    """화가별 비율을 유지하며 train 70 / val 15 / test 15 로 나눠 split 열을 추가한다."""
    from sklearn.model_selection import train_test_split

    train, rest = train_test_split(df, test_size=0.30, stratify=df["artist"], random_state=seed)
    val, test = train_test_split(rest, test_size=0.50, stratify=rest["artist"], random_state=seed)
    out = df.copy()
    out.loc[train.index, "split"] = "train"
    out.loc[val.index, "split"] = "val"
    out.loc[test.index, "split"] = "test"
    return out


# ───────────────────────── 이슈 #4·#5: CLIP 임베딩 ─────────────────────────
@lru_cache(maxsize=1)
def _get_clip():
    import torch
    from transformers import CLIPModel, CLIPProcessor

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = CLIPModel.from_pretrained(CLIP_MODEL_NAME).to(device).eval()
    processor = CLIPProcessor.from_pretrained(CLIP_MODEL_NAME)
    return model, processor, device


def _l2(x: np.ndarray) -> np.ndarray:
    return x / np.clip(np.linalg.norm(x, axis=-1, keepdims=True), 1e-12, None)


def _check_img(img) -> np.ndarray:
    arr = np.asarray(img)
    if arr.ndim != 3 or arr.shape[2] != 3 or arr.dtype != np.uint8:
        raise ValueError(
            f"RGB uint8 (H,W,3) 이미지가 필요합니다. 받은 값: shape={arr.shape}, dtype={arr.dtype}"
        )
    return arr


def embed_images(imgs: list, batch_size: int = 64) -> np.ndarray:
    """여러 장을 한 번에 임베딩. (n,512) float32, L2 정규화. 인덱스 구축용."""
    import torch

    model, processor, device = _get_clip()
    out = []
    for i in range(0, len(imgs), batch_size):
        batch = [_check_img(x) for x in imgs[i : i + batch_size]]
        inputs = processor(images=batch, return_tensors="pt").to(device)
        with torch.no_grad():
            # get_image_features의 반환 형식이 transformers 버전마다 달라서 직접 계산한다.
            pooled = model.vision_model(pixel_values=inputs["pixel_values"]).pooler_output
            feats = model.visual_projection(pooled)
        out.append(feats.float().cpu().numpy())
    emb = np.concatenate(out, axis=0) if out else np.zeros((0, EMB_DIM), np.float32)
    if emb.shape[-1] != EMB_DIM:
        raise RuntimeError(
            f"임베딩 차원이 {emb.shape[-1]}입니다 (기대 {EMB_DIM}). transformers 버전/모델을 확인하세요."
        )
    return _l2(emb).astype(np.float32)


def embed_image(img: np.ndarray) -> np.ndarray:
    """이미지 1장 -> (512,) L2 정규화 CLIP 임베딩."""
    return embed_images([img])[0]


def embed_text(texts) -> np.ndarray:
    """문장(들) -> (n,512) L2 정규화 CLIP 임베딩."""
    import torch

    if isinstance(texts, str):
        texts = [texts]
    model, processor, device = _get_clip()
    inputs = processor(text=list(texts), padding=True, truncation=True, return_tensors="pt").to(
        device
    )
    with torch.no_grad():
        pooled = model.text_model(
            input_ids=inputs["input_ids"], attention_mask=inputs.get("attention_mask")
        ).pooler_output
        feats = model.text_projection(pooled)
    emb = feats.float().cpu().numpy()
    if emb.shape[-1] != EMB_DIM:
        raise RuntimeError(f"텍스트 임베딩 차원이 {emb.shape[-1]}입니다 (기대 {EMB_DIM}).")
    return _l2(emb).astype(np.float32)


# ───────────────────────── 인덱스 읽기 ─────────────────────────
_NAME_SPECIAL = {
    "pierre-auguste-renoir": "Pierre-Auguste Renoir",
    "vincent-van-gogh": "Vincent van Gogh",
}


def display_name(name: str) -> str:
    """데이터셋의 'vincent-van-gogh' 형식을 표시용 'Vincent van Gogh'로 바꾼다.
    이미 표시용 이름(대문자 포함)이면 그대로 돌려준다."""
    if name != name.lower():
        return name
    if name in _NAME_SPECIAL:
        return _NAME_SPECIAL[name]
    return " ".join(w.capitalize() for w in name.split("-"))


ARTIST_INFO_CSV = ARTIFACTS / "artists_info.csv"


def load_artist_info(path: Path | str = ARTIST_INFO_CSV) -> dict:
    """화가 소개를 {표시용 화가 이름: {"years", "nationality", "intro"}}로 돌려준다.
    이름은 load_index()의 meta["artist"]와 같다. 파일이 없으면 빈 dict."""
    path = Path(path)
    if not path.exists():
        log.warning("%s가 없어 화가 소개를 비워 둡니다.", path.name)
        return {}
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    return {
        r.artist: {"years": r.years, "nationality": r.nationality, "intro": r.intro}
        for r in df.itertuples()
    }


def _read_index(d: Path) -> tuple[np.ndarray, pd.DataFrame]:
    """파일(또는 가짜 인덱스)에서 인덱스를 읽는다. 캐시는 load_index가 맡는다."""
    if not ((d / "embeddings.npy").exists() and (d / "meta.csv").exists()):
        # artifacts 파일이 없는 환경(CI 등)에서도 앱·테스트가 돌도록 가짜 인덱스로 대체한다.
        log.warning(
            "embeddings.npy·meta.csv가 없어 가짜 인덱스를 씁니다. 평가·결과 보고에는 쓰지 마세요."
        )
        emb, meta = _fake_index()
        meta = meta.copy()
        meta.attrs["fake"] = True  # 확인: idx["meta"].attrs.get("fake")
        return emb, meta
    emb = np.load(d / "embeddings.npy")
    meta = pd.read_csv(d / "meta.csv", dtype={"id": str})
    meta["artist"] = meta["artist"].map(display_name)  # 'vincent-van-gogh' -> 'Vincent van Gogh'
    meta.attrs["fake"] = False
    if len(emb) != len(meta):
        raise ValueError(
            f"embeddings 행 수({len(emb)}) != meta 행 수({len(meta)}). build_index.py를 다시 실행하세요."
        )
    ver = d / "clip_model.txt"
    if ver.exists() and ver.read_text().strip() != CLIP_MODEL_NAME:
        raise ValueError(
            f"인덱스는 {ver.read_text().strip()}로 만들어졌지만 코드는 {CLIP_MODEL_NAME}를 씁니다. "
            "명화와 사용자 입력은 같은 CLIP 모델이어야 합니다."
        )
    return emb, meta


@lru_cache(maxsize=4)
def _cached_index(path: str, stamp: tuple) -> tuple[np.ndarray, pd.DataFrame]:
    emb, meta = _read_index(Path(path))
    emb.flags.writeable = False  # 캐시를 공유하므로 실수로 고치지 못하게 한다
    return emb, meta


def load_index(artifacts_dir: Path | str = ARTIFACTS) -> dict:
    """{"emb": (N,512), "meta": DataFrame} 를 반환. 행 수와 모델 버전을 검사한다.
    같은 파일이면 한 번만 읽고, meta는 복사본을 돌려준다(파일이 바뀌면 다시 읽는다)."""
    d = Path(artifacts_dir)
    stamp = tuple(
        (f.stat().st_mtime_ns, f.stat().st_size) if f.exists() else None
        for f in (d / "embeddings.npy", d / "meta.csv", d / "clip_model.txt")
    )
    emb, meta = _cached_index(str(d.resolve()), stamp)
    return {"emb": emb, "meta": meta.copy()}


# ───────────────────────── 이슈 #7: 닮은 이유 키워드 ─────────────────────────
_KW_CACHE: dict = {"fn": None, "axes": None}


def _unit_vec(v: np.ndarray) -> np.ndarray:
    return v / (np.linalg.norm(v) + 1e-8)


def _keyword_axes() -> np.ndarray:
    """쌍마다 (한쪽 문장 평균 - 반대쪽 문장 평균) 방향 벡터 (P, 512). 문장 표현을 여러 개 평균내는 앙상블."""
    fn = embed_text
    if _KW_CACHE["fn"] is not fn:
        axes = []
        for _, _, pos, neg in KEYWORD_PAIRS:

            def side(phrases):
                texts = [t.format(p) for p in phrases for t in KEYWORD_TEMPLATES]
                return _unit_vec(np.asarray(embed_text(texts), dtype=np.float32).mean(axis=0))

            axes.append(side(pos) - side(neg))
        _KW_CACHE["fn"], _KW_CACHE["axes"] = fn, np.stack(axes).astype(np.float32)
    return _KW_CACHE["axes"]


def clip_keywords(emb: np.ndarray, k: int = 3) -> list[tuple]:
    """그림의 특징 키워드 k개를 [("두꺼운 붓 자국", 0.91), ...] 점수 내림차순으로 돌려준다.

    반대 문장쌍마다 '어느 쪽에 더 가까운지'를 보되, 전체 명화(인덱스) 평균 대비 얼마나 치우쳤는지로 잰다.
    점수는 0.5(평범) ~ 1.0(매우 뚜렷). 한 쌍에서는 한쪽 표시어만 나온다.
    """
    emb = np.asarray(emb, dtype=np.float32).reshape(-1)
    if emb.shape != (EMB_DIM,):
        raise ValueError(f"임베딩은 ({EMB_DIM},)여야 합니다: {emb.shape}")
    axes = _keyword_axes()
    ref = load_index()["emb"] @ axes.T  # (N, P): 전체 명화의 쌍별 치우침
    z = (_unit_vec(emb) @ axes.T - ref.mean(axis=0)) / (ref.std(axis=0) + 1e-6)
    out = []
    for i in np.argsort(-np.abs(z))[: max(k, 0)]:
        pos, neg = KEYWORD_PAIRS[i][:2]
        score = 0.5 * (1.0 + math.erf(abs(float(z[i])) / math.sqrt(2.0)))
        out.append((pos if z[i] > 0 else neg, round(score, 2)))
    return out
