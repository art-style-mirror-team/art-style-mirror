# Technology Stack

## 언어와 런타임

| 항목 | 값 | 근거 |
| --- | --- | --- |
| 언어 | Python 3.11 | `requirements.txt` 주석, CI `python-version: "3.11"`, `pyproject.toml` `target-version = "py311"` |
| 문법 | `from __future__ import annotations`, PEP 604(`X \| None`), 내장 제네릭(`list[tuple]`) | 모든 모듈 |
| 실행 환경 | 로컬(`127.0.0.1:7860`). Windows `.venv`, macOS/Linux 지원 | README, AGENTS.md |
| 패키지 관리 | pip + `requirements.txt`(전부 `==` 고정). lock 파일 없음. `pyproject.toml`은 도구 설정(Ruff·pytest)만 있고 패키지로 배포하지 않음 | |
| 프런트엔드 | 별도 빌드 없음. Gradio가 화면을 만든다. 수작업 CSS·JS·정적 파일 없음(#37 `static/`은 이 브랜치에 없음) | |
| 화면 문장 | Markdown 문자열(`gr.Markdown`), 한국어. 별도 템플릿 엔진·i18n 라이브러리 없이 f-string과 모듈 상수 dict로 만든다 | `modules/explain.py` |

## 라이브러리 (requirements.txt, 1일차 2026-11-19 고정, 이후 ruff 추가 — 2026-11-27 확인)

| 라이브러리 | 버전 | 용도 | 현재 import 위치 |
| --- | --- | --- | --- |
| numpy | 2.4.6 | 배열, 임베딩, 확률 계산 | `app`, 모든 `modules`, `tests` |
| pandas | 3.1.1 | 색인 메타 DataFrame | `modules.data`, `tests` |
| scipy | 1.17.1 | `jensenshannon` (JSD) | `modules.explain` |
| scikit-learn | 1.9.1 | 팔레트 군집(`MiniBatchKMeans`), 로지스틱 회귀 판정(#11 예정) | `modules.features` |
| matplotlib | 3.11.2 | 레이더 차트 `Figure`(pyplot 미사용), 한글 글꼴 탐색 | `modules.explain`, `tests` |
| opencv-python-headless | 5.1.0.95 | 리사이즈, 색·선 특징(#17·#18) | `modules.features` |
| torch | 2.15.0 | CLIP 모델 실행(#4·#5) | 없음 (예정, 2026-11-19 기준) |
| transformers | 5.23.0 | CLIP (`CLIPProcessor` 등, plan.md 3장) | 없음 (예정, 2026-11-19 기준) |
| datasets | 5.2.0 | WikiArt 로드(#3) | 없음 (예정, 2026-11-19 기준) |
| gradio | 6.32.0 | 웹 UI | `app` |
| pytest | 9.2.0 | 테스트 | `tests` |
| ruff | 0.17.6 | 포매터·린터 (CI가 이 줄을 읽어 같은 버전 설치) | 도구 |

- #22(해석 문장)는 새 라이브러리가 필요 없다. 한국어 조사(이/가 등) 처리용 외부 패키지도 `requirements.txt`에 없으므로, 필요하면 표준 라이브러리만으로 처리하거나 의존성 추가를 D의 PR로 따로 정해야 한다.
- CLIP 모델 이름·체크포인트는 A가 #5에서 상수 하나로 정하기로 했다(`docs/notes/D.md`). 규칙상 명화와 사용자 입력은 같은 CLIP 모델 버전이어야 한다.
- Linux CI·설치에서는 torch CPU판을 `https://download.pytorch.org/whl/cpu`에서 먼저 설치한다(`2.15.0+cpu`가 `torch==2.15.0`을 충족).

## Gradio 사용 현황 (`app.py`, 2026-11-27)

- 쓰는 API: `gr.Blocks(title=...)`, `gr.Row`, `gr.Column(scale=1)`, `gr.Markdown`, `gr.Image(type="numpy", image_mode="RGB", label=...)`, `gr.Button(variant="primary")`, `gr.Plot(label=...)`, `gr.Accordion(open=False)`, `gr.JSON`, `gr.Error`, `Button.click(fn, inputs, outputs)`, `Blocks.launch(server_name="127.0.0.1")`
- 쓰지 않는 API: 사용자 `css`·`js`·`head`, `theme`, 정적 파일 경로, `gr.HTML`, `gr.State`, `gr.Tabs`, 이벤트 체인(`.then`), 진행 표시(`gr.Progress`), 이미지 `sources`(카메라) 지정
- 카드 Markdown은 `gr.Markdown`이 렌더링한다. 카드에 쓰는 문법: `###` 제목, `**굵게**`, 번호·글머리 목록, `<sub>` HTML, `>` 인용
- 이전 CodeKB의 "#37 구현 전에 확인할 것(Gradio 6.x `css`·`js`·정적 파일 제공 방법)"은 #37 코드가 이 브랜치에 없어 이번 문서에서 뺐다. #37을 다시 시작할 때 확인한다
- `.gitignore`가 `.gradio/`(Gradio 작업 폴더)를 무시한다

## 데이터

| 데이터 | 출처 | 조건 |
| --- | --- | --- |
| WikiArt | `huggan/wikiart` (81,444점, 화가 129명) | 비상업 연구용 |
| WikiArt 축소판(화가 24명) | `slpkl/wikiart-subsample` 등 | 원본 조건 따름 |
| 화가 소개 | Kaggle "Best Artworks of All Time" `artists.csv` | CC BY-NC-SA 3.0 |

원본 이미지는 커밋하지 않는다(`.gitignore`의 `/data/`, `samples/disagree/`, `*.pt`). 그래서 `similar_works()`의 `path`(`data/wikiart/...jpg`)는 지금 화면에 이미지로 띄울 수 없다.

## 도구·인프라

| 항목 | 값 |
| --- | --- |
| CI | GitHub Actions `.github/workflows/ci.yml`: `ruff (format + lint)` 작업, `pytest (Python 3.11)` 작업 (`actions/checkout@v4`, `actions/setup-python@v5`, pip 캐시) |
| 테스트 | pytest (`tests/`, `pyproject.toml`의 `testpaths`, `model` 마커), 가짜 모델 `tests/fakes.py`, 커버리지 도구 없음 |
| 린터·포매터 | Ruff 0.17.6 — `pyproject.toml`: py311, line-length 100, 기본 규칙 + `I`, 큰따옴표, `.claude`·`aidlc` 제외. `.git-blame-ignore-revs` 있음 |
| 노트북 | Jupyter (`notebooks/eval.ipynb`, kernel Python 3) |
| 사전 계산 | Colab GPU에서 한 번 계산 후 파일 공유(plan.md 9.5) |
| 배포 | 없음. HF Spaces는 선택(#29), 하게 되면 수동 |
| 줄바꿈 | `.gitattributes`로 LF 고정(Windows 스크립트만 CRLF) |
| 라이선스 | 코드 MIT, 데이터는 각 조건 |

CI·`pyproject.toml`·`.gitignore`·`.gitattributes` 항목은 2026-11-19·11-26 스캔 기준이며 이번에는 열지 않았다.
