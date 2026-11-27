# Reverse Engineering Timestamp

## Run Record

- Date: 2026-11-27
- Commit: f7107b399e1db543a13e93ccca3d440525e3aff2

집중 스캔(focused), 깊이 Minimal, intent `explain-sentences`(#22 해석 문장 템플릿), 브랜치 `feat/22-explain-sentences`. 기존 저장소 판정은 STALE이었다. 깊게 읽은 파일은 `modules/explain.py`, `app.py`, `contracts/interfaces.md`, `tests/test_explain.py`, `tests/test_smoke.py`, `tests/fakes.py`, `requirements.txt` 7개다. `modules/data.py`(`KEYWORDS`·`clip_keywords`)·`classify.py`·`features.py`(함수 목록·`TODO`·상수), `docs/plan.md`(#22 행), `docs/notes/D.md`는 훑어보기만 했다. 의존성 폴더(`.venv/`), 캐시(`__pycache__/`, `.pytest_cache/`, `.ruff_cache/`), AI-DLC 설치물(`.claude/`, `aidlc/`, `.aidlc-version`)은 열지 않았다. 프로젝트의 테스트·빌드·앱은 실행하지 않았다.

이전 실행: 2026-11-26, 커밋 `45ad17b677f1f652672b78a77ede58f516094030`, 집중 스캔(intent `gradio-glass-ui`, #37). 그 실행이 적어 둔 #37 전용 내용(`static/g.css`·`static/g.js`, G안 화면 계획, Gradio CSS·JS 확인 항목)은 이 브랜치에 해당 코드가 없어 문서에서 빼거나 "이 브랜치에 없음"으로 표시했다. 그 실행의 깊은 범위 6개 파일은 이번에 모두 다시 깊게 읽었으므로 `analyzed.paths`에 있고 `shallow.paths`에 중복해 적지 않았다. 그보다 앞선 2026-11-19 전체 스캔(커밋 `b481de72629367d78716a04480687bcbf4882ec5`, intent `mvp-inception`)의 범위(`./`)와 이전 훑어보기 범위는 `shallow.paths`로 둔다.

## Scope of Analysis

```yaml
scope_version: 1
kind: partial
intent: explain-sentences
fingerprint: 1dff798ab7ac3197172373c887fd4ffeef5810aa
analyzed:
  paths:
    - modules/explain.py
    - app.py
    - contracts/interfaces.md
    - tests/test_explain.py
    - tests/test_smoke.py
    - tests/fakes.py
    - requirements.txt
  components:
    - app
    - modules.explain
    - tests.fakes
    - tests.smoke
    - tests.explain
    - contracts
    - requirements
shallow:
  paths:
    - ./
    - docs/aidlc-guide.md
    - docs/plan.md
    - docs/notes/D.md
    - LICENSE
    - modules/data.py
    - modules/classify.py
    - modules/features.py
    - tests/conftest.py
    - tests/test_classify.py
    - tests/test_features.py
    - pyproject.toml
    - .github/
    - .gitignore
```
