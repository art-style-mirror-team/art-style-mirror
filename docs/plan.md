# 닮은 화가·화풍 분석기 (art-style-mirror) — 프로젝트 계획서

> 기준일: 2026-11-19 · 작성: 김현승(D)
> 이 문서는 팀 공용 계획서이자 AI 코딩 도구(Claude Code, AI-DLC 등)가 읽는 기준 문서다.
> 함수 시그니처의 최종 기준은 `contracts/interfaces.md`다. 이 문서와 다르면 그 파일을 따른다.

---

## 1. 프로젝트 개요

어떤 이미지든 넣으면 닮은 화가·화풍 Top 3를 찾고, 왜 닮았는지 색과 선으로 설명하는 프로그램을 4명이 2주 안에 MVP로 완성해 GitHub에 공개한다. 발표는 없고, 실행 가능한 코드와 README가 올라간 GitHub 저장소가 최종 산출물이다.

- **입력**: 일반 사진, 직접 그린 그림, 완성된 그림, 연필 스케치
- **출력**: 닮은 화가 Top 3(신뢰도 %와 신뢰 등급), 닮은 화풍 Top 3, 비슷한 명화 3점, CLIP 키워드 설명, 색·선 비교 설명과 레이더 차트
- **한 줄 피치**: "두 개의 눈으로 보고, 신뢰도로 고른다" — CLIP은 소재·분위기·양식을, OpenCV는 색·선의 정확한 수치를 보고, 두 관점을 합친 신뢰도 순으로 Top 3를 정한다.

### 1.1 MVP 범위

| 구분 | 기능 |
| --- | --- |
| 필수 | 입력 유형 판별(사진/그림/스케치) |
| 필수 | 두 관점 판정: CLIP(소재·분위기·양식) 확률 + OpenCV(색·선) 확률 |
| 필수 | 두 관점을 합친 신뢰도 순 Top 3 + 결과 신뢰 등급(높음/보통/낮음) |
| 필수 | 비슷한 명화 3점, CLIP 키워드 설명, 1·2위 대조 설명, 레이더 차트 |
| 필수 | 판정 3종·합치기 3종 정확도 비교표, 보정 오차(ECE)와 신뢰도 다이어그램 |
| 필수 | Gradio 화면(로컬 실행) + GitHub 저장소 공개(README, 스크린샷) |
| 선택 | 성장 지도, 색 전이 미리보기, 화가 30~50명 확장, Hugging Face Spaces 배포 |

### 1.2 데이터셋

- `huggan/wikiart` (Hugging Face): 81,444점, 화가 129명, 장르 11개, 화풍 27개 라벨. **비상업 연구용.**
- 개발 시작은 화가 24명 축소판(예: `slpkl/wikiart-subsample`)으로 하고, 여유가 있으면 30~50명으로 확장한다.
- 화가 소개: Kaggle "Best Artworks of All Time"의 `artists.csv` (CC BY-NC-SA 3.0).
- 테스트용 그림: 팀원이 직접 그린 그림 10~20장 + 엇갈림 시험 세트(7장 참고).
- 원본 이미지는 Git에 올리지 않는다. README에 출처와 비상업 조건을 명시한다.

### 1.3 기술 스택

Python 3.11, Hugging Face `transformers`·`datasets`(CLIP), OpenCV, scikit-learn(선형 분류기), SciPy(엔트로피, 젠슨-섀넌 발산), NumPy, pandas, matplotlib(레이더 차트), Gradio, pytest, Git/GitHub. Hugging Face Spaces 배포는 선택.

---

## 2. 팀과 역할

한 사람이 한 모듈을 끝까지 책임지고, 각자 다른 파일에서 작업해 Git 충돌을 최소화한다.

| 역할 | 담당자 | 맡는 일 | 주요 파일 |
| --- | --- | --- | --- |
| A — 데이터·CLIP | 홍승민 | 화가 선별, 학습·검증·테스트 70/15/15 분할, CLIP 임베딩 계산·저장, CLIP 키워드 설명(문장 앙상블), 화가 소개 결합, 변형 안정성 측정 | `modules/data.py`, `scripts/build_index.py` |
| B — 판정·융합 | 홍예원 | 입력 유형 판별, 판정 3종 비교, CLIP 쪽 확률, 온도 보정, 두 관점 합치기 3종 비교와 가중치 선정, 최종 평가(정확도·ECE) | `modules/classify.py`, `notebooks/eval.ipynb` |
| C — 색·선 분석 | 심현준 | 사용자 입력 전처리(CLIP보다 먼저 실행), 색 6종·선 5종 특징, 화가별 프로필, OpenCV 쪽 확률, 피셔 점수로 약한 특징 거르기 | `modules/features.py`, `scripts/build_profiles.py` |
| D — 신뢰도·UI·통합 | 김현승 | 저장소 관리, 결과 신뢰 등급 판정, 1·2위 대조 설명, 해석 문장, 레이더 차트, 결과 카드, Gradio 화면, 전체 통합 | `modules/explain.py`, `app.py` |

8일차 이후 A·B·C가 여유가 생기면 D의 통합, README, 데모 GIF를 나눠 맡는다.

---

## 3. 처리 흐름

사용자 입력은 전처리를 먼저 거친 뒤 두 관점으로 나뉜다. CLIP은 소재·분위기·양식을, OpenCV는 그림 픽셀에서 색·선 수치를 따로 계산하고, 두 관점의 확률을 합쳐 Top 3를 정한다.

