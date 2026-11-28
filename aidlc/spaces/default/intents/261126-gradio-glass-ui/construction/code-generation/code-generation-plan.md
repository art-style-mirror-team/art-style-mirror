# 코드 생성 계획 — #37 G안 Gradio 화면

## Summary

- Builds: G안 글래스 화면(카메라 첫 화면 → 분석 중 → 결과·명화·색·선·화풍)과 브라우저 기록 화면, 화면용 데이터 함수, 단계별 진행을 알리는 분석 핸들러
- Touches: `modules/explain.py`, `static/g.css`, `static/g.js`, `app.py`, `tests/test_explain.py`, 새 `tests/test_app.py`
- Tests: pytest 단위 테스트 약 21개(explain 12, app 9) + 기존 `tests/test_smoke.py` 그대로 통과, JS 화면은 브라우저(Playwright + Edge, 360×780)로 흐름 확인

## 구조

- **화면**: `gr.HTML` 하나가 화면 전체를 맡는다. `static/g.js`(js_on_load)가 DOM을 직접 그리고, `static/g.css`(css_template)가 모양을 정한다. Gradio 기본 여백·푸터는 `head`의 전역 스타일로 숨긴다.
- **입력**: JS가 사진(실시간 카메라 프레임 또는 선택 창의 파일)을 `upload(file)`로 서버에 올리고 `trigger('submit', {path})`로 분석을 요청한다. 멈추기는 `trigger('stop')`.
- **진행·결과 전달**: Python 분석 핸들러는 단계마다 화면 상태(dict)를 숨긴 `gr.JSON`에 내보내고, 그 `change` 이벤트의 `js`가 `window.gApp.update(view)`로 화면에 넘긴다.
- **데이터**: 화면에 필요한 값은 `explain.build_view(result)`(계약 밖 보조 함수)가 만든다. 화면은 `result`를 직접 읽지 않는다.
- **계약**: `analyze()` 반환 11개 키, `run()`의 `(text, fig, detail)`, `render_card()`는 그대로 둔다(NFR1).

## 단계

- [ ] **Step 1. 기준선 확인** — 바꾸기 전에 `pytest -q`와 `ruff check .`·`ruff format --check .`를 돌려 결과(통과·실패 수)를 기록한다. (NFR1, NFR5)
- [ ] **Step 2. `explain.py` 화면용 데이터** (FR7, FR3, FR4, FR5)
  - `ARTIST_KO`(화가 24명 한글 이름), `STYLE_KO`(화풍 한글 이름) 상수 추가. 표에 없으면 원래 이름을 쓴다(FR7.2).
  - `build_view(result) -> dict` 추가: JSON 직렬화 가능한 dict만 돌려준다(FR7.1).
    - `head`: 머리말(`TYPE_INTRO`), 1위 한글·원래 이름, 대표 화풍, 1위 %(정수) (FR3.1, FR3.2)
    - `level`: 등급, 막대 칸 수(높음 3·보통 2·낮음 1), 한 줄 설명(`LEVEL_NOTE` 기반) (FR3.3)
    - `top3`: 순위·짧은 이름·% (FR3.4)
    - `views`: CLIP 1위·OpenCV 1위, 같은지 여부 (FR3.5)
    - `low`: 낮음일 때 CLIP·OpenCV 상위 3개 (FR3.6)
    - `radar`: 축 이름(`FEATURE_KO`), 내 값·1위 평균 값(0~1로 자름, `_radar_value()` 규칙), 가까운 축(`why_top1`)·먼 축(`toward_top2`) 번호, 2위 이름. 스케치면 선 특징 5개만 (FR4.1, FR4.2, FR4.4, FR7.3)
    - `styles`, `keywords`, `metrics`(값 4개와 한 줄 뜻), `disclaimer` (FR5.1–FR5.4)
  - `render_card()`, `_radar()` 등 기존 함수는 바꾸지 않는다.
- [ ] **Step 3. `tests/test_explain.py` 동작 테스트 추가** (NFR5, FR7)
  - 보통 등급 정상 경로: 필드가 모두 있고 `json.dumps`가 된다.
  - 낮음 등급: `low`에 두 관점 상위 3개가 있다.
  - 스케치: 레이더 축이 선 특징 5개다.
  - 두 관점 1위가 같을 때·다를 때 `views.same` 값.
  - 한글 이름표에 없는 화가는 원래 이름 그대로.
  - 레이더 값이 0~1 밖이면 잘린다.
