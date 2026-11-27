# 요구사항 — #11 선형 분류기(로지스틱 회귀) 학습·저장

## Intent 분석 (목표)

모듈 B(`modules/classify.py`)에 CLIP 임베딩 기반 **선형 분류기(로지스틱 회귀)** 판정 방식을
하나 더 추가한다. 이는 #9 kNN(`_knn_logits`), #10 중심점(`_centroid_logits`)과 **같은 입출력
모양**을 갖는 세 번째 후보로, 이후 #14 판정 방식 선정·#15 융합에서 비교·선택될 수 있게 하는 것이
목적이다. 이번 이슈의 산출물은 **코드와 동작 테스트뿐**이며, 학습된 모델 파일·노트북·정확도
수치는 범위가 아니다.

## 기능 요구사항 (Functional Requirements)

### FR1. 상수·비공개 함수 추가 (`modules/classify.py`)
- **FR1.1** 모듈 상수 `LINEAR_PATH`를 추가한다. 값은 `artifacts/linear.pkl`을 가리키며, 기존
  `CALIBRATION_PATH`와 같은 방식(모듈 기준 절대 경로)으로 정의한다.
- **FR1.2** 아래 네 비공개 함수를 추가한다. 모두 밑줄 접두(`_`)로 시작하는 내부 헬퍼이며
  `contracts/interfaces.md`의 공개 계약에 속하지 않는다.

### FR2. `_fit_linear(by, C=1.0)` — 학습
- **FR2.1** `load_index()`의 **학습셋(`split=="train"`)만으로** 학습한다. 검증·테스트 행은
  학습에 쓰지 않는다.
- **FR2.2** 입력 임베딩은 기존 `_l2_normalize`로 정규화한 뒤 사용한다.
- **FR2.3** `sklearn.linear_model.LogisticRegression`을 `C=C`, 수렴에 충분한 `max_iter`,
  고정 `random_state`로 학습한다.
- **FR2.4** 라벨(화가·화풍)의 클래스 목록은 색인의 `meta[by]`에서 읽는다. 클래스 수·이름을
  코드에 숫자/문자열로 하드코딩하지 않는다.
- **FR2.5** `by`는 색인 메타 열 이름(`"artist"` 또는 `"style"`)을 받아 그 열에 대한 모델 하나를
  학습해 돌려준다.

### FR3. `_save_linear(models, path=LINEAR_PATH)` — 저장
- **FR3.1** `{"artist": <artist 모델>, "style": <style 모델>, "C": {...}, "sklearn_version": ...}`
  형태의 dict를 `joblib`으로 `path`에 저장한다.
- **FR3.2** `"C"`는 `by`별로 사용한 C값을 기록한다. `"sklearn_version"`은 저장 시점의 sklearn
  버전 문자열을 기록한다(로드 호환성 추적용).

### FR4. `_load_linear(path=LINEAR_PATH)` — 로드
- **FR4.1** 저장된 dict를 읽어 그대로 돌려준다.
- **FR4.2** 파일이 없으면 **알기 쉬운 `FileNotFoundError`**를 던진다(무엇이 왜 없는지 메시지로
  설명).
- **FR4.3** `lru_cache`로 캐싱하더라도 테스트에서 `_load_linear.cache_clear()`로 캐시를 비울 수
  있어야 한다.

### FR5. `_linear_logits(E, by, model=None)` — 로짓 계산 (형제 함수와 동일 모양)
- **FR5.1** `model`이 주어지지 않으면 `_load_linear()[by]`를 사용한다.
- **FR5.2** 입력 `E`는 `(n, 512)` 형태다. 2차원이 아니면 `ValueError`를 던진다.
- **FR5.3** `n==0`(0장)이면 `(이름 목록, (0, 이름 수) 형태의 빈 z)`를 돌려준다.
- **FR5.4** `E`를 `_l2_normalize`한 뒤 `z = model.decision_function(E)`를 계산한다.
- **FR5.5** 반환은 `(이름 목록, z)`이며 이름 목록은 `model.classes_`의 정렬 순서, `z`는
  `(n, 이름 수)` 형태로 **#9 `_knn_logits`·#10 `_centroid_logits`와 동일한 모양**이다.

