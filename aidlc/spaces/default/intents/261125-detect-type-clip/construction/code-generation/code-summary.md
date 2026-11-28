# Code Summary — #8 `detect_type()` CLIP zero-shot

## 변경·생성 파일

| 파일 | 변경 |
| --- | --- |
| `modules/classify.py` | `detect_type()` 스텁(`TODO(#8)`)을 CLIP zero-shot 구현으로 교체. 모듈 상수 `TYPE_PROMPTS`와 헬퍼 `_l2()` 추가, `from modules import data` import 추가 |
| `tests/test_classify.py` | 신규. `detect_type` 가짜 기반 동작 테스트 4개 |

다른 `modules/*.py`, `contracts/interfaces.md`, `tests/fakes.py`, `tests/test_smoke.py`는 건드리지 않았다.

## 핵심 구현 결정

- `TYPE_PROMPTS`: photo 3 / painting 4 / sketch 3 = 총 10개 영어 문장(Q1). 리뷰 요청으로 조정: photo는 "실제 장면"으로 좁혀 종이 그림을 폰으로 찍은 입력이 photo로 끌려가지 않게 하고, 직접 그린 색 그림("a colored drawing on paper")을 painting에 포함. 프롬프트가 영어인 이유 주석은 "CLIP이 영어 캡션으로 학습돼"로 수정. 로직은 그대로.
- 유형별 문장을 `data.embed_text(prompts)`로 임베딩 → 평균 → `_l2()`로 재정규화한 프로토타입 1개. 입력 `img_emb`도 `_l2()`로 정규화 후 각 프로토타입과 코사인 유사도 최대인 유형 반환(Q2: 프로토타입 평균).
- **모듈 경유 호출**: `data.embed_text(...)`로 불러 autouse 가짜가 끼워진다. 프롬프트 임베딩을 매 호출 계산해(9문장, 가벼움) `monkeypatch`가 항상 반영되도록 했다 — 모듈 전역 캐시를 쓰지 않는다.
- 결정성: `dict` 삽입 순서 보존 + `sim > best_sim`(엄격 부등호)로 동률 시 앞 유형 유지 → 같은 입력에 항상 같은 결과. 입력은 `np.asarray(..., float32)`로 받아 list도 허용.
- 새 모델 함수를 만들지 않아 `tests/fakes.py` 수정 불필요(FR2.2).

## 테스트 결과 (실제 실행, 2026-11-25)

- 범위 실행 `pytest tests/test_classify.py tests/test_smoke.py -q` → **19 passed, 2 skipped** (리뷰 수정 후 재실행 포함).
- 전체 `pytest -q` → **34 passed, 2 skipped**. (skip 2개는 `@pytest.mark.model` 실제 모델 테스트로 기본/CI에서 건너뜀 — 정상.)
- `ruff format .` → 26 files unchanged. `ruff check --fix .` → All checks passed.
- `tests/test_smoke.py::test_classify_formats`는 **수정 없이** 그대로 통과(NFR2).

신규 테스트 4개: `test_detect_type_returns_valid_literal`, `test_detect_type_deterministic`, `test_detect_type_matches_prompt_class`, `test_detect_type_scale_invariant`.

## 실행했지만 이 단계에서 돌리지 않은 테스트

- 실제 CLIP으로 도는 테스트는 추가하지 않았다(Q3: 가짜 기반만). `@pytest.mark.model` 범위 밖.

## 계획 대비 편차

- 없음. 계획 6단계 모두 수행. (주: Code Generation 중 빌드 에이전트가 막판에 멈춰, 산출물 기록 단계를 컨덕터가 마무리하고 테스트·ruff를 직접 실행해 결과를 확인했다. 코드·테스트 내용은 계획 그대로다.)
