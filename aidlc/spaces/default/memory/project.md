# Project-Level Rules

> Project-specific specialisation and corrections. Loaded after `org.md` and
> `team.md` as strict-additive guidance.
> Populated by practices-discovery and the self-learning loop.
>
> Use sparingly: most teams don't need a project layer. Reach for it
> only when this specific project needs stable, durable guidance beyond the
> team practice (for example, package-specific release checks or an additional
> regression suite for a legacy component).

## Way of Working

<!-- Project-specific specialisation. Example: -->
<!-- This monorepo requires package-scoped branch names and a package owner -->
<!-- review in addition to the team's normal merge policy. -->
<!-- A project that merges into another branch than team.md names says so on its own line, read before team.md's: -->
<!-- - **Integration branch**: develop -->

- **Integration branch**: main
- 팀 규칙의 기준은 루트 `AGENTS.md`와 `docs/plan.md` 9장, AI-DLC 사용법은 `docs/aidlc-guide.md`다.
- 이슈 하나 = 브랜치 하나(`feat/<이슈번호>-<내용>`, 버그는 `fix/...`) = intent 하나 = PR 하나.
- `main`에는 GitHub PR과 리뷰 1명 승인을 거쳐 **머지 커밋**으로만 합친다. org 기본값의 squash 머지와 rebase 머지는 쓰지 않는다. 개별 커밋과 머지 기록이 모두 남아야 한다(plan.md 9.2).
- Construction은 지금 체크아웃한 이슈 브랜치에서 진행한다. 별도 worktree·Bolt 브랜치를 만들지 않는다. 불가피하게 만들면 squash하지 않고 머지 커밋으로 이슈 브랜치에 합친다.
- 팀 Unit claim(`--claim`, `unit share/publish/pin/land`)과 Operation 단계는 쓰지 않는다.

## Walking Skeleton

<!-- Project-specific specialisation. Example: -->
<!-- The walking skeleton must exercise the legacy service adapter as well -->
<!-- as the new service boundary. -->

- 1일차 스텁(`modules/` 4개 파일의 `TODO(#n)`)과 `app.py`가 이미 walking skeleton이다. 입력 이미지 → 전처리 → CLIP·OpenCV 두 관점 → `fuse()` → 신뢰 등급 → 결과 카드까지 끝까지 돈다.
- 검증 명령: `pytest` (Windows: `.venv\Scripts\python -m pytest`). `tests/test_smoke.py`가 전체 파이프라인과 `contracts/interfaces.md`의 반환 형식을 검사한다.

## Testing Posture

<!-- Project-specific specialisation. -->

- 모든 변경은 `pytest` 전체 통과가 조건이다. GitHub Actions CI(`.github/workflows/ci.yml`)가 PR마다 같은 검사를 돌린다.
- `tests/test_smoke.py`는 인터페이스 형식 검사다. 실제 구현으로 바꿔도 그대로 통과해야 하며, 통과시키려고 검사를 약하게 고치지 않는다.
- 정확도·ECE 같은 평가 수치는 검증셋으로 계산하고 실제 실행 결과만 기록한다. 테스트셋은 #26 최종 평가에서 한 번만 쓴다.

## Guard Policy

<!-- Project-specific. Mode: strict, relaxed, or off. Strict here holds for every intent, whatever one person asks in chat; relaxed or off here applies to every intent whose policy came from its scope, unless the person sets another; changing this line changes it. A section under the retired Change Control heading, written by an earlier release, is still read. -->

## Deployment

<!-- Project-specific specialisation. -->

## Code Style

<!-- Project-specific specialisation. -->

- Ruff 설정은 `pyproject.toml`에 있다(target py311, line-length 100, 기본 규칙 + import 정렬 `I`). 코드를 쓴 뒤 `ruff format .`과 `ruff check --fix .`를 실행한다. CI의 `ruff (format + lint)` 검사가 통과해야 머지한다.
- `.claude/`, `aidlc/`는 AI-DLC 생성 파일이라 Ruff 검사 대상에서 뺀다.

## Tech Stack

<!-- Technology choices locked for this project. -->

