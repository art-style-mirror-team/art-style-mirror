# Integration Test Instructions — #9 kNN 투표 방식 판정

표준 전략이라 통합 테스트 지침을 둔다. 다만 이 범위는 **단위 간 통합이 없다**: 유닛이 하나이고,
`_knn_logits`·`_topk_accuracy`는 기존 색인(`load_index`)을 읽어 쓰는 내부 함수다.

## 경계
- `u1-knn-vote` ↔ 기존 색인(`modules/data.load_index`): 읽기 전용 소비. 새 계약 없음.
- 전체 파이프라인 형식 통합은 기존 `tests/test_smoke.py`가 계속 검사한다(이번 변경에서 불변).

## 실행
```
.venv\Scripts\python -m pytest tests/test_smoke.py
```
- `test_smoke.py`는 입력→전처리→판정→`fuse()`→결과 카드까지 반환 형식을 검사한다. 이번 변경 후에도
  그대로 통과해야 한다(실제로 통과: 전체 47 passed, 2 skipped).

## 기대 커버리지
- 신규 통합 테스트는 불필요(단위 간 경계 없음). 기존 스모크 테스트 녹색 유지가 통합 기준.

## 데이터·환경
- 가짜 색인(단위 테스트) / 스텁 색인(스모크). 외부 서비스·네트워크 없음.
