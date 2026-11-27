"""Gradio 진입점 (담당: 김현승, D).

실행: python app.py  →  http://127.0.0.1:7860
처리 순서는 plan.md 3장을 따른다. 각 모듈이 스텁이어도 끝까지 돈다.

화면은 G안 글래스 화면(#37)이다. `gr.HTML` 하나가 화면 전체를 맡고, `static/g.js`가 DOM을 그리며
`static/g.css`가 모양을 정한다. 화면은 사진을 올린 뒤 `trigger('submit', {path})`로 `analyze_view`를
부르고, `analyze_view`가 단계마다 내보내는 화면 상태(dict)는 숨긴 `gr.JSON`을 거쳐
`window.gApp.update()`로 화면에 전달된다.
"""

from __future__ import annotations

import base64
import io
import logging
from collections.abc import Generator, Iterator
from pathlib import Path

import gradio as gr
import numpy as np
from gradio.utils import get_upload_folder
from PIL import Image, ImageOps

from modules import classify, data, explain, features

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent
STATIC_DIR = REPO_ROOT / "static"
# 명화 비교(FR8): similar_works()를 한 번 더 부를 때의 후보 수, 화면에 보일 명화 수,
# 브라우저로 보낼 수 있는 이미지 확장자(저장소 data/ 폴더 안의 파일만, NFR7), 화면용 이미지 긴 변.
COMPARE_K = 30
COMPARE_N = 3
WORK_IMAGE_EXTS = frozenset({".jpg", ".jpeg", ".png", ".webp"})
WORK_LONG_SIDE = 512
WORK_THUMB_SIDE = 320
# 분석 단계 이름. 화면(static/g.js의 STEPS)은 이 순서의 번호(0~3)로 진행을 표시한다.
STEP_NAMES = ("prepare", "clip", "opencv", "fuse")
FONTS_HEAD = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;'
    '500;700&family=Noto+Serif+KR:wght@600;700&display=swap">'
)
# 숨긴 gr.JSON 값이 바뀌면 화면에 넘긴다(Python 함수 없이 브라우저에서만 실행).
UPDATE_JS = "(v) => { if (window.gApp) { window.gApp.update(v); } }"


def _analyze_steps(img: np.ndarray, ctx: dict | None = None) -> Generator[str, None, dict]:
    """analyze()의 처리 순서. 각 단계를 시작하기 전에 단계 이름(STEP_NAMES)을 내보내고,
    끝나면 result를 돌려준다(StopIteration.value). 모델 호출 수·순서는 analyze()와 같다.

    ctx(dict)를 넘기면 계산한 이미지 임베딩을 ctx["emb"]에 담는다. 명화 비교(analyze_view)가
    CLIP을 다시 부르지 않고 같은 임베딩을 쓰기 위한 내부 인자이며, result는 바뀌지 않는다."""
    # 1. 전처리 (C) — 사용자 입력에만 적용
    yield "prepare"
    img = features.preprocess_input(img)
    gray = features.is_grayscale(img)

    # 2. CLIP 관점 (A → B)
    yield "clip"
    emb = data.embed_image(img)
    if ctx is not None:
        ctx["emb"] = emb
    input_type = classify.detect_type(emb)
    keywords = data.clip_keywords(emb, k=3)
    p_clip_all = classify.predict_clip(emb)
    p_clip = p_clip_all["artists"]
    similar = classify.similar_works(emb, k=3)

    # 3. OpenCV 관점 (C)
    yield "opencv"
    feats = features.extract_features(img, gray=gray)
    p_cv = features.predict_cv(feats, gray=gray)

    # 4. 신뢰도 (B → D) — 최종 순위는 항상 fuse() 결과
    yield "fuse"
    top3 = classify.fuse(p_clip, p_cv)
    max_sim = similar[0]["score"] if similar else 0.0
    confidence = explain.assess_confidence(top3, p_clip, p_cv, max_sim)

    # 5. 설명 (D)
    profiles = features.load_profiles()
    top1 = top3[0][0]
    top2 = top3[1][0] if len(top3) > 1 else top1
    # 스케치는 색 특징을 빼고 선 특징만 대조한다(predict_cv(gray=True)와 같은 기준).
    cmp_feats = {f: feats[f] for f in features.LINE_FEATURES if f in feats} if gray else feats
    comparison = explain.compare(cmp_feats, profiles, top1, top2)

    def _top(p: dict, k: int = 3) -> list[tuple]:
        return sorted(p.items(), key=lambda x: -x[1])[:k]

    return {
        "input_type": input_type,
        "gray": gray,
        "top3": top3,
        "styles_top3": _top(p_clip_all["styles"]),
        "p_clip_top": _top(p_clip),
        "p_cv_top": _top(p_cv),
        "confidence": confidence,
        "keywords": keywords,
        "similar": similar,
        "features": feats,
        "top1_profile": profiles[top1],
        "comparison": comparison,
    }


