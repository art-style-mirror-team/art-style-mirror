# Security Test Instructions — #11 선형 분류기

## 해당 없음 (주의 1건)

자격증명·외부 입력 경계·인증/인가 코드가 없다. 추가 함수는 로컬 색인으로 학습하고 로컬 파일을
읽고 쓸 뿐이다.

- **joblib/pickle 로드 주의**: `_load_linear`는 `joblib.load`(내부적으로 pickle)로 모델을 읽는다.
  pickle 로드는 신뢰할 수 있는 파일에만 해야 한다. 이번 범위에서 `LINEAR_PATH`는 팀이 자체 학습·저장한
  `artifacts/linear.pkl`만 가리키며 외부/사용자 제공 파일을 읽지 않으므로 현재 위험은 없다. 추후
  외부에서 받은 pkl을 로드하게 되면 그때 검증을 추가한다.
- 비밀값 하드코딩 없음. `random_state=0`은 재현용 시드로 비밀이 아니다.
