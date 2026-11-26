# Unit Dependency DAG — #9 kNN 투표 방식 판정

단위가 하나뿐이라 의존 간선이 없다. DAG는 노드 하나(`u1-knn-vote`)로 구성되며 순환이 없다.

## Dependency DAG

- `u1-knn-vote` — 의존 단위 없음(`depends_on: []`).

## Integration points

- 내부 통합만 있다: `u1-knn-vote`는 기존 `modules/data.load_index`와 `modules/classify._l2_normalize`를
  읽어 쓴다(둘 다 이미 존재). 새 단위 간 계약(API·이벤트·공유 스키마)은 없다.
- `data.load_index`는 Unit A 소유이지만, 이는 기존 공개 계약(`contracts/interfaces.md`)의 **읽기
  전용 소비**이며 새 계약을 만들지 않으므로 `depends_on`에 넣지 않는다(빌드·테스트가 Unit A의 새
  코드를 필요로 하지 않는다).

## Parallel development opportunities

- 단일 단위라 병렬화 대상이 없다. 유효한 위상 정렬은 `u1-knn-vote` 하나뿐이다.

## Edge block (machine-readable)

```yaml
units:
  - name: u1-knn-vote
    kind: library
    depends_on: []
```
