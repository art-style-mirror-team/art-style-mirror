# 요구사항 — #8 `detect_type()` CLIP zero-shot 구현

## Intent 분석

`modules/classify.py`(Unit B)의 스텁 `detect_type(img_emb)`를 실제 CLIP zero-shot
분류기로 바꾼다. 목표는 입력 이미지의 유형(사진·그림·스케치)을 CLIP 임베딩만으로
판별해, 이후 파이프라인(화이트밸런스 적용 여부, 결과 카드의 `input_type` 표시)이
쓸 수 있는 세 리터럴 중 하나를 안정적으로 돌려주는 것이다. 유형별 영어 문장
앙상블을 `data.embed_text(...)`로 임베딩하고 입력 임베딩과 비교한다.

## 기능 요구사항 (FR)

### FR1. `detect_type(img_emb)` CLIP zero-shot 판별
- **FR1.1** 입력은 CLIP 이미지 임베딩 `img_emb`(L2 정규화, shape `(512,)`의 `np.ndarray`)다. 함수는 이미지가 아니라 임베딩을 받는다(계약 유지).
- **FR1.2** 반환은 `"photo"` · `"painting"` · `"sketch"` 세 리터럴 중 **정확히 하나**다. `contracts/interfaces.md`에 고정된 형식이며 변경하지 않는다. "unknown" 같은 제4의 값은 없다.
- **FR1.3** 각 유형을 묘사하는 **영어 문장 앙상블**(유형당 여러 문장)을 `data.embed_text(list[str])`로 임베딩한다. 반드시 `data` 모듈을 경유해 호출한다(FR2).
- **FR1.4** 유형별 문장 임베딩을 평균해 유형당 **프로토타입 벡터 1개**를 만들고(평균 후 L2 재정규화), 입력 `img_emb`와의 **코사인 유사도가 최대**인 유형을 반환한다.
- **FR1.5** 같은 입력에 대해 **결정적**이다(동일 `img_emb` → 항상 동일 결과). 유형 문장과 그 임베딩은 매 호출 재계산하지 않고 캐시해도 된다(동작 불변).

### FR2. 모델 함수의 모듈 경유 호출
- **FR2.1** 문장 임베딩은 `modules.data`를 통해 `data.embed_text(...)`로 부른다. `from modules.data import embed_text`로 직접 바인딩하지 않는다 — 기본 `pytest`·CI가 `tests/fakes.py`의 가짜로 바꿔 끼울 수 있어야 한다.
- **FR2.2** 유형 판별용 모델 함수를 **새로 만들 경우에만** `tests/fakes.py`의 `FAKES`에 대응 가짜를 추가한다. (현재 `fake_embed_text`는 이미 존재하므로 `embed_text`만 쓰면 추가 불필요.)

### FR3. 동작 테스트 `tests/test_classify.py`
- **FR3.1** `detect_type`의 동작 테스트를 `tests/test_classify.py`에 둔다(요청 문구의 `test/`는 저장소 관례 `tests/`로 맞춘다).
- **FR3.2** 기본 `pytest`·CI에서 도는 **가짜 기반** 테스트만 둔다. 최소: ① 반환이 세 리터럴 중 하나인지 ② 동일 입력에 결정적인지 ③ 각 유형 쪽으로 심은 가짜 임베딩이 해당 유형으로 분류되는지(happy path).
- **FR3.3** 실제 CLIP을 내려받는 테스트는 추가하지 않는다(`@pytest.mark.model` 범위 밖, 이번 작업에서 제외 — 아래 Out of scope).

## 비기능 요구사항 (NFR)

- **NFR1 (테스트 가능성)** 변경 후 `pytest` 전체가 통과한다(Windows: `.venv\Scripts\python -m pytest`). 기본 실행과 CI는 실제 모델 없이, `tests/fakes.py`의 가짜로만 통과해야 한다.
- **NFR2 (계약 형식 유지)** `tests/test_smoke.py`(특히 `detect_type`의 반환 형식 검사)가 **수정 없이** 그대로 통과한다. 통과시키려 스모크 테스트를 약화하지 않는다.
- **NFR3 (모델 일관성)** 유형 판별 임베딩은 명화·사용자 입력과 **같은 CLIP 모델 버전**을 쓴다. `img_emb`를 만든 `data.embed_image`와 문장을 임베딩하는 `data.embed_text`가 같은 모델이어야 비교가 유효하다.
- **NFR4 (코드 스타일)** `ruff format .`과 `ruff check --fix .`를 통과한다(`pyproject.toml`, line-length 100, import 정렬 `I`). 한국어 docstring·snake_case 등 기존 관례를 따른다.

## 제약 (Constraints)

- **C1** `contracts/interfaces.md`는 변경하지 않는다. `detect_type(img_emb) -> str` 시그니처와 반환 리터럴은 고정.
- **C2** Unit B 범위만 수정한다: `modules/classify.py`의 `detect_type` 본문과 테스트 `tests/test_classify.py`. 다른 `modules/*.py`는 고치지 않는다(필요하면 이슈로 요청).
- **C3** 커밋은 작게 단계별로 나눈다. `main` 직접 push·force·rebase·squash 금지, PR+리뷰 1명+머지 커밋.

## 가정 (Assumptions)

- **A1** 유형 문장은 **영어**로 작성한다(Q1). 근거: 사용 CLIP이 영어 학습 기반일 가능성이 높아 zero-shot 품질이 낫다. (검증 책임: B, 실제 모델 연결 후 #26 평가 때 확인 가능.)
- **A2** 앙상블 결합은 **프로토타입 평균** 방식이다(Q2). 유사도 평균 대신 채택.
- **A3** 구체 영어 문구 세트는 Code Generation에서 B가 확정한다(예: "a photo", "a painting", "a pencil sketch"에 몇 개 변형 추가).
- **A4** CLIP 모델 ID는 아직 코드에 고정되지 않았다(#4·#5 소관). `detect_type`은 `data` 모듈이 로드하는 모델을 그대로 쓰고, 모델 ID를 직접 지정하지 않는다.

## Out of scope

- `predict_clip`·`similar_works`·`fuse` 등 `classify.py`의 다른 함수(#9~#15).
- 실제 CLIP으로 도는 `@pytest.mark.model` 테스트(이번엔 가짜 기반만 — Q3).
- `app.py`·UI 통합, 정확도·ECE 등 평가 수치 산출(#26).
- 유형 문장 언어를 한국어/다국어로 바꾸는 실험.

## Open questions

- **OQ1** 유형당 영어 문장 개수와 정확한 문구 — Code Generation에서 B가 확정(동작 테스트는 가짜 기반이라 문구에 영향받지 않음).
