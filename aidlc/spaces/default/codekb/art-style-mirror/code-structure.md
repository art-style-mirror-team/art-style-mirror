# Code Structure

## 디렉터리 구성

```
art-style-mirror/
├── app.py                      # D — Gradio 진입점, 파이프라인 조립
├── modules/
│   ├── __init__.py             # docstring 한 줄
│   ├── data.py                 # A — 데이터·CLIP (스텁)
│   ├── classify.py             # B — 판정·융합 (스텁, similar_works는 #13에서 정리)
│   ├── features.py             # C — 색·선 분석 (부분 스텁)
│   └── explain.py              # D — 신뢰도·설명·레이더 (구현됨, 경계값 임시, 문장은 #22 대상)
├── scripts/
│   ├── build_index.py          # A — NotImplementedError (#4)
│   └── build_profiles.py       # C — NotImplementedError (#19)
├── tests/
│   ├── conftest.py             # 루트 sys.path 추가, model 표시 건너뛰기, 가짜 모델 끼우기
│   ├── fakes.py                # 가짜 embed_image / embed_text (FAKES)
│   ├── test_smoke.py           # 계약 형식 + 전체 파이프라인
│   ├── test_explain.py         # D compare()·레이더 동작 + analyze 스케치 대조 기준
│   ├── test_classify.py        # B 동작 테스트 (훑어보기)
│   └── test_features.py        # C 동작 테스트 (훑어보기)
├── contracts/interfaces.md     # 변경 불가 함수 계약
├── docs/plan.md, docs/aidlc-guide.md, docs/notes/{A,B,C,D}.md
├── notebooks/eval.ipynb        # B — 계획 셀 1개
├── artifacts/.gitkeep          # 사전 계산 결과 자리 (비어 있음)
├── samples/.gitkeep            # 팀원 그림·엇갈림 시험 세트 자리 (비어 있음)
├── .github/                    # CI(ruff·pytest), PR 템플릿, 계약 변경 이슈 템플릿, CODEOWNERS
├── pyproject.toml              # Ruff·pytest 도구 설정만 (패키지 배포 안 함)
├── requirements.txt, README.md, AGENTS.md, CLAUDE.md, LICENSE, .gitattributes, .gitignore
```

`static/` 폴더는 없다. 이전 CodeKB에 적혀 있던 #37용 `static/g.css`·`static/g.js`는 이 브랜치(`f7107b3`)에 존재하지 않는다.

## 파일 분류 (code-analysis-guide 분류)

줄 수는 2026-11-27 집중 스캔 범위(`app.py`, `modules/explain.py`, `contracts/interfaces.md`, `tests/test_explain.py`, `tests/test_smoke.py`, `tests/fakes.py`, `requirements.txt`)만 다시 셌고, 나머지는 2026-11-19 전체 스캔 기준이다.

| 파일 | 분류 | 줄 수 | 비고 |
| --- | --- | --- | --- |
| `app.py` | Controller/Handler | 105 | UI 이벤트 → `analyze()` → `render_card()` |
| `modules/data.py` | Service + Repository(색인) | 138 (11-19) | 화가 24명 `ARTIST_STYLE`, 가짜 색인 24×20, 한국어 `KEYWORDS` 15개 |
| `modules/classify.py` | Service | 95 (11-19) | 학습셋 중심점 기반 가짜 확률, `calibration.json` 로더 |
| `modules/features.py` | Service + Utility(전처리) | 116 (11-19) | `cv2.resize`, 흑백 판정 실제, 특징·프로필 가짜 |
| `modules/explain.py` | Service + Static(차트·문구) | 264 | 등급·대조·카드·레이더 실제 구현 |
| `scripts/build_index.py`, `scripts/build_profiles.py` | Utility(배치) | 13씩 (11-19) | 미구현 |
| `tests/test_smoke.py`, `tests/test_explain.py` | Test | 188, 177 | 상세는 `component-inventory.md` |
| `tests/fakes.py` | Test(가짜 모델) | 51 | `fake_embed_image`, `fake_embed_text`, `FAKES` |
| `tests/conftest.py` | Test(공용 설정) | | 훑어보기 |
| `contracts/interfaces.md` | Configuration(계약 문서) | 72 | |
| `requirements.txt`, `pyproject.toml`, `.github/workflows/ci.yml` | Configuration | 13, 21, 60 | `requirements.txt`만 이번에 다시 확인 |
| `notebooks/eval.ipynb` | Test/분석(예정) | 28 | 코드 셀 없음 |

## `modules/explain.py` 내부 구성