def _finish(steps: Generator[str, None, dict]) -> dict:
    """단계 생성기를 끝까지 돌려 result를 돌려준다."""
    while True:
        try:
            next(steps)
        except StopIteration as done:
            return done.value


def analyze(img: np.ndarray) -> dict:
    """이미지 하나를 받아 render_card()가 쓰는 result dict를 만든다. (형식: contracts/interfaces.md)"""
    return _finish(_analyze_steps(img))


def run(img: np.ndarray | None):
    if img is None:
        raise gr.Error("이미지를 먼저 올려 주세요.")
    result = analyze(img)
    text, fig = explain.render_card(result)
    detail = {
        "input_type": result["input_type"],
        "confidence": result["confidence"],
        "CLIP Top 3": result["p_clip_top"],
        "OpenCV Top 3": result["p_cv_top"],
        # "path" 키가 있으면 Gradio가 파일로 오인해 내려받으려 하므로 화면용 dict에서는 뺀다.
        "similar_works": [{k: v for k, v in w.items() if k != "path"} for w in result["similar"]],
    }
    return text, fig, detail


# --- G안 화면 연결 (#37) ---------------------------------------------------------------


def _upload_dir() -> Path:
    """Gradio가 업로드한 파일을 두는 폴더(GRADIO_TEMP_DIR, 없으면 시스템 임시 폴더/gradio).
    테스트는 이 함수를 바꿔 끼워 업로드 폴더를 정한다."""
    return Path(get_upload_folder())


def _safe_upload_path(raw: str) -> Path | None:
    """화면이 보낸 경로가 업로드 폴더 안의 실제 파일이면 그 경로, 아니면 None.
    심볼릭 링크·`..`는 풀어서 비교하므로 폴더 밖 파일은 읽지 않는다."""
    try:
        root = _upload_dir().resolve()
        path = Path(raw).resolve(strict=True)
    except (OSError, RuntimeError, ValueError):
        return None
    if path == root or not path.is_relative_to(root) or not path.is_file():
        return None
    return path


def _read_rgb(path: Path) -> np.ndarray:
    """이미지 파일을 RGB np.ndarray(uint8)로 읽는다. 휴대폰 사진의 EXIF 회전을 반영한다."""
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im)
        return np.asarray(im.convert("RGB"), dtype=np.uint8).copy()


def _error(message: str) -> dict:
    return {"phase": "error", "message": message}


# --- 명화 비교 (FR8) ------------------------------------------------------------------


