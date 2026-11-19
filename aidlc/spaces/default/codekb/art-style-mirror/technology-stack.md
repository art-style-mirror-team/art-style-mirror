# Technology Stack

## 언어와 런타임

| 항목 | 값 | 근거 |
| --- | --- | --- |
| 언어 | Python 3.11 | `requirements.txt` 주석, CI `python-version: "3.11"`, README |
| 문법 | `from __future__ import annotations`, PEP 604(`X \| None`), 내장 제네릭(`list[tuple]`) | 모든 모듈 |
| 실행 환경 | 로컬(`127.0.0.1:7860`). Windows `.venv`, macOS/Linux 지원 | README, AGENTS.md |
| 패키지 관리 | pip + `requirements.txt`(전부 `==` 고정). lock 파일·`pyproject.toml` 없음 | |

## 라이브러리 (requirements.txt, 1일차 2026-11-19 고정)

| 라이브러리 | 버전 | 용도 | 현재 import 위치 |
| --- | --- | --- | --- |
| numpy | 2.4.6 | 배열, 임베딩, 확률 계산 | `app`, 모든 `modules`, `tests` |
| pandas | 3.1.1 | 색인 메타 DataFrame | `modules.data`, `tests` |
| scipy | 1.17.1 | `jensenshannon` (JSD) | `modules.explain` |
| scikit-learn | 1.9.1 | 로지스틱 회귀 판정(#11) | 없음 (예정) |
| matplotlib | 3.11.2 | 레이더 차트 `Figure`, 한글 글꼴 탐색 | `modules.explain`, `tests` |
| opencv-python-headless | 5.1.0.95 | 리사이즈, 색·선 특징(#17·#18) | `modules.features` |
| torch | 2.15.0 | CLIP 모델 실행(#4·#5) | 없음 (예정) |
| transformers | 5.23.0 | CLIP (`CLIPProcessor` 등, plan.md 3장) | 없음 (예정) |
| datasets | 5.2.0 | WikiArt 로드(#3) | 없음 (예정) |
| gradio | 6.32.0 | 웹 UI | `app` |
| pytest | 9.2.0 | 테스트 | `tests` |

- CLIP 모델 이름·체크포인트는 아직 코드 어디에도 정해져 있지 않다. 규칙상 명화와 사용자 입력은 같은 CLIP 모델 버전이어야 한다(#4·#5에서 고정 필요).
- Linux CI·설치에서는 torch CPU판을 `https://download.pytorch.org/whl/cpu`에서 먼저 설치한다(`2.15.0+cpu`가 `torch==2.15.0`을 충족).

## 데이터

| 데이터 | 출처 | 조건 |
| --- | --- | --- |
| WikiArt | `huggan/wikiart` (81,444점, 화가 129명) | 비상업 연구용 |
| WikiArt 축소판(화가 24명) | `slpkl/wikiart-subsample` 등 | 원본 조건 따름 |
| 화가 소개 | Kaggle "Best Artworks of All Time" `artists.csv` | CC BY-NC-SA 3.0 |

원본 이미지는 커밋하지 않는다(`.gitignore`의 `/data/`, `samples/disagree/`, `*.pt`).

## 도구·인프라

| 항목 | 값 |
| --- | --- |
| CI | GitHub Actions `.github/workflows/ci.yml` (`actions/checkout@v4`, `actions/setup-python@v5`, pip 캐시) |
| 테스트 | pytest (`tests/`), 커버리지 도구 없음 |
| 린터·포매터 | 설정 없음 |
| 노트북 | Jupyter (`notebooks/eval.ipynb`, kernel Python 3) |
| 사전 계산 | Colab GPU에서 한 번 계산 후 파일 공유(plan.md 9.5) |
| 배포 | 없음. HF Spaces는 선택(#29) |
| 줄바꿈 | `.gitattributes`로 LF 고정(Windows 스크립트만 CRLF) |
| 라이선스 | 코드 MIT, 데이터는 각 조건 |
