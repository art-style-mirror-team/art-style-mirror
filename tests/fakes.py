"""테스트용 가짜 모델 함수.

실제 CLIP 모델을 내려받거나 불러오지 않고, 계약(contracts/interfaces.md)과 같은 형식의 결과를
결정적으로 돌려준다. `tests/conftest.py`가 `model` 표시가 없는 테스트에서 이 함수들로 바꿔 끼운다.
"""

from __future__ import annotations

import hashlib

import numpy as np

EMB_DIM = 512


def _seed(*parts: bytes | str) -> int:
    h = hashlib.sha1()
    for p in parts:
        h.update(p.encode("utf-8") if isinstance(p, str) else p)
    return int.from_bytes(h.digest()[:8], "little")


def _unit(v: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(v, axis=-1, keepdims=True)
    return (v / np.maximum(norm, 1e-12)).astype(np.float32)


def fake_embed_image(img: np.ndarray) -> np.ndarray:
    """`data.embed_image`와 같은 형식: (512,), L2 정규화. 같은 이미지는 같은 벡터."""
    img = np.asarray(img)
    if img.dtype != np.uint8 or img.ndim != 3 or img.shape[2] != 3:
        raise ValueError("이미지는 RGB np.ndarray(uint8), shape (H, W, 3)이어야 합니다.")
    rng = np.random.default_rng(_seed("fake-image", img.tobytes(), str(img.shape)))
    return _unit(rng.normal(size=EMB_DIM))


def fake_embed_text(texts: list[str]) -> np.ndarray:
    """`data.embed_text`와 같은 형식: (n, 512), 각 행 L2 정규화."""
    if isinstance(texts, str):
        texts = [texts]
    rows = [np.random.default_rng(_seed("fake-text", t)).normal(size=EMB_DIM) for t in texts]
    return _unit(np.array(rows, dtype=np.float64).reshape(len(texts), EMB_DIM))


# 모듈 경로 → {함수 이름: 가짜}. 모델을 부르는 함수가 늘면 여기에 추가한다.
FAKES = {
    "modules.data": {
        "embed_image": fake_embed_image,
        "embed_text": fake_embed_text,
    },
}
