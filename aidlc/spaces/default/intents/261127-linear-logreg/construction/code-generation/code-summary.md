# Code Summary — #11 선형 분류기(로지스틱 회귀)

## 생성/수정한 파일

- `modules/classify.py` — `import joblib`, `import sklearn`,
  `from sklearn.linear_model import LogisticRegression` 추가. `LINEAR_PATH` 상수 추가.
  비공개 함수 4개 추가: `_fit_linear(by, C=1.0)`, `_save_linear(models, path=LINEAR_PATH)`,
  `_load_linear(path=LINEAR_PATH)`, `_linear_logits(E, by, model=None)`. 기존 공개 함수
  (`predict_clip`, `similar_works`, `fuse`, `detect_type`)와 헬퍼(`_centroids`, `_l2_normalize`)는
  변경하지 않음.
- `tests/test_classify.py` — 파일 끝에 `# --- #11 logreg` 절 추가(헬퍼 `_linear_index`/`_biased`
  + 테스트 7개).

지정된 2개 파일만 변경. `contracts/interfaces.md`·`tests/test_smoke.py`·`requirements.txt` 등 그 외
파일은 그대로. `artifacts/linear.pkl`·노트북은 생성하지 않음(#9 머지 후 별도 커밋).

## 리뷰 반영 (revision)

- **(R1)** `_linear_logits` 이진 분류 처리를 `np.column_stack([-z, z])` → `np.column_stack([np.zeros_like(z), z])`로
  변경. `[0, z]`로 쌓으면 `softmax(z) = [sigmoid(-z), sigmoid(z)] = [1-p, p]`가 되어 `model.predict_proba`와
  정확히 일치한다(이전 `[-z, z]`는 `sigmoid(2z)`라 불일치). argmax 동작은 그대로 유지.
- **(R2)** `_save_linear` 끝에서 `_load_linear.cache_clear()` 호출. `@lru_cache` 때문에 같은 경로에 다시
  저장해도 옛 모델이 읽히던 문제를 막아, 재저장 후 새 모델이 읽힌다.
- 테스트 2개 추가: softmax=predict_proba 동치(`np.allclose`), 같은 경로 `C=1.0`→`C=0.1` 재저장 반영.

## 핵심 구현 결정

- **이진 클래스 `decision_function` 정형화**: sklearn은 2클래스일 때 `decision_function`이 `(n,)`을
  주고 양수는 `classes_[1]` 쪽을 선호한다. `z.ndim == 1`이면 `np.column_stack([np.zeros_like(z), z])`로
  쌓아 column 0 = `classes_[0]`, column 1 = `classes_[1]` 점수가 되게 해 `(n, 이름 수)` 모양을 보장하고
  `softmax(z)`가 `predict_proba`와 일치하게 한다(R1). 3클래스 이상은 `decision_function`이 이미
  `classes_` 순서의 `(n, n_classes)`를 주므로 그대로 사용. 반환은 `(list(model.classes_), z)`로
  #9 `_knn_logits`·#10 `_centroid_logits`와 동일.
- **학습셋 한정·위치 기반 추출**: `train = (meta["split"]=="train").to_numpy()` 불리언 마스크로
  `emb[train]`을 거르고 라벨은 `meta.loc[train, by]`. 클래스 수·이름 하드코딩 없음. (라벨 인덱스가
  아니라 위치 기준 — 기존 `_centroids` 방식, load_index 위치 계약 준수.)
- **정규화**: 학습 입력·추론 입력 모두 기존 `_l2_normalize` 적용.
- **저장/로드**: `_save_linear`는 `{"artist","style","C":{...},"sklearn_version":...}`를 `joblib.dump`
  (상위 폴더 자동 생성). `_load_linear`는 `@lru_cache(maxsize=1)`, 파일 없으면 경로+학습/저장 힌트가
  담긴 한국어 `FileNotFoundError`. 테스트에서 `cache_clear()` 가능.

## 테스트 커버리지 (신규 9개, 요구 1개당 1개 이상)

monkeypatch로 `classify.load_index`에 작은 가짜 색인 주입, 저장은 `tmp_path`에만:
학습셋 한정(FR2.1), 치우친 입력 argmax(FR5.4), 저장→로드 라운드트립 z 동일(FR3/FR4/NFR1),
반환 모양(FR5.5), 1차원 `ValueError`(FR5.2), 0장 입력(FR5.3), 파일 없음 `FileNotFoundError`(FR4.2),
softmax=predict_proba 동치(R1, FR5.4/NFR2), 같은 경로 재저장 C 반영(R2, FR3.1).

## 실제 실행 결과 (예측 아님)

- `ruff format .` → 27 files left unchanged. `ruff check --fix .` → All checks passed!
- `python -m pytest tests/test_classify.py -q` → **17 passed** (기존 8 + 신규 9).
- `python -m pytest -q` (전체, 스모크 포함) → **123 passed, 5 skipped**
  (skip은 `@pytest.mark.model` 테스트, `--run-model` 없이 건너뜀 — 정상).
- 환경: Python venv, scikit-learn 1.9.1, joblib 1.6.0.

## 실행했으나 미실행 테스트 / 계획과의 차이

- 작성했으나 실행 못 한 테스트: 없음(신규 7개 모두 실행·통과).
- 계획과의 차이: 없음.
