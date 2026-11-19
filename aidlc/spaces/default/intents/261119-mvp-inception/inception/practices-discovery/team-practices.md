# Team Practices

> 이번 단계(practices-discovery 인터뷰)에서 새로 정한 것만 적는다. `project.md`에 이미 있는 규칙은 그대로 두고 여기에 중복하지 않는다(Q5). 근거는 `evidence.md`.

## Way of Working

- **Integration branch**: main
- 그 밖의 작업 방식은 project.md `## Way of Working`을 따른다.

## Walking Skeleton

- project.md `## Walking Skeleton`을 따른다.

## Testing Posture

- **Methodology**: custom
- **Methodology evidence**: 인터뷰 Q1에서 B(계약 검사가 먼저 있고, 동작 테스트는 구현과 함께)를 골랐다. 1일차부터 `tests/test_smoke.py`가 스텁과 함께 있었다.
- **Ordering**: 계약 형식 검사(`tests/test_smoke.py`)는 먼저 있고 그대로 통과해야 하며, 각 이슈의 동작 테스트는 구현과 함께 작성해 같은 PR에서 실행한다.
- 커버리지 하한 없음. pytest 전체 통과가 조건이다.

## Deployment

- 자동 배포는 없다. 로컬 실행(`python app.py`, `http://127.0.0.1:7860`)만 한다.
- Hugging Face Spaces 배포(#29)는 하게 되면 수동으로 올린다.
- 롤백은 머지 커밋을 `git revert -m 1 <merge>`로 되돌리는 새 PR로 한다.

## Code Style

- 포매팅과 린트는 Ruff로 하고 CI에서 실행한다.
- Ruff 설정과 CI 변경은 D의 PR로 도입한다. 도입 전까지는 지금 코드의 관례(snake_case, 대문자 상수, 타입 힌트, 한국어 docstring)를 따른다.
