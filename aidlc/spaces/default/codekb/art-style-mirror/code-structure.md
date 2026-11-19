# Code Structure

## 디렉터리 구성

```
art-style-mirror/
├── app.py                      # D — Gradio 진입점, 파이프라인 조립
├── modules/
│   ├── __init__.py             # docstring 한 줄
│   ├── data.py                 # A — 데이터·CLIP (스텁)
│   ├── classify.py             # B — 판정·융합 (스텁)
│   ├── features.py             # C — 색·선 분석 (스텁, 크기 맞추기·흑백 판정은 실제)
│   └── explain.py              # D — 신뢰도·설명·레이더 (구현됨, 경계값 임시)
├── scripts/
│   ├── build_index.py          # A — NotImplementedError (#4)
│   └── build_profiles.py       # C — NotImplementedError (#19)
├── tests/
│   ├── conftest.py             # 저장소 루트를 sys.path에 추가
│   └── test_smoke.py           # 계약 형식 + 전체 파이프라인
├── contracts/interfaces.md     # 변경 불가 함수 계약
├── docs/plan.md, docs/aidlc-guide.md
├── notebooks/eval.ipynb        # B — 계획 셀 1개
├── artifacts/.gitkeep          # 사전 계산 결과 자리 (비어 있음)
├── samples/.gitkeep            # 팀원 그림·엇갈림 시험 세트 자리 (비어 있음)
├── .github/                    # CI, PR 템플릿, 계약 변경 이슈 템플릿
├── requirements.txt, README.md, AGENTS.md, CLAUDE.md, LICENSE, .gitattributes, .gitignore
```

## 파일 분류 (code-analysis-guide 분류)

| 파일 | 분류 | 줄 수 | 비고 |
| --- | --- | --- | --- |
| `app.py` | Controller/Handler | 99 | UI 이벤트 → `analyze()` → `render_card()` |
| `modules/data.py` | Service + Repository(색인) | 138 | 화가 24명 `ARTIST_STYLE`, 가짜 색인 24×20 |
| `modules/classify.py` | Service | 95 | 학습셋 중심점 기반 가짜 확률, `calibration.json` 로더 |
| `modules/features.py` | Service + Utility(전처리) | 116 | `cv2.resize`, 흑백 판정 실제, 특징·프로필 가짜 |
| `modules/explain.py` | Service + Static(차트·문구) | 196 | 등급·대조·카드·레이더 실제 구현 |
| `scripts/build_index.py`, `scripts/build_profiles.py` | Utility(배치) | 13씩 | 미구현 |
| `tests/conftest.py`, `tests/test_smoke.py` | Test | 5, 163 | |
| `contracts/interfaces.md` | Configuration(계약 문서) | 72 | |
| `requirements.txt`, `.github/workflows/ci.yml` | Configuration | 12, 39 | |
| `notebooks/eval.ipynb` | Test/분석(예정) | 28 | 코드 셀 없음 |

## 코드 패턴

- **모듈 docstring 규약**: 각 모듈 첫 줄에 Unit 문자·담당자, "1일차 스텁" 설명, "함수 이름·입출력 형식은 그대로 두고 내용만 바꾼다"를 적는다.
- **스텁 표시 규약**: 스텁 함수 본문 첫 줄에 `# TODO(#n): 스텁 — #n <할 일> (담당 X)`. docstring 끝에 `(스텁: …)`로 가짜 동작을 밝힌다. 목록은 `code-quality-assessment.md`.
- **결정적 가짜 값**: `_seed(*parts)`(SHA-1 앞 8바이트) → `np.random.default_rng`. `data.py`와 `features.py`에 같은 `_seed`가 각각 있다(모듈 독립을 위한 의도적 중복).
- **캐시**: `@lru_cache(maxsize=1)`로 색인(`data._build_index`, `_artist_directions`), 중심점(`classify._centroids`), 프로필(`features._profiles`), 한글 글꼴(`explain._korean_font`)을 한 번만 만든다. `load_index()`는 `meta.copy()`, `load_profiles()`는 dict 얕은 복사를 돌려주고 임베딩 배열은 `setflags(write=False)`로 보호한다.
- **모듈 상수**: 특징 이름(`COLOR_FEATURES`, `LINE_FEATURES`, `NUMERIC_FEATURES`), 임계값(`NEAR_DUPLICATE = 0.95`, `LOGIT_SCALE = 20.0`, `EPS = 0.01`, 등급 경계 6개), 한글 문구(`FEATURE_KO`, `TYPE_INTRO`, `LEVEL_NOTE`, `DISCLAIMER`)를 모듈 상단에 둔다.
- **`from __future__ import annotations`**와 타입 힌트(`np.ndarray`, `dict`, `list[tuple]`)를 모든 모듈에 쓴다. 반환 dict의 상세 형식은 타입이 아니라 docstring·계약 문서로 표현한다.
- **입력 검증**: 이미지 형식 오류는 `ValueError`(한국어 메시지), UI의 빈 입력은 `gr.Error`.
- **이름 규칙**: snake_case 함수, UPPER_CASE 상수, `_` 접두 비공개 보조 함수.