- [ ] **Step 4. `static/g.css`** (FR1–FR6 모양, NFR2, NFR3)
  - 시안 G의 색·글꼴·여백(360×780 기준, 가로 스크롤 없음, 누르는 영역 44px 이상)
  - 첫 화면 틀(4:5 꺾쇠, 바깥 어둡게), 도크, 분석 중 단계, 결과·색·선·화풍 시트, 진행 막대
  - 차례로 나타나기·시트 높이 전환·레이더 그리기 애니메이션, `prefers-reduced-motion`에서 모두 끔
- [ ] **Step 5. `static/g.js`** (FR1–FR6, NFR3)
  - 화면 상태: 첫 화면 → 분석 중 → 결과 → 색·선 → 화풍, 진행 막대 이동, 뒤로·앞으로 방향
  - 첫 화면: 보안 주소이고 카메라 권한이 있으면 실시간 미리보기, 아니면 어두운 배경. 셔터(미리보기 있으면 프레임 캡처, 없으면 선택 창), 앨범(선택 창, `accept="image/*"`) (FR1.4–FR1.6)
  - `upload(file)` → `trigger('submit', {path})`, 분석 중 아이콘·시트 끌어내리기 → `trigger('stop')` 후 첫 화면 (FR2.4, FR6.4, FR6.5)
  - `window.gApp.update(view)`: 진행 단계 갱신, 완료 시 결과로 자동 이동, 오류면 한 줄 알림 후 첫 화면 (FR2.2, FR2.3, FR2.5)
  - 결과 %·화풍 막대 차오르기, 레이더 SVG 그리기와 축 강조 순서 (FR3.2, FR4.3, FR5.1)
  - 시트 손잡이 드래그(120px 넘으면 첫 화면), 첫 화면에서 다시 셔터를 누르면 새 분석 (FR6.4, FR6.6)
  - 모든 버튼에 `data-testid`
- [ ] **Step 6. `app.py` 연결** (FR2, NFR1, NFR4)
  - `analyze()` 안의 순서를 단계 이름을 내보내는 내부 생성기 `_analyze_steps(img)`로 옮기고, `analyze()`는 그것을 끝까지 돌려 같은 `result`를 돌려준다(반환 형식 그대로, 모델 호출 수 그대로).
  - `analyze_view(evt)` 생성기 핸들러: 업로드 경로 검사(Gradio 업로드 폴더 안의 파일만) → RGB `np.ndarray` 읽기 → 단계마다 `{"phase": "loading", "step": n}` → 끝나면 `{"phase": "result", "view": explain.build_view(result)}`. 빈 입력·읽기 실패·분석 오류는 `{"phase": "error", "message": ...}` (FR2.1–FR2.5)
  - `build_demo()`: `gr.HTML`(css_template=g.css, js_on_load=g.js, head=전역 스타일) + 숨긴 `gr.JSON` + `submit`(분석)·`stop`(`cancels`로 분석 취소)·JSON `change`(js로 화면 갱신) 연결. 정적 파일은 `Path(__file__).parent / "static"`에서 읽고, 없으면 원인을 담은 오류를 낸다.
  - `run()`은 그대로 둔다(테스트·상세 JSON 용).
- [ ] **Step 7. 새 `tests/test_app.py`** (FR2, NFR1, NFR5)
  - `analyze_view`가 단계 4개를 차례로 내보낸 뒤 `result` 화면 상태로 끝난다(정상 경로).
  - 업로드 폴더 밖 경로는 분석하지 않고 `error`를 낸다.
  - 이미지가 아닌 파일이면 `error`를 낸다.
  - 빈 요청(`path` 없음)이면 `error`를 낸다.
  - `_analyze_steps` 결과와 `analyze()` 결과가 같다.
- [x] **Step 8. 검사와 화면 확인** (NFR1, NFR2, NFR3, NFR5)
  - `ruff format .`, `ruff check --fix .`, `pytest -q` 전체 통과
  - `python app.py`로 띄워 브라우저(360×780)에서 확인: 앨범 선택 → 분석 중 단계 → 결과 자동 이동 → 색·선 → 화풍 → 시트 끌어내리기 → 첫 화면 → 다시 셔터, 낮음 등급·스케치 화면, 애니메이션 줄이기 설정
- [x] **Step 9. 정리** — `code-summary.md`, `traceability.json` 작성

### 범위 추가 (2026-11-27): 명화 비교·기록