1. `preprocess_input()` (C): 종이 영역 자르기, 화이트밸런스 보정, 크기 맞추기, 흑백 판별
2. CLIP 관점(소재·분위기·양식): `embed_image()`·`clip_keywords()` (A) → `predict_clip()`·`similar_works()` (B)
3. OpenCV 관점(색·선): `extract_features()` → `predict_cv()` (C)
4. 신뢰도: `fuse()`로 Top 3 결정 (B) → `assess_confidence()`로 등급 (D)
5. 설명: `compare()`·`render_card()` (D)

규칙:

- 화이트밸런스는 **사용자 입력에만** 적용한다. 명화에 적용하면 고흐의 노란 톤 같은 화가 고유의 색까지 지워진다. 명화는 크기 맞추기만 한다.
- CLIP용 크기 조절·정규화는 `CLIPProcessor`가 자동으로 한다.
- 명화 변환과 사용자 입력 변환에는 반드시 같은 CLIP 모델 버전을 쓴다.
- CLIP의 512개 숫자는 각각의 의미를 해석할 수 없다. 색·선 특징은 512개 숫자가 아니라 그림 픽셀에서 OpenCV로 직접 계산한다.

---

## 4. 모듈 인터페이스

1일차에 아래 시그니처를 확정하고, 이후 변경은 PR과 팀 합의로만 한다. 이미지는 모두 RGB `np.ndarray`(uint8)로 주고받는다.

```python
# A: modules/data.py
embed_image(img) -> np.ndarray              # CLIP 임베딩, shape (512,), L2 정규화
embed_text(texts) -> np.ndarray             # 문장 임베딩, shape (n, 512)
load_index() -> dict                        # {"emb": (N,512), "meta": DataFrame[id, artist, style, genre, path, split]}  split = train/val/test
clip_keywords(emb, k=3) -> list[tuple]      # [("두꺼운 붓 자국", 0.71), ...] 소재·분위기·양식 문장쌍 비교

# B: modules/classify.py
detect_type(img_emb) -> str                 # "photo" | "painting" | "sketch"
predict_clip(emb) -> dict                   # {"artists": {name: prob}, "styles": {name: prob}}  온도 보정 적용
similar_works(emb, k=3) -> list[dict]       # [{"id", "artist", "style", "path", "score"}], 유사도 0.95 이상 제외
fuse(p_clip, p_cv) -> list[tuple]           # [(artist, prob)x3]  calibration.json의 w·방식 사용

# C: modules/features.py
preprocess_input(img) -> np.ndarray         # 사용자 입력 전용: 종이 영역 자르기, 화이트밸런스, 크기 맞추기
is_grayscale(img) -> bool                   # 흑백(스케치) 여부
extract_features(img, gray=False) -> dict   # {"brightness", "contrast", "saturation", "warmth", "color_diversity",
                                            #  "edge_density", "direction", "straight_ratio", "roughness", "stroke_length", "palette"}
load_profiles() -> dict                     # {artist: {feature: (mean, std)}}  학습셋으로만 계산
predict_cv(features, gray=False) -> dict    # {artist: prob}  z값 거리 → 확률, 온도 보정 적용

# D: modules/explain.py
assess_confidence(p_fused, p_clip, p_cv, max_sim) -> dict  # {"level": "높음|보통|낮음", "margin", "entropy", "jsd", "max_sim"}
compare(features, profiles, top1, top2) -> dict            # {"why_top1": [2개], "toward_top2": [2개], "z": {feature: z값}}
render_card(result) -> (str, figure)                       # 해석 문장 + 레이더 차트
```

**스텁 규칙**: 1일차 스텁은 빈 함수가 아니라 위 형식과 똑같은 모양의 가짜 결과를 돌려줘야 한다. 그래야 첫날부터 `app.py`가 끝까지 돈다.

---

## 5. 저장소 구조

```
art-style-mirror/
├── app.py                  # Gradio 진입점 (D)
├── AGENTS.md               # AI 도구 공통 규칙
├── CLAUDE.md               # @AGENTS.md 한 줄
├── contracts/
│   └── interfaces.md       # 변경 불가 기준 (4장의 함수 시그니처)
├── docs/
│   └── plan.md             # 이 문서
├── modules/
│   ├── data.py             # A
│   ├── classify.py         # B
│   ├── features.py         # C
│   └── explain.py          # D
├── scripts/
│   ├── build_index.py      # 임베딩 사전 계산 (A)
│   └── build_profiles.py   # 화가 프로필 사전 계산 (C)
├── artifacts/              # embeddings.npy, meta.csv, profiles.json, linear.pkl, calibration.json
├── notebooks/eval.ipynb    # 판정·합치기 비교, ECE (B)
├── .claude/                # AI-DLC 엔진 파일 (aidlc config가 생성)
├── aidlc/                  # AI-DLC 기록 (intent별 상태·audit·산출물, 팀 규칙 memory/)
├── aidlc.settings.json     # AI-DLC 모델 preset
├── samples/                # 팀원 그림·엇갈림 시험 세트
├── tests/
│   └── test_smoke.py       # 전체 파이프라인이 오류 없이 도는지
├── .github/
│   └── pull_request_template.md
├── requirements.txt
└── README.md
```

