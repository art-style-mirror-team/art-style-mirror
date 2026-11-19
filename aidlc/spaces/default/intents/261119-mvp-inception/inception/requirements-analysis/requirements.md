# Requirements — 닮은 화가·화풍 분석기 MVP

> 이 문서는 새 요구사항을 만들지 않는다. 기준 문서는 `docs/plan.md`(1·4·6·7·8장), GitHub 이슈 #1~#30, `contracts/interfaces.md`이고, 여기서는 그 내용을 ID를 붙여 인용만 한다. 출처가 서로 다르면 기준 문서를 따른다. 함수 형식은 `contracts/interfaces.md`를 따른다.

## 의도 분석

- **목표**: 어떤 이미지든 넣으면 닮은 화가·화풍 Top 3를 찾고, 왜 닮았는지 색과 선으로 설명하는 Gradio 앱을 4명이 2주 안에 MVP로 만들어 GitHub에 공개한다. 최종 산출물은 실행 가능한 코드와 README다(plan.md 1장).
- **이번 작업의 범위**: Inception 기록만 남긴다. 코드는 바꾸지 않는다. Construction은 이슈별 intent에서 따로 진행한다(초기 요청).
- **현재 상태**: 1일차 스텁이 walking skeleton이다. 입력부터 결과 카드까지 끝까지 돌고, A·B·C 함수는 계약과 같은 모양의 가짜 값을 돌려준다(코드 분석 결과 `aidlc/spaces/default/codekb/art-style-mirror/business-overview.md`, `architecture.md`, `code-structure.md`).
- **유형**: 브라운필드 MVP. 여러 컴포넌트에 걸치지만 모듈 4개로 나뉘어 있다. 복잡도는 보통이다.

## 기능 요구사항

ID 옆의 "확인"은 각 이슈의 완료 기준을 그대로 옮긴 것이다. 정확도 기준은 검증셋에서 실제로 실행한 결과로만 판단한다.

### FR1. 입력 처리 (Unit C, 일부 B)

