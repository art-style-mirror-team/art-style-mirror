"""검증셋 작품 중 학습셋과 거의 같은 작품(코사인 0.95 이상) 목록을 만든다.

결과: artifacts/near_duplicates.csv (열: id, split, train_id, sim)
- 검증셋 작품마다 가장 비슷한 학습셋 작품 1개만 기록하고, sim이 기준 이상인 것만 남긴다.
- 테스트셋은 열지 않는다(AGENTS.md 규칙 6). 최종 평가(#26) 때 같은 기준으로 따로 만든다.
- 기준 0.95는 similar_works()의 NEAR_DUPLICATE와 같은 값이다.

사용법: python scripts/find_near_duplicates.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from modules import data as D

THRESHOLD = 0.95
OUT = D.ARTIFACTS / "near_duplicates.csv"


def find_near_duplicates(emb, meta, split="val", threshold=THRESHOLD):
    """split 작품 중 학습셋과 코사인 threshold 이상인 작품을 DataFrame으로 돌려준다."""
    tgt = np.flatnonzero((meta["split"] == split).to_numpy())
    trn = np.flatnonzero((meta["split"] == "train").to_numpy())
    sims = emb[tgt] @ emb[trn].T
    best = sims.argmax(axis=1)
    top = sims[np.arange(len(tgt)), best]
    keep = top >= threshold
    out = pd.DataFrame(
        {
            "id": meta["id"].to_numpy()[tgt[keep]],
            "split": split,
            "train_id": meta["id"].to_numpy()[trn[best[keep]]],
            "sim": np.round(top[keep], 4),
        }
    )
    return out.sort_values("sim", ascending=False).reset_index(drop=True)


if __name__ == "__main__":
    idx = D.load_index()
    if idx["meta"].attrs.get("fake"):
        sys.exit("실제 색인(artifacts/)이 없어 중단합니다.")
    df = find_near_duplicates(idx["emb"], idx["meta"])
    df.to_csv(OUT, index=False)
    n_val = int((idx["meta"]["split"] == "val").sum())
    print(f"{OUT.name}: {len(df)}장 / 검증셋 {n_val}장 ({len(df) / n_val:.1%})")
    print(f"0.99 이상: {int((df['sim'] >= 0.99).sum())}장")
