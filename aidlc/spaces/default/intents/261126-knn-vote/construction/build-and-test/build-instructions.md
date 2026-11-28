# Build Instructions — #9 kNN 투표 방식 판정

## 의존성 설치
- Python 3.11, `requirements.txt`의 고정 버전. (Windows)
  ```
  py -3.11 -m venv .venv
  .venv\Scripts\activate
  pip install -r requirements.txt
  ```
- 이번 변경은 새 의존성을 추가하지 않는다(numpy 등 기존 패키지만 사용).

## 환경 설정
- 별도 환경 변수·로컬 서비스 없음. 모델 다운로드 없음(테스트는 가짜 색인 사용).

## 빌드
- 컴파일·번들 단계 없는 순수 Python. "빌드"는 린트·테스트 통과로 갈음한다.
  ```
  .venv\Scripts\python -m ruff format --check .
  .venv\Scripts\python -m ruff check .
  ```

## 빌드 검증
- `.venv\Scripts\python -m pytest` 전체 통과(아래 test-results.md 참고).

## 흔한 문제
- `from modules import ...` 실패 시: 저장소 루트에서 실행하거나(노트북은 `#9 kNN` 첫 셀이
  `sys.path`에 루트를 넣는다), venv 활성화 여부 확인.
