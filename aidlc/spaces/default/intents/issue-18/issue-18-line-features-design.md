# Issue #18 — 선 특징 5종 설계

- 상태: 설계 문서 작성
- 담당: C (심현준)
- 범위: `modules/features.py`의 `extract_features()`가 반환하는 선 특징 5종
- 계약: `contracts/interfaces.md` 변경 없음
- 제외: 기존 색 특징 및 `preprocess_input()` 전처리 구현은 수정하지 않는다. PR #42·#43과의 병합 충돌을 최소화한다.

## 입력 및 반환 계약

- 입력 이미지는 RGB `np.ndarray`, dtype `uint8`, shape `(H, W, 3)`이며 파이프라인에서는 `preprocess_input()`을 거친 이미지를 사용한다.
- 함수명과 시그니처 `extract_features(img, gray=False) -> dict`를 유지하고, 반환 키 11개와 `palette` 형식을 보존한다.
- 이번 이슈의 선 특징 키는 `edge_density`, `direction`, `straight_ratio`, `roughness`, `stroke_length`다. 다섯 값은 모두 Python `float`이며 각각 `[0.0, 1.0]` 범위로 반환한다. 계산 결과는 경계에서 clamp한다.
- `direction`은 에지 방향의 집중도를 나타내는 방향 일관성으로, 2배각 가중 평균 벡터의 길이를 `[0.0, 1.0]` 범위로 반환한다.
- `gray`는 판정 모듈이 색 특징과 선 특징 중 무엇을 사용할지 선택하는 플래그다. `extract_features()`는 `gray=True`와 `gray=False` 모두 같은 입력 이미지에서 같은 방식으로 선 특징을 계산한다. `gray=True` 전용 선 특징 경로나 별도 가중치는 두지 않는다.

## 공통 영상 처리

1. 입력의 RGB 채널을 `cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)`로 8-bit 명암 영상으로 변환한다. `gray` 값에 따라 입력 채널 순서나 변환을 달리하지 않는다.
2. 명암 영상에 `cv2.GaussianBlur()` (커널 5×5, `sigmaX=1`)를 적용해 픽셀 노이즈의 영향을 줄인다.
3. 흐린 명암 영상에서 `cv2.Canny()` (threshold 50, 150)로 공통 에지 마스크를 만든다. 영상 크기는 계약에 따라 긴 변 512px를 기준으로 하며, 비율 특징은 영상 픽셀 수로 나눠 크기에 무관하게 정규화한다.
4. 방향은 흐린 명암 영상의 `cv2.Sobel()` 기울기로 계산한다. 직선 검출 및 선 길이 계산은 공통 에지 마스크를 사용한다.

## 특징별 계산 및 정규화

| 특징 | OpenCV/NumPy 계산 | `[0.0, 1.0]` 정규화 및 해석 |
| --- | --- | --- |
| `edge_density` | Canny 에지 마스크의 0이 아닌 픽셀 수를 NumPy로 센다. | `edge_pixel_count / (H * W)`. 에지가 전혀 없으면 `0.0`. 에지 픽셀 비율이므로 이미 `[0, 1]`이며 최종값은 범위 내로 clamp한다. 높을수록 에지가 촘촘하다. |
| `direction` | 에지 픽셀 위치에서 Sobel `gx`, `gy`를 구한다. 에지의 방향은 기울기 방향에 90도를 더한 선 접선 방향으로 보고, 각도를 0–180도 범위의 `theta`로 만든다. 기울기 크기를 가중치로 하여 `cos(2*theta)`와 `sin(2*theta)`의 평균 벡터를 구한다. 두 배 각도를 사용해 0도와 180도가 같은 무방향 직선으로 취급되도록 한다. | 2배각 가중 평균 벡터의 길이 `hypot(cos_mean, sin_mean)`를 `[0, 1]`로 clamp해 반환한다. 값이 1에 가까울수록 에지 방향이 일관되고, 0에 가까울수록 여러 방향이 섞여 있다. 에지가 없거나 기울기 크기의 합이 0이면 `0.0`을 반환한다. |
| `straight_ratio` | `cv2.HoughLinesP()`로 공통 에지 마스크의 선분을 찾고, 각 선분을 1픽셀 두께로 별도 마스크에 그린다. 허프 마스크와 에지 마스크의 교집합 픽셀만 직선 에지로 센다. 검출 매개변수는 긴 변 `L=max(H,W)`에 비례해 `threshold=max(10, round(0.03*L))`, `minLineLength=max(10, round(0.05*L))`, `maxLineGap=max(2, round(0.01*L))`로 정한다. | `straight_edge_pixel_count / edge_pixel_count`. 분모가 0이면 `0.0`. 허프 선분이 겹쳐도 교집합 마스크 픽셀은 한 번만 세며 최종값을 `[0, 1]`로 clamp한다. 높을수록 에지 중 직선으로 설명되는 비율이 크다. |
| `roughness` | 흐린 명암 영상에 `cv2.Laplacian(..., cv2.CV_32F)`를 적용하고 NumPy로 절댓값 평균을 계산한다. `e = mean(abs(laplacian)) / 255`로 입력 밝기 범위를 정규화한다. | `e / (e + 0.1)`. 결과를 `[0, 1]`로 clamp한다. 높을수록 고주파 명암 변화가 많고 표면·선이 거칠다. `0.1`은 고정된 스케일 상수이며 데이터셋 학습으로 맞추지 않는다. |
| `stroke_length` | Canny 마스크를 OpenCV의 3×3 십자 구조 요소로 반복 침식해 형태학적 skeleton을 만든다. 각 반복에서 `current - open(current)`을 skeleton에 누적하고, 더 침식할 픽셀이 없어지면 종료한다. skeleton을 8-연결 `cv2.connectedComponentsWithStats()`로 나누고, 픽셀 수가 3 미만인 조각은 제외한다. 남은 각 성분의 skeleton 픽셀 수를 해당 획의 길이 근사값으로 삼는다. | 유효 성분이 없으면 `0.0`. 그렇지 않으면 성분별 길이의 산술 평균을 영상 대각선 길이 `sqrt(H²+W²)`로 나눈다. 최종값은 `[0, 1]`로 clamp한다. 높을수록 연결된 평균 획이 길다. skeleton 기반 길이는 픽셀 단위의 근사치이지 물리적인 붓 길이는 아니다. |

