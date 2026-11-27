# Code Quality Assessment

이 평가는 파일을 읽어서 한 것이다. 2026-11-19 전체 스캔, 2026-11-26 집중 스캔, 2026-11-27 집중 스캔(#22: D 영역·테스트·가짜 모델·계약·requirements) 모두 `pytest`·CI·앱을 실행하지 않았으므로 통과 여부나 수치는 적지 않는다. 마지막으로 기록된 실행 결과는 `docs/notes/D.md`의 "48 passed, 2 skipped"(PR #46·#44 머지 직전, 사람이 실행)이며 이 스캔이 확인한 값이 아니다.

## 테스트

| 항목 | 상태 |
| --- | --- |
| 프레임워크 | pytest 9.2.0. `tests/conftest.py`가 루트를 `sys.path`에 넣고, `model` 표시 테스트를 기본으로 건너뛰며, 나머지에서는 모델 함수를 `tests/fakes.py`의 가짜로 바꿔 끼운다 |
| 범위 | `test_smoke.py` 15개 함수(17개 케이스, 그중 `model` 2개 기본 건너뜀), `test_explain.py` 16개 함수(17개 케이스), `test_classify.py`·`test_features.py`(이번에 열지 않음) |
| 성격 | `test_smoke.py`는 형식(계약) 검사 중심: shape·L2 노름·키 집합·확률 합 1·내림차순·`split` 값. `test_explain.py`는 `compare()` 경계 동작, `app.analyze`의 스케치 대조 기준, 레이더 축·값 |
| 엣지 케이스 | 스케치(흑백 3채널) 입력, `gray=True` 경로, 데이터셋 밖 입력(`max_sim=0.2` → 낮음), 상세 JSON `path` 제거, NaN·inf·bool·numpy 수·std 0·잘못된 프로필·빈 특징·미등록 화가, 레이더 범위 밖 값·숫자 아닌 특징 |
| 커버리지 | 측정 도구·설정 없음 |
| 규칙 | `tests/test_smoke.py`는 실제 구현으로 바꿔도 그대로 통과해야 하며, 통과시키려고 약하게 고치지 않는다(project.md) |

빈틈:
- 정확도·보정 품질 테스트는 없다(평가는 `eval.ipynb` 몫).
- **`render_card()` 문장은 형식만 검사한다**: `(str, Figure)`와 `DISCLAIMER` 포함뿐이다. 입력 유형별 제목, 등급 3종 분기, 관점 엇갈림 문장, 키워드 줄, 대조 문장 유무, 2위 없음은 테스트가 없다. #22 완료 기준(입력 3종 × 등급 3종)을 검사하는 동작 테스트가 필요하다.
- `assess_confidence()` 동작 테스트는 `test_smoke.py`의 2개(높음, 데이터셋 밖 낮음)뿐이고 "보통" 경로는 검사하지 않는다.
- 파이프라인 테스트에서 `input_type`·`keywords`는 스텁(`detect_type`, `clip_keywords`)이 임베딩으로 정하므로 테스트가 고를 수 없다. 조합 검사는 `result` dict를 직접 만들어야 한다.
- 잘못된 이미지 입력(`ValueError`) 경로를 검사하는 테스트는 없다(2026-11-19 기준).

## 린트·스타일

- Ruff 0.17.6(`pyproject.toml`: py311, line-length 100, 기본 규칙 + import 정렬 `I`, 큰따옴표, `.claude`·`aidlc` 제외). CI `ruff (format + lint)` 작업이 `ruff format --check`와 `ruff check`를 돌리고 실패하면 머지하지 않는다
- 코드 자체는 일관됨: snake_case, 상수 대문자, 타입 힌트, 한국어 docstring. 깊게 읽은 파일에 `# noqa`는 없다

## CI/CD

- `.github/workflows/ci.yml`: PR, `main` push, 수동 실행 → `ruff` 작업(5분 제한) + `pytest` 작업(Ubuntu, Python 3.11, CPU torch 선설치, `pip install -r requirements.txt`, `pytest -q`, 20분 제한) (2026-11-26 기준)
- 최소 권한(`contents: read`), 같은 ref 동시 실행 취소
- 배포 파이프라인 없음(MVP는 로컬 실행). main은 승인 1명과 CI 2개가 필요(`docs/notes/D.md`)

## 문서

| 문서 | 평가 |
| --- | --- |
| `README.md` | 실행법(Windows/macOS/Linux), 데이터 출처·비상업 조건, 팀 표. "1일차 뼈대, 결과는 가짜 값" 명시. 정확도표·스크린샷은 #30 예정 (2026-11-19 기준) |
| `docs/plan.md` | 요구사항·식·일정·이슈·Git 규칙이 상세함. #22 완료 기준은 "입력 3종 × 등급 3종 모두 자연스러운 문장" 한 줄이라 "자연스러움"의 판정 기준은 따로 정해야 함 |
| `docs/notes/{A,B,C,D}.md` | 역할별 결정·열린 문제(작업 전 읽기 규칙, `AGENTS.md`). D 노트에 #22 관련 메모 2건(선 방향 일관성 문장, 유형·흑백 판정 엇갈림) |
| `contracts/interfaces.md` | 함수·`result` 키·해석 확인 사항이 명확함 |
| docstring | 모든 공개 함수에 반환 형식과 스텁 여부. `compare()`는 경계 동작까지 자세함. `render_card()`는 한 줄뿐, `_radar()`는 없음 |
| PR·이슈 템플릿 | 검증 결과·AI 판단 이유·체크리스트, 계약 변경 절차 |

## 빠른 평가 (good / fair / poor)

| 항목 | 등급 | 근거 |
| --- | --- | --- |
| 이름 명확성 | good | 함수·상수 이름이 계약·plan.md 용어와 같음 |
| 함수 크기 | good | 대부분 30줄 이하. `app.analyze`(약 48줄), `render_card`(약 55줄)는 순차 조립이라 수용 가능하나, #22에서 문장 조합이 늘면 `render_card`를 문장 조각 보조 함수로 나눌 후보 |
| 오류 처리 | fair | 이미지 형식 `ValueError`, 빈 입력 `gr.Error`, 미등록 화가 `KeyError`(`compare`). 파일 I/O(`calibration.json` JSON 오류) 처리 없음, 로깅 없음 |
| 테스트 존재 | good | 모든 계약 함수와 전체 경로가 테스트됨(형식 수준). D의 `compare`·레이더는 동작 수준까지, 카드 문장은 형식 수준만 |
| 중복 | good | `_seed` 중복(data·features·fakes)은 모듈 독립을 위한 의도적 중복 |

## 기술 부채·주의 신호

### 의도된 1일차 스텁 (`TODO(#n)`)

2026-11-19 전체 스캔 기준 목록에, 2026-11-27 `TODO` 검색(`modules/`)과 `docs/notes/D.md`로 확인한 변화를 반영했다.

| 위치 | 이슈 | 현재 동작 |
| --- | --- | --- |
| `data.embed_image`, `data.embed_text` | #5 | 입력 해시 기반 가짜 벡터 |
| `data.load_index` | #3, #4 | 24명 × 20점 가짜 색인 |
| `data.clip_keywords` | #7 | 15개 한국어 키워드 중 무작위 |
| `classify.detect_type` | #8 | `emb[:3]` argmax (PR #56 대기) |
| `classify.predict_clip` | #9–#12, #14 | 가짜 색인 학습셋 중심점 softmax |
| `classify.fuse` | #15 | 가중합만 |
| `features.preprocess_input` | #16 | 리사이즈 위주(종이 자르기·화이트밸런스 없음) |
| `features.extract_features` | #17, #18 | 가짜 값(`direction`은 PR #44부터 0~1) |
| `features.load_profiles` | #19 | 가짜 프로필 |
| `features.predict_cv` | #20, #14 | 식은 실제, `T = 1.0`, 피셔 점수 거르기 없음 |
| `scripts/build_index.py`, `scripts/build_profiles.py` | #4, #19 | `NotImplementedError` |
| `explain.py` 등급 경계값 6개 | #24 | 임시값 |

이것들은 결함이 아니라 계획된 상태다(project.md DECIDED). 각 스텁은 그 이슈 담당자만 바꾼다.

### 설계 수준 주의점

1. **Unit 간 import**: B→A(`load_index`), C→A(`ARTISTS`). 상세는 `dependencies.md`.
2. **`T_cv` 소유 불일치**: `calibration.json`(B)에 `T_cv`가 있으나 `predict_cv`(C)는 `T = 1.0` 하드코딩.
3. **화가 이름 암묵 계약**: `app.py`의 `profiles[top1]` — `fuse()` 결과 이름이 `load_profiles()` 키에 없으면 `KeyError`.
4. **float 입력 캐스팅**: `features.preprocess_input`은 범위 확인 없이 `astype(np.uint8)`(2026-11-19 기준). Gradio 경로(uint8)에서는 영향 없음.
5. **`calibration.json` 파싱 오류 미처리**: `classify.load_calibration`은 JSON 오류를 그대로 올린다(조용한 실패는 아님).
6. **CLIP 모델 버전 미고정**: A가 #5에서 상수 하나로 정하기로 함(`docs/notes/D.md`). 그 전까지 "같은 CLIP 모델 버전" 규칙은 코드로 보장되지 않음.
7. **문서 차이**: plan.md 5장·10.1의 `aidlc.settings.json`이 저장소에 없음, plan.md 트리에 `.github/workflows/ci.yml` 누락(2026-11-19 기준).

### D 영역 — #22 해석 문장 관점 (2026-11-27 집중 스캔)

1. **입력 유형이 제목에만 쓰임**: `TYPE_INTRO`(`explain.py:38-42`)는 제목 한 줄(216행)에만 들어간다. 등급 문구·엇갈림 문장·대조 문장은 사진·그림·스케치 모두 같다.
2. **등급 문구가 두 갈래**: 분기는 낮음 / 그 외(218-235행)이고, `LEVEL_NOTE["높음"]`이 빈 문자열이라 높음에는 해설이 없다. 보통은 "애매한 부분이 있어요." 한 문장뿐이다.
3. **스케치에 색 표현**: 관점 엇갈림 문장이 "분위기는 …, **색감**·선은 … 쪽에 가까워요."(239행)로 고정이다. 스케치는 `predict_cv(gray=True)`가 선 특징만 쓰므로 "색감"이 사실과 맞지 않는다.
4. **CLIP 키워드가 나열뿐**: `**CLIP 키워드**: 키워드(0.71), …`(243행). 키워드는 한국어 명사구(A 스텁 `KEYWORDS`, 예: "두꺼운 붓 자국")라 문장에 넣을 수 있지만, 실제 구현(#7) 뒤에도 명사구일지는 계약이 정하지 않는다(`(str, float)`만 고정). 키워드가 비어 있는 경우도 계약상 막혀 있지 않다(`k=3`이면 길이 3).
5. **조사 미처리**: `"{특징}이(가) {top1} 평균에 더 가까워요."`(248행). 특징 이름 끝 글자(예: "밝기" → 가, "선 방향 일관성" → 이)에 따라 조사를 고르지 않는다. "선 방향 일관성이 … 더 가까워요"가 자연스러운지 확인하라는 메모가 있다(`docs/notes/D.md` 81행).
6. **`gray`와 `input_type` 엇갈림**: 흑백 판정(C, 픽셀)과 유형 판별(B, CLIP)이 다를 수 있다(예: 연한 그림이 흑백 → 선 특징만 대조, 제목은 "이 그림은"). #25에서 정할 문제로 노트에 있으나, 문장이 어느 쪽을 기준으로 할지 #22에서도 부딪힌다. `render_card()`는 지금 `gray`를 쓰지 않는다.
7. **문구가 함수 안에 흩어짐**: 문구 상수는 4개뿐이고 나머지 문장은 `render_card()` 안 f-string이다. 3×3 조합 문구를 상수 표로 모으면 테스트·검토가 쉬워진다.
8. **대체값 방식 차이**: `TYPE_INTRO.get(..., "이 이미지는")`는 대체값이 있고 `LEVEL_NOTE[level]`은 `KeyError`. 계약상 세 값만 오므로 문제는 아니나 한쪽으로 맞추는 것이 좋다.
9. **2위 없음 처리 이중화**: `app.analyze`는 2위가 없으면 `top2 = top1`, `render_card`는 `top2 = None`. 동작상 문제는 없다(`fuse()` 계약상 늘 3개).
10. **레이더와 대조의 기준 차이**: 레이더는 `result["features"]` 전체로 그려 스케치에서도 색 축이 나오고, 대조(`compare`)는 스케치면 선 특징만 쓴다(`app.py:43`).
11. **레이더 축 선택 기준**: `_radar()`는 `isinstance(v, (int, float))`라 `np.float32` 값을 빼지만, `compare()`는 `_finite_number`로 numpy 실수를 받는다. 지금 스텁은 Python `float`라 영향 없음.
12. **테스트 파일 docstring**: `tests/test_explain.py` 첫 줄이 "explain.compare() 동작 테스트 (#21)"인데 레이더(#45) 테스트도 있고 #22 문장 테스트가 더해질 예정이다.

이전 CodeKB(2026-11-26)의 "`direction` 의미 변경 대기"(PR #44·#46)는 2026-11-27 두 PR 머지로 해소됐다(`FEATURE_KO["direction"]` = "선 방향 일관성", `_radar_value()`는 자르기만). "#37 PR 크기"와 "CSS·JS 린터 없음" 항목은 #37 코드가 이 브랜치에 없어 뺐다.

### 보안·규정

- 로컬 바인딩(`127.0.0.1`), 인증 없음(로컬 단일 사용자 MVP), 비밀값·환경변수 사용 없음
- 사용자 이미지는 메모리에서만 처리하고 저장하지 않는다(엇갈림 저장 #25는 미구현)
- 카드 Markdown에는 화가 이름·화풍·키워드·특징 이름 같은 내부 데이터만 넣고 사용자 입력 문자열은 넣지 않는다. #22에서 문장 템플릿을 늘려도 이 원칙을 유지한다. 키워드가 실제 CLIP 구현(#7)에서 외부 문장 목록으로 바뀌어도 Markdown 특수문자가 섞일 수 있음을 염두에 둔다
- 데이터 라이선스(비상업)는 README에 명시됨
- 원본 이미지·대용량 파일 커밋 금지는 `.gitignore`(`/data/`, `*.pt`)와 PR 체크리스트로 관리
