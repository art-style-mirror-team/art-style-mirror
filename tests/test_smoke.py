"""전체 파이프라인이 오류 없이 돌고, 각 함수가 contracts/interfaces.md 형식을 지키는지 확인한다.
실제 구현으로 바꾼 뒤에도 이 테스트는 그대로 통과해야 한다."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from matplotlib.figure import Figure

import app
from modules import classify, data, explain, features

FEATURE_KEYS = {
    "brightness",
    "contrast",
    "saturation",
    "warmth",
    "color_diversity",
    "edge_density",
    "direction",
    "straight_ratio",
    "roughness",
    "stroke_length",
    "palette",
}


@pytest.fixture
def color_img() -> np.ndarray:
    return np.random.default_rng(0).integers(0, 256, size=(300, 400, 3), dtype=np.uint8)


@pytest.fixture
def sketch_img() -> np.ndarray:
    g = np.random.default_rng(1).integers(150, 256, size=(700, 500), dtype=np.uint8)
    return np.stack([g, g, g], axis=-1)


def _is_prob_dict(p: dict) -> bool:
    return (
        bool(p)
        and all(isinstance(k, str) and 0 <= v <= 1 for k, v in p.items())
        and abs(sum(p.values()) - 1) < 1e-6
    )


# --- A: data -------------------------------------------------------------


def test_embed_image_shape_and_norm(color_img):
    e = data.embed_image(color_img)
    assert e.shape == (512,)
    assert abs(np.linalg.norm(e) - 1) < 1e-5
    assert float(e @ data.embed_image(color_img)) >= 0.99  # #5 완료 기준


def test_embed_text_shape():
    e = data.embed_text(["vivid colors", "muted colors"])
    assert e.shape == (2, 512)
    assert np.allclose(np.linalg.norm(e, axis=1), 1, atol=1e-5)


def test_load_index_format():
    index = data.load_index()
    assert index["emb"].shape[1] == 512
    meta = index["meta"]
    assert isinstance(meta, pd.DataFrame)
    assert list(meta.columns) == ["id", "artist", "style", "genre", "path", "split"]
    assert len(meta) == index["emb"].shape[0]
    assert set(meta["split"]) == {"train", "val", "test"}


def test_clip_keywords_format(color_img):
    kws = data.clip_keywords(data.embed_image(color_img), k=3)
    assert len(kws) == 3
    assert all(isinstance(k, str) and isinstance(s, float) for k, s in kws)
    assert [s for _, s in kws] == sorted((s for _, s in kws), reverse=True)


# --- B: classify ---------------------------------------------------------


def test_classify_formats(color_img):
    emb = data.embed_image(color_img)
    assert classify.detect_type(emb) in {"photo", "painting", "sketch"}

    p = classify.predict_clip(emb)
    assert set(p) == {"artists", "styles"}
    assert _is_prob_dict(p["artists"]) and _is_prob_dict(p["styles"])

    works = classify.similar_works(emb, k=3)
    assert len(works) == 3
    assert all(set(w) == {"id", "artist", "style", "path", "score"} for w in works)

    p_cv = features.predict_cv(features.extract_features(features.preprocess_input(color_img)))
    top3 = classify.fuse(p["artists"], p_cv)
    assert len(top3) == 3
    assert [prob for _, prob in top3] == sorted((prob for _, prob in top3), reverse=True)


def test_similar_works_excludes_itself():
    index = data.load_index()
    works = classify.similar_works(index["emb"][0], k=3)
    assert index["meta"].at[0, "id"] not in {w["id"] for w in works}
    assert all(w["score"] < classify.NEAR_DUPLICATE for w in works)


# --- C: features ---------------------------------------------------------


def test_preprocess_and_grayscale(color_img, sketch_img):
    out = features.preprocess_input(color_img)
    assert out.dtype == np.uint8 and out.ndim == 3 and out.shape[2] == 3
    assert max(out.shape[:2]) == 512
    assert not features.is_grayscale(out)
    assert features.is_grayscale(features.preprocess_input(sketch_img))


@pytest.mark.parametrize("gray", [False, True])
def test_features_and_predict_cv(color_img, gray):
    feats = features.extract_features(features.preprocess_input(color_img), gray=gray)
    assert set(feats) == FEATURE_KEYS
    assert len(feats["palette"]) == 5 and all(len(c) == 3 for c in feats["palette"])
    assert _is_prob_dict(features.predict_cv(feats, gray=gray))


def test_load_profiles_format():
    profiles = features.load_profiles()
    assert set(profiles) == set(data.ARTISTS)
    for prof in profiles.values():
        for mean, std in prof.values():
            assert isinstance(mean, float) and std > 0


# --- D: explain ----------------------------------------------------------


def test_assess_confidence_format():
    p_clip = {"a": 0.7, "b": 0.2, "c": 0.1}
    conf = explain.assess_confidence([("a", 0.6), ("b", 0.3), ("c", 0.1)], p_clip, p_clip, 0.9)
    assert set(conf) == {"level", "margin", "entropy", "jsd", "max_sim"}
    assert conf["level"] == "높음"
    assert conf["jsd"] == pytest.approx(0.0, abs=1e-9)
    assert 0 <= conf["entropy"] <= 1


def test_assess_confidence_low_when_out_of_dataset():
    p = {"a": 0.34, "b": 0.33, "c": 0.33}
    assert explain.assess_confidence(p, p, p, max_sim=0.2)["level"] == "낮음"


def test_compare_with_fake_profiles():
    profiles = {
        "A": {"brightness": (0.8, 0.1), "contrast": (0.2, 0.1), "warmth": (0.5, 0.1)},
        "B": {"brightness": (0.2, 0.1), "contrast": (0.8, 0.1), "warmth": (0.5, 0.1)},
    }
    out = explain.compare(
        {"brightness": 0.75, "contrast": 0.7, "warmth": 0.5, "palette": []}, profiles, "A", "B"
    )
    assert out["why_top1"] == ["brightness"]
    assert out["toward_top2"] == ["contrast"]
    assert set(out["z"]) == {"brightness", "contrast", "warmth"}


# --- 전체 파이프라인 ------------------------------------------------------


@pytest.mark.parametrize("fixture", ["color_img", "sketch_img"])
def test_pipeline_end_to_end(request, fixture):
    result = app.analyze(request.getfixturevalue(fixture))
    text, fig = explain.render_card(result)
    assert isinstance(text, str) and explain.DISCLAIMER in text
    assert isinstance(fig, Figure)
    assert result["confidence"]["level"] in {"높음", "보통", "낮음"}


def test_gradio_app_builds():
    assert app.build_demo() is not None


def test_run_detail_has_no_file_like_dicts(color_img):
    _, _, detail = app.run(color_img)
    assert all("path" not in w for w in detail["similar_works"])
