"""B — `classify.detect_type()` 동작 테스트 (#8).

모두 가짜 기반이다. `tests/conftest.py`의 autouse fixture가 `modules.data`의 모델
함수를 `tests/fakes.py`의 가짜로 바꿔 끼우므로 실제 CLIP 모델은 내려받지 않는다.
따라서 `@pytest.mark.model`을 붙이지 않는다.
"""

from __future__ import annotations

import numpy as np

from modules import classify, data

TYPES = {"photo", "painting", "sketch"}


def _sample_emb() -> np.ndarray:
    """가짜 `data.embed_image`로 만든 결정적 이미지 임베딩."""
    img = np.random.default_rng(0).integers(0, 256, size=(64, 64, 3), dtype=np.uint8)
    return data.embed_image(img)


def test_detect_type_returns_valid_literal():
    # happy path: 반환은 계약이 정한 세 리터럴 중 하나.
    assert classify.detect_type(_sample_emb()) in TYPES


def test_detect_type_deterministic():
    # 같은 입력 → 같은 결과.
    emb = _sample_emb()
    assert classify.detect_type(emb) == classify.detect_type(emb)


def test_detect_type_matches_prompt_class(monkeypatch):
    # 각 유형을 한 축(one-hot)에 몰아주는 가짜로 바꿔, 그 축 벡터를 넣으면 해당 유형이
    # 나오는지 확인한다. 핵심 정확성: 프로토타입·코사인 argmax가 제대로 작동하는가.
    classes = list(classify.TYPE_PROMPTS)

    def stub(texts):
        if isinstance(texts, str):
            texts = [texts]
        rows = []
        for text in texts:
            vec = np.zeros(512, dtype=np.float32)
            cls = next(c for c in classes if text in classify.TYPE_PROMPTS[c])
            vec[classes.index(cls)] = 1.0
            rows.append(vec)
        return np.array(rows, dtype=np.float32)

    monkeypatch.setattr(data, "embed_text", stub)

    for i, cls in enumerate(classes):
        basis = np.zeros(512, dtype=np.float32)
        basis[i] = 1.0
        assert classify.detect_type(basis) == cls


def test_detect_type_scale_invariant():
    # 방향이 같고 크기만 다른 입력은 같은 유형으로 분류된다(코사인 기반).
    emb = _sample_emb()
    assert classify.detect_type(emb) == classify.detect_type(emb * 3.0)
