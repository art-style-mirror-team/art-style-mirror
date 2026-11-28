# Requirements Analysis — 질문 (#8 detect_type CLIP zero-shot)

맥락: `detect_type(img_emb) -> "photo" | "painting" | "sketch"` 를 CLIP zero-shot으로 구현한다.
반환 형식은 `contracts/interfaces.md`에 고정되어 변경 불가. 유형별 문장을 `data.embed_text(...)`(모듈 경유)로 임베딩해 입력 임베딩과 비교한다. 아래는 동작을 좌우하는 선택지다.

## Q1. [제품] 유형 판별 문장(prompt)의 언어

CLIP zero-shot은 "a photo of ..." 같은 문장을 임베딩해 입력과 비교한다. 어떤 언어로 쓸까?

- A. 영어 ("a photo", "a painting", "a pencil sketch" 등) — 대부분의 CLIP이 영어로 학습됨
- B. 한국어 ("사진", "그림/회화", "연필 스케치" 등)
- C. 영어+한국어를 모두 앙상블에 포함
- X. Other (please specify)

[Answer]: A (영어)

## Q2. [개발자] 문장 앙상블을 하나의 점수로 합치는 방식

유형마다 문장이 여러 개다. 입력 임베딩과 어떻게 비교할까?

- A. 유형별 문장 임베딩을 평균해 프로토타입 벡터 1개를 만들고, 입력과의 코사인 유사도 비교 (간단·안정적)
- B. 유형별 각 문장과의 코사인 유사도를 모두 구한 뒤 평균
- C. 둘 다 구현해 비교해 보고 결정
- X. Other (please specify)

[Answer]: A (클래스별 프로토타입 평균 벡터와 코사인 유사도)

## Q3. [개발자] `test_classify.py`의 동작 테스트 범위

기본 `pytest`·CI는 `tests/fakes.py`의 가짜(`fake_embed_text`/`fake_embed_image`)를 끼워 돈다.

- A. 가짜 기반 동작 테스트만: 반환이 세 리터럴 중 하나인지, 같은 입력에 결정적인지, 가짜로 심은 유형이 맞게 나오는지
- B. A에 더해, 실제 CLIP으로 도는 `@pytest.mark.model` 테스트도 1개 추가 (`pytest --run-model`로만 실행)
- X. Other (please specify)

[Answer]: A (가짜 기반 동작 테스트만)

## Q4. [개발자] 테스트 파일 위치

요청 문구에는 `test/test_classify.py`라고 적혔지만, 이 저장소의 테스트는 모두 `tests/`(복수형, `tests/test_smoke.py` 등)에 있다.

- A. `tests/test_classify.py` — 기존 테스트 폴더 관례에 맞춤
- B. `test/test_classify.py` — 요청 문구 그대로 새 폴더 생성
- X. Other (please specify)

[Answer]: A (tests/test_classify.py)
