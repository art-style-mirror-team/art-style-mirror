# AI-DLC 사용 가이드 (art-style-mirror)

> 기준: AI-DLC v2.11.4 (2026-11-13 릴리스), [awslabs/aidlc-workflows](https://github.com/awslabs/aidlc-workflows)
> 대상: 팀원 4명. 이 프로젝트에서 AI-DLC를 **언제, 어떤 명령으로, 어디까지** 쓰는지 정리한다.
> 규칙의 기준은 `AGENTS.md`, 함수 형식의 기준은 `contracts/interfaces.md`다. 이 문서와 다르면 그 파일들을 따른다.

## 1. AI-DLC가 하는 일

AI-DLC(AI-Driven Development Life Cycle)는 AI 코딩 도구가 요구사항 → 설계 → 코드 → 테스트를 **단계별로** 밟게 하고, **단계마다 사람의 승인**을 받게 하는 워크플로다. 승인 화면에서 "Approve" 또는 "Request Changes"를 고른다.

우리가 쓰는 이유는 두 가지다.

1. 네 명의 AI가 같은 규칙과 같은 계약(`contracts/interfaces.md`)을 따르게 해서 통합 때 모듈이 깨지지 않게 한다.
2. AI가 왜 그렇게 만들었는지 기록(`audit/`)이 남아, PR의 "AI 판단 이유 3줄"을 근거 있게 쓸 수 있다.

### V1과 달라진 점 (plan.md 초안은 V1 기준이었다)

| | V1 (예전) | v2.11.4 (지금) |
| --- | --- | --- |
| 설치 | 규칙 파일 복사 | `aidlc` CLI 설치 후 `aidlc config` |
| 기록 위치 | `aidlc-docs/` | `aidlc/spaces/default/intents/<id>/` |
| Claude Code 규칙 | 루트 `CLAUDE.md` | `.claude/CLAUDE.md` + `.claude/` 아래 skill·agent·hook |
| 단계 | Inception / Construction / Operations | Initialization · Ideation · Inception · Construction · Operation 5단계 + 워크플로 프로필 |
| 시작 | 자유 문장 | `/aidlc <프로필>: <할 일>` |

## 2. 설치

### 2.1 D가 1일차에 한 번 (저장소 설정)

```powershell
# 1) CLI 설치 (Windows). 스크립트가 서명되어 있지 않아 이 셸에서만 실행 정책을 풀어 준다.
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
irm https://github.com/awslabs/aidlc-workflows/releases/latest/download/install.ps1 | iex
# 설치 후 터미널·VS Code를 새로 연다 (PATH 반영)

# 2) 저장소에 설정 (브랜치: feat/2-aidlc-inception)
cd art-style-mirror
aidlc config --harness claude
aidlc doctor
```

macOS/Linux: `curl -fsSL https://github.com/awslabs/aidlc-workflows/releases/latest/download/install.sh | sh`

`aidlc config`가 만드는 것과 처리 방법:

| 경로 | 처리 |
| --- | --- |
| `.claude/` (skill, agent, stage, hook, `settings.json`, `CLAUDE.md`) | 커밋 |
| `aidlc/` (기록, 팀 규칙 `aidlc/spaces/default/memory/`) | 커밋 |
| `aidlc.settings.json` (모델 preset) | 커밋 |
| `.gitignore`, `AGENTS.md` | AI-DLC가 자기 블록만 덧붙인다. 기존 내용이 그대로인지 diff로 확인 |
| `.mcp.json` (MCP 서버 5종, AWS용 포함) | 이 프로젝트에는 필요 없다. 끄거나 커밋하지 않는다 |
| `aidlc.settings.local.json`, `.claude/settings.local.json` | 개인 파일, 커밋 금지 (자동으로 ignore) |

config 후 **루트 `CLAUDE.md`(`@AGENTS.md` 한 줄)가 바뀌지 않았는지** 꼭 확인한다. Claude Code는 루트 `CLAUDE.md`와 `.claude/CLAUDE.md`를 둘 다 읽으므로 둘 다 있어도 된다.

### 2.2 나머지 팀원 (각자 PC)

설정 파일은 저장소에 이미 있으므로 CLI만 설치하면 된다.

```powershell
irm https://github.com/awslabs/aidlc-workflows/releases/latest/download/install.ps1 | iex
cd art-style-mirror
git pull
aidlc doctor          # 통과해야 한다
```

그다음 Claude Code에서 "이 저장소의 규칙을 요약해 줘"라고 물어서 `AGENTS.md`의 규칙(자기 모듈만 수정, 계약 변경 금지 등)을 실제로 읽는지 확인한다. (plan.md 10.5 마지막 줄)

## 3. 1일차: Inception 1회 (D 진행, 전원 확인) — 이슈 #2

프로필은 **`classic`** 을 쓴다. "V1 방식으로 Inception과 Construction을 거쳐 Build and Test까지" 가는 프로필이라 plan.md 구조와 가장 가깝다.

```text
/aidlc classic: docs/plan.md를 요구사항으로 닮은 화가·화풍 분석기 MVP를 만든다.
- contracts/interfaces.md는 변경 불가 계약이다. 계약 설계 단계에서는 이 파일을 그대로 인용하고 고치지 않는다.
- 작업 단위(Unit)는 A 데이터·CLIP, B 판정·융합, C 색·선, D 신뢰도·UI·통합 4개로 고정한다.
  네 Unit은 서로 의존하지 않는다(1일차 스텁으로 이미 분리되어 있다).
- 기존 코드는 1일차 스텁이고 app.py가 끝까지 돈다. 이것을 walking skeleton으로 본다.
- 검증 명령은 `.venv\Scripts\python -m pytest` 이다.
- 규칙은 AGENTS.md를 따른다.
```

단계별로 확인할 것:

| 단계 | 확인할 것 |
| --- | --- |
| Reverse Engineering | 저장소에 코드가 있으므로 자동으로 돈다. 스텁 구조가 맞게 정리됐는지만 본다 |
| Practices Discovery | `AGENTS.md`의 핵심 규칙(계약 불변, 데이터 분할, 같은 CLIP 버전, `fuse()`만 순위 결정)이 `aidlc/spaces/default/memory/project.md`·`team.md`에 들어갔는지 |
| Requirements / User Stories | plan.md 1.1 MVP 범위를 벗어난 기능이 끼어들지 않았는지. 선택 기능은 `stretch`로 남긴다 |
| Units Generation | Unit이 정확히 A·B·C·D 4개인지, **의존 관계(DAG)가 서로 독립**인지. D가 A·B·C에 의존하게 만들면 D가 7일차까지 시작을 못 한다 |
| Contract Design | 만들어진 계약서가 `contracts/interfaces.md`와 **함수 이름·입출력이 같은지**. 다르면 Request Changes |
| Build and Test | 검증 명령이 `pytest`로 등록됐는지, 통과하는지 |

결과물(`.claude/`, `aidlc/`, `aidlc.settings.json`)은 **PR 하나로 한 번만** 올리고, 이후 Inception 산출물은 고치지 않는다.

## 4. 2~10일차: 이슈별 Construction

**이슈 하나 = 브랜치 하나 = intent 하나 = PR 하나.** 각자 자기 이슈 브랜치에서 AI-DLC를 시작하고, 각 단계 승인은 **담당자 본인**이 한다.

### 4.1 프로필 고르기

| 이슈 유형 | 프로필 | 이슈 |
| --- | --- | --- |
| 함수 하나·작은 기능 | `express` (가장 가벼운 요구사항 → 코드 → 테스트) | #3–#8, #13, #16–#19, #21–#23, #27 |
| 실험·비교가 많은 작업 | `classic` | #9–#12 판정 비교, #14–#15 보정·합치기, #20 피셔 점수, #24 등급 경계값, #26 최종 평가 |
| 버그 수정 | `bugfix` (수정 + 회귀 테스트) | `fix/...` 브랜치 |
| 배포 | `infra` | #29 Hugging Face Spaces |
| 통합 | `classic` | #25 |

애매하면 `/aidlc <할 일>`만 쓰면 AI가 프로필을 제안하고, 확인 후 진행한다.

### 4.2 시작 예시

```text
# A — 이슈 #5
/aidlc express: #5 embed_image()·embed_text() 구현. contracts/interfaces.md는 변경 불가.
modules/data.py만 수정한다. 같은 이미지 두 번 넣으면 유사도 0.99 이상이어야 한다.

# B — 이슈 #12
/aidlc classic: #12 kNN·중심점·로지스틱 회귀 판정을 검증셋으로 비교해 predict_clip()의 최종 방식을 정한다.
contracts/interfaces.md는 변경 불가. 테스트셋은 쓰지 않는다. 결과는 notebooks/eval.ipynb에 비교표로 남긴다.

# C — 이슈 #17
/aidlc express: #17 색 특징 6종을 extract_features()에 구현한다. contracts/interfaces.md는 변경 불가.
modules/features.py만 수정. cv2.imread()는 BGR이므로 RGB로 바꾼다.

# D — 이슈 #21
/aidlc express: #21 compare()로 1위 이유·2위 쪽 특징을 대조한다. contracts/interfaces.md는 변경 불가.
modules/explain.py만 수정. 다른 모듈은 스텁을 그대로 쓴다.
```

### 4.3 PR 올릴 때

- PR 본문의 **AI 판단 이유 3줄**은 해당 intent의 `audit/` 기록에서 핵심만 골라 쓴다. 본인이 설명할 수 있어야 머지한다.
- PR 본문에 intent 경로(`aidlc/spaces/default/intents/<id>/`)를 적는다.
- intent 기록 폴더는 코드와 같은 PR로 커밋한다. 파일 수 제한(1~3개)은 **코드 파일 기준**으로 센다.
- `pytest`가 통과해야 한다. AI-DLC의 Build and Test 단계에서 통과했어도 PR 전에 한 번 더 돌린다.

## 5. 쓰지 않는 기능

| 기능 | 쓰지 않는 이유 |
| --- | --- |
| 팀 Unit claim (`/aidlc --claim <unit>`, `unit share/publish/land`) | 공용 통합 브랜치에 직접 push하는 방식이라 "main 보호 + PR 1명 승인" 규칙과 맞지 않는다. 2주 프로젝트에는 운영 부담이 크다 |
| Operation 단계 (배포 파이프라인, 모니터링 등) | MVP 범위 밖이다. #29 배포만 `infra` 프로필로 한다 |
| `feature`·`enterprise`·`mvp` 프로필 | 20~30단계로 2주 일정에 무겁다 |
| AWS MCP 서버 | AWS를 쓰지 않는다 |

## 6. 충돌 예방

- intent마다 기록 폴더가 따로 생기고 `audit/`도 PC별 파일로 나뉘어서, 네 명이 동시에 써도 충돌이 거의 없다.
- 개인 커서 파일(`aidlc/active-space`, `intents/active-intent`, `aidlc/.aidlc-clone-id`, `aidlc/.aidlc-sessions/` 등)은 AI-DLC의 `.gitignore` 블록이 막는다. `git status`에 보이면 커밋하지 말고 D에게 알린다.
- 남의 intent 폴더는 고치지 않는다. 남의 모듈 파일처럼 이슈로 요청한다.
- 팀 규칙 파일(`aidlc/spaces/default/memory/team.md`, `project.md`)을 바꿔야 하면 별도 PR로 한다.

## 7. 비용과 시간

- 실행되는 단계마다 승인이 필요하다. `express`는 짧지만 `classic`은 승인이 15번 안팎이라 시간을 잡아 둔다.
- 토큰을 많이 쓴다. 기본 preset은 `balanced`이고 공식 권장 모델은 Claude Opus 4.8이다. 각자 요금제 한도를 확인하고, 한도가 빠듯하면 작은 이슈는 AI-DLC 없이 Claude Code로 바로 작업해도 된다(규칙은 `AGENTS.md`로 똑같이 적용된다).
- AI가 만든 수치·결과는 직접 실행해서 확인한다. (AGENTS.md 규칙 5)

## 8. 아직 확인하지 못한 것

공식 문서에서 명확히 확인하지 못한 부분이다. Inception PR에서 직접 확인하고 이 문서를 고친다.

- [ ] `aidlc config`가 루트 `CLAUDE.md`를 건드리는지
- [ ] `AGENTS.md`·`.gitignore`에 붙는 블록의 정확한 표시 문구
- [ ] 팀원마다 다른 도구(Cursor, Codex 등)를 쓸 때 `aidlc config --harness <도구>`를 추가로 돌려도 Claude 설정과 함께 쓸 수 있는지
- [ ] Contract Design 단계에 기존 계약 파일을 고정 입력으로 주는 공식 방법이 있는지 (지금은 시작 문장과 승인 게이트로 막는다)

## 참고

- 시작하기: https://github.com/awslabs/aidlc-workflows/blob/main/docs/guide/01-getting-started.md
- 단계 설명: https://github.com/awslabs/aidlc-workflows/blob/main/docs/guide/04-phases-and-stages.md
- 워크플로 프로필: https://github.com/awslabs/aidlc-workflows/blob/main/docs/guide/workflow-profiles.md
- 산출물 경로: https://github.com/awslabs/aidlc-workflows/blob/main/docs/guide/14-artifacts-reference.md
- 설치·업데이트: https://github.com/awslabs/aidlc-workflows/blob/main/docs/guide/18-install-and-lifecycle.md