| 구역 | 행 | 이름 | 역할 |
| --- | --- | --- | --- |
| 상수 | 19-24 | `EPS`, `GAP_TOL`, `HIGH_*`·`LOW_*` 6개 | z값 분모 하한, 동점 허용 오차, 임시 등급 경계값 |
| 문구 상수 | 26-55 | `FEATURE_KO`, `TYPE_INTRO`, `LEVEL_NOTE`, `DISCLAIMER`, `_KO_FONT_CANDIDATES` | 화면 한국어 문구(값은 `api-documentation.md` 1장). #22가 다룰 곳 |
| 등급 | 58-108 | `_ranked`, `_normalized_entropy`, `_jsd`, `assess_confidence` | plan.md 6.3 지표 계산 |
| 대조 | 111-161 | `_finite_number`, `_usable_stat`, `compare` | 1·2위 z값 대조 |
| 차트 | 164-198 | `_korean_font`(캐시), `_radar_value`, `_radar` | 극좌표 레이더 `Figure` |
| 카드 | 201-264 | `_pct`, `_ko_list`, `render_card` | Markdown 카드 조립. 등급 분기·엇갈림·키워드·대조 문구가 함수 안 f-string. #22가 다룰 곳 |

## `app.py` 내부 구성

| 이름 | 역할 |
| --- | --- |
| `analyze(img) -> dict` | 파이프라인 조립, `result` 12개 키. 안에 보조 함수 `_top(p, k=3)`(확률 dict 상위 k) |
| `run(img)` | 빈 입력 `gr.Error`, `analyze` → `render_card`, 상세 JSON(`path` 제거) → `(text, fig, detail)` |
| `build_demo() -> gr.Blocks` | 화면 구성과 이벤트 연결. 머리말에 `explain.DISCLAIMER` |
| `demo` (모듈 변수) | import 시점에 `build_demo()` 실행. `gradio app.py` 자동 재시작이 이 이름을 찾음 |
| `__main__` | `demo.launch(server_name="127.0.0.1")` |

## 코드 패턴

- **모듈 docstring 규약**: 각 모듈 첫 줄에 Unit 문자·담당자, "1일차 스텁" 설명, "함수 이름·입출력 형식은 그대로 두고 내용만 바꾼다"를 적는다.
- **스텁 표시 규약**: 스텁 함수 본문 첫 줄에 `# TODO(#n): 스텁 — #n <할 일> (담당 X)`. docstring 끝에 `(스텁: …)`로 가짜 동작을 밝힌다. 목록은 `code-quality-assessment.md`.
- **결정적 가짜 값**: `_seed(*parts)`(SHA-1 앞 8바이트) → `np.random.default_rng`. `data.py`, `features.py`, `tests/fakes.py`에 같은 `_seed`가 각각 있다(모듈 독립을 위한 의도적 중복).
- **캐시**: `@lru_cache(maxsize=1)`로 색인, 중심점, 프로필, 한글 글꼴(`explain._korean_font`)을 한 번만 만든다.
- **모듈 상수**: 특징 이름, 임계값, 한글 문구를 모듈 상단에 둔다. 화면 문구는 `explain.py` 상수에서 가져온다(`app.py`도 `explain.DISCLAIMER`를 씀). 다만 `render_card()` 안 문구 대부분은 아직 상수가 아니다.
- **문구 상수의 대체값 방식이 다름**: `TYPE_INTRO.get(input_type, "이 이미지는")`는 대체값이 있고, `LEVEL_NOTE[level]`은 없다(계약 밖 값이면 `KeyError`).
- **`from __future__ import annotations`**와 타입 힌트를 모든 모듈에 쓴다. 반환 dict의 상세 형식은 타입이 아니라 docstring·계약 문서로 표현한다.
- **입력 검증**: 이미지 형식 오류는 `ValueError`(한국어 메시지), UI의 빈 입력은 `gr.Error`, 프로필에 없는 화가는 `KeyError`(`compare`).
- **이름 규칙**: snake_case 함수, UPPER_CASE 상수, `_` 접두 비공개 보조 함수. Ruff(line-length 100, import 정렬 `I`)로 강제.
- **모델 함수 호출 규칙**: 다른 모듈은 `data.embed_image(...)`처럼 모듈을 통해 부른다(가짜 바꿔 끼우기 때문). `app.py`가 이 규칙을 따른다. `explain.py`는 모델 함수를 부르지 않는다.
- **테스트 작성 방식**: `tests/test_explain.py`는 가짜 프로필 dict를 직접 만들어 D 함수에 넣고, 파이프라인 경로가 필요할 때만 함수 안에서 `import app`을 한다.
