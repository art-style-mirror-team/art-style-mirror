<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-11-26 — log 투표의 eps를 1e-3으로, `_knn_logits(..., eps=1e-3)` 키워드 인자로 노출(FR1.5, NFR5). 담당자 판단: 1e-9·1e-12는 투표 0인 정답의 log 확률이 너무 낮아 #14 온도 보정 NLL이 소수 사례에 끌려감.
- 2026-11-26 — `_topk_accuracy`는 `labels`=이름 리스트(len n), 반환=`dict {k: 정확도}`로 확정(FR2.1~FR2.2). #10·#11 재사용 전제(FR2.3).

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-11-26 — Request Changes로 검토 지적 R-01~R-05를 모두 요구사항에 반영: R-01 유사도 max(sim,0) clip(FR1.4~1.5), R-02 노트북 artist·style 둘 다/비교 기준 artist(FR4.1), R-03 이웃 동점 색인 위치순·비정상 입력 ValueError 등(FR1.8~1.9), R-04 미지 label 오답·ks 초과 제한(FR2.4), R-05 NFR5 검증 기준·테스트(FR3.4). 모두 #9 한정 결정이라 standing rule로 승격하지 않음. 담당자 지시로 User Stories는 건너뜀.
