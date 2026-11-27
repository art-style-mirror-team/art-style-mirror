# Reverse Engineering Timestamp

## Run Record

- Date: 2026-11-28
- Commit: cd3a97f579df81ffc790bef6a3cced20102a0910

## Scope of Analysis

```yaml
scope_version: 1
kind: partial
intent: linear-logreg
fingerprint: 80c4bee21a677a14e0617908b1cc10227783346f
analyzed:
  paths:
    - modules/classify.py
    - tests/test_classify.py
  components:
    - modules.classify
    - tests.classify
shallow:
  paths:
    - ./
    - app.py
    - contracts/interfaces.md
    - docs/aidlc-guide.md
    - docs/plan.md
    - docs/notes/D.md
    - LICENSE
    - modules/data.py
    - modules/explain.py
    - modules/features.py
    - pyproject.toml
    - requirements.txt
    - tests/conftest.py
    - tests/test_explain.py
    - tests/test_features.py
    - tests/test_smoke.py
    - .github/
    - .gitignore
```
