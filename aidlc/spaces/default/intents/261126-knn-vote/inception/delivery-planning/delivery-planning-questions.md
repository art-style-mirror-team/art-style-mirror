# Delivery Planning — Questions (#9 kNN 투표 방식 판정)

이 intent는 작업 단위가 하나(U1 `u1-knn-vote`)뿐이라 순서·분배 결정이 사실상 없다. 전략 질문은
아래처럼 자명하게 정해지므로 별도로 묻지 않는다(검증 명령만 Step 6에서 승인받는다).

## 전략 질문 (프로젝트당 1답)

## Q1. 무엇을 먼저 만들까(위험/가치/얇은 슬라이스/혼합)?
[Answer]: 해당 없음 — 단위가 하나라 순서 선택이 없다. 1일차 스텁(`modules/`·`app.py`)이 이미
입력→전처리→CLIP·OpenCV→`fuse()`→결과 카드까지 도는 walking skeleton(처음부터 끝까지 도는 최소
동작 슬라이스)이다. #9는 그 안의 판정 로직 한 조각을 실제 구현으로 바꾼다.

## Q2. 공식 점수 모델(WSJF 등)로 순위를 매길까?
[Answer]: 아니오 — 단일 단위라 순위 매길 대상이 없다.

## Q3. Bolt 하나의 크기는?
[Answer]: Bolt(한 번의 Construction 통과로 한 조각을 만들어 돌아가게 하는 단위) 하나 = U1 전체.

## Q4. 여러 Bolt를 동시에 만들 수 있나?
[Answer]: 해당 없음 — Bolt가 하나다. 직렬(unit-major, serial).

## Q5. 외부에서 막는 것이 있나(API·데이터·승인·타 팀 핸드오프)?
[Answer]: 없음. 기존 색인(`load_index`)과 기존 함수만 읽어 쓰므로 완전히 팀 내에서 끝난다.

## Q6. 이 작업에서 가장 걱정되는 점은?
[Answer]: 수치적 안정성(음수 유사도·투표 0 → log)과 결정성(동점)이다. 이는 요구사항 FR1.4~1.9,
NFR5와 그 테스트(FR3.4)로 이미 다룬다.

## 빌드 담당
[Answer]: `aidlc-developer-agent`(AI)가 구현하며, 프로젝트 규칙상 Unit B(판정·융합, 담당 홍예원)
범위다. Construction은 현재 체크아웃한 이슈 브랜치(`feat/9-knn-vote`)에서 진행하고 별도
worktree·Bolt 브랜치를 만들지 않는다.
