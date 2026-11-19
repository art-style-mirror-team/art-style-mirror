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

**버전은 `.aidlc-version`(2.11.4)으로 고정한다.** `releases/latest`는 팀원마다 다른 버전이 깔릴 수 있으므로 쓰지 않는다. 버전을 올릴 때는 팀과 합의하고 이 파일과 아래 주소를 함께 바꾼다.

```powershell
# 1) CLI 설치 (Windows, 일반 PowerShell). 스크립트가 서명되어 있지 않아 이 셸에서만 실행 정책을 풀어 준다.
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
irm https://github.com/awslabs/aidlc-workflows/releases/download/v2.11.4/install.ps1 | iex
# 설치 후 열려 있던 터미널·VS Code·Claude 앱을 완전히 닫고 새로 연다 (PATH 반영)
aidlc version            # 2.11.4 확인

# 2) 저장소에 설정 (브랜치: feat/2-aidlc-inception). 먼저 dry-run으로 바뀔 파일을 본다.
cd art-style-mirror
aidlc config --harness claude --mcp none --dry-run
aidlc config --harness claude --mcp none     # --force는 쓰지 않는다
aidlc doctor --verbose
git diff                                       # 기존 파일이 덮이지 않았는지 확인
```

macOS/Linux: `curl -fsSL https://github.com/awslabs/aidlc-workflows/releases/download/v2.11.4/install.sh | sh`

`aidlc config`가 만드는 것과 처리 방법:

| 경로 | 처리 |
| --- | --- |
| `.claude/` (skill, agent, stage, hook, `settings.json`, `CLAUDE.md`) | 커밋 |
| `aidlc/` (기록, 팀 규칙 `aidlc/spaces/default/memory/`) | 커밋 |
| `aidlc.settings.json` (모델 preset) | 커밋 |
| `.gitignore`, `AGENTS.md` | AI-DLC가 자기 블록(`# BEGIN AI-DLC:gitignore` … `# END AI-DLC:gitignore`, `<!-- BEGIN AI-DLC:agents -->` … `<!-- END AI-DLC:agents -->`)만 덧붙인다. 블록 안은 손대지 않고, 기존 내용이 그대로인지 diff로 확인 |
| `.mcp.json` (MCP 서버) | `--mcp none`으로 만들지 않는다. AWS를 쓰지 않는다 |
| `aidlc.settings.local.json`, `.claude/settings.local.json` | 개인 파일, 커밋 금지 (자동으로 ignore) |

1일차 실제 실행 결과(2.11.4, `--harness claude --mcp none`): 새 파일 397개(`.claude/` 388개, `aidlc/` 9개), 기존 파일 변경은 `.gitignore`의 AI-DLC 블록 추가 하나뿐이었다. 루트 `CLAUDE.md`·`AGENTS.md`는 바뀌지 않았고, 프로젝트 버전 고정(pin 2.11.4)은 config가 자동으로 등록했다. `doctor`는 문제 0개, 경고 2개였다(hooks 미실행, `aidlc/` 미커밋 — 둘 다 정상).

**주의 — `.gitignore`가 AI-DLC 파일을 막지 않는지 확인한다.** 1일차에 `data/` 규칙(원본 이미지 폴더용)이 `.claude/tools/data/`까지 무시해서 AI-DLC 필수 파일 20여 개가 커밋되지 않을 뻔했다. 루트 전용 `/data/`로 고쳤다. config 후 아래 명령에 AI-DLC 블록의 개인 파일(`active-space`, `active-memory/`, `.aidlc-sessions/`)만 나와야 한다.

```bash
find .claude aidlc -type f | git check-ignore --verbose --stdin
```

config 후 **루트 `CLAUDE.md`(`@AGENTS.md` 한 줄)가 바뀌지 않았는지** 꼭 확인한다. Claude Code는 루트 `CLAUDE.md`와 `.claude/CLAUDE.md`를 둘 다 읽으므로 둘 다 있어도 된다. 생성된 `.claude/CLAUDE.md`와 `.claude/` 아래 파일은 손으로 고치지 않는다.

