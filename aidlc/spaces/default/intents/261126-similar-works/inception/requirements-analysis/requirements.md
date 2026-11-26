# 요구사항 — #13 `similar_works()` 실제 색인 검색 정리

> 스테이지: requirements-analysis · 범위: express · 깊이: Minimal
> 담당 Unit: B 판정·융합 (`modules/classify.py`, 홍예원)
> 출처: 초기 요청(project-description.json), `contracts/interfaces.md`(변경 불가),
> 코드 지식 베이스(`codekb/art-style-mirror/`), 현재 스텁 `modules/classify.py:69`

## 의도 분석

`modules/classify.py`의 `similar_works(emb, k=3)` 스텁을 **실제 색인 기준 검색**으로
정리한다. 목표는 입력 임베딩과 가장 닮은 명화 ≤ k점을, 자기 자신(거의 동일한 작품)을
제외하고, 결정적이고 안전한 방식으로 돌려주는 것이다. 함수 이름·인자·반환 형식은
`contracts/interfaces.md`가 정한 대로 **그대로 유지**한다(계약 변경 금지).

## 기능 요구사항 (FR)

### FR1 — 코사인 유사도 기반 검색
- **FR1.1** 입력 임베딩 `emb`와 색인 임베딩(`load_index()["emb"]`)을 각각 **L2 정규화**한
  뒤 내적(= 코사인 유사도)으로 유사도를 계산한다.
- **FR1.2** 검색 범위는 색인 **전체**다. `split`(train/val/test)으로 거르지 않는다.
- **FR1.3** 유사도 내림차순으로 정렬해 상위 후보를 고른다.

### FR2 — 자기 자신(근접 중복) 제외
- **FR2.1** 유사도가 `NEAR_DUPLICATE`(0.95) **이상**인 후보는 자기 자신으로 보고
  결과에서 제외한다. 즉 유사도 < 0.95 인 후보만 남긴다.

### FR3 — 반환 형식 (계약 준수)
- **FR3.1** 반환값은 `list[dict]`이며 각 원소는 키 `{"id", "artist", "style", "path", "score"}`를
  가진다. 길이는 ≤ k, `score` 내림차순이다. (`contracts/interfaces.md` B 표)
- **FR3.2** 값은 **파이썬 기본 타입**으로 돌려준다: `id`·`artist`·`style`·`path`는 `str`,
  `score`는 `float`. (pandas/numpy 스칼라 타입을 그대로 반환하지 않는다 — AS-3)

### FR4 — 엣지 케이스의 결정적 동작
- **FR4.1** `k == 0`이면 빈 리스트 `[]`를 돌려준다.
- **FR4.2** 제외 후 남은 후보 수가 k보다 적으면(또는 k가 후보 수보다 크면) 남은 후보
  전부를 돌려준다(예외 없이, 길이 ≤ 실제 후보 수).
- **FR4.3** 유사도가 같은 후보들의 순서는 **결정적**이다: score 내림차순 1차 정렬 +
  색인 행 위치 오름차순 2차 정렬(안정 정렬). 같은 입력·색인이면 항상 같은 순서를 돌려준다. (AS-1)

## 비기능 요구사항 (NFR)

### NFR1 — 계약 불변성
- `contracts/interfaces.md`의 `similar_works` 시그니처·반환 형식을 바꾸지 않는다.
  최종 순위는 이 함수가 아니라 `fuse()`가 정하므로, 이 함수가 순위를 뒤집지 않는다.

### NFR2 — 테스트
- 동작 테스트를 `tests/test_classify.py`에 추가한다. FR1~FR4를 각각 검증한다
  (코사인 정렬, 0.95 제외, 네이티브 타입, k=0, k>후보 수, 동점 결정성).
- `tests/test_smoke.py`는 **고치지 않는다**. 실제 구현 후에도 그대로 통과해야 한다.
- 변경 후 `pytest` 전체가 통과해야 한다(모델 함수는 `tests/fakes.py` 가짜로 대체되어 실행).

## 제약 (Constraints)

- C1: 자기 Unit(`modules/classify.py`)과 `tests/test_classify.py`만 수정한다.
  다른 `modules/` 파일·`tests/test_smoke.py`·`contracts/interfaces.md`는 건드리지 않는다.
- C2: 색인은 `modules.data.load_index()`를 통해 얻는다(`from modules.data import load_index`는
  현재 모듈 상단에 이미 있으며, 모델 테스트 대체 규칙은 `data.load_index` 호출 경로를 따른다).
- C3: 코드 작성 후 `ruff format .` / `ruff check --fix .`를 통과해야 한다(line-length 100).

## 가정 (Assumptions)

- AS-1: 동점 순서는 색인 행 위치(낮은 인덱스 우선)로 정한다 — FR4.3.
- AS-2: 색인·입력이 이미 정규화되어 있어도 함수 안에서 명시적으로 L2 정규화를 다시 수행한다
  (영벡터는 나눗셈 0 방지 처리).
- AS-3: 반환 스칼라는 파이썬 기본 타입으로 변환한다 — FR3.2.

## 범위 밖 (Out of Scope)

- 벡터화/ANN 등 성능 최적화(현재 색인 규모에서 선형 스캔으로 충분; 코드 지식 베이스에 메모됨).
- `predict_clip`·`fuse`·`detect_type` 등 같은 모듈의 다른 함수 변경.
- `calibration.json`·온도 보정·가중치 관련 변경.

## 열린 질문 (Open Questions)

- 없음. (가정 AS-1~AS-3은 승인 게이트에서 담당자가 조정 가능)
