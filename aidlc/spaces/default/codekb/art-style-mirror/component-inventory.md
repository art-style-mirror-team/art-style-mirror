# Component Inventory

각 컴포넌트의 함수 계약은 `api-documentation.md`, import 관계는 `dependencies.md`, 스텁 목록은 `code-quality-assessment.md`에 있다. 여기서는 책임·소유·상태만 적는다. `app`, `modules.explain`, `tests.smoke`, `tests.explain`, `tests.fakes`, `contracts`, `requirements`는 2026-11-27 집중 스캔(#22)으로 다시 확인했고, 나머지는 2026-11-19 전체 스캔과 이후 훑어보기 기준이다.

## Components

### app
- **파일**: `app.py`
- **Unit / 담당**: D (김현승)
- **책임**: Gradio 화면 구성(`build_demo`), 버튼 처리(`run`), 파이프라인 조립(`analyze`)으로 `result` dict(12개 키) 생성, 스케치일 때 대조용 특징을 선 특징으로 줄임, 상세 JSON에서 `path` 키 제거, 모듈 변수 `demo`
- **의존**: `modules.features`, `modules.data`, `modules.classify`, `modules.explain`, `gradio`, `numpy`
- **상태**: 구현됨(walking skeleton의 통합 지점). 화면은 기본 2열 한 장. #37 G안 화면 코드는 이 브랜치에 없음. 엇갈림 사례 자동 저장(#25)은 아직 없음. #22에서는 바꾸지 않음

### modules.data
- **파일**: `modules/data.py`
- **Unit / 담당**: A (홍승민)
- **책임**: CLIP 이미지·문장 임베딩, 명화 색인(임베딩+메타) 로드, CLIP 키워드 설명(`KEYWORDS` 15개 한국어 명사구), 화가·화풍 목록(`ARTIST_STYLE`, `ARTISTS`, `STYLES`, `GENRES`) 제공
- **의존**: `numpy`, `pandas`, `hashlib`, `functools`
- **상태**: 스텁(#3, #5, #7). 화가 24명 목록은 스텁용이며 #3에서 확정

### modules.classify
- **파일**: `modules/classify.py`
- **Unit / 담당**: B (홍예원)
- **책임**: 입력 유형 판별, CLIP 관점 화가·화풍 확률(온도 보정), 비슷한 명화 검색, 두 관점 합치기(`fuse`), `calibration.json` 로드
- **의존**: `modules.data.load_index`, `numpy`, `json`, `pathlib`
- **상태**: 스텁(#8, #9–#12, #15). `similar_works`는 #13에서 정리됨. `fuse`는 가중합만. `detect_type` 실제 구현은 PR #56 대기

### modules.features
- **파일**: `modules/features.py`
- **Unit / 담당**: C (심현준)
- **책임**: 사용자 입력 전처리(종이 자르기·화이트밸런스·512px), 흑백 판정, 색 6종·선 5종 특징, 화가 프로필, OpenCV 관점 확률
- **의존**: `modules.data.ARTISTS`, `cv2`, `numpy`, `sklearn.cluster`(팔레트)
- **상태**: 부분 스텁(#16–#20). `direction`은 PR #44 머지로 0~1 방향 일관성(`docs/notes/D.md`)

### modules.explain
- **파일**: `modules/explain.py`
- **Unit / 담당**: D (김현승)
- **책임**: 결과 신뢰 등급(1·2위 차이, 정규화 엔트로피, JSD, 데이터셋 유사도), 1·2위 대조, 해석 문장(`render_card`), 레이더 차트, 화면 한국어 문구 상수(`FEATURE_KO`, `TYPE_INTRO`, `LEVEL_NOTE`, `DISCLAIMER`)
- **의존**: `numpy`, `scipy.spatial.distance`, `matplotlib`(`Figure`, `font_manager`) (다른 `modules` import 없음)
- **상태**: 구현됨. `compare`는 #21, 레이더 `direction` 표시는 #45에서 정리. 등급 경계값만 임시(#24). **해석 문장(#22) 진행 중**: 지금은 입력 유형이 제목에만, 등급이 낮음/그 외 두 갈래에만, 키워드가 나열에만 쓰임

### scripts.build_index
- **파일**: `scripts/build_index.py`
- **Unit / 담당**: A (홍승민)
- **책임**: WikiArt 축소판의 CLIP 임베딩 사전 계산 → `artifacts/embeddings.npy`, `meta.csv`
- **의존**: 없음(아직 import 없음)
- **상태**: 미구현 — `NotImplementedError("#4에서 구현 예정")` (2026-11-19 기준)

### scripts.build_profiles
- **파일**: `scripts/build_profiles.py`
- **Unit / 담당**: C (심현준)
- **책임**: 학습셋(`split == "train"`)만으로 화가 프로필 계산 → `artifacts/profiles.json`. 명화에 화이트밸런스 금지
- **의존**: 없음(아직 import 없음)
- **상태**: 미구현 — `NotImplementedError("#19에서 구현 예정")` (2026-11-19 기준)

### notebooks.eval
- **파일**: `notebooks/eval.ipynb`
- **Unit / 담당**: B (홍예원)
- **책임**: 판정 3종 비교(#12), 온도 보정(#14), 합치기 3종 비교(#15) — 검증셋. 최종 평가(#26) — 테스트셋 한 번
- **의존**: 없음(코드 셀 없음)
- **상태**: 계획 마크다운 셀 1개뿐 (2026-11-19 기준)

### tests
- **파일**: `tests/conftest.py`, `tests/test_classify.py`, `tests/test_features.py` (+ 아래 `tests.smoke`, `tests.explain`, `tests.fakes`)
- **Unit / 담당**: 공용 설정은 D, 동작 테스트는 각 Unit 담당
- **책임**: 루트 `sys.path` 추가, `@pytest.mark.model` 기본 건너뛰기(`--run-model`/`RUN_MODEL_TESTS=1`로 실행, 아니면 `HF_HUB_OFFLINE`·`TRANSFORMERS_OFFLINE`), `model` 표시 없는 테스트에서 `data.embed_image`·`embed_text`를 `fakes.FAKES`로 바꿔 끼움. B·C 동작 테스트
- **의존**: `pytest`, `numpy`, `app`, `modules.*`
- **상태**: 공용 설정은 동작 중. `conftest.py`·`test_classify.py`·`test_features.py`는 이번 스캔에서 열지 않음

### tests.fakes
- **파일**: `tests/fakes.py`
- **Unit / 담당**: 공용 (D)
- **책임**: 실제 CLIP 없이 계약 형식의 결정적 결과를 주는 `fake_embed_image`(RGB uint8 3채널이 아니면 `ValueError`, 같은 이미지 → 같은 벡터), `fake_embed_text`(`str` 하나도 받음), 바꿔 끼울 목록 `FAKES = {"modules.data": {"embed_image", "embed_text"}}`
- **의존**: `hashlib`, `numpy`
- **상태**: 동작 중. `clip_keywords`·`detect_type`은 모델 함수가 아니라 스텁이라 `FAKES`에 없음 → 파이프라인 테스트에서 입력 유형·키워드는 임베딩 값에 따라 정해지고 테스트가 고를 수 없음

### tests.smoke
- **파일**: `tests/test_smoke.py`
- **Unit / 담당**: 공용 (계약 형식 검사, 1일차 D 작성)
- **책임**: 계약 함수의 반환 형식, 전체 파이프라인(컬러·스케치), Gradio 빌드, 상세 JSON의 `path` 제거 검사. 실제 구현으로 바꿔도 그대로 통과해야 하며 약하게 고치지 않음
- **의존**: `app`, `modules.{classify,data,explain,features}`, `pytest`, `numpy`, `pandas`, `matplotlib.figure`
- **상태**: 테스트 함수 15개(17개 케이스), 그중 `model` 표시 2개는 기본 실행에서 건너뜀. `render_card()`는 `(str, Figure)`·`DISCLAIMER` 포함만 검사

### tests.explain
- **파일**: `tests/test_explain.py`
- **Unit / 담당**: D (#21, #45)
- **책임**: `compare()` 경계 동작(정렬·최대 2개·동점·같은 화가·NaN/inf/bool/palette 건너뜀·numpy 수·std 0·잘못된 프로필·한쪽 프로필에만 있는 특징·빈 입력·미등록 화가 `KeyError`), `app.analyze`가 스케치에서만 색 특징을 빼고 대조하는지, 레이더 `_radar()`의 축 라벨·값 자르기·숫자 아닌 특징 건너뜀
- **의존**: `modules.explain`, (함수 안에서) `app`, `modules.features`, `pytest`, `numpy`, `math`
- **상태**: 테스트 함수 16개(17개 케이스). `render_card()` 문장 동작 테스트는 없음 — #22에서 추가할 파일. 모듈 docstring은 아직 "compare() 동작 테스트 (#21)"

### contracts
- **파일**: `contracts/interfaces.md` (변경 절차: `.github/ISSUE_TEMPLATE/contract-change.yml`)
- **Unit / 담당**: 공용 (팀 합의로만 변경, AI 도구는 수정하지 않음)
- **책임**: 공통 규칙 4개, 16개 함수의 이름·인자·반환 형식, `render_card()`에 넘기는 `result` 키 표(11행), 1일차 해석 확인 사항 3개의 최종 기준
- **의존**: 없음
- **상태**: 1일차(2026-11-19) 확정 이후 변경 없음(2026-11-27 확인). `render_card`는 `(str, Figure)`만 정하고 문장 내용은 정하지 않음

### requirements
- **파일**: `requirements.txt`
- **Unit / 담당**: 공용 (변경은 D의 PR)
- **책임**: Python 3.11 기준 런타임·도구 버전 12개를 `==`로 고정
- **의존**: 없음
- **상태**: 2026-11-27 확인, 변경 없음. 버전 표는 `technology-stack.md`

### ci
- **파일**: `.github/workflows/ci.yml`, `.github/pull_request_template.md`, `.github/CODEOWNERS`
- **Unit / 담당**: D (저장소 관리)
- **책임**: PR·`main` push·수동 실행마다 `ruff (format + lint)`와 `pytest (Python 3.11)` 두 작업. PR 본문 형식(검증 결과, AI 판단 이유 3줄, 체크리스트), 경로별 리뷰어
- **의존**: `requirements.txt`(ruff 버전 포함), `pyproject.toml`, CPU torch 인덱스
- **상태**: 동작 설정 있음(실행 결과는 이 스캔에서 확인하지 않음). 이번에는 열지 않음