- **FR1.1** 사용자 입력을 RGB `np.ndarray`(uint8)로 받아 종이 영역 자르기, 화이트밸런스, 긴 변 512px 맞추기, 흑백 판별을 한다. 화이트밸런스는 사용자 입력에만 적용한다(#16). 확인: 종이 그림 사진의 배경이 흰색에 가까워진다.
- **FR1.2** 입력 유형을 사진/그림/스케치 중 하나로 판별한다(#8). 확인: 샘플 15장 중 12장 이상 정답.

### FR2. CLIP 관점 (Unit A·B)

- **FR2.1** WikiArt 축소판을 화가 24명으로 확정하고 학습 70% / 검증 15% / 테스트 15%로 나눈다(#3). 확인: `meta.csv`의 split 열에 train/val/test가 있다.
- **FR2.2** CLIP 임베딩을 미리 계산해 저장하고(#4), `embed_image()`·`embed_text()`를 구현한다(#5). 명화와 사용자 입력에 같은 CLIP 모델 버전을 쓴다. 확인: `embeddings.npy` 행 수가 meta 행 수와 같다. 같은 이미지를 두 번 넣으면 유사도가 0.99 이상이다.
- **FR2.3** `clip_keywords()`가 반대 문장쌍과 표현 앙상블로 소재·분위기·양식 키워드를 낸다(#7). 확인: 고흐 작품에서 붓터치·소용돌이 계열 키워드가 상위에 온다.
- **FR2.4** 화가 소개(`artists.csv`)를 결합한다(#6). 확인: 소개가 없는 화가를 목록으로 만들고 짧은 소개를 직접 보충한다.
- **FR2.5** 판정 3종(kNN 투표, 중심점, 선형 분류기)을 검증셋에서 비교하고 `predict_clip()`의 최종 방식을 고른다(#9~#12). 확인: `eval.ipynb`에 비교표가 있다.
- **FR2.6** `similar_works()`가 비슷한 명화 3점을 돌려준다. 유사도 0.95 이상(자기 자신)은 제외한다(#13). 확인: 데이터셋 작품을 넣어도 자기 자신이 나오지 않는다.

### FR3. OpenCV 관점 (Unit C)

- **FR3.1** 색 특징 6종(#17)과 선 특징 5종(#18)을 그림 픽셀에서 계산한다. 확인: 밝은 그림과 어두운 그림의 값이 예상대로 다르다. 몬드리안과 고흐 작품의 직선 비율이 뚜렷이 다르다.
- **FR3.2** 화가·화풍별 프로필을 학습셋으로만 집계한다. 명화에는 화이트밸런스를 적용하지 않는다(#19). 확인: `profiles.json`에 화가 × 특징별 평균·표준편차가 있다.
- **FR3.3** `predict_cv()`가 z값 거리를 확률로 바꾸고, 피셔 점수로 약한 특징을 뺀다. 스케치는 선 특징만 쓴다(#20, plan.md 6.1). 확인: 검증셋 Top-3 정확도와 제외한 특징 목록을 기록한다.

### FR4. 보정과 합치기 (Unit B)

- **FR4.1** p_clip과 p_cv의 온도 T를 각각 검증셋 NLL로 정하고 `calibration.json`에 저장한다(#14).
- **FR4.2** `fuse()`가 가중합·가중곱·RRF를 비교해 w와 방식을 정한다. 최종 순위는 `fuse()` 결과만 쓴다(#15, plan.md 6.2).

### FR5. 신뢰도와 설명 (Unit D)

- **FR5.1** `assess_confidence()`가 1·2위 차이, 정규화 엔트로피, JSD, 데이터셋 유사도로 높음/보통/낮음 등급을 매긴다(#24). 확인: 높음 등급의 실제 정확도가 80% 이상이 되는 경계값을 검증셋으로 기록한다.
- **FR5.2** `compare()`가 1위인 이유와 2위 느낌이 나는 부분을 대조한다(#21). 확인: 가짜 프로필로 단위 테스트가 통과한다.
- **FR5.3** 해석 문장 템플릿이 입력 유형과 등급별로 문구를 낸다(#22). 확인: 입력 3종 × 등급 3종 모두 자연스러운 문장이 나온다.
- **FR5.4** 레이더 차트로 내 그림과 1위 화가 평균을 비교한다(#23). 확인: 특징 이름이 한글이고 두 도형을 구분할 수 있다.
- **FR5.5** 등급이 낮음이면 "뚜렷하게 닮은 화가가 없어요"와 함께 CLIP·OpenCV 결과를 따로 보여준다. 두 관점이 엇갈리면 숨기지 않는다(plan.md 6.3).

### FR6. 통합과 공개 (Unit D, 전원)

- **FR6.1** Gradio 화면에 전체 파이프라인을 연결하고, 크게 엇갈린 사례를 `samples/disagree/`에 자동 저장한다(#25). 확인: 엇갈림 시험 세트를 포함한 샘플에서 오류 없이 결과 카드가 나온다.
- **FR6.2** README에 설치·실행법, 스크린샷, 데모 GIF, 정확도표·ECE·안정성, 데이터 출처·비상업 조건, 한계를 쓰고 GitHub에 공개한다(#30). 확인: 출처와 비상업 용도를 명시한다.

### FR7. 평가 (Unit B·A)

- **FR7.1** 테스트셋으로 Top-1·Top-3 정확도, ECE(구간 10), 신뢰도 다이어그램을 낸다. 테스트셋은 이때 한 번만 쓴다(#26).
- **FR7.2** 변형 5종을 적용한 뒤 1위가 유지되는 비율을 방식별로 잰다(#27).

## 비기능 요구사항

- **NFR1 (인터페이스 안정성)** 함수 이름과 입출력 형식은 `contracts/interfaces.md`를 따르고 바꾸지 않는다. 확인: 실제 구현으로 바꿔도 `tests/test_smoke.py`가 그대로 통과한다(AGENTS.md 2·#2).
- **NFR2 (검증)** 모든 변경은 `pytest` 전체 통과가 조건이다. 계약 검사가 먼저 있고, 동작 테스트는 구현과 함께 같은 PR에서 쓴다. 커버리지 하한은 두지 않는다. 확인: PR마다 CI(`.github/workflows/ci.yml`)가 통과한다(project.md·`team-practices.md` Testing Posture).
- **NFR3 (데이터 분할)** 프로필과 분류기는 학습셋, T·w·등급 경계값은 검증셋으로만 정한다. 테스트셋은 #26에서만 연다. 확인: 기준값이 정해진 노트북·스크립트가 test split을 읽지 않는다(AGENTS.md 6).
- **NFR4 (이미지 형식)** 모든 처리는 RGB uint8, 긴 변 512px로 맞춘 뒤 한다. `cv2.imread()` 결과는 RGB로 바꾼다. 확인: 모듈 입출력 형식 검사가 통과한다(AGENTS.md 9).
- **NFR5 (실행 환경)** Python 3.11에서 로컬로 실행한다(`python app.py`, `127.0.0.1:7860`). 자동 배포는 없다. 확인: 네 명 모두 clone 후 `pip install`에 성공한다(#1, `team-practices.md` Deployment).
- **NFR6 (저장소 크기와 라이선스)** 원본 이미지와 100MB 이상 파일은 커밋하지 않는다. WikiArt는 비상업 연구용임을 README에 적는다(AGENTS.md 3·11).
- **NFR7 (코드 스타일)** Ruff로 포매팅·린트하고 CI에서 실행한다. 도입은 D의 PR로 한다(`team-practices.md` Code Style).

## 제약

- 일정: 2주. 1일차에 인터페이스 확정, 7일차까지 모듈 단독 완성, 11일차 기능 동결(plan.md 7장).
- 조직: 역할 4개(A 데이터·CLIP, B 판정·융합, C 색·선, D 신뢰도·UI·통합). 각자 자기 모듈 파일만 수정한다(AGENTS.md 1).
- 협업: 이슈 하나 = 브랜치 하나 = PR 하나. 머지 커밋만 쓰고 squash·rebase·force push는 하지 않는다(project.md Way of Working).
- 기술 스택은 `requirements.txt`에 고정한다(project.md Tech Stack).

## 가정

- 1일차 스텁과 `app.py`가 이미 walking skeleton이다. 근거: `tests/test_smoke.py`가 전체 파이프라인을 검사한다(project.md Walking Skeleton).
- 선택 기능(성장 지도, 색 전이, 화가 30~50명 확장 #28, HF Spaces 배포 #29)은 필수 이슈가 끝났을 때만 시작한다(plan.md 8장).

## 범위 밖

- 이번 작업에서 하는 코드 변경, Construction, 배포, 운영 단계.
- 새 요구사항이나 범위 추가. plan.md와 이슈에 없는 것은 만들지 않는다.
- 선택 기능을 MVP 필수로 올리는 것.

## 열린 질문 (다음 단계로 넘김)

- **Unit 간 import**: `modules/classify.py:15`는 A의 `load_index`를, `modules/features.py:17`은 A의 `ARTISTS`를 import한다. "Unit은 서로 의존하지 않는다"는 결정과 어떻게 맞출지 Domain Design과 Units Generation에서 정한다(`architecture.md` Improvement Opportunities).
- **`T_cv` 소유**: 보정값 파일은 B 소유인데 C의 `predict_cv()`는 `T = 1.0`을 코드에 넣어 두었다. 읽기 경로를 Contract Design에서 확인한다.
- **화가 이름 일치**: A의 `meta.csv`, B의 확률 키, C의 `profiles.json` 키가 같은 이름이라는 암묵 계약이 있다(`app.py:57`). Contract Design에서 확인한다.
- **CLIP 모델 ID**: 코드에 아직 고정되어 있지 않다. #4·#5에서 하나로 정한다.
