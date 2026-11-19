# Evidence

리드: `aidlc-pipeline-deploy-agent`, 단독 작업. 깊이 Minimal, brownfield, 첫 실행. 이 단계에서 `pytest`·CI·앱은 실행하지 않았다.

## 살펴본 것

| 출처 | 확인한 내용 |
| --- | --- |
| `AGENTS.md`, `docs/plan.md` 9장, `docs/aidlc-guide.md` | 팀 규칙 원본, 머지 커밋만 사용, squash 금지 |
| `aidlc/spaces/default/memory/project.md` | 이미 확정된 Way of Working·Walking Skeleton·Testing Posture·Decided·Forbidden·Mandated |
| `.github/workflows/ci.yml` | `pytest -q`만 실행. 린트·커버리지·배포 단계 없음 |
| `requirements.txt` | 커버리지·린트 도구 없음 |
| `git log` | conventional 접두어, 작은 커밋, 머지 커밋. squash 흔적 없음 |
| `aidlc/spaces/default/codekb/art-style-mirror/code-structure.md` | `from __future__ import annotations`·타입 힌트·docstring 패턴 |
| `aidlc/spaces/default/codekb/art-style-mirror/technology-stack.md` | pytest, 커버리지 도구 없음, 배포 없음(HF Spaces는 선택 #29) |
| `aidlc/spaces/default/codekb/art-style-mirror/dependencies.md` | Unit 간 import 2개(B→A, C→A), 순환 없음 |
| `aidlc/spaces/default/codekb/art-style-mirror/code-quality-assessment.md` | 린터·포매터 설정 없음, 이름·docstring 관례 일관, 배포 파이프라인 없음 |
| `aidlc/spaces/default/codekb/art-style-mirror/architecture.md` | 배포 단위 1개(`python app.py`), 네트워크 경계·DB 없음 |
| `aidlc/spaces/default/codekb/art-style-mirror/business-overview.md` | MVP 범위, HF Spaces 배포는 stretch |

## 인터뷰 결정 (`practices-discovery-questions.md`)

- **Q1 B**: 테스트 방식은 `custom`. 계약 형식 검사가 먼저 있고, 동작 테스트는 구현과 함께 같은 PR에서 작성·실행한다.
- **Q2 A**: 커버리지 하한 없음. `pytest` 전체 통과만 조건이다(org 기본값 80% 하한을 쓰지 않는다).
- **Q3 B**: Ruff(포매팅+린트)를 도입하고 CI에서 실행한다.
- **Q4 A**: 자동 배포 없음. #29 HF Spaces는 하게 되면 수동. 롤백은 머지 커밋 revert PR(org 기본값 "merge 시 staging 배포"는 해당 없음).
- **Q5 X**: project.md에 이미 있는 규칙은 그대로 두고 team.md에 중복하지 않는다. team.md에는 이번에 새로 정한 것만 올린다. 그래서 `discovered-rules.md`는 `None.`이다.

## 후속 작업

- Ruff 도입(`requirements.txt`·설정 파일)과 CI 린트 단계 추가는 이 단계에서 하지 않았다. D의 후속 PR로 한다.
