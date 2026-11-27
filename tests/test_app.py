"""app.analyze_view()와 _analyze_steps() 동작 테스트 (#37). 모델 함수는 conftest가 가짜로 바꿔 끼운다."""

from __future__ import annotations

import json
from pathlib import Path

import gradio as gr
import numpy as np
import pytest
from PIL import Image

import app


def _png(path: Path, seed: int = 0) -> Path:
    rng = np.random.default_rng(seed)
    Image.fromarray(rng.integers(0, 256, size=(300, 240, 3), dtype=np.uint8)).save(path)
    return path


def _evt(data) -> gr.EventData:
    return gr.EventData(None, data)


@pytest.fixture
def upload_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """tmp_path 안의 폴더를 Gradio 업로드 폴더로 지정한다."""
    folder = tmp_path / "uploads"
    folder.mkdir()
    monkeypatch.setattr(app, "_upload_dir", lambda: folder)
    return folder


def _no_analysis(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*_args, **_kwargs):
        raise AssertionError("분석을 시작하면 안 된다")

    monkeypatch.setattr(app, "_analyze_steps", fail)


def test_analyze_view_reports_four_steps_then_result(upload_dir):
    path = _png(upload_dir / "photo.png")
    out = list(app.analyze_view(_evt({"path": str(path)})))
    assert out[:4] == [{"phase": "loading", "step": n} for n in range(4)]
    assert len(out) == 5
    assert out[-1]["phase"] == "result"
    assert set(out[-1]["view"]) >= {"head", "level", "top3", "radar"}
    json.dumps(out)  # gr.JSON으로 그대로 보낼 수 있어야 한다


def test_analyze_view_rejects_path_outside_upload_dir(upload_dir, tmp_path, monkeypatch):
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    path = _png(outside / "photo.png")
    _no_analysis(monkeypatch)
    sneaky = upload_dir / ".." / "elsewhere" / "photo.png"  # `..`로 폴더 밖을 가리키는 경로
    for raw in (str(path), str(sneaky)):
        out = list(app.analyze_view(_evt({"path": raw})))
        assert len(out) == 1 and out[0]["phase"] == "error"
        assert out[0]["message"]


def test_analyze_view_rejects_non_image_file(upload_dir, monkeypatch):
    path = upload_dir / "notes.png"
    path.write_text("이미지가 아니다", encoding="utf-8")
    _no_analysis(monkeypatch)
    out = list(app.analyze_view(_evt({"path": str(path)})))
    assert out == [
        {"phase": "error", "message": "이미지 파일을 읽지 못했어요. 다른 이미지로 해 보세요."}
    ]


@pytest.mark.parametrize("data", [{}, {"path": ""}, {"path": None}, None])
def test_analyze_view_without_path_is_error(upload_dir, monkeypatch, data):
    _no_analysis(monkeypatch)
    out = list(app.analyze_view(_evt(data)))
    assert out == [{"phase": "error", "message": "이미지를 먼저 골라 주세요."}]


def test_analyze_view_turns_analysis_failure_into_error(upload_dir, monkeypatch):
    path = _png(upload_dir / "photo.png")

    def broken(_img, _ctx=None):
        yield "prepare"
        raise RuntimeError("가짜 고장")

    monkeypatch.setattr(app, "_analyze_steps", broken)
    out = list(app.analyze_view(_evt({"path": str(path)})))
    assert out[0] == {"phase": "loading", "step": 0}
    assert out[-1]["phase"] == "error" and len(out) == 2


def test_analyze_steps_matches_analyze():
    img = np.random.default_rng(5).integers(0, 256, size=(400, 300, 3), dtype=np.uint8)
    steps = app._analyze_steps(img)
    names = []
    while True:
        try:
            names.append(next(steps))
        except StopIteration as done:
            from_steps = done.value
            break
    assert names == list(app.STEP_NAMES)
    expected = app.analyze(img)
    assert set(from_steps) == set(expected)
    assert from_steps["top3"] == expected["top3"]
    assert from_steps["confidence"] == expected["confidence"]
    assert from_steps["comparison"] == expected["comparison"]
    assert from_steps["features"].keys() == expected["features"].keys()


# --- 명화 비교 (FR8, NFR4, NFR7) ---------------------------------------------------------


def _cand(wid: str, artist: str, score: float, path: str = "data/none.jpg") -> dict:
    return {"id": wid, "artist": artist, "style": "Impressionism", "path": path, "score": score}


def _res(level: str = "보통", top1: str = "Claude Monet") -> dict:
    return {"top3": [(top1, 0.5), ("Raphael", 0.3), ("Rembrandt", 0.2)],
            "confidence": {"level": level}}  # fmt: skip


CANDS = [
    _cand("1", "Raphael", 0.9),
    _cand("2", "Rembrandt", 0.85),
    _cand("2", "Rembrandt", 0.85),  # 같은 작품은 한 번만
    _cand("3", "Claude Monet", 0.8),
    _cand("4", "Claude Monet", 0.7),
]


