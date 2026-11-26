# Cross-Unit Traceability — #9 kNN 투표 방식 판정

**Verdict: PASS (기능 요구사항 전부 커버; NFR는 횡단 조건으로 충족, 아래 설명)**

단일 유닛(U1 `u1-knn-vote`)이라 단위 간 분산은 없다. `aidlc engine sensor-traceability
--stage build-and-test` 출력 기준.

## 기능 요구사항 (FR) — 전부 커버

| ID | Covered | Owning Unit / File |
|---|---|---|
| FR1.1~FR1.9 | ✅ | u1-knn-vote / `modules/classify.py` (`_knn_logits`) |
| FR2.1~FR2.5 | ✅ | u1-knn-vote / `modules/classify.py` (`_topk_accuracy`) |
| FR3.1~FR3.4 | ✅ | u1-knn-vote / `tests/test_classify.py` (#9 절) |
| FR4.1~FR4.6 | ✅ | u1-knn-vote / `notebooks/eval.ipynb` (#9 절) |

24개 FR 하위 ID 모두 커버. 누락·orphan 없음.

## 비기능 요구사항 (NFR) — 자동 추적 미매핑, 근거로 충족

자동 추적 센서는 NFR을 단일 파일에 매핑하지 못해 `uncovered`로 표시했다(횡단 품질 조건이라 그렇다).
각 NFR은 아래 근거로 충족된다:

| ID | 내용 | 충족 근거 |
|---|---|---|
| NFR1 | 결정성 | `tests/test_classify.py`의 이름순·색인 위치순 동점 테스트, 재현 테스트 |
| NFR2 | 데이터 분할 | 이웃은 학습셋만(`split=="train"`) 테스트, 노트북은 `split=="val"`만 사용, 테스트셋 미사용 |
| NFR3 | 계약·범위 불변 | `contracts/interfaces.md`·`predict_clip`·`tests/test_smoke.py` 변경 없음(diff 0), 신규 함수 비공개 |
| NFR4 | 품질 게이트 | `pytest` 47 passed·2 skipped, `ruff` 통과 (test-results.md) |
| NFR5 | 평가 안정성 | `eps=1e-3` 기본값·투표 0 → `log(1e-3)` 테스트, 노트북은 서명에서 eps를 읽음 |

## 게이트에서 알릴 finding
- 자동 요구사항 추적이 NFR1~NFR5를 미커버로 표시함(단일 파일 매핑 불가). 위 근거로 실제 충족이며,
  승인 전 함께 알린다.
