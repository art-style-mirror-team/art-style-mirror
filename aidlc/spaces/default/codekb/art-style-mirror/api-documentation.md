# API Documentation

이 저장소에는 HTTP/REST/DB API가 없다. API 표면은 (1) `contracts/interfaces.md`가 정한 모듈 함수 계약, (2) `app.analyze()`가 만드는 `result` dict, (3) Gradio 화면, (4) `artifacts/` 파일 계약 네 가지다. (5)는 D 쪽 출력을 바꿀 때 지켜야 하는 형식을 테스트 기준으로 모은 것이다.

**기준 문서는 `contracts/interfaces.md`다.** 아래 표는 그 파일을 요약하고 현재 구현 상태를 덧붙인 것일 뿐이며, 이름·인자·반환 형식이 다르면 계약 파일이 맞다. 계약은 팀 합의(계약 변경 이슈) 후 별도 PR로만 바꾸고, AI 도구는 이 파일을 고치지 않는다.

## 공통 규칙 (계약)

- 이미지: RGB `np.ndarray`, `uint8`, `(H, W, 3)`. `cv2.imread()` 결과는 RGB로 변환
- 사용자 입력은 `preprocess_input()`(긴 변 512px)을 거친 뒤 다른 함수에 넘긴다. 명화는 크기 맞추기만, 화이트밸런스 없음
- 확률 dict `{name: prob}`: 값 0~1, 합 1
- 최종 순위는 항상 `fuse()` 결과

## 1. 모듈 함수 계약

A·B·C의 "구현 상태" 열은 2026-11-19 전체 스캔 기준이다(이후 스캔은 훑어보기만 함). D는 2026-11-27 기준이다.

### A — `modules/data.py`

| 함수 | 반환 (계약) | 구현 상태 |
| --- | --- | --- |
| `embed_image(img) -> np.ndarray` | `(512,)`, L2 정규화 | 스텁 `TODO(#5)`. RGB uint8 3채널이 아니면 `ValueError` |
| `embed_text(texts) -> np.ndarray` | `(n, 512)`, 각 행 L2 정규화, `texts: list[str]` | 스텁 `TODO(#5)`. `str` 하나도 받음 |
| `load_index() -> dict` | `{"emb": (N, 512), "meta": DataFrame[id, artist, style, genre, path, split]}`, `split ∈ train/val/test`, 행 순서 = `emb` | 스텁 `TODO(#3)`. 24명 × 20점(14/3/3) 가짜 색인. `path`는 실제 파일이 없는 `data/wikiart/<artist>_<id>.jpg` |
| `clip_keywords(emb, k=3) -> list[tuple]` | `[(키워드, 점수)]` 길이 k, 점수 내림차순 | 스텁 `TODO(#7)`. `KEYWORDS` 15개 한국어 명사구(예: "두꺼운 붓 자국", "꿈같은 분위기", "정물") 중 무작위, 점수 0.55~0.85 소수 둘째 자리 (2026-11-27 훑어보기로 확인) |

### B — `modules/classify.py`

