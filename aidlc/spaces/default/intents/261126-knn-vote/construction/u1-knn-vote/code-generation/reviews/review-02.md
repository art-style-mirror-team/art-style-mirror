## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-11-26T13:48:59Z
**Iteration:** 1
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Minor | modules/classify.py > `_knn_logits` (sims, argsort) | 이웃 선택이 `(n, m)` 유사도 전체를 `np.argsort(-sims, axis=1, kind="stable")`로 정렬한 뒤 앞 k개만 쓴다. 가짜 색인에서는 문제가 없다. 하지만 노트북이 실제 색인의 val 전체를 k=5/10/20으로 세 번씩, artist와 style로 두 번씩 부르면(총 6회) 매번 `n×m` float32 행렬과 같은 크기의 int64 순서 배열을 만든다. 실제 색인이 크면 메모리와 시간이 부담될 수 있다. | 실제 색인으로 돌릴 때 부담이 보이면, 노트북에서 E_val을 청크로 나눠 부르거나 `_knn_logits`가 상위 k만 부분 정렬하도록 바꾼다. 부분 정렬로 바꿔도 FR1.8 동점 규칙(위치 앞선 쪽 우선)은 유지해야 한다. 지금은 필수가 아니다. | New |
| R-02 | Minor | notebooks/eval.ipynb > #9 kNN 평가 셀 (`n_voted`) | "표를 받은 이름 수"를 `z > np.log(eps) + 1e-9`로 센다. 이 값은 노트북 안에 `eps = 1e-3`을 하드코딩한 것이라 `_knn_logits`의 기본 `eps`와 따로 놀 수 있다. 기본 `eps`가 바뀌면 이름 수 평균이 조용히 틀어진다. | `_knn_logits`의 `eps`를 노트북에서 명시적으로 넘기거나(`eps=eps`), 기본값이 바뀌면 이 셀도 함께 고친다는 주석을 남긴다. | New |

> R-01 Not re-checked this round

> R-02 Not re-checked this round

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| `.venv\Scripts\python -m pytest -q` | 47 passed, 2 skipped | 기본 실행에서 전체 통과. 건너뛴 2개는 모델 마커 테스트로 보인다. |
| notebooks/eval.ipynb JSON 점검 | nbformat 4.5, 모든 코드 셀 outputs 0건, execution_count 전부 None | 출력이 지워져 있다(FR4.5). nbformat 패키지는 venv에 없어 스키마 검증 대신 JSON 구조로 확인했다. |
| `git status` / `git diff HEAD -- contracts` | contracts/ 변경 없음 | NFR3 충족. `modules/classify.py`와 `tests/test_classify.py`는 이전 리뷰 이후 별도 변경 흔적이 없고 `_knn_logits(E, k, by, eps=1e-3)` 시그니처가 그대로다. |

### Summary

수정된 노트북은 요구사항을 충족한다. sys.path 부트스트랩은 cwd가 notebooks/일 때 부모를 루트로 잡고 저장소 루트에서도 그대로 동작한다. eps는 `inspect.signature(classify._knn_logits).parameters["eps"].default`로 읽으며 하드코딩이 없다. 가짜 색인 플래그, 화가 수 nunique, k=5/10/20 × artist/style의 Top-1·Top-3, k별 표받은 이름 수 평균이 모두 남아 있고, 테스트셋은 사용하지 않는다(val 마스크만 사용). 막을 만한 문제는 없다.