- [x] **Step 10. `app.py` 비교 명화 고르기** (FR8.1, FR8.5, FR8.8, NFR4, NFR7)
  - `_analyze_steps()`의 모델 호출 수·순서와 `analyze()`·`run()` 결과는 그대로 둔다. `analyze_view`가 쓸 임베딩은 내부 인자(예: 결과를 담을 dict)로 넘겨받는다.
  - `_compare_works(emb, result) -> list[dict]`: `classify.similar_works(emb, k=30)` 1회. 등급이 높음·보통이고 후보에 1위 화가 작품이 있으면 그중 첫 작품을 맨 앞에, 나머지는 비슷한 순으로 채워 최대 3점(같은 `id`는 한 번). 그 밖에는 비슷한 순 3점. 각 항목에 `top1_work`(1위 화가 작품인지) 표시.
  - 명화 파일: `path`를 저장소 루트 기준으로 풀어 `data/` 폴더 안의 실제 jpg·jpeg·png·webp 파일일 때만 읽는다(`resolve(strict=True)`, `is_relative_to`). 읽으면 RGB uint8로 바꾸고 긴 변 512px로 줄인 뒤(화이트밸런스 없음, `preprocess_input` 쓰지 않음) `features.extract_features(img, gray=features.is_grayscale(img))`로 특징을 구하고, 화면용으로 긴 변 320px JPEG data URL을 만든다. 파일이 없거나 읽기 실패면 `image`·`features`는 `None`.
  - `analyze_view`: 분석이 끝난 뒤 `_compare_works`를 부르고 `explain.build_view(result, works)`로 화면 데이터를 만든다. 비교 명화 계산이 실패하면 경고 로그를 남기고 `works=[]`로 결과는 그대로 보여 준다.
- [x] **Step 11. `explain.py` 명화 비교 데이터** (FR7.4, FR8.2, FR8.4–FR8.6, FR4.6, FR9.1)
  - `build_view(result, works=None)`: `works`가 비어 있으면 `compare`는 `None`. 있으면 `compare`에 `eyebrow`·`title`(FR8.2 문구 규칙), `mine_palette`(내 대표색 hex 5개), `works`(화가 전체·짧은 이름, 작품 번호 `id`, 표시 이름 "짧은 이름 #id", 화풍 한글, 유사도 % 정수, `image`, `palette` hex 5개 또는 `None`, `radar` 축별 값 0~1 또는 `None`, 내 값과 차이 작은 축 2개 `near`·큰 축 2개 `far`).
  - 기록용으로 `kind`(사진·그림·스케치: 흑백이면 스케치, 아니면 `input_type`)와 `history_name`(낮음이면 "닮은 화가 없음")을 넣는다.
  - 기존 반환 키와 `render_card()`는 그대로.
- [x] **Step 12. 테스트 추가** (NFR5)
  - `tests/test_explain.py`: `works` 없음 → `compare is None`; 1위 화가 작품 → "가장 닮은 명화예요"; 낮음 등급 → "가장 비슷한 명화예요"; 명화 특징 없음 → `palette`·`radar`가 `None`; 대표색 hex 변환; `near`·`far`가 차이 기준으로 골라짐; `kind`·`history_name`.
  - `tests/test_app.py`: 1위 화가 작품이 맨 앞; 낮음이면 비슷한 순; 후보 없음 → 빈 목록; `data/` 밖 경로는 이미지·특징 없음; `data/` 안 실제 PNG는 data URL과 특징이 생김(monkeypatch로 데이터 폴더 지정); `analyze_view` 결과에 `compare`가 있음.
- [x] **Step 13. `static/g.js`·`static/g.css` 명화 페이지** (FR8, FR3.7, FR4.5–FR4.7, FR6.3, NFR2, NFR3)
  - 진행 막대 4단계(결과·명화·색·선·화풍), `compare`가 없으면 "명화"를 숨기고 결과 → 색·선 (FR8.9).
  - 시트 위 머리말·제목, 내 사진(이미 가진 사진)과 명화 나란히(이미지 없으면 화가 이름 카드), 유사도 배지; 시트에 CLIP 유사도 막대·% 올라가기(0.9초), 대표색 비교(없으면 숨김), 다른 명화 3점(누르면 바꾸고 움직임 다시), 버튼 "이전"·"색·선 비교 보기".
  - 결과 페이지 버튼 "가장 닮은 명화 보기"/"비슷한 명화 보기", 색·선 "이전"은 명화로.
  - 색·선 레이더 탭 "○○ 평균"·"이 명화"(선택된 명화 `radar`가 있을 때만): 비교 다각형·축 강조·카드 제목 바뀜, 처음 누를 때만 그리기 움직임.
  - 새 CSS 선택자는 `.g-app` 아래로 우선순위를 높여 Gradio 기본 스타일(`img`, `h1` 등)에 지지 않게 한다. `prefers-reduced-motion`에서 움직임 끔. 새 버튼에 `data-testid`.