### FR6. 동작 테스트 (`tests/test_classify.py`)
- **FR6.1** 파일 끝에 `# --- #11 logreg` 절로 테스트를 추가한다. 기존 테스트와 `tests/test_smoke.py`는
  고치지 않는다.
- **FR6.2** 작은 가짜 색인을 `classify.load_index`에 monkeypatch한다(모듈을 통해 호출).
- **FR6.3** 저장은 `tmp_path`에만 한다. 실제 `artifacts/`에 쓰지 않는다.
- **FR6.4** 다음을 검사한다: (a) **학습셋만** 사용하는지, (b) 학습 데이터 쪽으로 치우친 입력에서
  그 이름의 `z`가 가장 큰지, (c) 저장→불러오기 후 `z`가 같은지, (d) 반환 모양, (e) 1차원 입력
  `ValueError`, (f) 0장 입력, (g) 파일 없음 `FileNotFoundError`.

## 비기능 요구사항 (Non-Functional Requirements)

- **NFR1 (결정성)** 고정 `random_state`로 같은 입력에서 같은 결과가 나와야 한다. 저장→로드
  라운드트립 후 `z`가 동일해야 한다(FR6.4c).
- **NFR2 (형식 일관성)** `_linear_logits`의 반환 모양은 #9·#10 형제 함수와 바이트 단위로 호환되는
  `(이름 목록, (n, 이름 수) z)`여야 한다. 최종 순위는 이후 `fuse()`만 쓰므로 이 함수가 순위를
  뒤집지 않는다.
- **NFR3 (테스트 통과)** 변경 후 `pytest` 전체가 통과해야 한다. 모델 함수가 아니므로
  `@pytest.mark.model`·`tests/fakes.py`의 `FAKES` 추가는 필요 없다.
- **NFR4 (코드 스타일)** `ruff format .`·`ruff check --fix .`를 통과한다(line-length 100, import
  정렬 `I`). snake_case·대문자 상수·한국어 docstring 관례를 따른다.

## 제약 (Constraints)

- **C1** `contracts/interfaces.md`를 변경하지 않는다. `predict_clip()`도 이번에 바꾸지 않는다
  (#12에서 결정).
- **C2** 수정 파일은 `modules/classify.py`, `tests/test_classify.py` 둘뿐이다(자기 Unit = 모듈 B).
- **C3** `artifacts/linear.pkl` 생성과 노트북 작업은 이번 범위가 아니다(#9 머지 후 별도 커밋).
- **C4** 온도 T·가중치 w·등급 경계값을 정하지 않는다(검증셋 전용, 이번 범위 밖). 프로필·분류기
  학습은 학습셋만 쓴다.
- **C5** 커밋은 작게 단계별로 나눈다. `main` 직접 push·force·rebase·squash 금지. PR은 머지 커밋.

## 가정 (Assumptions)

- **A1** `max_iter=1000` — 요청문 "충분히"의 구체값. (owner: 담당 B, 상태: 미검증)
- **A2** `random_state=0` — 요청문 "고정"의 구체값. (owner: 담당 B, 상태: 미검증)
- **A3** 두 모델을 만들 때 `models = {"artist": _fit_linear("artist", C=...), "style": _fit_linear("style", C=...)}` 형태로 조립하고, 저장 payload의 `"C"`는 `{"artist": C, "style": C}`로 기록한다.
- **A4** #9 `_knn_logits`·#10 `_centroid_logits`는 아직 코드에 없으나, 이번 `_linear_logits`는 요청문이
  명시한 `(이름 목록, (n, 이름 수) z)` 모양을 기준으로 삼는다.

## 범위 밖 (Out of Scope)

- `artifacts/linear.pkl` 실제 생성·커밋, 학습 스크립트/노트북(`notebooks/eval.ipynb`).
- 정확도·ECE 등 평가 수치 산출(검증셋/테스트셋).
- `predict_clip()`·`fuse()` 등 공개 함수 동작 변경, 판정 방식 최종 선정(#14).
- 온도 보정·가중치·등급 기준값 결정.

## 열린 질문 (Open Questions)

- A1·A2(`max_iter`, `random_state`)의 구체값은 추론값이다. 다른 값을 원하면 승인 게이트에서
  지정하면 된다. 그 외 열린 질문 없음.
