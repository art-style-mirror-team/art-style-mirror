# API Documentation

이 저장소에는 HTTP/REST/DB API가 없다. API 표면은 (1) `contracts/interfaces.md`가 정한 모듈 함수 계약, (2) `app.analyze()`가 만드는 `result` dict, (3) Gradio 화면, (4) `artifacts/` 파일 계약 네 가지다.

**기준 문서는 `contracts/interfaces.md`다.** 아래 표는 그 파일을 요약하고 현재 구현 상태를 덧붙인 것일 뿐이며, 이름·인자·반환 형식이 다르면 계약 파일이 맞다. 계약은 팀 합의(계약 변경 이슈) 후 별도 PR로만 바꾼다.

## 공통 규칙 (계약)

- 이미지: RGB `np.ndarray`, `uint8`, `(H, W, 3)`. `cv2.imread()` 결과는 RGB로 변환
- 사용자 입력은 `preprocess_input()`(긴 변 512px)을 거친 뒤 다른 함수에 넘긴다. 명화는 크기 맞추기만, 화이트밸런스 없음
- 확률 dict `{name: prob}`: 값 0~1, 합 1
- 최종 순위는 항상 `fuse()` 결과

## 1. 모듈 함수 계약

### A — `modules/data.py`

| 함수 | 반환 (계약) | 구현 상태 |
| --- | --- | --- |
| `embed_image(img) -> np.ndarray` | `(512,)`, L2 정규화 | 스텁 `TODO(#5)`. RGB uint8 3채널이 아니면 `ValueError` |
| `embed_text(texts) -> np.ndarray` | `(n, 512)`, 각 행 L2 정규화, `texts: list[str]` | 스텁 `TODO(#5)`. `str` 하나도 받음 |
| `load_index() -> dict` | `{"emb": (N, 512), "meta": DataFrame[id, artist, style, genre, path, split]}`, `split ∈ train/val/test`, 행 순서 = `emb` | 스텁 `TODO(#3)`. 24명 × 20점(14/3/3) 가짜 색인 |
| `clip_keywords(emb, k=3) -> list[tuple]` | `[(키워드, 점수)]` 길이 k, 점수 내림차순 | 스텁 `TODO(#7)`. 15개 한국어 키워드 중 무작위 |

### B — `modules/classify.py`

| 함수 | 반환 (계약) | 구현 상태 |
| --- | --- | --- |
| `detect_type(img_emb) -> str` | `"photo"` \| `"painting"` \| `"sketch"` | 스텁 `TODO(#8)`. `emb[:3]` argmax |
| `predict_clip(emb) -> dict` | `{"artists": {name: prob}, "styles": {name: prob}}`, 온도 보정 | 스텁 `TODO(#9–#12)`. 학습셋 중심점 코사인 × 20 → softmax(`T_clip`) |
| `similar_works(emb, k=3) -> list[dict]` | `[{"id", "artist", "style", "path", "score"}]` 길이 ≤ k, score 내림차순, 유사도 0.95 이상 제외 | 스텁 `TODO(#13)`. 가짜 색인 전체 검색 |
| `fuse(p_clip, p_cv) -> list[tuple]` | `[(artist, prob)] × 3`, 내림차순. `p_clip = predict_clip()["artists"]`, `calibration.json`의 `w`·`method` | 스텁 `TODO(#15)`. 가중합만, 합집합 정규화 후 상위 3 |

계약 밖 공개 보조: `load_calibration() -> dict` (기본 `{"T_clip": 1.0, "T_cv": 1.0, "w": 0.8, "method": "weighted_sum"}`, `artifacts/calibration.json`이 있으면 덮어씀), 상수 `NEAR_DUPLICATE`(테스트가 참조).

### C — `modules/features.py`

