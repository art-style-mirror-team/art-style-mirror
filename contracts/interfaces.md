# 모듈 인터페이스 (변경 불가 기준)

> 이 파일이 함수 시그니처의 최종 기준이다. `docs/plan.md`와 다르면 이 파일을 따른다.
> 함수 이름·인자·반환 형식은 **팀 합의 후 별도 PR로만** 바꾼다. AI 도구는 이 파일을 수정하지 않는다.
> 확정일: 1일차 (2026-11-19)

## 공통 규칙

- 이미지는 모두 RGB `np.ndarray`, dtype `uint8`, shape `(H, W, 3)`로 주고받는다. `cv2.imread()` 결과(BGR)는 반드시 RGB로 바꾼다.
- 사용자 입력은 `preprocess_input()`을 거친 뒤(긴 변 512px) 다른 함수에 넘긴다. 명화에는 크기 맞추기만 하고 화이트밸런스는 하지 않는다.
- 확률 dict `{name: prob}`는 값이 0~1이고 합이 1이다.
- 최종 순위는 항상 `fuse()` 결과만 쓴다.

## A — `modules/data.py` (홍승민)

| 함수 | 반환 |
| --- | --- |
| `embed_image(img) -> np.ndarray` | CLIP 이미지 임베딩, shape `(512,)`, L2 정규화 |
| `embed_text(texts) -> np.ndarray` | 문장 임베딩, shape `(n, 512)`, 각 행 L2 정규화. `texts`는 `list[str]` |
| `load_index() -> dict` | `{"emb": (N, 512), "meta": DataFrame}`. meta 열은 순서대로 `id, artist, style, genre, path, split`, `split` ∈ `train / val / test`, 행 순서는 `emb`와 같다 |
| `clip_keywords(emb, k=3) -> list[tuple]` | `[("두꺼운 붓 자국", 0.71), ...]` 길이 k, 점수 내림차순 |

## B — `modules/classify.py` (홍예원)

| 함수 | 반환 |
| --- | --- |
| `detect_type(img_emb) -> str` | `"photo"` \| `"painting"` \| `"sketch"` |
| `predict_clip(emb) -> dict` | `{"artists": {name: prob}, "styles": {name: prob}}`, 온도 보정 적용 |
| `similar_works(emb, k=3) -> list[dict]` | `[{"id", "artist", "style", "path", "score"}]` 길이 ≤ k, score 내림차순, 유사도 0.95 이상 제외 |
| `fuse(p_clip, p_cv) -> list[tuple]` | `[(artist, prob)] × 3`, prob 내림차순. `p_clip`은 `predict_clip(emb)["artists"]`, `p_cv`는 `predict_cv()` 결과. `artifacts/calibration.json`의 `w`·`method`를 쓴다 |

## C — `modules/features.py` (심현준)

| 함수 | 반환 |
| --- | --- |
| `preprocess_input(img) -> np.ndarray` | 사용자 입력 전용. 종이 영역 자르기, 화이트밸런스, 긴 변 512px. RGB uint8 |
| `is_grayscale(img) -> bool` | 흑백(스케치) 여부 |
| `extract_features(img, gray=False) -> dict` | 키 11개: `brightness, contrast, saturation, warmth, color_diversity, edge_density, direction, straight_ratio, roughness, stroke_length, palette`. `palette`는 `[[r, g, b], ...]`, 나머지는 float |
| `load_profiles() -> dict` | `{artist: {feature: (mean, std)}}`, 학습셋으로만 계산, `palette` 제외 |
| `predict_cv(features, gray=False) -> dict` | `{artist: prob}`. z값 거리 → 확률, 온도 보정 적용. `gray=True`면 선 특징만 사용 |

## D — `modules/explain.py` (김현승)

| 함수 | 반환 |
| --- | --- |
| `assess_confidence(p_fused, p_clip, p_cv, max_sim) -> dict` | `{"level": "높음"\|"보통"\|"낮음", "margin", "entropy", "jsd", "max_sim"}`. `p_fused`는 `fuse()` 결과, `p_clip`·`p_cv`는 `{artist: prob}`, `max_sim`은 `similar_works()[0]["score"]` |
| `compare(features, profiles, top1, top2) -> dict` | `{"why_top1": [특징 이름 ≤ 2], "toward_top2": [특징 이름 ≤ 2], "z": {feature: 1위 기준 z값}}` |
| `render_card(result) -> (str, Figure)` | 해석 문장(Markdown) + 레이더 차트(matplotlib Figure) |

### `render_card()`에 넘기는 `result` (`app.analyze()`가 만든다)

| 키 | 값 |
| --- | --- |
| `input_type` | `detect_type()` 결과 |
| `gray` | `is_grayscale()` 결과 |
| `top3` | `fuse()` 결과 |
| `styles_top3` | `predict_clip()["styles"]` 상위 3개 `[(style, prob)]` |
| `p_clip_top`, `p_cv_top` | 각 관점의 상위 3개 `[(artist, prob)]` (등급 "낮음"일 때 따로 표시) |
| `confidence` | `assess_confidence()` 결과 |
| `keywords` | `clip_keywords()` 결과 |
| `similar` | `similar_works()` 결과 |
| `features` | `extract_features()` 결과 |
| `top1_profile` | `load_profiles()[top1]` |
| `comparison` | `compare()` 결과 |

## 1일차에 확인이 필요한 부분

plan.md 4장에서 해석이 갈릴 수 있는 곳을 아래처럼 정했다. 다르게 정하려면 1일차 안에 PR로 고친다.

1. `fuse()`의 `p_clip`은 `predict_clip()`이 돌려주는 dict 전체가 아니라 `["artists"]`만 받는다.
2. `fuse()`가 Top 3만 돌려주므로 `assess_confidence()`는 엔트로피를 계산할 때 나머지 확률을 남은 화가에게 고르게 나눈다고 본다. 전체 분포가 필요하면 `fuse()` 반환 형식을 바꾸는 별도 PR이 필요하다.
3. `compare()`의 `why_top1`·`toward_top2`는 문장이 아니라 특징 이름(예: `"brightness"`)이다. 문장은 `render_card()`가 만든다.
