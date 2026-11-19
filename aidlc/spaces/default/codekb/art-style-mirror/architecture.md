# Architecture

## Architecture Analysis

### System Overview

단일 프로세스 로컬 Python 앱이다. `app.py`가 Gradio Blocks 화면을 띄우고, 버튼을 누르면 `app.analyze()`가 `modules/` 패키지의 4개 모듈 함수를 정해진 순서로 호출해 `result` dict를 만든 뒤 `explain.render_card()`가 결과 카드(Markdown)와 레이더 차트(matplotlib `Figure`)를 만든다. 사전 계산 결과는 `artifacts/`의 파일(임베딩·메타·프로필·보정값)로 공유하도록 설계돼 있으나 지금은 비어 있고, 스텁이 같은 모양의 가짜 데이터를 메모리에서 만든다.

### Architectural Style

모듈형 모놀리스(Modular Monolith) + 파이프라인. 근거:

- 배포 단위 1개(`python app.py`), 네트워크 경계 없음, DB 없음
- 모듈 경계 = 담당자 경계 = 파일 경계(A `data.py`, B `classify.py`, C `features.py`, D `explain.py`·`app.py`). 경계의 기준은 `contracts/interfaces.md`의 함수 시그니처
- 처리 흐름은 순차 파이프라인이며, 각 단계는 순수 함수에 가깝다(입력 → dict/배열). 상태는 `functools.lru_cache`로 캐시한 색인·프로필뿐

### Component Relationships

```mermaid
flowchart LR
    UI["app.py<br/>Gradio UI + analyze()"] --> F["modules.features (C)"]
    UI --> D["modules.data (A)"]
    UI --> C["modules.classify (B)"]
    UI --> E["modules.explain (D)"]
    C -->|"load_index()"| D
    F -->|"ARTISTS"| D
    C -.->|"calibration.json (예정)"| ART[("artifacts/")]
    D -.->|"embeddings.npy, meta.csv (예정)"| ART
    F -.->|"profiles.json (예정)"| ART
    SI["scripts/build_index.py (A)"] -.->|"생성 예정"| ART
    SP["scripts/build_profiles.py (C)"] -.->|"생성 예정"| ART
    T["tests/test_smoke.py"] --> UI
```
<!-- Text fallback: app.py는 features(C), data(A), classify(B), explain(D)를 모두 호출한다. classify는 data.load_index()를, features는 data.ARTISTS를 import한다. explain과 data는 다른 모듈을 import하지 않는다. data·features·classify는 artifacts/의 embeddings.npy·meta.csv, profiles.json, calibration.json을 읽도록 예정돼 있고, scripts/build_index.py와 scripts/build_profiles.py가 그 파일을 만들 예정이다(둘 다 NotImplementedError). tests/test_smoke.py는 app과 모든 모듈을 호출한다. -->

모듈 간 실제 import는 두 개뿐이다: B → A(`classify.py:15`, `load_index`), C → A(`features.py:17`, `ARTISTS`). D(`explain.py`)는 다른 모듈을 import하지 않고 인자로 받은 dict만 쓴다. 상세 목록은 `dependencies.md`.

### Data Flow

1. 사용자 이미지(Gradio `type="numpy"`, `image_mode="RGB"`) → `features.preprocess_input()`: RGB uint8, 긴 변 512px
2. `features.is_grayscale()` → `gray` 플래그(채널 차 평균 < 8)
3. CLIP 관점: `data.embed_image()` → 512차원 L2 정규화 벡터 → `classify.detect_type()`, `data.clip_keywords()`, `classify.predict_clip()`(화가·화풍 확률), `classify.similar_works()`(색인 코사인 검색, 0.95 이상 제외)
4. OpenCV 관점: `features.extract_features()`(11개 키) → `features.predict_cv()`(z값 거리 → 확률, 스케치는 선 특징만)
5. `classify.fuse(p_clip, p_cv)` → Top 3 `[(artist, prob)]`
6. `explain.assess_confidence(top3, p_clip, p_cv, similar[0]["score"])` → 등급·지표
7. `features.load_profiles()` + `explain.compare(feats, profiles, top1, top2)` → 1·2위 대조
8. `result` dict(11개 키) → `explain.render_card()` → (Markdown, Figure). `app.run()`은 상세 JSON에서 `similar`의 `path` 키를 뺀다(Gradio가 파일로 오인하는 문제)

