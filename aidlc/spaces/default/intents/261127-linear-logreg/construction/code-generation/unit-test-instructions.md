# 단위 테스트 지침 — #11 선형 분류기

## 프레임워크·설정

- pytest 9.2.0 (이미 설치). 추가 설정 불필요. `tests/conftest.py`의 `--run-model` 옵션·마커는 그대로.
- 이 작업의 함수는 **모델 함수가 아니다**(CLIP 등을 부르지 않음). 따라서 `@pytest.mark.model` 불필요,
  `tests/fakes.py`의 `FAKES` 추가 불필요.

## 이 변경의 테스트 실행 명령 (범위 한정)

Windows:

```
.venv\Scripts\python -m pytest tests/test_classify.py
```

macOS/Linux:

```
.venv/bin/python -m pytest tests/test_classify.py
```

- 위 명령으로 이 변경의 동작 테스트를 집중 실행한다.
- 전체 통과(스모크 포함)는 Build and Test와 CI가 `pytest` 전체로 확인한다. 머지 조건은
  `pytest` 전체 통과이며, 이 작업도 끝에 전체를 한 번 돌려 확인한다.

## 테스트 내용 (요구 1개당 1개 이상)

`tests/test_classify.py` 끝 `# --- #11 logreg` 절에 다음을 둔다:

1. **학습셋만 사용** — val/test 라벨이 결과 클래스에 영향 주지 않음 확인 (FR2.1)
2. **치우친 입력 → 그 이름 z 최대** — 특정 클래스 쪽으로 만든 임베딩에서 `argmax(z)`가 그 클래스 (FR5.4)
3. **저장→로드 라운드트립 z 동일** — `_save_linear`→`_load_linear` 후 `_linear_logits` 결과 동일 (FR3, FR4, NFR1)
4. **반환 모양** — `(이름 목록, z)`, `z.shape == (n, 이름 수)`, 이름 목록 = `model.classes_` 정렬 (FR5.5)
5. **1차원 입력 ValueError** — `E.ndim != 2`면 `ValueError` (FR5.2)
6. **0장 입력** — `n==0`이면 `(이름 목록, (0, 이름 수))` (FR5.3)
7. **파일 없음 FileNotFoundError** — 없는 경로로 `_load_linear` 시 알기 쉬운 `FileNotFoundError` (FR4.2)
8. **(R1) softmax = predict_proba** — 2클래스 가짜 색인에서 `_linear_logits`의 `z`에 행별 softmax를 적용한
   결과가 `model.predict_proba(_l2_normalize(E))`와 `np.allclose` (FR5.4, NFR2)
9. **(R2) 재저장 C 반영** — `tmp_path`에 `C=1.0` 모델 저장·로드 후 같은 경로에 `C=0.1` 모델을 저장하면
   `_save_linear`의 `cache_clear()` 덕에 다시 로드한 `C`가 `0.1` (FR3.1)

## Mocking / 테스트 데이터

- `monkeypatch.setattr(classify, "load_index", lambda: fake_index)`로 작은 가짜 색인 주입
  (모듈을 통해 호출하므로 `classify.load_index`를 패치). `fake_index`는
  `{"emb": (N,512) float32, "meta": DataFrame(id,artist,style,genre,path,split)}`.
- 저장은 반드시 `tmp_path`에만. 실제 `artifacts/`에 쓰지 않는다.
- 각 테스트 시작에 `classify._load_linear.cache_clear()`로 `lru_cache`를 비운다.

## 커버리지 목표

- 별도 커버리지 하한 없음(팀 규칙). 조건은 `pytest` 전체 통과. 요구 1개당 테스트 1개 이상(Minimal).