| 함수 | 반환 (계약) | 구현 상태 |
| --- | --- | --- |
| `preprocess_input(img) -> np.ndarray` | 사용자 입력 전용. 종이 영역 자르기, 화이트밸런스, 긴 변 512px, RGB uint8 | 부분 스텁 `TODO(#16)`. 2D→3채널, RGBA→RGB, 긴 변 512px 리사이즈만 |
| `is_grayscale(img) -> bool` | 흑백 여부 | 실제 구현: 채널 최대−최소 평균 < 8 |
| `extract_features(img, gray=False) -> dict` | 키 11개(`brightness, contrast, saturation, warmth, color_diversity, edge_density, direction, straight_ratio, roughness, stroke_length, palette`). `palette = [[r,g,b], ...]`, 나머지 float | 스텁 `TODO(#17)`. 0.1~0.9 가짜 값, `direction` 0~180, 팔레트 5색 |
| `load_profiles() -> dict` | `{artist: {feature: (mean, std)}}`, 학습셋만, `palette` 제외 | 스텁 `TODO(#19)` |
| `predict_cv(features, gray=False) -> dict` | `{artist: prob}`, z값 거리 → 확률, 온도 보정, `gray=True`면 선 특징만 | 식은 plan.md 6.1 그대로, `T = 1.0` 고정 `TODO(#20)` |

### D — `modules/explain.py`

| 함수 | 반환 (계약) | 구현 상태 |
| --- | --- | --- |
| `assess_confidence(p_fused, p_clip, p_cv, max_sim) -> dict` | `{"level": "높음"\|"보통"\|"낮음", "margin", "entropy", "jsd", "max_sim"}` | 구현됨. 경계값 임시(#24) |
| `compare(features, profiles, top1, top2) -> dict` | `{"why_top1": [≤2], "toward_top2": [≤2], "z": {feature: 1위 기준 z}}` | 구현됨 |
| `render_card(result) -> (str, Figure)` | Markdown 해석 문장 + matplotlib 레이더 차트 | 구현됨 |

`assess_confidence` 등급 규칙(현재 임시값): `(margin < 0.05 그리고 jsd > 0.50) 또는 max_sim < 0.50` → 낮음, `margin ≥ 0.15 그리고 jsd ≤ 0.30 그리고 max_sim ≥ 0.75` → 높음, 나머지 보통. 엔트로피는 계약 확인 사항 2에 따라 Top 3 밖 확률을 남은 화가에 고르게 나눈다고 보고 계산한다. JSD는 `scipy`의 `jensenshannon(base=2)` 제곱.

## 2. `result` dict (`app.analyze()` → `render_card()`)

| 키 | 값 |
| --- | --- |
| `input_type` | `detect_type()` 결과 |
| `gray` | `is_grayscale()` 결과 |
| `top3` | `fuse()` 결과 |
| `styles_top3` | `predict_clip()["styles"]` 상위 3 |
| `p_clip_top`, `p_cv_top` | 각 관점 상위 3 `[(artist, prob)]` |
| `confidence` | `assess_confidence()` 결과 |
| `keywords` | `clip_keywords()` 결과 |
| `similar` | `similar_works()` 결과 |
| `features` | `extract_features()` 결과 |
| `top1_profile` | `load_profiles()[top1]` |
| `comparison` | `compare()` 결과 |

## 3. 사용자 인터페이스 (Gradio)

- 실행: `python app.py` → `build_demo().launch(server_name="127.0.0.1")`, 기본 포트 7860
- 입력: `gr.Image(type="numpy", image_mode="RGB")`
- 동작: 버튼 "분석하기" → `run(img)`. 이미지가 없으면 `gr.Error("이미지를 먼저 올려 주세요.")`
- 출력: 결과 카드(`gr.Markdown`), 레이더 차트(`gr.Plot`, "내 그림 vs 1위 화가 평균"), 상세 수치(`gr.JSON`, 접힘): `input_type`, `confidence`, `CLIP Top 3`, `OpenCV Top 3`, `similar_works`(`path` 키 제거)

## 4. 파일 계약 (`artifacts/`, 모두 아직 없음)

| 파일 | 생성 | 사용 | 형식 출처 |
| --- | --- | --- | --- |
| `embeddings.npy`, `meta.csv` | A `scripts/build_index.py` | A `load_index()` | interfaces.md `load_index` |
| `profiles.json` | C `scripts/build_profiles.py` | C `load_profiles()` | `{artist: {feature: [mean, std]}}` (스크립트 docstring) |
| `calibration.json` | B (`eval.ipynb`) | B `load_calibration()` | 키 `T_clip`, `T_cv`, `w`, `method` (`classify.DEFAULT_CALIBRATION`) |
| `linear.pkl` | B (#11) | B `predict_clip()` (예정) | plan.md 5장 |