- `.gitignore`에 추가: `.venv/`, `__pycache__/`, `.ipynb_checkpoints/`, `data/`(원본 이미지), `samples/disagree/`, `*.pt`, `.env`
- `artifacts/`의 작은 파일(화가 24명 기준 임베딩 약 6MB)은 커밋해서 팀원이 다시 계산하지 않게 한다. GitHub은 100MB가 넘는 파일을 거부하므로 화가를 늘리면 크기를 다시 확인한다.

---

## 6. 신뢰도 평가 방식

Top 3는 CLIP 확률과 OpenCV 확률을 보정한 뒤 가중합한 신뢰도 순으로 정하고, 결과 전체는 4가지 지표로 높음·보통·낮음 등급을 매긴다. 모든 기준값(온도 T, 가중치 w, 등급 경계)은 **검증셋**으로 정하고, **테스트셋은 최종 평가(#26)에서 한 번만** 쓴다.

### 6.1 관점별 확률

| 관점 | 보는 것 | 확률 계산 | 담당 |
| --- | --- | --- | --- |
| CLIP | 소재·분위기·양식 | 선형 분류기 점수 z_a에 소프트맥스: p_clip(a) = exp(z_a/T) / Σ exp(z_j/T) | B |
| OpenCV | 색·선 수치 | 화가 프로필과의 z값 거리를 확률로 변환 (아래 식) | C |

```
z(a,f)  = (x_f − μ(a,f)) / max(σ(a,f), ε)      ε = 0.01
D_a     = (1/F) · Σ_f z(a,f)²
p_cv(a) = exp(−D_a / 2T) / Σ_j exp(−D_j / 2T)
```

- 스케치는 색 특징을 빼고 선 특징만으로 F를 줄인다.
- 피셔 점수 = (화가별 평균들의 분산) / (화가 내부 분산의 평균). 낮은 특징은 확률 계산에서 빼고 설명에만 쓴다.
- CLIP 키워드는 반대 문장쌍(예: "vivid colors" / "muted colors")을 비교하고, 비슷한 표현 여러 개의 평균을 쓴다(프롬프트 앙상블).

### 6.2 보정하고 합치기

두 확률은 자신감의 단위가 다르므로 먼저 각각 온도 T를 맞춘다. 검증셋에서 T를 0.5~5로 바꿔보며 정답 화가 확률의 −log 평균(NLL)이 가장 작은 값을 고른다.

| 합치기 방식 | 식 | 특징 | 용도 |
| --- | --- | --- | --- |
| 가중합 | p(a) = w·p_clip(a) + (1−w)·p_cv(a) | 한쪽 확률의 오차에 덜 민감 | 기본값 |
| 가중곱 | p(a) ∝ p_clip(a)^w · p_cv(a)^(1−w) | 두 관점이 모두 동의할 때만 높음, 잡음에 민감 | 비교 |
| RRF | 점수(a) = Σ 1/(60 + 순위) | 보정 불필요, 대신 확률이 아님 | 기준선 |

w는 검증셋에서 0, 0.1, …, 1.0을 대입해 Top-3 정확도가 가장 높은 값으로 정하고 T와 함께 `artifacts/calibration.json`에 저장한다. w = 1.0이 최선이면 판정은 CLIP만 쓰고 OpenCV는 설명에만 쓴다. 그 결과도 README에 기록한다.

### 6.3 결과 신뢰 등급

| 지표 | 계산 | 나쁜 신호 |
| --- | --- | --- |
| 1·2위 차이 | m = p(1위) − p(2위) | 작음: 애매한 판정 |
| 정규화 엔트로피 | H = −Σ p·log p / log K (K = 화가 수) | 1에 가까움: 거의 모름 |
| 두 관점 일치도 | JSD(p_clip, p_cv), 밑 2 로그, 0~1 | 큼: 두 관점이 엇갈림 |
| 데이터셋 유사도 | 가장 비슷한 명화와의 코사인 유사도 | 낮음: 웹툰·사진 등 데이터셋 밖 입력 |

| 등급 | 조건 | 화면 표시 |
| --- | --- | --- |
| 높음 | m 큼, JSD 작음, 유사도 높음 | 정상 결과 |
| 보통 | 하나라도 경계값 근처 | 결과 + "애매한 부분이 있어요" |
| 낮음 | m 작고 JSD 큼, 또는 유사도 매우 낮음 | "뚜렷하게 닮은 화가가 없어요" + CLIP·OpenCV 결과를 따로 표시 |

- 최종 순위는 항상 `fuse()` 결과로 정하고, OpenCV가 결과를 몰래 뒤집지 않는다. 두 관점이 엇갈리면 숨기지 않고 "분위기는 고흐, 색감은 모네"처럼 보여준다.
- 등급 경계값은 검증셋에서 "높음 등급 판정의 실제 정확도가 80% 이상"이 되는 지점으로 정한다.
- 설명은 1위와 2위를 대조한다. 1위 쪽이 더 가까운 특징은 "1위인 이유", 2위 쪽이 더 가까운 특징은 "2위 느낌이 나는 부분"으로 보여준다.
- 크게 엇갈린 사례는 그림과 두 결과를 `samples/disagree/`에 자동 저장해 원인 분석과 README 한계 항목에 쓴다.
- 구현 참고: SciPy의 `jensenshannon(p, q, base=2)`는 발산의 제곱근을 돌려주므로 제곱해서 JSD로 쓴다.

### 6.4 검증 방법

- **정확도 비교표**: CLIP 단독, OpenCV 단독, 가중합, 가중곱, RRF의 Top-1·Top-3 정확도
- **보정 오차(ECE)**: "신뢰도 70%"라고 한 판정이 실제로 70% 맞는지 확인한다. 구간 M = 10, 신뢰도 다이어그램을 README에 넣는다.
  ```
  ECE = Σ_m (|B_m| / n) · | acc(B_m) − conf(B_m) |
  ```
- **변형 안정성**: 밝기 ±10%, 살짝 회전, 가장자리 자르기 등 5종 변형 후 1위 유지 비율
- **엇갈림 시험 세트**: 해바라기 사진, 노란 추상화, 어두운 농민 그림, 연필 스케치, 노란 조명 아래 찍은 그림, 웹툰, 피카소 작품을 팀원이 모아 예상대로 등급이 나오는지 확인한다.

---

## 7. 2주 일정

1일차에 인터페이스를 확정하고, 7일차까지 각 모듈을 단독으로 완성한 뒤, 11일차부터는 새 기능 없이 버그 수정, README 정리, GitHub 공개만 한다.

| 단계 | 일차 | A 데이터·CLIP | B 판정·융합 | C 색·선 | D 신뢰도·UI |
| --- | --- | --- | --- | --- | --- |
| 준비 | 1 | 전원: 저장소·시그니처 확정, 브랜치·PR 규칙, AGENTS.md, AI-DLC Inception | ← | ← | ← |
| 모듈 개발 | 2–7 | 데이터 분할, 임베딩·키워드 | 유형 판별, 판정 3종 비교 | 색·선 특징, 프로필·확률 계산 | 비교 로직, 문장·레이더 차트 |
| 통합 | 8–10 | 변형 안정성 측정, 화가 확장(선택) | 온도 보정, 두 관점 합치기 | 통합 지원, README 초안 | 신뢰 등급, Gradio 통합(전원) |
| 마무리 | 11–14 | 11 최종 평가·기능 동결 → 12 버그 수정 → 13 README·데모 GIF → 14 GitHub 공개 | ← | ← | ← |

관문:
- **1일차 끝**: 인터페이스 확정 (스텁으로 `app.py`가 돎)
- **7일차 끝**: 모듈 단독 완성
- **11일차**: 기능 동결 (이후 새 기능 금지)

### 7.1 주고받는 날

모듈 사이에 무엇을 언제 넘기는지 정리한 표다. 8장 이슈의 일차에서 끌어냈다. 받는 쪽은 그 전까지 스텁으로 작업한다. 스텁이 실제와 같은 형식이라 상대 모듈이 끝나지 않아도 자기 코드와 테스트를 먼저 완성할 수 있다. 넘기는 날이 늦어질 것 같으면 바로 이슈 댓글과 스탠드업에 알린다.

| 일차 | 주는 쪽 → 받는 쪽 | 넘기는 것 | 받는 쪽이 하는 일 |
| --- | --- | --- | --- |
| 3 | A → C | `artifacts/meta.csv` (split, path) — #3 | 학습셋 이미지 목록으로 프로필 집계 준비 (#19) |
| 4 | A → B | `artifacts/embeddings.npy`, `embed_image()` — #4·#5 | 가짜 색인을 실제 색인으로 바꾸고 판정 비교 시작 (#9~#12) |
| 6 | C → B·D | `artifacts/profiles.json`, 특징별 값 범위 — #19 | B는 p_cv 준비, D는 레이더 차트·대조 설명 확인 (#21·#23) |
| 7 | C → B | `predict_cv()` 실제 구현, 피셔 점수로 뺀 특징 목록 — #20 | 검증셋 p_cv로 온도 T_cv 결정 (#14) |
| 7 끝 | 전원 | **관문: 모듈 단독 완성** | 각 모듈이 실제 구현으로 `pytest` 통과 |
| 8–9 | B → D | `artifacts/calibration.json`, `fuse()` — #14·#15 | 검증셋으로 등급 경계값 결정 (#24) |
| 9–10 | 전원 | 통합 (#25) | 엇갈림 시험 세트 포함 샘플이 오류 없이 결과 카드까지 |
| 11 | B | **기능 동결**, 테스트셋 최종 평가 (#26) — 한 번만 | 이후 버그 수정만 |
| 12–13 | A·B·C → 전원 | README (#30) | 설치·실행법, 정확도표·ECE·안정성, 데이터 출처·비상업 조건, 한계 |

---

## 8. GitHub 이슈 목록

아래 30개를 GitHub Issues에 등록하고 라벨(`data`, `model`, `features`, `ui`, `infra`, `docs`, `stretch`)과 담당자를 붙인다. 하나의 이슈 = 하나의 브랜치 = 하나의 PR이 원칙이다. (선택) 이슈와 성장 지도·색 전이 미리보기는 `stretch` 라벨로 등록하고, 11일차 기능 동결 전에 필수 이슈가 모두 끝났을 때만 시작한다.

| # | 이슈 | 담당 | 일차 | 완료 기준 |
| --- | --- | --- | --- | --- |
| 1 | 저장소 생성, 폴더 구조, `.gitignore`, `requirements.txt`, 브랜치 보호 규칙, AGENTS.md·CLAUDE.md·AI-DLC 규칙 파일 | D | 1 | 네 명 모두 clone 후 `pip install` 성공 |
| 2 | 모듈 인터페이스 스텁(가짜 결과 반환)과 contracts/interfaces.md 작성, AI-DLC Inception 1회 | 전원 | 1 | 4개 모듈 파일이 import 오류 없이 열리고 `app.py`가 돎 |
| 3 | WikiArt 축소판 로드, 화가 24명 확정, 학습 70% / 검증 15% / 테스트 15% 분할 | A | 2–3 | `meta.csv`의 split 열에 train/val/test |
| 4 | CLIP 임베딩 사전 계산 스크립트 (Colab GPU) | A | 3–4 | `embeddings.npy` 생성, 행 수 = meta 행 수 |
| 5 | `embed_image()`·`embed_text()` 구현 | A | 4 | 같은 이미지 두 번 넣으면 유사도 0.99 이상 |
| 6 | 화가 소개 데이터(`artists.csv`) 결합 | A | 5 | 소개 없는 화가 목록화, 짧은 소개 직접 보충 |
| 7 | `clip_keywords()`: 소재·분위기·양식 반대 문장쌍 목록, 표현 앙상블 | A | 6–7 | 고흐 작품에서 붓터치·소용돌이 계열 키워드가 상위 |
| 8 | `detect_type()`: CLIP zero-shot으로 사진/그림/스케치 판별 | B | 2–3 | 샘플 15장 중 12장 이상 정답 |
| 9 | kNN 투표 방식 판정 | B | 4 | 검증셋 Top-1·Top-3 정확도 계산 |
| 10 | 화가·화풍 중심점 방식 판정 | B | 5 | 같은 지표로 계산 |
| 11 | 선형 분류기(로지스틱 회귀) 학습·저장 | B | 6 | `linear.pkl` 저장, 화가별 점수 출력 |
| 12 | 판정 3종 비교(검증셋) + `predict_clip()` 최종 방식 선정 | B | 7 | `eval.ipynb`에 비교표 |
| 13 | `similar_works()`: 비슷한 명화 3점, 자기 자신 제외 | B | 7 | 데이터셋 작품을 넣어도 자기 자신이 나오지 않음 |
| 14 | 온도 보정: p_clip·p_cv 각각 T 결정 | B | 8 | 검증셋 NLL 감소, T를 `calibration.json`에 저장 |
| 15 | `fuse()`: 가중합·가중곱·RRF 비교, w 선정 | B | 8–9 | 비교표 작성, w와 방식 저장 |
| 16 | `preprocess_input()`: 종이 영역 자르기, 화이트밸런스(사용자 입력만), 긴 변 512px, 흑백 감지. 1일차에 가짜 버전 먼저 | C | 2–3 | 종이 그림 사진의 배경이 흰색에 가까워짐 |
| 17 | 색 특징 6종 (팔레트, 밝기, 대비, 채도, 색온도, 색 다양성) | C | 3–4 | 밝은 그림과 어두운 그림에서 값이 예상대로 다름 |
| 18 | 선 특징 5종 (선 밀도, 방향, 직선 비율, 거칠기, 윤곽선 길이) | C | 4–5 | 몬드리안과 고흐 작품의 직선 비율이 뚜렷이 다름 |
| 19 | 화가·화풍별 프로필 집계 (학습셋만) | C | 6 | `profiles.json`에 화가 × 특징별 평균·표준편차 |
| 20 | `predict_cv()`: z값 거리 → 확률, 피셔 점수로 약한 특징 제외 | C | 7 | 검증셋 Top-3 정확도와 제외 특징 목록 기록 |
| 21 | `compare()`: 1위 이유·2위 쪽 특징 대조 | D | 3–5 | 가짜 프로필로 단위 테스트 통과 |
| 22 | 해석 문장 템플릿 (입력 유형별, 등급별 문구, CLIP 키워드) | D | 5–6 | 입력 3종 × 등급 3종 모두 자연스러운 문장 |
| 23 | 레이더 차트 (내 그림 vs 1위 화가 평균) | D | 6 | 특징 이름 한글, 두 도형 구분 가능 |
| 24 | `assess_confidence()`: 1·2위 차이, 엔트로피, JSD, 데이터셋 유사도 → 등급 | D | 8–9 | 높음 등급 정확도 80% 이상이 되는 경계값을 검증셋으로 기록 |
| 25 | **통합**: Gradio 화면에 전체 파이프라인 연결, 엇갈림 사례 자동 저장 | D (+전원) | 9–10 | 엇갈림 시험 세트 포함 샘플이 오류 없이 결과 카드 출력 |
| 26 | 최종 평가: 테스트셋 Top-1·Top-3, ECE, 신뢰도 다이어그램 | B | 10–11 | 테스트셋은 이때 한 번만 사용, README용 표·그림 완성 |
| 27 | 변형 안정성 측정 (변형 5종, 1위 유지 비율) | A | 10–11 | 방식별 유지 비율 표 |
| 28 | (선택) 화가 30~50명으로 확장 | A | 9–10 | 임베딩·프로필·분류기·보정값 재생성 후 재측정 |
| 29 | (선택) Hugging Face Spaces 배포 | D | 11–12 | 공개 URL에서 외부인이 실행 가능 |
| 30 | README(설치·실행법, 스크린샷, 데모 GIF, 정확도표·ECE·안정성, 데이터 출처·라이선스, 한계) + GitHub 공개 정리 | A·B·C | 12–13 | 출처와 비상업 용도 명시 |

---

## 9. Git 협업 규칙

`main`은 항상 실행 가능한 상태로 유지하고, 모든 변경은 PR과 리뷰 1명 승인을 거친다.

### 9.1 브랜치·커밋·PR

- **브랜치 이름**: `feat/<이슈번호>-<내용>` (예: `feat/17-color-features`), 버그는 `fix/...`
- **커밋 메시지**: `feat: 채도 특징 추가`, `fix: 흑백 이미지 오류 수정`, `docs: README 업데이트`, `test: ...`, `chore: ...`
- **PR 규칙**: 본문에 `Closes #<이슈번호>`, 리뷰어 1명 지정, 승인 후 작성자가 GitHub 화면의 "Merge pull request"(머지 커밋) 방식으로 머지. PR은 하루 안에 리뷰한다.
- **PR 크기**: 파일 1~3개, 변경 300줄 이내. 크면 쪼갠다.
- **충돌 예방**: 작업 시작 전 `git fetch origin` 후 `git merge origin/main`. 남의 모듈 파일은 직접 고치지 않고 이슈로 요청한다.
- **금지**: `main`에 직접 push, `--force` push, rebase로 공유 기록 수정, 대용량 데이터 커밋

### 9.2 커밋·머지 기록 남기기

GitHub의 커밋 히스토리에 개별 커밋과 머지 기록이 모두 남아야 한다.

| 저장소 설정 (Settings → General → Pull Requests) | 값 | 이유 |
| --- | --- | --- |
| Allow merge commits | 켜기 | PR의 커밋이 전부 남고 머지 기록이 생김 |
| Allow squash merging | 끄기 | 커밋이 하나로 뭉쳐져 개별 기록이 사라짐 |
| Allow rebase merging | 끄기 | 머지 기록이 남지 않음 |
| Automatically delete head branches | 켜기 | 브랜치가 지워져도 커밋·머지 기록은 main에 남음 |
| 브랜치 보호의 Require linear history | 끄기 | 켜면 머지 커밋이 금지됨 |

- 작게, 자주 커밋한다. 기능 하나를 다 만든 뒤 한 번에 올리지 않는다.
- 각자 자기 PC와 계정으로 커밋한다. `git config user.email`은 GitHub 가입 이메일과 같게 맞춘다.
- AI(Claude Code 등)가 커밋할 때도 한 번에 몰지 말고 단계별로 나눠 커밋하게 한다.
- 기록은 커밋 목록, Insights → Network(브랜치 흐름), Insights → Contributors(사람별 기여)에서 확인하고, 마지막에 README에 캡처를 넣는다.

### 9.3 브랜치 보호 (`main`)

팀원 3명이 조직에 합류하고 첫 PR들이 머지된 뒤에 켠다. (승인 1명이 필수라 혼자서는 머지할 수 없기 때문이다.)
- Require a pull request before merging: 켜기 — AI 도구의 실수로 인한 `main` 직접 push도 막는다
- Require approvals: 1
- Require status checks to pass: CI(`pytest`)가 생기면 켜기
- Do not allow bypassing the above settings: **끄기** — 급한 수정은 D가 처리한다
- Require linear history: **끄기**
- 강제 push 금지·브랜치 삭제 금지 유지

리뷰가 밀리지 않도록 리뷰 짝을 정한다: A ↔ B, C ↔ D. 짝은 `.github/CODEOWNERS`로 리뷰 요청을 자동으로 보내는 기본값이다. 작성자가 아닌 팀원은 누구나 다른 사람의 PR을 리뷰하고 승인할 수 있고, 승인 1명이면 머지할 수 있다. 짝이 하루 안에 못 보면 다른 팀원이 본다. 대기 중인 PR은 매일 스탠드업에서 확인한다.

### 9.4 운영

- **매일 10분 스탠드업**: 어제 한 일, 오늘 할 일, 막힌 점
- **진행 상황**: [GitHub Projects 보드](https://github.com/orgs/art-style-mirror-team/projects/1)(Todo / In Progress / Review / Done). 카드 이동 규칙은 아래와 같다.

| 열 | 들어가는 때 | 누가 |
| --- | --- | --- |
| Todo | 이슈가 보드에 추가될 때 | 자동 |
| In Progress | 이슈 브랜치를 만들고 작업을 시작할 때 | **담당자가 직접** |
| Review | 본문에 `Closes #n`이 있는 PR을 열 때 | 자동 |
| Done | PR이 머지되어 `Closes #n`으로 이슈가 닫힐 때 | 자동 |

- PR은 리뷰받을 준비가 됐을 때 연다. 중간에 Draft PR을 열려면 `Closes #n`을 빼 두었다가 Ready로 바꿀 때 넣는다(넣는 순간 카드가 Review로 간다).
- `Closes #n`은 반드시 쓴다. 빠뜨렸다면 머지 후 카드를 Done으로 옮긴다. 그러면 이슈가 자동으로 닫힌다.
- 한 사람이 동시에 In Progress에 두는 카드는 2개 이하로 한다. 막히면 카드를 그대로 두고 이슈 댓글과 스탠드업에 알린다.
- 리뷰에서 수정 요청을 받아도 카드는 Review에 둔다. 머지되지 않고 PR을 닫으면 카드를 In Progress로 되돌린다.
- 스탠드업은 보드를 띄워 놓고 Review 열(대기 중인 리뷰)부터 본다.
- 보드의 Status 선택지는 화면에서만 추가·수정한다. API로 통째로 바꾸면 워크플로가 참조하는 값이 사라져 자동화가 꺼진다(1일차에 실제로 겪음).
- **막히면**: 2시간 넘게 막히면 바로 공유

### 9.5 리스크와 플랜 B

| 리스크 | 플랜 B |
| --- | --- |
| CLIP 임베딩 계산이 느림 | Colab GPU에서 한 번만 계산 후 파일로 공유, 화가 수 유지 |
| 스케치가 소수 화가에게만 몰림 | `sketch_and_study` 장르 포함, 스케치는 명화도 흑백 변환 후 비교 |
| 선형 분류기 정확도가 낮음 | kNN 투표를 기본값으로 쓰고, 비교표는 그대로 README에 수록 |
| OpenCV 확률이 판정을 오히려 흐림 | 검증셋으로 w를 정하고, w = 1.0이 최선이면 판정은 CLIP만, OpenCV는 설명에만 사용 |
| 보정·등급 기준값을 정할 시간이 부족 | T = 1, 가중합 w = 0.8로 고정하고 등급은 1·2위 차이 하나로만 판정, README에 한계로 명시 |
| C의 OpenCV 작업이 늦어짐 | CLIP 키워드 설명만으로 "왜 닮았나" 최소 버전을 먼저 완성 |
| 통합이 10일차까지 끝나지 않음 | (선택) 이슈를 버리고 11일차 동결 유지 |

결과 화면에는 "픽셀 수치 기반의 통계적 해석이며 미술사적 평가가 아님"을 명시한다.

---

## 10. AI-DLC 협업 방식

팀원 4명이 모두 AI 코딩 도구를 적극 활용하되, 모두의 AI가 같은 규칙과 같은 인터페이스를 따르게 해서 통합 때 모듈이 깨지지 않게 한다. AI-DLC(AWS Labs, https://github.com/awslabs/aidlc-workflows)는 AI가 요구사항 → 설계 → 구현 → 검증을 단계별로 밟고 단계마다 사람의 승인을 받게 하는 방법론이다.

> AI-DLC v2.11.4 기준. 설치·명령·프로필 선택 등 자세한 사용법은 [aidlc-guide.md](aidlc-guide.md)를 따른다.

### 10.1 저장소에 심어둘 파일

| 파일 | 역할 |
| --- | --- |
| `AGENTS.md` | 모든 AI 도구가 읽는 팀 공통 규칙 (10.3) |
| `CLAUDE.md` | `@AGENTS.md` 한 줄만 넣어 Claude Code도 같은 규칙을 읽게 함. `/init`으로 자동 생성하지 않는다 |
| `contracts/interfaces.md` | 4장의 함수 시그니처. AI가 수정할 수 없는 변경 불가 기준 |
| `.claude/`, `aidlc.settings.json` | AI-DLC 엔진 파일과 모델 preset. 1일차에 `aidlc config --harness claude`로 생성. AI-DLC용 Claude 안내는 `.claude/CLAUDE.md`에 들어간다 |
| `aidlc/` | AI-DLC가 남기는 요구사항·설계·진행 기록(`aidlc/spaces/default/intents/<id>/`)과 팀 규칙(`memory/project.md`, `team.md`). Git에 함께 커밋 |

### 10.2 단계별 운영

| 단계 | 시기 | 누가 | 하는 일 |
| --- | --- | --- | --- |
| Inception | 1일차 | D 1명, 결과는 전원 확인 | 경량 Inception으로 Reverse Engineering과 Practices Discovery(팀 규칙 확정, `team.md`)까지 승인하고 중단·보관했다. 요구사항·작업 단위·계약은 이 계획서와 이슈, `contracts/interfaces.md`가 기준이다(작업 단위 A·B·C·D 4개, 서로 의존하지 않음). 결과는 PR로 `main`에 한 번 올린다 |
| Construction | 2~10일차 | 각 모듈 담당자 | 자기 이슈 브랜치에서 이슈 하나당 intent 하나로 설계 → 구현 → 테스트. 각 단계 승인은 담당자 본인이 한다 |
| 마무리 | 11~14일차 | 전원 | 버그 수정(`/aidlc bugfix`), README 정리, GitHub 공개. AI-DLC의 Operation 단계는 쓰지 않는다 |

작은 작업(함수 하나)은 `express`, 버그 수정은 `bugfix` 프로필로 짧게 끝내고, 판정 모델 비교처럼 실험이 많은 작업만 `classic`으로 전체 절차를 밟는다. 팀 Unit claim 기능(`/aidlc --claim`)은 PR 규칙과 맞지 않아 쓰지 않는다.

### 10.3 AGENTS.md 핵심 규칙

- 자기 모듈 파일만 수정한다. 다른 모듈이 필요하면 이슈로 요청한다.
- `contracts/interfaces.md`의 함수 이름·입출력 형식은 바꾸지 않는다. 바꿔야 하면 팀 합의 후 별도 PR로 한다.
- `main`에 직접 push하지 않고, 원본 이미지·대용량 파일을 커밋하지 않는다.
- AI는 코드를 작성한 뒤 핵심 판단 이유를 PR 설명에 3줄로 적는다. 담당자는 그 내용을 설명할 수 있어야 머지한다.
- 정확도·수치는 실제 실행 결과만 쓴다. AI가 예상치를 결과처럼 적지 않는다.
- 프로필·분류기는 학습셋으로만, 온도 T·가중치 w·등급 기준값은 검증셋으로만 정한다. 테스트셋은 최종 평가(#26)에서만 연다.
- 명화와 사용자 입력은 반드시 같은 CLIP 모델 버전으로 변환한다.
- 최종 순위는 `fuse()` 결과만 쓴다. OpenCV·키워드 쪽 코드가 순위를 따로 뒤집지 않는다.
- 이미지는 RGB `np.ndarray`(uint8), 긴 변 512px로 맞춘 뒤 처리한다. 화이트밸런스는 사용자 입력에만 적용한다. `cv2.imread()`는 BGR을 돌려주므로 반드시 RGB로 변환한다.
- 커밋은 작게, 단계별로 나눈다. 머지는 머지 커밋 방식만 쓴다.
- WikiArt는 비상업 연구용이므로 README에 출처와 용도를 반드시 적는다.

### 10.4 기록 파일 충돌 방지

- Inception 산출물은 1일차에 한 번 올리고 이후에는 고치지 않는다.
- Construction 기록은 intent별 폴더(`aidlc/spaces/default/intents/<id>/`)에 따로 생기고 `audit/`도 PC별로 나뉘므로 서로 겹치지 않는다. 남의 intent 폴더는 고치지 않는다.
- 개인 커서 파일(`active-intent`, `.aidlc-clone-id`, `.aidlc-sessions/` 등)은 커밋하지 않는다. AI-DLC가 `.gitignore`에 추가하는 블록이 막는다.
- 팀 규칙 파일(`memory/team.md`, `project.md`)에서 충돌이 나면 서로의 내용을 모두 살리는 쪽으로 합치고, 애매하면 스탠드업에서 정한다.

### 10.5 역할별 시작 요청 예시

AI-DLC는 `/aidlc <프로필>: <본문>` 형태로 시작한다(예: `/aidlc express: #21 compare() 구현...`). 이슈별 예시는 [aidlc-guide.md](aidlc-guide.md) 4장에 있다. 각 역할의 기본 본문은 아래와 같다.

- **A (홍승민)**: "contracts/interfaces.md는 변경 불가. WikiArt 축소판에서 화가 24명을 로드해 70/15/15로 나누고, CLIP 임베딩을 artifacts/에 저장하는 스크립트, embed_image()·embed_text(), 소재·분위기·양식 문장쌍으로 키워드를 뽑는 clip_keywords()를 만든다."
- **B (홍예원)**: "contracts/interfaces.md는 변경 불가. CLIP 임베딩으로 kNN·중심점·로지스틱 회귀 판정을 검증셋으로 비교해 predict_clip()을 정하고, 온도 보정과 가중합·가중곱·RRF를 비교하는 fuse()를 만든다. 테스트셋은 최종 평가에서만 쓴다."
- **C (심현준)**: "contracts/interfaces.md는 변경 불가. preprocess_input(), OpenCV 색 6종·선 5종 extract_features(), 학습셋 기준 화가 프로필, z값 거리를 확률로 바꾸는 predict_cv()를 만들고, 피셔 점수로 약한 특징을 가른다."
- **D (김현승)**: "contracts/interfaces.md는 변경 불가. 1·2위를 대조하는 compare(), 1·2위 차이·엔트로피·JSD·데이터셋 유사도로 등급을 매기는 assess_confidence(), 해석 문장, 레이더 차트, Gradio 화면을 만든다. 다른 모듈은 스텁으로 대체해 먼저 돌린다."

1일차 끝나기 전에 네 명 모두 자기 PC에서 AI 도구가 규칙 파일을 실제로 읽는지 확인한다.

---

## 11. 1일차 체크리스트 (D 주관)

- [ ] 조직과 공개 저장소 생성, 팀원 3명 초대(Base permission: Write)
- [ ] 머지 설정: merge commit만 허용, head branch 자동 삭제
- [ ] 뼈대 파일과 스텁을 단계별 커밋으로 push
- [ ] `main` 브랜치 보호 켜기 (linear history 끄기)
- [ ] 라벨 7개, 이슈 30개, Projects 보드
- [ ] AGENTS.md, CLAUDE.md, contracts/interfaces.md, PR 템플릿
- [x] AI-DLC 설치(`aidlc config --harness claude`)와 Inception 1회 (Practices Discovery까지 승인 후 중단·보관, PR로 올리기)
- [ ] 4명 모두 `aidlc doctor` 통과
- [ ] 4명 모두 첫 PR(README 팀원 표에 이름 추가) 머지 완료
- [ ] 4명 모두 `python app.py` 실행 확인

---

## 참고 자료

- WikiArt 데이터셋: https://huggingface.co/datasets/huggan/wikiart
- AI-DLC: https://github.com/awslabs/aidlc-workflows
- 온도 보정: Guo et al., "On Calibration of Modern Neural Networks" (2017), https://arxiv.org/abs/1706.04599
- 분류기 결합(합 규칙): Kittler et al., "On Combining Classifiers" (1998)
- 역순위 융합: Cormack et al., "Reciprocal Rank Fusion" (2009)
- CLIP 프롬프트 앙상블: Radford et al., "Learning Transferable Visual Models From Natural Language Supervision" (2021)