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
- AI-DLC 기록은 `aidlc-docs/<A|B|C|D>/`의 자기 폴더에만 쓴다.

## 실행

```bash
py -3.11 -m venv .venv        # Windows. macOS/Linux: python3.11 -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py                 # http://127.0.0.1:7860
pytest
```
