# Unit Test Instructions — u1-knn-vote (#9 kNN 투표 방식 판정)

## Framework & setup
- pytest(기존 러너). 추가 설정·의존성 없음. 모델 다운로드 없는 순수 수치 테스트.
- 가짜 색인을 `classify.load_index`에 `monkeypatch`로 끼워 검사한다(실제 모델·색인 불필요이므로
  `@pytest.mark.model` 불필요).

## 이 유닛 테스트 실행 명령 (unit-scoped)
```
.venv\Scripts\python -m pytest tests/test_classify.py
```
(이 유닛의 테스트는 `tests/test_classify.py`에만 추가한다. 전체 스위트는 Build and Test / 검증
명령 `.venv\Scripts\python -m pytest`가 따로 돌린다.)

## 작성할 테스트 (`# --- #9 kNN` 절, 표준 전략 기준 8~10개)
- `_knn_logits`: 반환 형식 `(이름 목록, (n, 이름 수) z)`와 이름 목록이 색인에서 읽혀 정렬됨.
- 학습셋 한정: `split=="val"`/`"test"` 이웃은 투표에 포함되지 않음.
- 가중 투표: 유사도 큰 이웃이 많은 이름의 z가 더 큼.
- 음수 유사도 clip: 음수 유사도가 0으로 처리되어 모든 z가 유한함.
- eps 바닥값: 투표 0인 이름의 z가 `log(1e-3)`와 같음(기본 eps), `eps` 키워드 인자 동작.
- 결정성: 이름 순위 동점은 이름순(FR1.6), 이웃 선택 동점은 색인 위치순(FR1.8)으로 재현 가능.
- 엣지: `k<=0`·빈 학습셋 → `ValueError`(학습셋이 비면 n 무관), k 초과 → clamp, n=0 → 빈 z.
- `_topk_accuracy`: `dict {k: 정확도}` 반환, 미지 label 오답(FR2.4), `ks` 초과 clamp,
  행 수≠labels 길이·`ks<=0` → `ValueError`(FR2.5).

## 커버리지
- 프로젝트에 커버리지 하한 없음(team.md). pytest 전체 통과가 조건. 수치 기록은 가짜 색인에서 금지.

## 모킹/데이터
- 작은 결정적 가짜 색인(`emb`·`meta` DataFrame, `split`·`artist`·`style` 열, `attrs["fake"]=True`)을
  테스트 안에서 만들어 `classify.load_index`에 monkeypatch. 외부 데이터·네트워크 없음.