| 함수 | 반환 (계약) | 구현 상태 |
| --- | --- | --- |
| `detect_type(img_emb) -> str` | `"photo"` \| `"painting"` \| `"sketch"` | 스텁 `TODO(#8)`. `emb[:3]` argmax (PR #56 대기) |
| `predict_clip(emb) -> dict` | `{"artists": {name: prob}, "styles": {name: prob}}`, 온도 보정 | 스텁 `TODO(#9–#12)`. 학습셋 중심점 코사인 × 20 → softmax(`T_clip`) |
| `similar_works(emb, k=3) -> list[dict]` | `[{"id", "artist", "style", "path", "score"}]` 길이 ≤ k, score 내림차순, 유사도 0.95 이상 제외 | #13에서 정리: 정규화 코사인, 색인 전체, 동점은 행 순서, `k <= 0`이면 `[]` |
| `fuse(p_clip, p_cv) -> list[tuple]` | `[(artist, prob)] × 3`, 내림차순. `p_clip = predict_clip()["artists"]`, `calibration.json`의 `w`·`method` | 스텁 `TODO(#15)`. 가중합만, 합집합 정규화 후 상위 3 |

계약 밖 공개 보조: `load_calibration() -> dict` (기본 `{"T_clip": 1.0, "T_cv": 1.0, "w": 0.8, "method": "weighted_sum"}`, `artifacts/calibration.json`이 있으면 덮어씀), 상수 `NEAR_DUPLICATE`(테스트가 참조).

### C — `modules/features.py`

| 함수 | 반환 (계약) | 구현 상태 |
| --- | --- | --- |
| `preprocess_input(img) -> np.ndarray` | 사용자 입력 전용. 종이 영역 자르기, 화이트밸런스, 긴 변 512px, RGB uint8 | 부분 스텁 `TODO(#16)` |
| `is_grayscale(img) -> bool` | 흑백 여부 | 실제 구현 |
| `extract_features(img, gray=False) -> dict` | 키 11개(`brightness, contrast, saturation, warmth, color_diversity, edge_density, direction, straight_ratio, roughness, stroke_length, palette`). `palette = [[r,g,b], ...]`, 나머지 float | 부분 스텁 `TODO(#17)`. `direction`은 PR #44 머지로 0~1 "방향 일관성"(`docs/notes/D.md`), 팔레트 5색 |
| `load_profiles() -> dict` | `{artist: {feature: (mean, std)}}`, 학습셋만, `palette` 제외 | 스텁 `TODO(#19)` |
| `predict_cv(features, gray=False) -> dict` | `{artist: prob}`, z값 거리 → 확률, 온도 보정, `gray=True`면 선 특징만 | 식은 plan.md 6.1 그대로, `T = 1.0` 고정 `TODO(#20)` |

계약 밖 공개 상수(`app.py`·테스트가 참조): `COLOR_FEATURES`(5개), `LINE_FEATURES`(5개), `NUMERIC_FEATURES`.

### D — `modules/explain.py`

| 함수 | 반환 (계약) | 구현 상태 |
| --- | --- | --- |
| `assess_confidence(p_fused, p_clip, p_cv, max_sim) -> dict` | `{"level": "높음"\|"보통"\|"낮음", "margin", "entropy", "jsd", "max_sim"}` | 구현됨. 경계값 임시(#24). `p_fused`는 리스트·dict 둘 다 받음 |
| `compare(features, profiles, top1, top2) -> dict` | `{"why_top1": [≤2], "toward_top2": [≤2], "z": {feature: 1위 기준 z}}` | 구현됨(#21). 계약 확인 사항 3: 목록은 문장이 아니라 특징 이름, 문장은 `render_card()`가 만든다 |
| `render_card(result) -> (str, Figure)` | 해석 문장(Markdown) + matplotlib 레이더 차트 | 구현됨. **문장 내용은 계약이 정하지 않는다** — #22 대상 |

`assess_confidence` 등급 규칙(현재 임시값): `(margin < 0.05 그리고 jsd > 0.50) 또는 max_sim < 0.50` → 낮음, `margin ≥ 0.15 그리고 jsd ≤ 0.30 그리고 max_sim ≥ 0.75` → 높음, 나머지 보통. `margin`은 1·2위 차이(후보가 하나면 그 확률). 엔트로피는 계약 확인 사항 2에 따라 Top 3 밖 확률을 남은 화가에 고르게 나눈다고 보고 계산하며, `K = max(len(p_clip), len(p_cv), len(top3))`. JSD는 `scipy`의 `jensenshannon(base=2)` 제곱이며 한쪽 합이 0이면 1.0.

`compare` 동작: 두 프로필과 `features`에 모두 있고 유한한 실수(bool 제외, numpy 실수 허용)이며 프로필 값이 `(mean, std)` 모양인 특징만 비교한다. z = (x − mean) / max(std, `EPS`=0.01). `gap = |z2| − |z1|`이 `GAP_TOL`(1e-9)보다 크면 `why_top1`, 작으면(음수) `toward_top2`, 각각 차이가 큰 순·동점은 이름 순으로 최대 2개. `top1 == top2`이면 두 목록은 비우고 `z`만. 프로필에 없는 화가는 `KeyError`.

#### `render_card` 출력 (2026-11-27, `explain.py:209-264`)

순서대로 아래 줄을 `"\n"`으로 이어 붙인다. 분기 그림은 `architecture.md`의 "결과 카드 만들기".

| 순서 | 조건 | 문구(그대로) | 쓰는 `result` 키 |
| --- | --- | --- | --- |
| 1 | 항상 | `### {TYPE_INTRO[input_type] 또는 '이 이미지는'} 이런 화가와 닮았어요` | `input_type` |
| 2a | `level == "낮음"` | `**신뢰 등급: 낮음** — {LEVEL_NOTE} 두 관점의 결과를 따로 보여드릴게요.` + `- 소재·분위기·양식(CLIP): 화가 n%, …` + `- 색·선(OpenCV): 화가 n%, …` | `confidence.level`, `p_clip_top`, `p_cv_top` |
| 2b | 높음·보통 | `1. **화가** — n%` × Top 3, `**신뢰 등급: {level}**` (+ ` — {LEVEL_NOTE}`, 문구가 빈 문자열이 아닐 때만 = 보통) | `top3`, `confidence.level` |
| 3 | CLIP 1위 ≠ OpenCV 1위 | `분위기는 **{clip 1위}**, 색감·선은 **{cv 1위}** 쪽에 가까워요.` (입력 유형·`gray`와 무관) | `p_clip_top`, `p_cv_top` |
| 4 | 항상 | `**닮은 화풍**: 화풍 n%, …` | `styles_top3` |
| 5 | 항상 | `**CLIP 키워드**: 키워드(0.71), …` (나열, 문장 아님) | `keywords` |
| 6 | `why_top1` 있음 | `**{top1}인 이유**: {특징 한글, …}이(가) {top1} 평균에 더 가까워요.` | `comparison`, `top3` |
| 7 | 2위 있음 + `toward_top2` 있음 | `**{top2} 느낌이 나는 부분**: {특징 한글, …}` | `comparison`, `top3` |
| 8 | `similar` 있음 | `**비슷한 명화**: 화가 #id (0.87), …` | `similar` |
| 9 | 항상 | `<sub>1·2위 차이 · 엔트로피 · 관점 차이(JSD) · 데이터셋 유사도</sub>` (소수 둘째 자리) | `confidence` |
| 10 | 항상 | `> {DISCLAIMER}` | — |

확률은 `_pct()` = `f"{p*100:.0f}%"`, 특징 이름 목록은 `_ko_list()` = `FEATURE_KO`로 바꿔 `", "`로 잇는다. `result["gray"]`, `result["features"]`·`top1_profile`은 문장에 쓰지 않는다(뒤 둘은 레이더용).

레이더 `Figure`: 5×5인치·100dpi 극좌표, "내 그림"(`#d9480f` 실선)과 "`{1위} 평균`"(`#1c7ed6` 점선), 반투명 채우기 0.15. 축은 `FEATURE_KO` 순서 중 프로필에 있고 값이 `int`/`float`인 특징, 값은 `_radar_value()`로 0~1에 자르기만 한다(#45부터 `direction`도 변환 없음). 한글 글꼴은 `Malgun Gothic → AppleGothic → NanumGothic → Noto Sans CJK KR → Noto Sans KR` 중 설치된 첫 글꼴.

#### D 화면 문구 상수 (2026-11-27)

| 상수 | 값 |
| --- | --- |
| `FEATURE_KO` | `brightness` 밝기, `contrast` 대비, `saturation` 채도, `warmth` 색온도, `color_diversity` 색 다양성, `edge_density` 선 밀도, `direction` 선 방향 일관성, `straight_ratio` 직선 비율, `roughness` 거칠기, `stroke_length` 윤곽선 길이 (`palette` 없음) |
| `TYPE_INTRO` | `photo` "사진을 그림처럼 놓고 보면", `painting` "이 그림은", `sketch` "이 스케치의 선을 보면" (없으면 "이 이미지는") |
| `LEVEL_NOTE` | `높음` "", `보통` "애매한 부분이 있어요.", `낮음` "뚜렷하게 닮은 화가가 없어요." |
| `DISCLAIMER` | "픽셀 수치 기반의 통계적 해석이며 미술사적 평가가 아닙니다." (`app.build_demo()`도 사용) |

이전 CodeKB의 "`direction` 라벨은 '선 방향', `/180` 변환" 설명은 PR #46·#44 머지(2026-11-27)로 더 이상 맞지 않는다.

## 2. `result` dict (`app.analyze()` → `render_card()`)

`app.analyze()`가 만드는 키는 12개다(계약 표는 `p_clip_top`·`p_cv_top`을 한 행에 적어 11행).

| 키 | 값 | 카드·화면 활용 |
| --- | --- | --- |
| `input_type` | `detect_type()` 결과: `"photo"`\|`"painting"`\|`"sketch"` | 카드 제목(`TYPE_INTRO`). 그 밖의 문장에는 안 씀 |
| `gray` | `is_grayscale()` 결과 (`bool`, 테스트가 `is`로 비교) | 카드에서 안 씀. `app.analyze` 안에서 대조 특징을 선으로 줄이는 데만 씀 |
| `top3` | `fuse()` 결과 | 최종 순위의 유일한 출처 |
| `styles_top3` | `predict_clip()["styles"]` 상위 3 | "닮은 화풍" 줄 |
| `p_clip_top`, `p_cv_top` | 각 관점 상위 3 `[(artist, prob)]` | 등급 "낮음"·관점 엇갈림 표시 |
| `confidence` | `assess_confidence()` 결과 | 등급 분기·문구, 지표 4개 |
| `keywords` | `clip_keywords()` 결과 `[(키워드, 점수)]` | "CLIP 키워드" 줄 |
| `similar` | `similar_works()` 결과 | `path`는 스텁 가짜 경로라 이미지 없음. Gradio 출력에 그대로 넘기면 파일로 오인됨 |
| `features` | `extract_features()` 결과 (스케치여도 11개 키 유지) | 레이더 "내 그림" |
| `top1_profile` | `load_profiles()[top1]` | 레이더 "1위 화가 평균" |
| `comparison` | `compare()` 결과 | "이유"·"2위 느낌" 문장 |

## 3. 사용자 인터페이스 (Gradio, 2026-11-27 현재)

- 실행: `python app.py` → `demo.launch(server_name="127.0.0.1")`, 기본 포트 7860. `gradio app.py`(자동 재시작)는 모듈 변수 `demo`를 찾는다
- 구성: `gr.Blocks(title="닮은 화가·화풍 분석기")` → 제목·설명 Markdown(끝에 `<sub>DISCLAIMER</sub>`) → `gr.Row` 안 2열(`scale=1`씩): 왼쪽 `gr.Image(type="numpy", image_mode="RGB", label="이미지")` + `gr.Button("분석하기", variant="primary")`, 오른쪽 `gr.Markdown()` 카드 + `gr.Plot(label="내 그림 vs 1위 화가 평균")` → `gr.Accordion("상세 수치", open=False)` 안 `gr.JSON()`
- 이벤트: `button.click(run, inputs=image, outputs=[card, radar, detail])` 하나뿐. 이미지가 없으면 `gr.Error("이미지를 먼저 올려 주세요.")`
- 상세 JSON: `input_type`, `confidence`, `CLIP Top 3`, `OpenCV Top 3`, `similar_works`(`path` 키 제거)
- 쓰지 않는 것: 사용자 CSS·JS·`head`, 정적 파일, 테마, 카메라 소스 지정, 진행 표시, 상태(`gr.State`), 여러 페이지·탭. #37 G안 화면은 이 브랜치에 없다
- 카드 문장은 `gr.Markdown`에 그대로 들어가므로 #22에서 문장이 바뀌어도 화면 코드는 바뀌지 않는다

## 4. 파일 계약 (`artifacts/`, 모두 아직 없음)

| 파일 | 생성 | 사용 | 형식 출처 |
| --- | --- | --- | --- |
| `embeddings.npy`, `meta.csv` | A `scripts/build_index.py` | A `load_index()` | interfaces.md `load_index` |
| `profiles.json` | C `scripts/build_profiles.py` | C `load_profiles()` | `{artist: {feature: [mean, std]}}` (스크립트 docstring) |
| `calibration.json` | B (`eval.ipynb`) | B `load_calibration()` | 키 `T_clip`, `T_cv`, `w`, `method` (`classify.DEFAULT_CALIBRATION`) |
| `linear.pkl` | B (#11) | B `predict_clip()` (예정) | plan.md 5장 |

이 절은 2026-11-19 전체 스캔 기준이다.

## 5. D 출력을 바꿀 때 지켜야 하는 형식 (테스트 기준)

| 대상 | 고정된 형식 | 근거 |
| --- | --- | --- |
| `explain.render_card(result)` | `(str, Figure)`, 문자열에 `DISCLAIMER` 포함, 컬러·스케치 입력 모두 예외 없음 | `tests/test_smoke.py::test_pipeline_end_to_end` |
| `explain.DISCLAIMER` | 이름 유지(테스트와 `app.build_demo()`가 참조) | `tests/test_smoke.py`, `app.py:86` |
| `explain.FEATURE_KO` 값 | 레이더 라벨 테스트가 "선 밀도", "선 방향 일관성"을 그대로 비교 | `tests/test_explain.py::test_radar_uses_direction_as_is`, `test_radar_skips_non_numeric_and_missing_features` |
| `explain.EPS` | 이름·값 0.01 | `tests/test_explain.py::test_zero_std_uses_eps` |
| `explain._radar(features, profile, artist)` | 비공개지만 테스트가 직접 호출 | `tests/test_explain.py` 레이더 테스트 3개 |
| `app.analyze(img)` | 12개 키 `result`, `result["gray"]`는 `bool`, `result["features"]`는 스케치여도 색 특징 포함, 스케치면 `comparison["z"]` ⊆ `LINE_FEATURES` | `tests/test_smoke.py::test_pipeline_end_to_end`, `tests/test_explain.py::test_analyze_drops_color_features_only_for_sketch` |
| `app.run(img)` | 3개를 돌려주고 세 번째(`detail`)의 `similar_works` 각 항목에 `path` 없음 | `tests/test_smoke.py::test_run_detail_has_no_file_like_dicts` |
| `app.build_demo()` | `None`이 아님 | `tests/test_smoke.py::test_gradio_app_builds` |
| `explain.assess_confidence`, `compare` | 키 집합·등급·대조 결과 | `tests/test_smoke.py`, `tests/test_explain.py` |
| 계약 문서 | `contracts/interfaces.md` 변경 불가 | `AGENTS.md` 규칙 2, project.md DECIDED |

`render_card()`의 문장 내용(유형별·등급별 문구, 키워드 문장, 조사 처리)은 어떤 테스트도 검사하지 않는다. #22는 문장 동작 테스트를 `tests/test_explain.py`에 같은 PR로 넣어야 한다(팀 테스트 방식). 3×3 조합은 `detect_type` 스텁으로 고를 수 없으므로, 계약 형식의 `result` dict를 직접 만들어 넣는 방식이 맞다. 업무 규칙(최종 순위 `fuse()`만, "낮음"이면 두 관점 따로, 엇갈림 노출, `DISCLAIMER` 항상)은 `business-overview.md`를 본다.