### 2.2 config 직후: 팀 규칙을 AI-DLC 메모리에 심기

AI-DLC 기본 규칙에는 우리 방식과 부딪히는 것이 두 가지 있다.

- `phases/construction.md`: "TODO 표시 없는 placeholder 스텁 금지". 그대로 두면 AI가 **남의 모듈 스텁까지 구현하려 할 수 있다.**
- `org.md` Way of Working: Construction 중 AI-DLC가 만든 Bolt 브랜치를 **main에 squash 머지**하는 것이 기본값이다. 우리는 squash를 금지하고 머지 커밋만 쓴다(plan.md 9.2).

그래서 config 직후 `aidlc/spaces/default/memory/project.md`에 프로젝트 규칙을 넣었다(1일차 반영 완료, 파일 참고). 핵심은 아래와 같다. `team.md`는 Practices Discovery 게이트에서만 고친다. `aidlc/active-memory/`는 자동으로 만들어지는 복사본이라 고치지 않는다.

```markdown
## Way of Working
- **Integration branch**: main
- main에는 PR + 리뷰 1명 승인 후 머지 커밋으로만 합친다. org 기본값의 squash·rebase 머지는 쓰지 않는다.
- Construction은 지금 체크아웃한 이슈 브랜치에서 진행한다. 별도 worktree·Bolt 브랜치를 만들지 않는다.
```

그 밖에 `Walking Skeleton`(1일차 스텁 + `pytest`), `Testing Posture`, `Tech Stack`, `Decided` 5개(계약 불변, Unit 4개 독립, 스텁은 담당자만, 요구사항 출처는 plan.md·이슈, 순위는 `fuse()`만), `Forbidden` 6개, `Mandated` 5개가 들어 있다. 규칙을 바꾸려면 이 파일을 고치는 PR을 올린다.

### 2.3 Inception 전에: 실제로 도는지 확인 (30분)

`config`나 `doctor`가 종료 코드 0으로 끝나도 **hooks 신뢰, 질문·응답 기록, 승인 게이트까지 동작한다는 뜻은 아니다.** 지난 프로젝트(sound-haptic)는 이 확인 없이 시작했다가, hooks 신뢰 요청에서 멈춰 공식 Inception이 첫 단계에 머물렀다.

1. Claude Code를 저장소 루트에서 열고, 프로젝트·hooks 신뢰를 묻는 창이 뜨면 `.claude/settings.json`의 hooks 내용을 읽고 허용한다. (신뢰는 PC마다 따로 저장된다. 다른 사람이 대신 할 수 없다.)
2. 시험용 intent로 짧게 돌려 본다: `/aidlc poc: README 오타 하나 찾기`
3. 질문에 직접 답하고 첫 승인 게이트가 뜨는지, `aidlc/spaces/default/intents/<id>/audit/`에 기록이 남는지 확인한다.
4. 확인되면 시험 intent는 커밋하지 않고 지운다. 제품 계획과 섞지 않는다.

### 2.4 나머지 팀원 (각자 PC)

설정 파일은 저장소에 이미 있으므로 CLI만 설치하면 된다. **`aidlc config`를 다시 돌리지 않는다**(공통 설정이 재생성된다).

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
irm https://github.com/awslabs/aidlc-workflows/releases/download/v2.11.4/install.ps1 | iex
# 터미널·IDE 재시작 후
cd art-style-mirror
git pull
aidlc version            # 2.11.4
aidlc doctor --verbose   # 통과해야 한다
```

그다음 Claude Code를 열어 hooks 신뢰를 직접 확인·허용한다(2.3의 1번).

그다음 Claude Code에서 "이 저장소의 규칙을 요약해 줘"라고 물어서 `AGENTS.md`의 규칙(자기 모듈만 수정, 계약 변경 금지 등)을 실제로 읽는지 확인한다. (plan.md 10.5 마지막 줄)

## 3. 1일차: Inception 1회 (D 진행, 전원 확인) — 이슈 #2

프로필은 **`classic`** 을 쓴다. "V1 방식으로 Inception과 Construction을 거쳐 Build and Test까지" 가는 프로필이라 plan.md 구조와 가장 가깝다.

**시간 제한: 1일차 반나절.** 넘기면 아래 "막혔을 때"로 간다.

```text
/aidlc classic: docs/plan.md를 요구사항으로 닮은 화가·화풍 분석기 MVP를 만든다.
- Ideation 산출물(의도·범위·타당성)은 docs/plan.md 1장·6장·7장으로 갈음한다. 요구사항은 그 절을 근거로 추적한다.
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