- Python 3.11, Gradio(로컬 실행 `127.0.0.1`), Hugging Face `transformers`(CLIP)·`datasets`, OpenCV, scikit-learn, SciPy, NumPy, pandas, matplotlib, pytest. 버전은 `requirements.txt`에 고정한다.
- 데이터: WikiArt(`huggan/wikiart`, 비상업 연구용) 화가 24명 축소판, Kaggle `artists.csv`(CC BY-NC-SA 3.0). 원본 이미지는 커밋하지 않는다.

## Decided

<!-- Decisions made in earlier stages that should not be re-asked. -->
<!-- Format: DECIDED: [decision] (Stage [slug], [date]) -->

- DECIDED: 함수 이름·입출력 형식의 기준은 `contracts/interfaces.md`이며, 팀 합의(계약 변경 이슈) 후 별도 PR 없이는 바꾸지 않는다. Contract Design은 이 파일을 그대로 인용한다 (Stage pre-inception, 2026-11-19)
- DECIDED: Unit은 A 데이터·CLIP(`modules/data.py`), B 판정·융합(`modules/classify.py`), C 색·선(`modules/features.py`), D 신뢰도·UI·통합(`modules/explain.py`, `app.py`) 4개이며 서로 의존하지 않는다. 스텁으로 이미 분리되어 있다 (Stage pre-inception, 2026-11-19)
- DECIDED: 1일차 스텁(`TODO(#n)` 표시)은 의도된 것이다. 각 스텁은 그 이슈 담당자만 실제 구현으로 바꾼다 (Stage pre-inception, 2026-11-19)
- DECIDED: 요구사항·범위·일정·이슈는 `docs/plan.md`(1·6·7·8장)와 GitHub 이슈 #1~#30이 출처다. Ideation 산출물은 이것으로 갈음한다 (Stage pre-inception, 2026-11-19)
- DECIDED: 최종 순위는 `fuse()` 결과만 쓴다. 두 관점이 엇갈리면 숨기지 않고 함께 보여준다 (Stage pre-inception, 2026-11-19)

## Scope Overrides

<!-- Custom scope rules for this project. -->

## Forbidden

<!-- Populated by practices-discovery affirmation gate. -->
<!-- Format: - NEVER [behavior] (affirmed [date]) -->
<!-- Example: - NEVER throw exceptions across service layer boundaries (affirmed 2026-05-17) -->

- NEVER 자기 Unit 밖의 `modules/` 파일을 수정한다. 다른 모듈이 필요하면 이슈로 요청한다 (affirmed 2026-11-19)
- NEVER 테스트셋으로 온도 T·가중치 w·등급 경계값을 정한다. 프로필·분류기는 학습셋, 기준값은 검증셋으로만 정한다 (affirmed 2026-11-19)
- NEVER 사람의 질문 응답·단계 승인·hooks 신뢰를 AI가 대신 채우거나 승인된 것처럼 기록한다 (affirmed 2026-11-19)
- NEVER `main`에 직접 push하거나 `--force` push, 공유 기록 rebase, squash 머지를 한다 (affirmed 2026-11-19)
- NEVER 원본 이미지나 100MB 이상 파일을 커밋한다 (affirmed 2026-11-19)
- NEVER 명화에 화이트밸런스를 적용한다. 화이트밸런스는 사용자 입력에만 쓴다 (affirmed 2026-11-19)

## Mandated

<!-- Populated by practices-discovery affirmation gate. -->
<!-- Format: - ALWAYS [behavior] (affirmed [date]) -->
<!-- Example: - ALWAYS use Result<T,E> for fallible operations in service layer (affirmed 2026-05-17) -->

- ALWAYS 변경 후 `pytest`를 실행해 통과를 확인한다 (affirmed 2026-11-19)
- ALWAYS 명화와 사용자 입력에 같은 CLIP 모델 버전을 쓴다 (affirmed 2026-11-19)
- ALWAYS 이미지는 RGB `np.ndarray`(uint8), 긴 변 512px로 맞춘 뒤 처리한다. `cv2.imread()` 결과는 RGB로 바꾼다 (affirmed 2026-11-19)
- ALWAYS PR 설명에 AI의 핵심 판단 이유 3줄과 실제 실행한 검증 명령·결과를 적는다 (affirmed 2026-11-19)
- ALWAYS 커밋은 작게, 단계별로 나눈다 (affirmed 2026-11-19)

## Corrections

<!-- Project-specific corrections from human feedback. -->
<!-- Format: NEVER/ALWAYS [behavior] (learned [date]) -->
