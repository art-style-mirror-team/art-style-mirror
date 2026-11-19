"""Gradio 진입점 (담당: 김현승, D).

실행: python app.py  →  http://127.0.0.1:7860
처리 순서는 plan.md 3장을 따른다. 각 모듈이 스텁이어도 끝까지 돈다.
"""

from __future__ import annotations

import gradio as gr
import numpy as np

from modules import classify, data, explain, features


def analyze(img: np.ndarray) -> dict:
    """이미지 하나를 받아 render_card()가 쓰는 result dict를 만든다. (형식: contracts/interfaces.md)"""
    # 1. 전처리 (C) — 사용자 입력에만 적용
    img = features.preprocess_input(img)
    gray = features.is_grayscale(img)

    # 2. CLIP 관점 (A → B)
    emb = data.embed_image(img)
    input_type = classify.detect_type(emb)
    keywords = data.clip_keywords(emb, k=3)
    p_clip_all = classify.predict_clip(emb)
    p_clip = p_clip_all["artists"]
    similar = classify.similar_works(emb, k=3)

    # 3. OpenCV 관점 (C)
    feats = features.extract_features(img, gray=gray)
    p_cv = features.predict_cv(feats, gray=gray)

    # 4. 신뢰도 (B → D) — 최종 순위는 항상 fuse() 결과
    top3 = classify.fuse(p_clip, p_cv)
    max_sim = similar[0]["score"] if similar else 0.0
    confidence = explain.assess_confidence(top3, p_clip, p_cv, max_sim)

    # 5. 설명 (D)
    profiles = features.load_profiles()
    top1 = top3[0][0]
    top2 = top3[1][0] if len(top3) > 1 else top1
    comparison = explain.compare(feats, profiles, top1, top2)

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


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="닮은 화가·화풍 분석기") as demo:
        gr.Markdown(
            "# 닮은 화가·화풍 분석기\n"
            "사진·그림·스케치를 올리면 닮은 화가 Top 3와 그 이유를 색과 선으로 설명합니다.\n\n"
            f"<sub>{explain.DISCLAIMER}</sub>"
        )
        with gr.Row():
            with gr.Column(scale=1):
                image = gr.Image(type="numpy", image_mode="RGB", label="이미지")
                button = gr.Button("분석하기", variant="primary")
            with gr.Column(scale=1):
                card = gr.Markdown()
                radar = gr.Plot(label="내 그림 vs 1위 화가 평균")
        with gr.Accordion("상세 수치", open=False):
            detail = gr.JSON()
        button.click(run, inputs=image, outputs=[card, radar, detail])
    return demo


if __name__ == "__main__":
    build_demo().launch(server_name="127.0.0.1")
