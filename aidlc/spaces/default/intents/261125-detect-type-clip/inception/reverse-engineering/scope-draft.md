# Reverse Engineering Timestamp

## Run Record

- Date: 2026-11-25
- Commit: c44fee456e97b7b9ae6038d99b2bb3509bfa8161

집중 재스캔(intent `detect-type-clip`). `modules/`, `contracts/`, `tests/`만 깊이 분석.

## Scope of Analysis

```yaml
scope_version: 1
kind: partial
intent: detect-type-clip
fingerprint: 41202ddcbdde0adc99fb74b421a0c93732a69041
analyzed:
  paths:
    - modules/
    - contracts/
    - tests/
  components:
    - modules.data
    - modules.classify
    - modules.features
    - modules.explain
    - tests
    - contracts
shallow:
  paths:
    - ./
    - app.py
    - scripts/
    - notebooks/
    - docs/
    - LICENSE
```
