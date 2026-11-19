# Code Quality Assessment

이 평가는 파일을 읽어서 한 것이다. 이 스캔에서 `pytest`·CI·앱을 실행하지 않았으므로 통과 여부나 수치는 적지 않는다.

## 테스트

| 항목 | 상태 |
| --- | --- |
| 프레임워크 | pytest 9.2.0, `tests/conftest.py`가 루트를 `sys.path`에 추가 |
| 범위 | 16개 테스트 함수(18개 실행 케이스). 16개 계약 함수 전부 + `app.analyze`·`run`·`build_demo` 호출 |
| 성격 | 형식(계약) 검사가 중심: shape·L2 노름·키 집합·확률 합 1·내림차순·`split` 값. 동작 검사는 D 쪽(`assess_confidence` 높음/낮음, `compare` 가짜 프로필), `similar_works` 자기 자신 제외, `preprocess_input` 512px·흑백 판정 |
| 엣지 케이스 | 스케치(흑백 3채널) 입력, `gray=True` 경로, 데이터셋 밖 입력(`max_sim=0.2` → 낮음), 상세 JSON `path` 제거 |
| 커버리지 | 측정 도구·설정 없음 |
| 규칙 | `tests/test_smoke.py`는 실제 구현으로 바꿔도 그대로 통과해야 하며, 통과시키려고 약하게 고치지 않는다(project.md) |

빈틈: 정확도·보정 품질 테스트는 없다(평가는 `eval.ipynb` 몫). `embed_image` 결정성(`>= 0.99`)은 #5 완료 기준을 그대로 검사한다. 잘못된 입력(`ValueError`) 경로를 검사하는 테스트는 없다.

## 린트·스타일

- 린터·포매터 설정 없음(`pyproject.toml`, `ruff.toml`, `.flake8` 없음). CI에 린트 단계 없음
- 코드 자체는 일관됨: snake_case, 상수 대문자, 타입 힌트, 한국어 docstring

## CI/CD

- `.github/workflows/ci.yml`: PR, `main` push, 수동 실행 → Ubuntu, Python 3.11, CPU torch 선설치, `pip install -r requirements.txt`, `pytest -q`
- 최소 권한(`contents: read`), 같은 ref 동시 실행 취소, 20분 제한
- 배포 파이프라인 없음(MVP는 로컬 실행). 브랜치 보호의 status check 요구는 plan.md 9.3에 따라 나중에 켬

## 문서

| 문서 | 평가 |
| --- | --- |
| `README.md` | 실행법(Windows/macOS/Linux), 데이터 출처·비상업 조건, 팀 표. "1일차 뼈대, 결과는 가짜 값" 명시. 정확도표·스크린샷은 #30 예정 |
| `docs/plan.md` | 요구사항·식·일정·이슈·Git 규칙이 상세함 |
| `contracts/interfaces.md` | 함수·`result` 키·해석 확인 사항이 명확함 |
| docstring | 모든 공개 함수에 반환 형식과 스텁 여부 |
| PR·이슈 템플릿 | 검증 결과·AI 판단 이유·체크리스트, 계약 변경 절차 |

## 빠른 평가 (good / fair / poor)

| 항목 | 등급 | 근거 |
| --- | --- | --- |
| 이름 명확성 | good | 함수·상수 이름이 계약·plan.md 용어와 같음 |
| 함수 크기 | good | 대부분 30줄 이하. `app.analyze`(약 45줄), `render_card`(약 44줄)는 순차 조립이라 수용 가능 |
| 오류 처리 | fair | 이미지 형식 `ValueError`, 빈 입력 `gr.Error`. 파일 I/O(`calibration.json` JSON 오류)·이름 불일치(`KeyError`) 처리 없음, 로깅 없음 |
| 테스트 존재 | good | 모든 계약 함수와 전체 경로가 테스트됨(형식 수준) |
| 중복 | good | `_seed` 중복(data·features)은 모듈 독립을 위한 의도적 중복 |

## 기술 부채·주의 신호

### 의도된 1일차 스텁 (`TODO(#n)`)

| 위치 | 이슈 | 현재 동작 |
| --- | --- | --- |
| `data.embed_image`, `data.embed_text` | #5 | 입력 해시 기반 가짜 벡터 |
| `data.load_index` | #3, #4 | 24명 × 20점 가짜 색인 |
| `data.clip_keywords` | #7 | 15개 키워드 중 무작위 |
| `classify.detect_type` | #8 | `emb[:3]` argmax |
| `classify.predict_clip` | #9–#12, #14 | 가짜 색인 학습셋 중심점 softmax |
| `classify.similar_works` | #13 | 가짜 색인 검색 |
| `classify.fuse` | #15 | 가중합만 |
| `features.preprocess_input` | #16 | 리사이즈만(종이 자르기·화이트밸런스 없음) |
| `features.extract_features` | #17, #18 | 가짜 값 |
| `features.load_profiles` | #19 | 가짜 프로필 |
| `features.predict_cv` | #20, #14 | 식은 실제, `T = 1.0`, 피셔 점수 거르기 없음 |
| `scripts/build_index.py`, `scripts/build_profiles.py` | #4, #19 | `NotImplementedError` |
| `explain.py` 등급 경계값 6개 | #24 | 임시값 |

이것들은 결함이 아니라 계획된 상태다(project.md DECIDED). 각 스텁은 그 이슈 담당자만 바꾼다.

### 설계 수준 주의점

1. **Unit 간 import**: B→A(`load_index`), C→A(`ARTISTS`). 상세는 `dependencies.md`.
2. **`T_cv` 소유 불일치**: `calibration.json`(B)에 `T_cv`가 있으나 `predict_cv`(C)는 `T = 1.0` 하드코딩(`features.py:105`).
3. **화가 이름 암묵 계약**: `app.py:57` `profiles[top1]` — `fuse()` 결과 이름이 `load_profiles()` 키에 없으면 `KeyError`.
4. **float 입력 캐스팅**: `features.py:44`는 범위 확인 없이 `astype(np.uint8)`. Gradio 경로(uint8)에서는 영향 없음.
5. **`calibration.json` 파싱 오류 미처리**: `classify.load_calibration`은 JSON 오류를 그대로 올린다(조용한 실패는 아님).
6. **CLIP 모델 버전 미고정**: 코드에 모델 ID가 아직 없음 — #4·#5에서 하나로 고정해야 "같은 CLIP 모델 버전" 규칙을 지킬 수 있음.
7. **문서 차이**: plan.md 5장·10.1의 `aidlc.settings.json`이 저장소에 없음, plan.md 트리에 `.github/workflows/ci.yml` 누락.

### 보안·규정

- 로컬 바인딩(`127.0.0.1`), 인증 없음(로컬 단일 사용자 MVP), 비밀값·환경변수 사용 없음
- 데이터 라이선스(비상업)는 README에 명시됨
- 원본 이미지·대용량 파일 커밋 금지는 `.gitignore`(`/data/`, `*.pt`)와 PR 체크리스트로 관리
