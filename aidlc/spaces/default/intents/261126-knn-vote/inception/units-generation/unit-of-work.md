# Units of Work — #9 kNN 투표 방식 판정

이 intent는 기존 `modules/classify.py`(Unit B — 판정·융합) 안에서 끝나는 작은 변경이라,
구현 단위는 **하나**다.

**출처(Sources)**: 이 단위 분해는
[`requirements.md`](../requirements-analysis/requirements.md)의 요구사항(FR1~FR4, NFR1~NFR5)을
근거로 한다. 아래 각 책임은 그 FR ID를 인용한다.

| Unit ID | Directory | Kind | Deployment | Complexity |
|---|---|---|---|---|
| U1 | `u1-knn-vote` | library | embedded (기존 모듈에 편입) | S |

## U1 — u1-knn-vote

- **설명**: CLIP 임베딩의 kNN 가중 투표로 화가·화풍 판정 로짓을 만드는 비공개 함수와, 그 로짓으로
  Top-k 정확도를 재는 재사용 유틸을 `modules/classify.py`에 추가한다. 동작 테스트와 검증셋 평가
  노트북 셀도 같은 단위에 포함한다.
- **책임(Responsibilities)**:
  - `_knn_logits(E, k, by, eps=1e-3)` — 학습셋 이웃 가중 투표 로짓 (FR1.1~FR1.9)
  - `_topk_accuracy(z, names, labels, ks=(1, 3))` — Top-k 정확도 유틸, #10·#11 재사용 (FR2.1~FR2.5)
  - `tests/test_classify.py`의 `# --- #9 kNN` 동작 테스트 (FR3.1~FR3.4)
  - `notebooks/eval.ipynb`의 `#9 kNN` 검증셋 평가 셀 (FR4.1~FR4.6)
- **Kind 근거**: `library` — 독립 실행체(service)가 아니라 기존 모듈에 편입되는 재사용 코드다.
  UI·배포 산출물이 없으므로 service/ui/packaging 설계 산출물은 해당 없음.
- **경계·제약(Implementation notes)**:
  - 공개 계약(`contracts/interfaces.md`)과 `predict_clip()`·`tests/test_smoke.py`는 불변(NFR3).
  - 신규 함수는 비공개(`_` 접두). 색인은 같은 CLIP 버전, 위치 기준(`.iloc`) 접근.
  - 기존 `_l2_normalize`와 학습셋 선택 패턴을 재사용한다.
- **Deployment model**: embedded — 별도 배포 없이 `modules/classify.py`에 합쳐진다.
- **프로젝트 Unit 대응**: U1은 프로젝트 규칙으로 고정된 Unit **B — 판정·융합**(담당 홍예원)의 이
  intent 범위 구현 단위다. 새 프로젝트 Unit을 만드는 것이 아니며, 수정 대상 파일은
  `modules/classify.py`, `tests/test_classify.py`, `notebooks/eval.ipynb` **셋뿐**이다.

이 intent에는 다른 단위가 없으므로 병렬화·순서 결정 대상이 아니다.