def _pick_works(candidates: list[dict], result: dict) -> list[dict]:
    """비교 명화 최대 COMPARE_N점을 고른다(FR8.1). 후보는 similar_works() 결과(비슷한 순).

    등급이 높음·보통이고 후보에 1위 화가 작품이 있으면 그중 가장 비슷한 1점을 맨 앞에 두고,
    나머지는 화가와 상관없이 비슷한 순으로 채운다. 그 밖에는 비슷한 순 COMPARE_N점이다.
    같은 id는 한 번만 넣는다. 각 항목에 top1_work(1위 화가 작품인지)를 붙인다."""
    top1 = str(result["top3"][0][0]) if result.get("top3") else ""
    low = result.get("confidence", {}).get("level") == "낮음"
    ordered = list(candidates)
    if not low:
        first = next((w for w in ordered if str(w.get("artist")) == top1), None)
        if first is not None:
            ordered = [first] + [w for w in ordered if w is not first]
    picked: list[dict] = []
    seen: set[str] = set()
    for w in ordered:
        wid = str(w.get("id"))
        if wid in seen:
            continue
        seen.add(wid)
        picked.append({**w, "top1_work": (not low) and str(w.get("artist")) == top1})
        if len(picked) >= COMPARE_N:
            break
    return picked


def _safe_data_path(raw) -> Path | None:
    """similar_works()의 path가 저장소 data/ 폴더 안의 실제 이미지 파일이면 그 경로, 아니면 None.
    상대 경로는 저장소 루트 기준으로 풀고, 링크·`..`를 풀어 실제 위치로 확인한다(NFR7)."""
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        root = (REPO_ROOT / "data").resolve(strict=True)
        p = Path(raw)
        path = (p if p.is_absolute() else REPO_ROOT / p).resolve(strict=True)
    except (OSError, RuntimeError, ValueError):
        return None
    if not path.is_relative_to(root) or not path.is_file():
        return None
    if path.suffix.lower() not in WORK_IMAGE_EXTS:
        return None
    return path


def _read_work(path: Path) -> np.ndarray:
    """명화 파일을 RGB uint8, 긴 변 WORK_LONG_SIDE(512)px로 읽는다. 화이트밸런스는 하지 않는다
    (features.preprocess_input()을 쓰지 않음)."""
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        w, h = im.size
        scale = WORK_LONG_SIDE / max(w, h)
        if scale != 1.0:
            im = im.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
        return np.asarray(im, dtype=np.uint8).copy()


def _jpeg_data_url(img: np.ndarray, long_side: int = WORK_THUMB_SIDE) -> str:
    """화면용 JPEG data URL(긴 변 long_side px). 파일 경로를 브라우저에 알리지 않는다."""
    im = Image.fromarray(img)
    im.thumbnail((long_side, long_side), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=82)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def _load_work(work: dict) -> dict:
    """명화 한 점의 화면용 이미지와 특징. 파일이 없거나 못 읽으면 image·features는 None."""
    out = {k: work.get(k) for k in ("id", "artist", "style", "score", "top1_work")}
    out.update(image=None, features=None)
    path = _safe_data_path(work.get("path"))
    if path is None:
        return out
    try:
        img = _read_work(path)
        out["features"] = features.extract_features(img, gray=features.is_grayscale(img))
        out["image"] = _jpeg_data_url(img)
    except (OSError, ValueError, Image.DecompressionBombError) as e:
        logger.warning("명화 이미지를 읽지 못했습니다: %s (%s)", path.name, e)
        out.update(image=None, features=None)
    return out


def _compare_works(emb: np.ndarray, result: dict) -> list[dict]:
    """명화 페이지에 보일 명화 최대 3점. similar_works(k=30)를 한 번 부르고(NFR4),
    고른 명화마다 data/ 안의 파일이 있으면 이미지(data URL)와 특징을 붙인다."""
    candidates = classify.similar_works(emb, k=COMPARE_K)
    return [_load_work(w) for w in _pick_works(candidates, result)]