- [x] **Step 14. `static/g.js`·`static/g.css` 기록** (FR1.7, FR9, NFR6)
  - 첫 화면 오른쪽 아래 기록 버튼(아이콘, `data-testid="g-history"`).
  - 결과까지 끝나면 `localStorage`(키 `g-history-v1`)에 기록 저장: 시각, `kind`, `history_name`, %, 등급, 썸네일(사진을 canvas로 긴 변 160px JPEG), 결과 화면 데이터(명화 `image`는 긴 변 96px로 줄이거나 뺌). 최근 30개, 넘으면 오래된 것부터. 모든 읽기·쓰기는 try/catch, 실패하면 한 줄 알림(FR9.10), 깨진 항목은 버림.
  - 기록 화면: 시트가 올라오며 "지난 분석"·개수, 종류 칩, 날짜 묶음, 행(썸네일·이름·"종류 · 시각"·%·등급 칩), 좌우 110px 밀어 지우기 + 4초 되돌리기, 숨은 지우기 버튼, 모두 지우기 확인 창, 빈 화면("사진 찍으러 가기"), "기록은 이 브라우저에만 저장돼요.", 아이콘·끌어내리기로 첫 화면.
  - 행을 누르면 저장된 화면 데이터로 결과 페이지를 연다(분석 다시 안 함, 배경은 썸네일).
- [x] **Step 15. 검사와 화면 확인** (NFR1–NFR7)
  - `ruff format .`, `ruff check --fix .`, `pytest -q` 전체 통과.
  - 가짜 모델로 앱을 띄워 Playwright + Edge(360×780)로 확인: 결과 → 명화(배지·막대·다른 명화 고르기) → 색·선(탭 전환) → 화풍, 명화 파일 있음·없음 두 경우, 기록 저장 → 기록 화면 → 밀어서 지우기·되돌리기 → 모두 지우기 → 기록에서 결과 열기, 저장소 막힘, 애니메이션 줄이기, 가로 스크롤 없음, 콘솔 오류 없음.
- [x] **Step 16. 정리** — `code-summary.md`, `traceability.json`에 Step 10–15 반영

## 커밋·PR 계획 (사람이 요청할 때 실행)

- 단계마다 작은 커밋으로 나눈다(`feat:`·`test:` 접두).
- PR ① Step 2·3(`explain.py`, `tests/test_explain.py`), PR ② Step 4·5(`static/g.css`, `static/g.js`), PR ③ Step 6·7(`app.py`, `tests/test_app.py`). PR ②는 300줄을 넘을 가능성이 커서 본문에 이유를 적는다.
- 이어서 PR ④ 명화 비교(Step 10–13), PR ⑤ 기록(Step 14). 두 기능을 #37에 넣은 사람의 결정과 이유를 본문에 적는다.
- 커밋·push·PR 생성은 사람이 요청할 때만 한다.

## Testing Contract