### Key Design Decisions

| 결정 | 근거 / 영향 |
| --- | --- |
| 계약 우선(contract-first): `contracts/interfaces.md`를 변경 불가 기준으로 둠 | 4명이 병렬로 일하면서 통합 깨짐을 막음. 변경은 계약 변경 이슈 템플릿 + 별도 PR |
| 1일차 스텁이 빈 함수가 아니라 같은 모양의 결정적 가짜 값을 돌려줌 | 첫날부터 `app.py`와 `tests/test_smoke.py`가 끝까지 돎. 같은 입력 → 같은 출력(입력 바이트 SHA-1 시드) |
| 최종 순위는 `fuse()`만 결정 | OpenCV·키워드가 순위를 몰래 뒤집지 않음. 엇갈림은 카드 문장으로 노출 |
| D의 등급 판정은 스텁이 아니라 plan.md 6.3 식을 실제 계산(경계값만 임시) | 통합 전에 등급·카드 로직을 검증 가능. 경계값은 #24에서 검증셋으로 확정 |
| 사전 계산 결과를 `artifacts/` 파일로 공유 | CLIP 계산을 한 번만(Colab GPU). 100MB 이상 파일 금지 |
| 보정값 기본값 `T=1, w=0.8, weighted_sum`(`classify.DEFAULT_CALIBRATION`) | plan.md 9.5 플랜 B와 같음. `calibration.json`이 생기면 덮어씀 |

### Improvement Opportunities

