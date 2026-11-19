# Component Inventory

각 컴포넌트의 함수 계약은 `api-documentation.md`, import 관계는 `dependencies.md`, 스텁 목록은 `code-quality-assessment.md`에 있다. 여기서는 책임·소유·상태만 적는다.

## Components

### app
- **파일**: `app.py`
- **Unit / 담당**: D (김현승)
- **책임**: Gradio 화면 구성(`build_demo`), 버튼 처리(`run`), 파이프라인 조립(`analyze`)으로 `result` dict 생성, 상세 JSON에서 `path` 키 제거
- **의존**: `modules.features`, `modules.data`, `modules.classify`, `modules.explain`, `gradio`, `numpy`
- **상태**: 구현됨(walking skeleton의 통합 지점). 엇갈림 사례 자동 저장(#25)은 아직 없음

### modules.data
- **파일**: `modules/data.py`
- **Unit / 담당**: A (홍승민)
- **책임**: CLIP 이미지·문장 임베딩, 명화 색인(임베딩+메타) 로드, CLIP 키워드 설명, 화가·화풍 목록(`ARTIST_STYLE`, `ARTISTS`, `STYLES`, `GENRES`) 제공
- **의존**: `numpy`, `pandas`, `hashlib`, `functools`
- **상태**: 스텁(#3, #5, #7). 화가 24명 목록은 스텁용이며 #3에서 확정

### modules.classify
- **파일**: `modules/classify.py`
- **Unit / 담당**: B (홍예원)
- **책임**: 입력 유형 판별, CLIP 관점 화가·화풍 확률(온도 보정), 비슷한 명화 검색, 두 관점 합치기(`fuse`), `calibration.json` 로드
- **의존**: `modules.data.load_index`, `numpy`, `json`, `pathlib`
- **상태**: 스텁(#8, #9–#13, #15). `fuse`는 가중합만

### modules.features
- **파일**: `modules/features.py`
- **Unit / 담당**: C (심현준)
- **책임**: 사용자 입력 전처리(종이 자르기·화이트밸런스·512px), 흑백 판정, 색 6종·선 5종 특징, 화가 프로필, OpenCV 관점 확률
- **의존**: `modules.data.ARTISTS`, `cv2`, `numpy`
- **상태**: 부분 스텁. `is_grayscale`·리사이즈·`predict_cv` 식은 실제, 나머지는 스텁(#16–#20)

### modules.explain
- **파일**: `modules/explain.py`
- **Unit / 담당**: D (김현승)
- **책임**: 결과 신뢰 등급(1·2위 차이, 정규화 엔트로피, JSD, 데이터셋 유사도), 1·2위 대조, 해석 문장, 레이더 차트, 면책 문구
- **의존**: `numpy`, `scipy.spatial.distance`, `matplotlib` (다른 `modules` import 없음)
- **상태**: 구현됨. 등급 경계값만 임시(#24). 해석 문장 템플릿 고도화(#22)·차트(#23) 이슈 열려 있음

### scripts.build_index
- **파일**: `scripts/build_index.py`
- **Unit / 담당**: A (홍승민)
- **책임**: WikiArt 축소판의 CLIP 임베딩 사전 계산 → `artifacts/embeddings.npy`, `meta.csv`
- **의존**: 없음(아직 import 없음)
- **상태**: 미구현 — `NotImplementedError("#4에서 구현 예정")`

### scripts.build_profiles
- **파일**: `scripts/build_profiles.py`
- **Unit / 담당**: C (심현준)
- **책임**: 학습셋(`split == "train"`)만으로 화가 프로필 계산 → `artifacts/profiles.json`. 명화에 화이트밸런스 금지
- **의존**: 없음(아직 import 없음)
- **상태**: 미구현 — `NotImplementedError("#19에서 구현 예정")`

### notebooks.eval
- **파일**: `notebooks/eval.ipynb`
- **Unit / 담당**: B (홍예원)
- **책임**: 판정 3종 비교(#12), 온도 보정(#14), 합치기 3종 비교(#15) — 검증셋. 최종 평가(#26) — 테스트셋 한 번
- **의존**: 없음(코드 셀 없음)
- **상태**: 계획 마크다운 셀 1개뿐

### tests
- **파일**: `tests/conftest.py`, `tests/test_smoke.py`
- **Unit / 담당**: 공용 (형식 검사, 1일차 D 작성)
- **책임**: 16개 계약 함수의 반환 형식과 전체 파이프라인(컬러·스케치), Gradio 빌드, 상세 JSON의 `path` 제거 검사. 실제 구현으로 바꿔도 그대로 통과해야 함
- **의존**: `app`, `modules.*`, `pytest`, `numpy`, `pandas`, `matplotlib`
- **상태**: 16개 테스트 함수(18개 실행 케이스)

### contracts
- **파일**: `contracts/interfaces.md`, `.github/ISSUE_TEMPLATE/contract-change.yml`
- **Unit / 담당**: 공용 (팀 합의로만 변경)
- **책임**: 함수 이름·인자·반환 형식, `result` dict 키, 1일차 해석 확인 사항 3개의 최종 기준. 변경 절차(이슈 템플릿)
- **의존**: 없음
- **상태**: 1일차(2026-11-19) 확정

### ci
- **파일**: `.github/workflows/ci.yml`, `.github/pull_request_template.md`
- **Unit / 담당**: D (저장소 관리)
- **책임**: PR·`main` push마다 Ubuntu/Python 3.11에서 `pytest -q`. PR 본문 형식(검증 결과, AI 판단 이유 3줄, 체크리스트)
- **의존**: `requirements.txt`, CPU torch 인덱스
- **상태**: 동작 설정 있음(실행 결과는 이 스캔에서 확인하지 않음)
