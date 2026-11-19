# Reverse Engineering Timestamp

## Run Record

- Date: 2026-11-19T18:14:36Z
- Commit: b481de72629367d78716a04480687bcbf4882ec5

전체 스캔(첫 스캔, NO_STORE), 깊이 Standard. 저장소 전체 `./`를 대상으로 했고, 의존성 폴더(`.venv/`), 캐시(`__pycache__/`, `.pytest_cache/`), AI-DLC 설치물(`.claude/`, `aidlc/`, `.aidlc-version`, `.gitignore`의 AI-DLC 구역)은 열지 않았다. `docs/aidlc-guide.md`와 `LICENSE`는 훑어보기만 했다. 프로젝트의 테스트·빌드·앱은 실행하지 않았다.

## Scope of Analysis

```yaml
scope_version: 1
kind: full
intent: mvp-inception
fingerprint: 1cfe2424ffdd7857e85820cda7207ec630c840ff
analyzed:
  paths:
    - ./
  components:
    - app
    - modules.data
    - modules.classify
    - modules.features
    - modules.explain
    - scripts.build_index
    - scripts.build_profiles
    - notebooks.eval
    - tests
    - contracts
    - ci
shallow:
  paths:
    - docs/aidlc-guide.md
    - LICENSE
```
