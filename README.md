# art-style-mirror
어떤 이미지든 닮은 화가,화풍 Top3를 찾고 색과 선으로 설명하는 프로그램

> **현재 상태: 1일차 뼈대.** 모든 모듈이 스텁이라 화면에 나오는 결과는 형식만 맞춘 가짜 값입니다.

일반 사진, 직접 그린 그림, 완성된 그림, 연필 스케치를 넣으면 다음을 보여 줍니다.

- 닮은 화가 Top 3 (신뢰도 %, 신뢰 등급 높음·보통·낮음)
- 닮은 화풍 Top 3, 비슷한 명화 3점
- CLIP 키워드 설명, 1·2위 대조 설명, 색·선 레이더 차트

CLIP은 소재·분위기·양식을, OpenCV는 색·선 수치를 보고, 두 관점을 합친 신뢰도 순으로 Top 3를 정합니다.
자세한 계획은 [docs/plan.md](docs/plan.md), 함수 형식은 [contracts/interfaces.md](contracts/interfaces.md)를 보세요.

## 실행법

Python 3.11이 필요합니다.

```powershell
# Windows (PowerShell)
git clone https://github.com/art-style-mirror-team/art-style-mirror.git
cd art-style-mirror
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

```bash
# macOS / Linux
git clone https://github.com/art-style-mirror-team/art-style-mirror.git
cd art-style-mirror
python3.11 -m venv .venv
source .venv/bin/activate
# Linux만: GPU가 없으면 CPU판 torch를 먼저 설치한다 (기본 설치는 CUDA 포함으로 수 GB)
pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
python app.py
```

브라우저에서 http://127.0.0.1:7860 을 엽니다. 테스트는 `pytest`로 돌립니다.

커밋 전에는 포매팅과 린트를 실행합니다. PR마다 CI가 같은 검사를 합니다.

```bash
ruff format .
ruff check --fix .
```

## 팀원

| 역할 | 이름 | GitHub | 맡는 일 |
| --- | --- | --- | --- |
| A — 데이터·CLIP | 홍승민 | | 데이터 분할, CLIP 임베딩, 키워드 설명 |
| B — 판정·융합 | 홍예원 | | 입력 유형 판별, 판정 비교, 온도 보정, 두 관점 합치기 |
| C — 색·선 분석 | 심현준 | | 입력 전처리, 색·선 특징, 화가 프로필 |
| D — 신뢰도·UI·통합 | 김현승 | [@KimHyeonSeung1213](https://github.com/KimHyeonSeung1213) | 신뢰 등급, 설명·레이더 차트, Gradio 화면, 통합 |

> 각자 첫 PR로 자기 줄에 GitHub 아이디를 채웁니다.

## 데이터 출처와 이용 조건

| 데이터 | 출처 | 조건 |
| --- | --- | --- |
| WikiArt (명화 81,444점, 화가 129명) | [huggan/wikiart](https://huggingface.co/datasets/huggan/wikiart) (Hugging Face) | **비상업 연구용** |
| WikiArt 축소판 (화가 24명) | `slpkl/wikiart-subsample` 등 (Hugging Face) | 원본 WikiArt 조건을 따름 |
| 화가 소개 | Kaggle "Best Artworks of All Time"의 `artists.csv` | **CC BY-NC-SA 3.0** (비상업, 저작자 표시, 동일 조건 변경 허락) |

- 이 프로젝트와 결과물은 **비상업 학습·연구 목적**으로만 사용합니다.
- 원본 이미지는 저장소에 포함하지 않습니다. 실행에 필요한 임베딩·프로필 같은 작은 파생 파일만 `artifacts/`에 둡니다.
- 결과는 픽셀 수치 기반의 통계적 해석이며 미술사적 평가가 아닙니다.
- 코드는 [MIT License](LICENSE)를 따릅니다. 데이터에는 위의 각 조건이 따로 적용됩니다.