### 막혔을 때 (플랜 B)

hooks·권한·런타임 오류로 공식 단계가 진행되지 않거나 반나절을 넘기면:

1. **기준 계획은 `docs/plan.md` + GitHub 이슈 30개**로 한다. 이미 Unit·의존성·완료 기준이 다 들어 있으므로 개발은 바로 시작할 수 있다.
2. 진행된 데까지의 공식 기록만 커밋하고, `aidlc-state.md`에 실제 멈춘 단계가 그대로 보이게 둔다.
3. **AI-DLC 산출물(요구사항·Unit 계획·승인 기록)을 사람이나 AI가 손으로 흉내 내서 쓰지 않는다.** 공식 상태와 손으로 쓴 문서가 갈라지면 무엇이 진짜인지 설명하는 문서가 계속 늘어난다(지난 프로젝트의 교훈).
4. 원인과 멈춘 단계를 이슈 #2에 적고, Construction은 각자 `express` 프로필이나 일반 Claude Code로 진행한다. 규칙은 `AGENTS.md`로 똑같이 적용된다.

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

## 8. 확인된 것과 남은 것

지난 프로젝트(2026-10-makerthon/sound-haptic, AI-DLC 2.11.2, Codex + Claude Code)의 실제 저장소로 확인했다.

- [x] 루트 `CLAUDE.md`(`@AGENTS.md`)와 생성된 `.claude/CLAUDE.md`는 함께 쓸 수 있다
- [x] 블록 표시 문구: `# BEGIN AI-DLC:gitignore` / `# END AI-DLC:gitignore`, `<!-- BEGIN AI-DLC:agents -->` / `<!-- END AI-DLC:agents -->`
- [x] 다른 도구도 같은 저장소에서 쓸 수 있다. `.claude/`와 `.codex/`가 함께 커밋되어 있었고 `aidlc/` 기록을 같이 썼다. Codex를 쓰는 팀원이 있으면 D가 `aidlc config --harness codex --mcp none`을 추가로 돌려 PR로 올린다
- [ ] Contract Design 단계에 기존 계약 파일을 고정 입력으로 주는 공식 방법 (지난 프로젝트는 그 단계까지 가지 않았다. 지금은 시작 문장, `project.md`의 DECIDED, 승인 게이트로 막는다)

### 지난 프로젝트에서 가져오지 않은 것

| 지난 프로젝트 | 이번에 쓰지 않는 이유 |
| --- | --- |
| 팀 Unit claim + Windows용 래퍼 스크립트(`scripts/aidlc.ps1`, `team.py`) | 2.11.2에서 Windows 공개 명령이 빠져 직접 만들어야 했다. 우리는 claim을 쓰지 않으므로 필요 없다 |
| 이름으로 시작하기·PM 배정표 자동화 | 4명·2주에는 GitHub 이슈 assignee로 충분하다 |
| 23KB짜리 AGENTS.md | 길면 AI도 사람도 덜 지킨다. 핵심 규칙만 두고 세부는 이 문서와 plan.md로 보낸다 |

## 참고

- 시작하기: https://github.com/awslabs/aidlc-workflows/blob/main/docs/guide/01-getting-started.md
- 단계 설명: https://github.com/awslabs/aidlc-workflows/blob/main/docs/guide/04-phases-and-stages.md
- 워크플로 프로필: https://github.com/awslabs/aidlc-workflows/blob/main/docs/guide/workflow-profiles.md
- 산출물 경로: https://github.com/awslabs/aidlc-workflows/blob/main/docs/guide/14-artifacts-reference.md
- 설치·업데이트: https://github.com/awslabs/aidlc-workflows/blob/main/docs/guide/18-install-and-lifecycle.md
