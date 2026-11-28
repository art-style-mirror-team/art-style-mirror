# Bolt Plan — #9 kNN 투표 방식 판정

**출처(Sources)**: `requirements.md`, `unit-of-work.md`, `unit-of-work-dependency.md`.

이 intent는 단위가 하나라 **Bolt**(한 번의 Construction 통과로 한 조각을 만들어 끝까지 돌아가게
하는 전달 슬라이스)가 하나뿐이다. 순서 선택이 없다.

## Bolt B1 — u1-knn-vote

- **포함 Unit**: U1 (`u1-knn-vote`).
- **Walking-skeleton 표시**: 해당 없음 — 1일차 스텁과 `app.py`가 이미 끝까지 도는 슬라이스이고,
  이 Bolt는 그 안의 판정 로직을 실제 kNN 구현으로 바꾼다. 새 skeleton 세리머니는 없다.
- **Definition of Done**:
  - `_knn_logits`·`_topk_accuracy`가 요구사항(FR1~FR2)대로 구현됨.
  - `tests/test_classify.py`의 `# --- #9 kNN` 테스트가 추가되고 `pytest` 전체 통과(FR3, NFR4).
  - `ruff format`·`ruff check` 통과(NFR4).
  - `notebooks/eval.ipynb`의 `#9 kNN` 셀이 가짜 색인에서 오류 없이 실행되고 출력은 지워짐(FR4).
  - `tests/test_smoke.py`·`contracts/interfaces.md`·`predict_clip()` 불변(NFR3).
- **확신 가설(Confidence hypothesis)**: kNN 가중 투표 로짓이 결정적으로(동점은 이름·위치순)
  계산되고 수치적으로 안정적이며(모든 z 유한), `_topk_accuracy`가 #10·#11에서 재사용 가능하다.
- **예상 데모**: 검증셋에서 `k=5,10,20`의 Top-1·Top-3 정확도와 k별 "표를 받은 이름 수 평균"을
  `eval.ipynb`로 산출(가짜 색인일 때는 수치 기록 금지), 그리고 `pytest` green.
