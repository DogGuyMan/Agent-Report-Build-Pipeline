# iSAQB + 닫힌 목록이 덮는 탐침 30개 — 다시 잰 결과

2026-10-28 · 조정자가 직접 잼 · 🔵 이번 세션에서 돌린 명령의 출력

**왜 쟀나.** 보고서 [`언어 불문 설계 용어 출처`](../../reports/언어%20불문%20설계%20용어%20출처.md) 가 "iSAQB 와 닫힌 목록을 합쳐 탐침 63개 중 30개" 라고 했다.
사용자가 E7(iSAQB 를 "국제 표준 어휘" 에 넣을지)을 정하기 전에 그 30개를 확인하자고 했다.

**무엇으로 쟀나.**

- iSAQB `isaqb-org/glossary` @ `bd3ce64e1f4a250ccd1806719723ff80b7202cb8` (2026-10-09) — `docs/1-terms/*/*.adoc` 의 영어 표제(`// tag::EN[]` 안의 첫 제목). 표제 274개
- 탐침 63개 — `scripts/probe.json`. 조정자가 고른 연구 도구이지 정답이 아니다
- 맞추는 규칙 — 소문자로 바꾸고, 괄호 안을 지우고, `-` `/` `–` `_` 를 공백으로 바꾼 뒤 완전 일치. 스크립트 `scripts/isaqb_match.py`
- 닫힌 목록(GoF 23 · SOLID 5 · 패키지 원칙 6 · GRASP 9)은 이름 목록이라 손으로 대조했다

## 결과 — 숫자는 30 그대로, 구성은 보고서와 다르다

| 갈래 | 수 | 탐침 |
|---|---|---|
| iSAQB 완전 일치 · 설계 뜻 | 26 | invariant · single responsibility principle · Liskov substitution principle · interface segregation principle · dependency inversion principle · common closure principle · dependency injection · coupling · cohesion · encapsulation · information hiding · abstraction · composition · interface · layer · separation of concerns · design pattern · singleton · observer · strategy · adapter · facade · visitor · refactoring · bounded context · ubiquitous language |
| SOLID 닫힌 목록 (iSAQB 에는 표기가 달라 완전 일치 실패) | 1 | open-closed principle — iSAQB 표제는 `Open-Close-Principle (OCP)` |
| GoF 닫힌 목록 | 2 | factory method · decorator |
| GRASP 닫힌 목록 | 1 | polymorphism |
| **합** | **30** | |

**보고서의 30 과 다른 곳 둘.**

1. **`node` 는 거짓 적중이다.** 완전 일치 27개 안에 들지만 iSAQB 표제가 `Node (Node.js)` 다 — 괄호를 지우는 규칙 때문에 맞았다. 그래프의 노드가 아니다. 보고서는 이것을 30 에 넣었다
2. **`open-closed principle` 이 빠져 있었다.** iSAQB 는 `Open-Close-Principle` 로 적어 완전 일치에 실패하고, 보고서는 SOLID 닫힌 목록이 이것을 덮는다는 점을 세지 않았다

둘이 서로 상쇄돼 합이 30 으로 같다.

**느슨하게만 걸린 것 (세지 않음).**

| 탐침 | iSAQB 표제 | 판단 |
|---|---|---|
| testability | `Testability Quality Attribute` | 같은 개념을 품질 속성으로 적었다. 넣으면 31 |
| tree | `Attack Tree` · `Quality Tree` | 다른 뜻 — 자료구조 · 호출 트리가 아니다 |

곁에 있지만 탐침과 같지 않은 표제: `Factory` (GoF 의 Factory Method 가 아님), `Acyclic Dependencies Principle` (circular dependency 를 다루는 원칙이지 같은 낱말이 아님).

## 덮지 못하는 33개

side effect · precondition · postcondition · single source of truth · inversion of control · inheritance · layered architecture · layering violation · circular dependency · dependency graph · call graph · call tree · caller · callee · data flow · deterministic · idempotent · granularity · representation · code smell · technical debt · convention · bisect · production code · test code · prerequisite · edge · node · vertex · tree · stage · pipeline · testability(느슨한 적중을 받아들이면 32개)

## 읽는 법

- iSAQB 의 26개는 정의 첫 줄을 보면 모두 설계 뜻이다(예: `Strategy` — "Design pattern for defining a family of algorithms").
- 완전 일치 규칙만으로는 표기 변형(`Open-Close`)을 놓치고 동형이의(`Node.js`)를 잡는다. iSAQB 를 범위 씨앗으로 쓰면 이 두 종류를 사람이 한 번 걸러야 한다.
