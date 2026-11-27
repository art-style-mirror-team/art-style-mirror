# Performance Test Instructions — #11 선형 분류기

## 해당 없음

성능 NFR이 정의되지 않은 범위다. 선형 분류기 추론(`decision_function`)은 작은 임베딩 행렬에 대한
단일 선형 연산으로 비용이 미미하며, 학습(`_fit_linear`)은 오프라인 1회성이라 요청 경로에 없다.

- 정확도·ECE 등 평가 수치는 검증셋으로 산출하며 이 범위가 아니다(#26 최종 평가).
- 성능 기준이 생기면 `notebooks/eval.ipynb`(#9 이후)에서 다룬다.
