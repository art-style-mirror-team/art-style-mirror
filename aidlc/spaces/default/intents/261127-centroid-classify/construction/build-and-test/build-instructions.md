# Build Instructions — #10 중심점 방식 판정

이 프로젝트는 컴파일/번들 단계가 없는 Python 패키지다. "빌드"는 의존성 설치 + 정적 검사(Ruff)이고,
검증은 pytest다.

## 의존성 설치

```
py -3.11 -m venv .venv          # Windows (macOS/Linux: python3.11 -m venv .venv)
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

이미 `.venv`가 있으면 재설치는 필요 없다. 이 이슈는 새 의존성을 추가하지 않는다.

## 환경 설정

- 환경 변수·외부 서비스 없음. 모델(CLIP) 다운로드는 기본 테스트·CI에서 쓰지 않는다
  (`@pytest.mark.model` 테스트만 사용하며 기본 실행에서 건너뜀).

## 빌드/정적 검사 명령

```
.venv\Scripts\python -m ruff format --check .
.venv\Scripts\python -m ruff check .
```

(macOS/Linux: `.venv/bin/python -m ruff ...`)

## 빌드 검증

- 두 Ruff 명령이 모두 통과하면 정적 검사 통과.
- import 오류·구문 오류는 `python -c "import modules.classify"`로 빠르게 확인할 수 있다.

## 흔한 문제 해결

- `.venv\Scripts\python`이 없으면 위 가상환경 생성 단계를 먼저 실행한다.
- Ruff가 포맷 차이를 보고하면 `.venv\Scripts\python -m ruff format .`로 고친 뒤 다시 검사한다.