def analyze_view(evt: gr.EventData) -> Iterator[dict]:
    """화면의 trigger('submit', {path}) 처리기. 화면 상태(dict)를 차례로 내보낸다.

    - 분석 단계마다 {"phase": "loading", "step": 0~3}
    - 끝나면 {"phase": "result", "view": explain.build_view(result, works)}
      (works = 명화 비교용 명화 목록. 계산에 실패하면 경고를 남기고 []로 결과는 그대로 보인다)
    - 경로 없음·업로드 폴더 밖·이미지가 아님·분석 오류는 {"phase": "error", "message": 한 줄}
    예외는 밖으로 내보내지 않는다(화면이 한 줄 알림 후 첫 화면으로 돌아간다).
    """
    payload = getattr(evt, "_data", None)
    raw = payload.get("path") if isinstance(payload, dict) else None
    if not isinstance(raw, str) or not raw.strip():
        yield _error("이미지를 먼저 골라 주세요.")
        return
    path = _safe_upload_path(raw)
    if path is None:
        logger.warning("업로드 폴더 밖이거나 없는 경로를 거부했습니다: %r", raw)
        yield _error("올린 이미지를 찾지 못했어요. 다시 골라 주세요.")
        return
    try:
        img = _read_rgb(path)
    except (OSError, ValueError, Image.DecompressionBombError) as e:
        logger.info("이미지를 읽지 못했습니다: %s (%s)", path.name, e)
        yield _error("이미지 파일을 읽지 못했어요. 다른 이미지로 해 보세요.")
        return

    try:
        ctx: dict = {}
        steps = _analyze_steps(img, ctx)
        while True:
            try:
                name = next(steps)
            except StopIteration as done:
                result = done.value
                break
            yield {"phase": "loading", "step": STEP_NAMES.index(name)}
        try:
            works = _compare_works(ctx["emb"], result)
        except Exception:
            # 명화 비교는 덧붙는 화면이라 실패해도 결과는 보인다(명화 페이지만 숨김, FR8.9).
            logger.warning("비교 명화를 고르지 못해 명화 페이지를 숨깁니다.", exc_info=True)
            works = []
        view = explain.build_view(result, works)
    except Exception:
        logger.exception("분석 중 오류: %s", path.name)
        yield _error("분석 중 문제가 생겼어요. 다른 이미지로 다시 해 보세요.")
        return
    yield {"phase": "result", "view": view}


def _read_static(name: str) -> str:
    path = STATIC_DIR / name
    try:
        return path.read_text(encoding="utf-8")
    except OSError as e:
        raise RuntimeError(f"화면 파일을 읽지 못했습니다: {path} ({e})") from e


def build_demo() -> gr.Blocks:
    css = _read_static("g.css")
    js = _read_static("g.js")
    with gr.Blocks(title="닮은 화가·화풍 분석기") as demo:
        # @keyframes는 컴포넌트 범위 CSS(css_template은 "#id { ... }" 안에 중첩) 안에 둘 수 없어
        # g.css 전체를 head의 전역 <style>로 싣는다. 선택자는 모두 .g- 접두.
        screen = gr.HTML(
            value="",
            html_template='<div class="g-root"></div>',
            js_on_load=js,
            head=FONTS_HEAD + "<style>" + css + "</style>",
            apply_default_css=False,
            elem_id="g-screen",
            disclaimer=explain.DISCLAIMER,
        )
        # 진행·결과 전달용. visible="hidden"은 DOM에 남아 change 이벤트가 돈다
        # (visible=False면 브라우저에 컴포넌트가 만들어지지 않는다).
        state = gr.JSON(value=None, visible="hidden", elem_id="g-state")
        analysis = screen.submit(analyze_view, inputs=None, outputs=state, show_progress="hidden")
        screen.stop(fn=None, inputs=None, outputs=None, cancels=[analysis])
        state.change(fn=None, inputs=state, outputs=None, js=UPDATE_JS)
    return demo


# `gradio app.py`(코드를 저장하면 자동 재시작)는 모듈의 `demo` 변수를 찾아 띄운다.
demo = build_demo()

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1")