```json
{
  "version": 1,
  "methodology": "custom",
  "source": "team",
  "ordering": "계약 형식 검사(`tests/test_smoke.py`)는 먼저 있고 그대로 통과해야 하며, 각 이슈의 동작 테스트는 구현과 함께 작성해 같은 PR에서 실행한다.",
  "scope": "express",
  "test_strategy": "minimal",
  "project_type": "brownfield",
  "applicable_notes": [
    {
      "layer": "org",
      "text": "We treat tests as a first-class deliverable in every Bolt. The specific\nmethodology (TDD, BDD, ATDD, or classic test-after) is affirmed at\npractices-discovery and recorded in `team.md` under this heading with explicit\n`Methodology` and `Ordering` fields; Code Generation resolves those fields\nindependently from coverage, tooling, and scope notes.\n\nWhen no posture has been affirmed, our default per scope is:\n- **Methodology**: test-after\n- **Ordering**: implement each applicable testable layer, then write and run\n  that layer's tests.\n- `mvp`, `enterprise`, `feature`, `infra` add an 80% line-coverage\n  floor and CI execution before merge.\n- `bugfix`, `security-patch` add a targeted regression for the specific\n  bug/vulnerability and require the existing suite to remain green.\n- `express` uses the Minimal strategy: requirement-driven unit tests (one per\n  requirement, with a happy-path floor per component); existing tests remain\n  green.\n- `poc`, `refactor`, `workshop`, `classic` add no extra new-test floor and require the\n  existing suite to remain green.\n\nThe active `Test Strategy` still applies in every scope and determines test\nvolume/types. Scope floors are additive; they never reduce or replace the\nselected strategy.\n\nBuild and Test verifies defined coverage floors and affirmed quality targets;\nthey may not be weakened to make a step pass.\n\nAffirm a stricter posture in `team.md` if the team commits to one."
    },
    {
      "layer": "team",
      "text": "- **Methodology**: custom\n- **Methodology evidence**: 인터뷰 Q1에서 B(계약 검사가 먼저 있고, 동작 테스트는 구현과 함께)를 골랐다. 1일차부터 `tests/test_smoke.py`가 스텁과 함께 있었다.\n- **Ordering**: 계약 형식 검사(`tests/test_smoke.py`)는 먼저 있고 그대로 통과해야 하며, 각 이슈의 동작 테스트는 구현과 함께 작성해 같은 PR에서 실행한다.\n- 커버리지 하한 없음. pytest 전체 통과가 조건이다."
    },
    {
      "layer": "project",
      "text": "- 모든 변경은 `pytest` 전체 통과가 조건이다. GitHub Actions CI(`.github/workflows/ci.yml`)가 PR마다 같은 검사를 돌린다.\n- `tests/test_smoke.py`는 인터페이스 형식 검사다. 실제 구현으로 바꿔도 그대로 통과해야 하며, 통과시키려고 검사를 약하게 고치지 않는다.\n- 실제 모델을 내려받거나 불러오는 테스트는 `@pytest.mark.model`로 표시한다. 기본 실행과 CI는 이를 건너뛰고 모델 함수를 `tests/fakes.py`의 가짜로 바꿔 끼운다(`pytest --run-model`로 실제 실행). 모델 함수는 다른 모듈에서 `data.embed_image(...)`처럼 모듈을 통해 부르고, 새 모델 함수에는 `tests/fakes.py`의 `FAKES`에 가짜를 추가한다.\n- 정확도·ECE 같은 평가 수치는 검증셋으로 계산하고 실제 실행 결과만 기록한다. 테스트셋은 #26 최종 평가에서 한 번만 쓴다."
    }
  ],
  "obligations": {
    "strategy": "minimal",
    "strategy_volume": [
      "One verifiable test per requirement at the narrowest effective level.",
      "At least one happy-path unit test per component.",
      "Unit tests are the default; a bugfix/security scope floor may require an integration or E2E regression when that is the narrowest level that reproduces the defect."
    ],
    "scope_floor": [
      "Keep the existing test suite green.",
      "This scope adds no extra new-test floor beyond the selected test strategy."
    ],
    "combination_rule": "Apply every selected-strategy obligation and every scope-floor obligation; neither replaces the other, and a targeted scope regression may add the narrowest necessary test type beyond the strategy default."
  },
  "plan_profile": {
    "methodology": "custom",
    "runner_step": "Verify the existing test runner/configuration and record the exact unit-scoped command.",
    "runner_ready_before_first_test": true,
    "testable_layers": [
      "Data model / database behavior",
      "Repository / data access",
      "Business logic",
      "API / endpoint",
      "Frontend behavior"
    ],
    "steps": [
      "Project structure and production configuration skeleton.",
      "Verify the existing test runner/configuration and record the exact unit-scoped command.",
      "Custom ordering - 계약 형식 검사(`tests/test_smoke.py`)는 먼저 있고 그대로 통과해야 하며, 각 이슈의 동작 테스트는 구현과 함께 작성해 같은 PR에서 실행한다.",
      "Implementation and tests - preserve that exact ordering; do not convert it to layer-local TDD.",
      "Environment/build configuration.",
      "Documentation and traceability."
    ]
  },
  "input_sha256": "sha256:8089a7fc2eb06341bfb02951c5e0e030276e7e8a3e38bfc6b0e7be2f1f014479",
  "contract_sha256": "sha256:2b682b6095ed36b4c0945571f932ed6e5fb3b2244f4196d20c2d023172ba3e52"
}
```