- B·C → A의 직접 import는 "Unit은 서로 의존하지 않는다"는 팀 결정과 코드 수준에서 어긋난다. 화가 목록·색인을 `artifacts/` 파일 계약으로만 주고받게 하거나, 의존을 계약 경유로 명시하는 방법을 Units Generation에서 정해야 한다(코드 변경은 각 담당자 이슈로).
- `T_cv`가 B 소유 `calibration.json`에 있는데 C의 `predict_cv()`는 `T = 1.0`을 하드코딩한다. 보정값 파일의 소유·읽기 경로를 정해야 한다.
- 화가 이름이 A(`meta.csv`)·B(확률 dict 키)·C(`profiles.json` 키)에서 같아야 한다는 암묵 계약이 있다(`app.py:57`의 `profiles[top1]`).
- 로깅·관측 수단이 없다. 로컬 MVP 범위에서는 수용 가능하나 엇갈림 사례 자동 저장(#25, `samples/disagree/`)이 사실상 유일한 기록 수단이 된다.

## Interaction Diagrams

### 이미지 분석 1회 (버튼 "분석하기")

```mermaid
sequenceDiagram
    actor U as 사용자
    participant G as Gradio (app.run)
    participant AN as app.analyze
    participant C as features (C)
    participant A as data (A)
    participant B as classify (B)
    participant D as explain (D)

    U->>G: 이미지 업로드 + 분석하기
    alt 이미지 없음
        G-->>U: gr.Error("이미지를 먼저 올려 주세요.")
    end
    G->>AN: analyze(img)
    AN->>C: preprocess_input(img)
    C-->>AN: RGB uint8, 긴 변 512px
    AN->>C: is_grayscale(img)
    C-->>AN: gray
    AN->>A: embed_image(img)
    A-->>AN: emb (512,)
    AN->>B: detect_type(emb)
    AN->>A: clip_keywords(emb, k=3)
    AN->>B: predict_clip(emb)
    B->>A: load_index() (중심점 계산, 캐시)
    B-->>AN: {"artists", "styles"}
    AN->>B: similar_works(emb, k=3)
    B-->>AN: 비슷한 명화 ≤3
    AN->>C: extract_features(img, gray)
    C-->>AN: feats (11개 키)
    AN->>C: predict_cv(feats, gray)
    C-->>AN: p_cv
    AN->>B: fuse(p_clip, p_cv)
    B-->>AN: top3
    AN->>D: assess_confidence(top3, p_clip, p_cv, max_sim)
    D-->>AN: level, margin, entropy, jsd, max_sim
    AN->>C: load_profiles()
    AN->>D: compare(feats, profiles, top1, top2)
    D-->>AN: why_top1, toward_top2, z
    AN-->>G: result (11개 키)
    G->>D: render_card(result)
    D-->>G: (Markdown, Figure)
    G-->>U: 결과 카드 + 레이더 차트 + 상세 JSON(path 제외)
```
<!-- Text fallback: 사용자가 이미지를 올리고 분석하기를 누르면 app.run이 이미지가 없을 때 gr.Error를 낸다. 있으면 app.analyze가 features.preprocess_input(긴 변 512px RGB uint8) → features.is_grayscale → data.embed_image(512차원) → classify.detect_type, data.clip_keywords, classify.predict_clip(내부에서 data.load_index 중심점), classify.similar_works → features.extract_features → features.predict_cv → classify.fuse(Top 3) → explain.assess_confidence(등급) → features.load_profiles + explain.compare(1·2위 대조) 순으로 호출해 result dict를 만든다. app.run은 explain.render_card로 Markdown 카드와 레이더 Figure를 받고, similar의 path 키를 뺀 상세 JSON과 함께 화면에 보여준다. -->

### 처리 흐름 요약 (image → preprocess → CLIP/OpenCV → fuse() → grade → result card)

```mermaid
flowchart TD
    IN["입력 이미지 (RGB np.ndarray)"] --> PRE["preprocess_input() + is_grayscale() (C)"]
    PRE --> CLIP["CLIP 관점: embed_image, clip_keywords (A) → detect_type, predict_clip, similar_works (B)"]
    PRE --> CV["OpenCV 관점: extract_features → predict_cv (C)"]
    CLIP --> FUSE["fuse(p_clip, p_cv) → Top 3 (B)"]
    CV --> FUSE
    FUSE --> GRADE["assess_confidence() → 높음/보통/낮음 (D)"]
    CLIP -->|"max_sim"| GRADE
    CV -->|"p_cv"| GRADE
    GRADE --> CMP["load_profiles() (C) + compare() (D)"]
    CMP --> CARD["render_card() → Markdown + 레이더 Figure (D)"]
    GRADE -->|"낮음이면 두 관점 따로 표시"| CARD
```
<!-- Text fallback: 입력 이미지 → preprocess_input·is_grayscale(C) → 두 갈래(CLIP: embed_image·clip_keywords(A), detect_type·predict_clip·similar_works(B) / OpenCV: extract_features → predict_cv(C)) → fuse()로 Top 3(B) → assess_confidence()로 등급(D, max_sim과 p_clip·p_cv도 입력) → load_profiles(C)+compare(D) → render_card()(D)가 결과 카드와 레이더 차트를 만든다. 등급이 낮음이면 카드가 두 관점 결과를 따로 보여준다. -->

### 사전 계산 (예정, 아직 미구현)

```mermaid
flowchart LR
    WA["WikiArt 축소판 (huggan/wikiart, 화가 24명)"] --> BI["scripts/build_index.py (A, #3·#4)"]
    BI --> EMB[("artifacts/embeddings.npy + meta.csv")]
    WA --> BP["scripts/build_profiles.py (C, #19, 학습셋만, 화이트밸런스 없음)"]
    BP --> PROF[("artifacts/profiles.json")]
    EMB --> EV["notebooks/eval.ipynb (B, #12·#14·#15: 검증셋)"]
    EV --> CAL[("artifacts/calibration.json, linear.pkl")]
```
<!-- Text fallback: WikiArt 축소판에서 scripts/build_index.py(A)가 embeddings.npy와 meta.csv를, scripts/build_profiles.py(C)가 학습셋만으로 profiles.json을 만들 예정이다. B는 eval.ipynb에서 검증셋으로 판정 방식·온도·가중치를 정해 calibration.json과 linear.pkl을 저장한다. 두 스크립트는 현재 NotImplementedError만 던지고 노트북은 계획 셀뿐이다. -->
