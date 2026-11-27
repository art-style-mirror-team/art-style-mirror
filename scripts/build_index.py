"""WikiArt 축소판 → 화가 23명 선별 → 70/15/15 분할 → CLIP 임베딩 사전 계산.

단계:
  meta  : 데이터셋 로드, 화가 선별, 분할, 이미지 저장(긴 변 512px), artifacts/meta.csv 생성   (이슈 #3)
  embed : meta.csv의 이미지를 CLIP으로 임베딩해 artifacts/embeddings.npy 저장              (이슈 #4)
  all   : 위 두 단계를 순서대로

Colab(GPU) 사용 예:
  !pip install -q datasets transformers torch pillow pandas scikit-learn
  !python scripts/build_index.py --stage all --dataset slpkl/wikiart-subsample

이미지(data/images)는 Git에 올리지 않는다. artifacts/의 meta.csv·embeddings.npy·clip_model.txt(약 14MB)만 커밋한다.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from modules import data as D

LONG_SIDE = 512
COL_CANDIDATES = {
    "artist": ("artist", "artist_name"),
    "style": ("style", "movement"),
    "genre": ("genre",),
}


def _pick(cols, names):
    return next((c for c in names if c in cols), None)


def _label_names(ds, col):
    """ClassLabel이면 정수를 이름으로 바꾼다."""
    feat = ds.features[col]
    return (lambda v: feat.int2str(int(v))) if hasattr(feat, "int2str") else (lambda v: str(v))


def resize_long_side(img: Image.Image, long_side: int = LONG_SIDE) -> Image.Image:
    w, h = img.size
    s = long_side / max(w, h)
    return img.resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS)


def stage_meta(a) -> None:
    from datasets import load_dataset

    ds = load_dataset(a.dataset, split=a.hf_split)
    print("컬럼:", ds.column_names)
    cols = {k: _pick(ds.column_names, v) for k, v in COL_CANDIDATES.items()}
    if cols["artist"] is None:
        raise SystemExit(f"화가 컬럼을 찾지 못했습니다. 컬럼 목록: {ds.column_names}")
    img_col = "image" if "image" in ds.column_names else _pick(ds.column_names, ("img", "picture"))
    if img_col is None:
        raise SystemExit(f"이미지 컬럼을 찾지 못했습니다. 컬럼 목록: {ds.column_names}")

    lab = ds.remove_columns([img_col])  # 이미지 디코딩 없이 라벨만
    raw = lab.to_pandas()
    df = pd.DataFrame({"row": np.arange(len(raw))})
    for k, c in cols.items():
        df[k] = raw[c].map(_label_names(ds, c)) if c else ""

    chosen = D.select_artists(df, n=a.n_artists, min_count=a.min_count)
    df = df[df["artist"].isin(chosen)]
    df = D.cap_per_artist(df, a.max_per_artist).reset_index(drop=True)
    df = D.split_dataframe(df)
    df["id"] = [f"{r:06d}" for r in df["row"]]

    img_dir = Path(a.image_dir)
    img_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, r in enumerate(df["row"]):
        p = img_dir / f"{r:06d}.jpg"
        if not p.exists():
            im = ds[int(r)][img_col].convert("RGB")
            resize_long_side(im).save(p, quality=95)  # 명화는 크기 맞추기만 (화이트밸런스 금지)
        paths.append(str(p))
        if (i + 1) % 200 == 0:
            print(f"  이미지 저장 {i + 1}/{len(df)}")
    df["path"] = paths

    D.ARTIFACTS.mkdir(exist_ok=True)
    df[["id", "artist", "style", "genre", "path", "split"]].to_csv(
        D.ARTIFACTS / "meta.csv", index=False
    )
    print(f"meta.csv 저장: {len(df)}점, 화가 {df['artist'].nunique()}명")
    print(df["split"].value_counts().to_string())


def stage_embed(a) -> None:
    meta = pd.read_csv(D.ARTIFACTS / "meta.csv", dtype={"id": str})
    chunks = []
    for s in range(0, len(meta), a.batch_size):
        part = meta["path"].iloc[s : s + a.batch_size]
        imgs = [np.asarray(Image.open(p).convert("RGB"), dtype=np.uint8) for p in part]
        chunks.append(D.embed_images(imgs, batch_size=a.batch_size))
        print(f"  임베딩 {min(s + a.batch_size, len(meta))}/{len(meta)}")
    emb = np.concatenate(chunks, axis=0)
    assert emb.shape == (len(meta), D.EMB_DIM), f"shape 불일치: {emb.shape} vs meta {len(meta)}행"
    np.save(D.ARTIFACTS / "embeddings.npy", emb)
    (D.ARTIFACTS / "clip_model.txt").write_text(D.CLIP_MODEL_NAME + "\n")
    print(f"embeddings.npy 저장: {emb.shape}, 모델 {D.CLIP_MODEL_NAME}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["meta", "embed", "all"], default="all")
    ap.add_argument("--dataset", default="slpkl/wikiart-subsample")
    ap.add_argument("--hf-split", default="train")
    ap.add_argument("--n-artists", type=int, default=23)
    ap.add_argument("--min-count", type=int, default=50)
    ap.add_argument("--max-per-artist", type=int, default=300)
    ap.add_argument("--image-dir", default="data/images")
    ap.add_argument("--batch-size", type=int, default=64)
    a = ap.parse_args()
    if a.stage in ("meta", "all"):
        stage_meta(a)
    if a.stage in ("embed", "all"):
        stage_embed(a)


if __name__ == "__main__":
    main()
