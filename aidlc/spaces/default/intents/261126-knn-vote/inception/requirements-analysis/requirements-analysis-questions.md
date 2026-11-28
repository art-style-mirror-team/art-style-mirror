# Requirements Analysis — Questions (#9 kNN 투표 방식 판정)

#9 요청 문구에 거의 모든 동작이 정해져 있어 열린 지점만 2개 묻습니다.

## Q1. [개발] `_topk_accuracy(z, names, labels, ks=(1, 3))`의 `labels` 형식과 반환

요청 문구는 `_knn_logits`의 반환만 정했고 `_topk_accuracy`의 입력 `labels`·반환 형식은 정하지 않았습니다. #10·#11에서도 재사용하므로 계약을 확정합니다. (`z`는 (n, 이름 수) 행렬, `names`는 열에 대응하는 이름 목록.)

- A. `labels` = 각 행의 정답 이름 리스트(길이 n, 문자열) · 반환 = `dict {k: 정확도}` (예: `{1: 0.52, 3: 0.78}`)
- B. `labels` = 정답 이름 리스트(길이 n, 문자열) · 반환 = `ks` 순서의 `tuple`/`list` (예: `(0.52, 0.78)`)
- C. `labels` = `names` 기준 정수 인덱스 배열(길이 n) · 반환 = `dict {k: 정확도}`
- X. Other (please specify)

[Answer]: A — `labels` = 각 행의 정답 이름 리스트(길이 n, 문자열), 반환 = `dict {k: 정확도}`.

## Q2. [개발] `z = log(투표 + 작은 값)`의 "작은 값"(epsilon)

투표 0인 이름도 유한한 z를 갖도록 더하는 작은 값입니다. 순위에는 영향이 거의 없고, 투표 0 항목의 바닥값만 정합니다.

- A. `1e-9`
- B. `1e-12` (`_l2_normalize`의 바닥값과 통일)
- C. 다른 값
- X. Other (please specify)

[Answer]: X — epsilon = `1e-3`, `_knn_logits`의 키워드 인자 `eps=1e-3`으로 노출한다. 1e-9·1e-12는 투표 0인 정답의 log 확률이 너무 낮아져 #14 온도 보정의 NLL이 소수 사례에 끌려간다. 추가 요구: k가 작으면 표를 받은 이름이 3개 미만이라 Top-3가 이름순 동점에 좌우될 수 있으므로, 노트북 #9 절에서 k별 "표를 받은 화가 수의 평균"도 함께 계산해 보여 준다.
