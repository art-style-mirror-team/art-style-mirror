# Build and Test Summary — #8 `detect_type`

## 빌드 상태 / 전제조건

- 빌드(의존성 설치 + 수집/임포트 확인): **성공**. 새 의존성 없음.
- 전제: Python 3.11 venv + `requirements.txt`. 모델 다운로드 불필요(가짜 끼우기).

## 테스트 유형 인벤토리

- 단위(가짜 기반): `tests/test_classify.py`(신규 4개) + `tests/test_smoke.py`(계약 형식).
- 전략 **Minimal** → 통합·성능·보안 지침 파일은 생성하지 않음.
- 실제 모델 테스트 `@pytest.mark.model` 2개는 기본/CI에서 건너뜀(설계대로).

## 커버리지 기대

- 팀/프로젝트 규칙상 커버리지 **하한 없음**. 조건은 `pytest` 전체 통과.

## Target Verification Matrix

| Target ID | Source | Expected | Actual | Evidence | Owning Stage | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| NFR1 | requirements.md NFR1 | `pytest` 전체 통과(가짜만) | 34 passed, 2 skipped, exit 0 | `pytest -q` (test-results.md) | build-and-test | Met |
| NFR2 | requirements.md NFR2 | `test_smoke.py` 수정 없이 통과 | 15 passed, 2 skipped (test_smoke) | `pytest tests/test_smoke.py -q` | build-and-test | Met |
| NFR3 | requirements.md NFR3 | 유형·이미지 임베딩 같은 CLIP 모델 | `data.embed_text`/`embed_image` 동일 모델 경유 | 코드 검토 `modules/classify.py` | build-and-test | Met |
| NFR4 | requirements.md NFR4 | ruff format/check 통과 | 26 formatted, All checks passed | `ruff format --check .` / `ruff check .` | build-and-test | Met |
| CI-before-merge | org 기본값 | (express 비적용) | — | — | n/a | N/A |

`CI-before-merge`: express/Minimal은 CI 실행 하한이 없고, 이 계획에 `ci-pipeline` EXECUTE 단계가 없어 비적용(N/A).

## 준비도

- Build-ready: 예. Test-ready: 예. Deployment-ready: 로컬 실행 기준 예(이 프로젝트는 자동 배포 없음).

## 알려진 한계 / 미결

- 실제 CLIP 기준 유형 판별 정확도는 측정하지 않음(가짜 기반, Q3). 실제 모델 평가는 #26 범위.
- 유형 프롬프트 문구 최종화는 실제 모델 연결(#4·#5) 후 조정될 수 있음(OQ1).
