# Risk & Sequencing Rationale — #9 kNN 투표 방식 판정

## 순서 근거

작업 단위가 하나뿐이라 순서를 고를 여지가 없다. 유효한 위상 정렬은 `u1-knn-vote` 하나이고,
Bolt도 B1 하나다. WSJF·위험 우선·가치 우선 같은 점수 모델은 비교 대상이 없어 적용하지 않는다.

Walking skeleton(처음부터 끝까지 도는 최소 동작 슬라이스) 관점에서, 1일차 스텁(`modules/` 4개와
`app.py`)이 이미 입력→전처리→CLIP·OpenCV→`fuse()`→결과 카드까지 돈다. 이 Bolt는 그 슬라이스를
새로 만드는 것이 아니라 판정 로직 한 조각을 실제 kNN 구현으로 교체한다. 따라서 새 skeleton
체크포인트 세리머니는 적용하지 않는다.

## 위험

| 위험 | 완화 |
|---|---|
| 수치 불안정(음수 유사도·투표 0 → `log`가 NaN/-inf) | FR1.4 `max(sim,0)` clip, FR1.5 모든 z 유한, FR3.4 테스트 |
| 비결정성(동점) | FR1.6 이름순·FR1.8 색인 위치순, FR3.4 테스트 |
| `#14` 온도 보정 왜곡 | NFR5 `eps=1e-3`로 투표 0 정답의 과도한 저확률 방지 |
| 계약·범위 침범 | NFR3: `contracts/interfaces.md`·`predict_clip`·`test_smoke.py` 불변, 비공개 함수 |
| 색인 라벨 인덱스 오용 | 위치 기준(`.iloc`)만 사용(FR1.7) |

사용한 휴리스틱: 해당 없음(단일 단위). Cohn/Reinertsen/SAFe 점수 모델은 비교 대상이 없어 미적용.
