# AGENTS.md — AI 도구 공통 규칙

이 저장소에서 일하는 모든 AI 코딩 도구(Claude Code, AI-DLC 등)는 아래 규칙을 따른다.
배경과 전체 계획은 `docs/plan.md`, 함수 시그니처는 `contracts/interfaces.md`가 기준이다.

## 프로젝트

어떤 이미지든 넣으면 닮은 화가·화풍 Top 3를 찾고, 왜 닮았는지 색과 선으로 설명하는 Gradio 앱.
CLIP(소재·분위기·양식)과 OpenCV(색·선) 두 관점의 확률을 합친 신뢰도 순으로 Top 3를 정한다.

| 역할 | 담당 | 파일 |
| --- | --- | --- |
| A 데이터·CLIP | 홍승민 | `modules/data.py`, `scripts/build_index.py` |
| B 판정·융합 | 홍예원 | `modules/classify.py`, `notebooks/eval.ipynb` |
| C 색·선 분석 | 심현준 | `modules/features.py`, `scripts/build_profiles.py` |
| D 신뢰도·UI·통합 | 김현승 | `modules/explain.py`, `app.py` |

## 반드시 지킬 규칙

1. **자기 모듈 파일만 수정한다.** 다른 모듈이 필요하면 직접 고치지 말고 이슈로 요청한다.
2. **`contracts/interfaces.md`의 함수 이름·입출력 형식은 바꾸지 않는다.** 바꿔야 하면 팀 합의 후 별도 PR로 한다.
3. **`main`에 직접 push하지 않는다.** `--force` push, 공유 기록 rebase도 금지. 원본 이미지·대용량 파일(100MB 이상)은 커밋하지 않는다.
4. **PR 설명에 AI의 핵심 판단 이유를 3줄로 적는다.** 담당자가 그 내용을 설명할 수 있어야 머지한다.
5. **정확도·수치는 실제 실행 결과만 쓴다.** 예상치를 결과처럼 적지 않는다.
6. **데이터 분할을 지킨다.** 프로필·분류기는 학습셋으로만, 온도 T·가중치 w·등급 기준값은 검증셋으로만 정한다. 테스트셋은 최종 평가(#26)에서만 연다.
7. **명화와 사용자 입력은 반드시 같은 CLIP 모델 버전으로 변환한다.**
8. **최종 순위는 `fuse()` 결과만 쓴다.** OpenCV·키워드 쪽 코드가 순위를 따로 뒤집지 않는다.
9. **이미지는 RGB `np.ndarray`(uint8), 긴 변 512px로 맞춘 뒤 처리한다.** 화이트밸런스는 사용자 입력에만 적용한다. `cv2.imread()`는 BGR이므로 반드시 RGB로 바꾼다.
10. **커밋은 작게, 단계별로 나눈다.** 기능 하나를 한 번에 몰아 커밋하지 않는다. 머지는 머지 커밋 방식만 쓴다.
11. **WikiArt는 비상업 연구용이다.** README에 출처와 용도를 반드시 적는다.

## 작업 방식

- 브랜치: `feat/<이슈번호>-<내용>` (예: `feat/17-color-features`), 버그는 `fix/...`
- 커밋 메시지: `feat: ...`, `fix: ...`, `docs: ...`, `test: ...`, `chore: ...`
- PR: 본문에 `Closes #<이슈번호>`, 리뷰어 1명, 파일 1~3개·변경 300줄 이내
- 작업 시작 전 `git fetch origin` 후 `git merge origin/main`
- 변경 후 `pytest`가 통과해야 한다. `tests/test_smoke.py`는 인터페이스 형식을 검사하므로 실제 구현으로 바꿔도 그대로 통과해야 한다.

## AI-DLC

사용법 전체는 `docs/aidlc-guide.md`를 따른다.

- 이슈 하나 = 브랜치 하나 = intent 하나 = PR 하나. 작은 작업은 `/aidlc express: ...`, 실험·비교는 `/aidlc classic: ...`, 버그는 `/aidlc bugfix: ...`.
- 시작 문장에 이슈 번호, 수정할 파일, "contracts/interfaces.md는 변경 불가"를 넣는다.
- 계약 설계 단계에서 `contracts/interfaces.md`와 다른 계약을 만들지 않는다. Unit은 A·B·C·D 4개로 고정하고 서로 의존하지 않게 한다.
- 각 단계 승인은 그 이슈의 담당자 본인이 한다. **AI는 사람의 질문 응답·단계 승인·hooks 신뢰를 대신 채우거나 승인된 것처럼 기록하지 않는다.** 게이트가 막히면 실제 상태를 그대로 보고한다.
- AI-DLC 버전은 `.aidlc-version`을 따른다. `aidlc config`를 다시 돌리거나 `.claude/` 생성 파일을 고치지 않는다(설정 변경은 D가 PR로).
- 기록은 `aidlc/spaces/default/intents/<id>/`에 남기고 코드와 같은 PR로 커밋한다. 남의 intent 폴더는 고치지 않는다. 개인 커서·세션 파일은 커밋하지 않는다.
- 팀 Unit claim(`/aidlc --claim`, `unit share/publish/land`)과 Operation 단계는 쓰지 않는다.

## 실행

```bash
py -3.11 -m venv .venv        # Windows. macOS/Linux: python3.11 -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py                 # http://127.0.0.1:7860
pytest
```
