# Unit Story Map — #9 kNN 투표 방식 판정

`stories.md`가 없으므로 요구사항(`FR`)의 하위 ID를 기준으로 매핑한다. 모든 요구사항은 단일 단위
`U1` (`u1-knn-vote`)이 구현한다.

| FR ID | Unit | Directory |
|---|---|---|
| FR1.1 | U1 | u1-knn-vote |
| FR1.2 | U1 | u1-knn-vote |
| FR1.3 | U1 | u1-knn-vote |
| FR1.4 | U1 | u1-knn-vote |
| FR1.5 | U1 | u1-knn-vote |
| FR1.6 | U1 | u1-knn-vote |
| FR1.7 | U1 | u1-knn-vote |
| FR1.8 | U1 | u1-knn-vote |
| FR1.9 | U1 | u1-knn-vote |
| FR2.1 | U1 | u1-knn-vote |
| FR2.2 | U1 | u1-knn-vote |
| FR2.3 | U1 | u1-knn-vote |
| FR2.4 | U1 | u1-knn-vote |
| FR2.5 | U1 | u1-knn-vote |
| FR3.1 | U1 | u1-knn-vote |
| FR3.2 | U1 | u1-knn-vote |
| FR3.3 | U1 | u1-knn-vote |
| FR3.4 | U1 | u1-knn-vote |
| FR4.1 | U1 | u1-knn-vote |
| FR4.2 | U1 | u1-knn-vote |
| FR4.3 | U1 | u1-knn-vote |
| FR4.4 | U1 | u1-knn-vote |
| FR4.5 | U1 | u1-knn-vote |
| FR4.6 | U1 | u1-knn-vote |

## Cross-cutting

- 없음. 단일 단위라 단위 간 분산 요구사항이 없다.

## Implementation order within U1

1. `_knn_logits` (FR1.*) → 2. `_topk_accuracy` (FR2.*) → 3. 동작 테스트 (FR3.*) →
4. 검증셋 평가 노트북 셀 (FR4.*).

## Coverage verification

- 열거된 24개 FR 하위 ID 모두 U1에 배정됨. U1은 모든 행을 가진다.
- NFR1~NFR5는 U1 구현·테스트 전반에 걸친 품질 조건으로, 별도 행 없이 U1이 함께 만족한다.
