# Practices Discovery 질문

초안(`team-practices.md`, `discovered-rules.md`)은 AGENTS.md, project.md, git 기록, CI 설정, 코드 분석 결과로 썼습니다. 아래는 근거만으로 정할 수 없어 팀이 정해야 하는 것입니다. 작업 방식(이슈 브랜치 → PR → 머지 커밋, 통합 브랜치 `main`)과 1일차 스텁을 walking skeleton으로 보는 것은 이미 project.md에 확정되어 있어 묻지 않습니다.

## Q1. [품질 담당] 테스트를 언제 쓰나요?

지금은 계약 형식 검사(`tests/test_smoke.py`)가 먼저 있고, 각 이슈의 동작 테스트는 구현한 뒤 붙이는 흐름입니다. 팀이 방식 이름을 정한 기록은 없습니다.

A. 구현 후 테스트 (test-after)
B. 계약 검사가 먼저 있고, 동작 테스트는 구현 후 (custom)
C. 테스트를 먼저 쓰고 구현 (TDD)
X. Other (please specify)

[Answer]: B

## Q2. [품질 담당] 코드 커버리지 하한을 둘까요?

AI-DLC 기본값은 MVP에 80% 라인 커버리지 하한을 붙입니다. 지금은 커버리지 도구가 없어서, 채택하면 `requirements.txt`와 CI를 바꾸는 D의 PR이 필요합니다.

A. 하한 없음. `pytest` 전체 통과만 조건으로 한다
B. 80% 하한을 채택한다 (D가 도구와 CI를 추가)
C. 낮은 하한(예: 50%)으로 시작한다
X. Other (please specify)

[Answer]: A

## Q3. [개발자] 포매터·린터를 도입할까요?

지금은 설정이 없습니다. 관찰된 관례는 snake_case, 대문자 상수, `from __future__ import annotations`, 타입 힌트, 한국어 docstring입니다.

A. 도구 없이 지금 관례만 유지한다
B. Ruff(린트+포맷)를 도입한다 (D의 PR)
C. Black + Ruff를 도입한다 (D의 PR)
X. Other (please specify)

[Answer]: B

## Q4. [릴리스 담당] 배포는 어떻게 하나요?

기본은 로컬 실행(`python app.py`, 127.0.0.1:7860)뿐이고, CI는 검사만 합니다. Hugging Face Spaces 배포(#29)는 선택 기능입니다. 롤백 초안은 머지 커밋을 `git revert -m 1`로 되돌리는 PR입니다.

A. 배포 없음. #29를 하면 수동으로 올린다. 롤백은 revert PR
B. #29를 하면 `main` 머지 때 자동 배포. 롤백은 revert PR
X. Other (please specify)

[Answer]: A

## Q5. [팀 전체] project.md와 겹치는 규칙은 어떻게 할까요?

`discovered-rules.md`에는 AGENTS.md에는 있지만 project.md의 강제 규칙(Mandated/Forbidden)에는 아직 없는 9개(Mandated 2, Forbidden 7)가 있습니다. 그중 2개(`contracts/interfaces.md` 계약 불변, 순위는 `fuse()` 결과만)는 project.md `## Decided`와 뜻이 같습니다. team.md의 다섯 섹션도 project.md와 내용이 일부 겹칩니다.

A. 9개 모두 강제 규칙으로 올리고, 겹침은 그대로 둔다
B. Decided와 겹치는 2개는 빼고 7개만 올린다. team.md에는 팀 공통 규칙만 짧게 둔다
C. 9개 모두 올리되, team.md에는 팀 공통 규칙만 짧게 둔다
X. Other (please specify)

[Answer]: X. project.md에 이미 있는 규칙(Way of Working, Walking Skeleton, Testing Posture, Decided, Forbidden, Mandated)은 그대로 두고 team.md에 중복하지 않는다. team.md에는 이번 단계에서 새로 정한 것만 올린다: 테스트 순서(계약 검사 먼저, 동작 테스트는 구현과 함께), 커버리지 하한 없음, Ruff 포매팅·린트(CI에서 실행), 자동 배포 없음(#29만 수동).