def test_pick_works_puts_top1_artist_work_first():
    out = app._pick_works(CANDS, _res("보통"))
    assert [w["id"] for w in out] == ["3", "1", "2"]
    assert [w["top1_work"] for w in out] == [True, False, False]


@pytest.mark.parametrize(
    ("result", "ids"),
    [(_res("낮음"), ["1", "2", "3"]), (_res("높음", top1="Edgar Degas"), ["1", "2", "3"])],
)
def test_pick_works_falls_back_to_similarity_order(result, ids):
    out = app._pick_works(CANDS, result)
    assert [w["id"] for w in out] == ids
    assert not any(w["top1_work"] for w in out)


def test_compare_works_calls_similar_works_once_with_k30(monkeypatch):
    calls = []

    def fake(emb, k=3):
        calls.append(k)
        return []

    monkeypatch.setattr(app.classify, "similar_works", fake)
    assert app._compare_works(np.zeros(512, dtype=np.float32), _res()) == []
    assert calls == [app.COMPARE_K] == [30]


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """tmp_path를 저장소 루트로 보고, 그 안에 data/wikiart/ 폴더를 만든다."""
    (tmp_path / "data" / "wikiart").mkdir(parents=True)
    monkeypatch.setattr(app, "REPO_ROOT", tmp_path)
    return tmp_path


def test_load_work_outside_data_has_no_image(repo, monkeypatch):
    def fail(*_a, **_k):
        raise AssertionError("data/ 밖 파일의 특징을 구하면 안 된다")

    monkeypatch.setattr(app.features, "extract_features", fail)
    _png(repo / "secret.png")  # data/ 밖
    (repo / "data" / "notes.txt").write_text("x", encoding="utf-8")  # 이미지 확장자가 아님
    for path in (
        "secret.png",
        "data/../secret.png",
        "data/notes.txt",
        "data/missing.jpg",
        "",
        None,
    ):
        out = app._load_work({**_cand("9", "Raphael", 0.5), "path": path, "top1_work": False})
        assert out["image"] is None and out["features"] is None
        assert out["id"] == "9" and "path" not in out


def test_load_work_inside_data_gives_data_url_and_features(repo, monkeypatch):
    import base64
    import io

    def no_wb(*_a, **_k):
        raise AssertionError("명화에는 화이트밸런스(preprocess_input)를 쓰지 않는다")

    seen = []
    real = app.features.extract_features

    def spy(img, gray=False):
        seen.append((img.shape, img.dtype, gray))
        return real(img, gray=gray)

    monkeypatch.setattr(app.features, "preprocess_input", no_wb)
    monkeypatch.setattr(app.features, "extract_features", spy)
    rng = np.random.default_rng(1)
    Image.fromarray(rng.integers(0, 256, size=(1000, 800, 3), dtype=np.uint8)).save(
        repo / "data" / "wikiart" / "claude-monet_3.png"
    )
    out = app._load_work(
        {**_cand("3", "Claude Monet", 0.8, "data/wikiart/claude-monet_3.png"), "top1_work": True}
    )
    assert seen == [((512, 410, 3), np.dtype("uint8"), False)]  # 긴 변 512px, RGB uint8
    assert out["features"]["palette"] and out["top1_work"] is True
    assert out["image"].startswith("data:image/jpeg;base64,")
    raw = base64.b64decode(out["image"].split(",", 1)[1])
    with Image.open(io.BytesIO(raw)) as im:
        assert max(im.size) == app.WORK_THUMB_SIDE


def test_analyze_view_result_has_compare(upload_dir, monkeypatch):
    calls = {"embed": 0}
    real_embed = app.data.embed_image

    def counting(img):
        calls["embed"] += 1
        return real_embed(img)

    monkeypatch.setattr(app.data, "embed_image", counting)
    path = _png(upload_dir / "photo.png")
    out = list(app.analyze_view(_evt({"path": str(path)})))
    view = out[-1]["view"]
    assert out[-1]["phase"] == "result"
    assert calls["embed"] == 1  # 명화 비교가 CLIP을 다시 부르지 않는다 (NFR4)
    assert view["compare"] is not None and 1 <= len(view["compare"]["works"]) <= 3
    # 스텁 색인의 path(data/wikiart/...)는 지금 파일이 없으므로 이미지·특징 없이 보인다
    assert all(w["image"] is None and w["radar"] is None for w in view["compare"]["works"])
    json.dumps(out)


def test_analyze_view_hides_compare_when_it_fails(upload_dir, monkeypatch, caplog):
    real = app.classify.similar_works

    def broken(emb, k=3):
        if k == app.COMPARE_K:  # 분석 안의 similar_works(k=3)는 그대로 두고 비교용만 고장
            raise RuntimeError("가짜 고장")
        return real(emb, k=k)

    monkeypatch.setattr(app.classify, "similar_works", broken)
    path = _png(upload_dir / "photo.png")
    with caplog.at_level("WARNING", logger="app"):
        out = list(app.analyze_view(_evt({"path": str(path)})))
    assert out[-1]["phase"] == "result"
    assert out[-1]["view"]["compare"] is None
    assert "비교 명화" in caplog.text