## 알려진 한계

- 수평선과 수직선이 반씩 있는 그림(예: 몬드리안 격자)은 2배각 벡터가 서로 상쇄돼 `direction`(방향 일관성)이 0에 가깝게 나온다. 몬드리안과 고흐의 구별은 `straight_ratio`가 담당한다.

## 흑백 입력 및 색 특징과의 경계

- `gray=True`와 `gray=False`는 선 특징에 대해 동일한 그레이 변환, blur, Canny, Sobel 및 후속 계산을 쓴다. 흑백 스케치도 선 특징으로 `predict_cv(gray=True)` 확률을 계산할 수 있어야 한다.
- `gray=True`라고 해서 선 특징 값을 0으로 만들거나 색 특징 값으로 대체하지 않는다. 반환하는 선 특징 값은 실제 입력 영상에서 계산한 값이다.
- `brightness`, `contrast`, `saturation`, `warmth`, `color_diversity`, `palette`의 계산 및 `preprocess_input()`은 이번 작업에서 수정하지 않는다. 기존 반환 키·팔레트 형식도 유지한다.
- 선 특징 계산용 그레이 변환은 함수 내부의 파생 영상에만 사용한다. 사용자 입력 전처리, 화이트밸런스, 색 특징 처리 순서에는 개입하지 않는다.

## 완료 기준

- 기존 반환 계약을 유지하며 선 특징 5개 각각이 Python `float`이고 항상 `[0.0, 1.0]` 안에 있다. 빈 에지 영상과 방향을 산출할 수 없는 영상도 정의된 기본값으로 처리한다.
- 같은 RGB 입력에서 `gray=True`와 `gray=False`로 추출한 선 특징 5개가 동일하다.
- 같은 크기와 비슷한 에지 밀도로 만든 기하학적 직선 위주 이미지가 곡선 및 짧은 붓터치 이미지보다 `straight_ratio`가 뚜렷하게 높아야 한다. 합성 고정 테스트에서는 직선 이미지 값이 비교 이미지보다 최소 `0.20` 높도록 검증한다.
- 특징별 결과가 반복 실행에서 결정적이어야 한다.

## 테스트 계획

1. `tests/test_smoke.py` 또는 기존 특징 테스트에 합성 RGB 이미지를 사용해 11개 키 계약, 선 특징 자료형, `[0.0, 1.0]` 범위 및 `palette` 형식의 비회귀를 확인한다.
2. 검은 배경에 수평·수직 직선을 그린 이미지와 곡선/짧은 붓터치 이미지의 `straight_ratio`를 비교한다. 고정된 합성 입력에서 차이가 `0.20` 이상인지 검증한다.
3. 균일 이미지에서는 `edge_density`, `direction`, `straight_ratio`, `roughness`, `stroke_length`가 모두 0인지, 선이 추가되면 관련 값이 증가하는지 확인한다.
4. 방향이 알려진 수평·수직 선 입력에서 `direction`이 각각 정규화된 기대 방향 부근인지 확인하고, 모든 입력에서 범위·결정성을 검증한다.
5. 매끄러운 단순 도형과 잔잔한 고주파 질감 입력의 `roughness`를 비교해 고주파 질감 쪽이 더 큰지 확인한다.
6. 동일한 흑백 스케치 배열을 `gray=True` 및 `gray=False`로 전달해 선 특징 다섯 값이 동일한지 확인한다.
7. 구현 후 `pytest`를 실행하고, `ruff format .` 및 `ruff check --fix .`로 프로젝트 규칙을 확인한다. 이 설계 단계에서는 Python 코드와 테스트를 수정하거나 실행하지 않는다.
