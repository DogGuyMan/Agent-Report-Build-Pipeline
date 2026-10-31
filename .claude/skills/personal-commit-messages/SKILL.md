---
name: personal-commit-messages
description: Apply whenever creating, proposing, rewriting, or reviewing git commit messages in this user's repositories — including squash/amend/rebase messages and PR titles. Enforces this user's format, a lowercase `[tag] : subject` one-liner in Korean with NO body and no trailers, ASCII-only punctuation in the subject, and category-based commit splitting. Trigger on "커밋해줘", "커밋 메시지", "commit this", "커밋 나눠줘", "스테이징하고 커밋", "PR 올려줘", or any time you are about to run `git commit` — even if the user never mentions message style. Also use when a large uncommitted worktree needs to be broken into a commit plan.
---

# Personal Commit Messages

이 사용자의 커밋 메시지 규칙이다. 핵심 목표는 **`git log --oneline` 한 화면으로 저장소 역사를 다 읽는 것**이다.
그래서 본문을 쓰지 않고, 대신 커밋을 더 잘게 나눈다.

## 형식

```
[tag] : 제목
```

- 태그는 **소문자**, 대괄호로 감싼다
- 대괄호와 콜론 사이에 **공백 한 칸**, 콜론 뒤에도 한 칸 (`[feat] : ...`)
- 제목은 한국어 한 줄, 마침표 없음
- **본문(메모)을 쓰지 않는다.** `Co-Authored-By` 같은 트레일러도 붙이지 않는다

## 태그

| 태그 | 쓰는 곳 |
|---|---|
| `feat` | 기능 추가 |
| `fix` | 버그 수정 |
| `build` | 빌드 시스템, 의존성, 타깃 배선 (CMake, vcpkg, 프리셋) |
| `test` | 테스트 코드와 검증 자산 |
| `docs` | 문서 |
| `chore` | 설정 파일, 스크립트, 잡무 |
| `refactor` | 동작 변화 없는 구조 변경 |
| `perf` | 성능 |

앞의 여섯 개가 주력이다. 새 태그가 필요해 보이면 만들어 쓰기 전에 사용자에게 물어라.

## 모듈이 여럿인 저장소

타깃/모듈 이름을 제목 앞에 붙이고 ` - ` 로 잇는다. 어느 모듈의 커밋인지가 태그보다 먼저 눈에 들어와야 한다.

```
[build] : core - pano_core 정적 라이브러리와 OpenCV PUBLIC 전파
[feat]  : server - QTcpServer bind 방식 QHttpServer 부트스트랩과 GET /health
[feat]  : app - Pretendard 임베드와 Script_Hangul 폴백 등록
```

(정렬용 공백은 제안 목록에서만 쓴다. 실제 커밋 메시지에는 넣지 않는다.)

## 제목에는 ASCII 구두점만

| 쓰지 마라 | 대신 |
|---|---|
| `—` (em-dash) | `-` |
| `→` | `->` |
| `·` (가운뎃점) | 두 항목이면 `&`, 셋 이상이면 `,` |

유니코드 구두점은 터미널과 git 도구마다 표시 폭이 달라져 `--oneline` 정렬이 깨진다.

```
나쁨: [test] : 스티칭 입력 데이터셋 — campus·yosemite·my_pictures
좋음: [test] : 스티칭 입력 이미지 데이터셋 - campus, yosemite, my_pictures

나쁨: [docs] : Python → C++ 포팅 플랜
좋음: [docs] : Python -> C++ 포팅 플랜과 핸드오프 보고서
```

## 커밋 나누기가 이 규칙의 절반이다

본문이 없으므로 제목이 감당하지 못하면 **설명을 늘리지 말고 커밋을 쪼개라.** 제목이 한 줄을 넘길 것 같으면
그건 커밋 하나에 두 가지 일이 들어 있다는 신호다.

나누는 축, 효과가 큰 순서대로:

1. **배선과 구현을 나눈다.** 빌드 설정(`build`)과 그 위에 올라가는 소스(`feat`)를 따로 올린다.
   나중에 "이 CMake 가 왜 이렇게 생겼나"를 커밋 하나로 읽을 수 있다.
2. **모듈별로 나눈다.** 한 커밋은 한 타깃만 건드린다.
3. **성격이 다른 자산을 나눈다.** 입력 데이터와 기대 출력, 코드와 대용량 바이너리는 따로.
4. **문서를 따로 올린다.** 코드 리뷰에서 문서 diff 가 코드 diff 를 덮지 않게 한다.

## 작업 순서

커밋을 만들기 전에 **계획을 먼저 보여주고 승인을 받아라.** 사용자는 목록을 보고 메시지 표현과 분할 단위를
고치는 편이다. 승인 없이 커밋하면 되돌리는 비용이 크다.

제안 형식 — 제목 한 줄과 그 커밋에 들어갈 경로:

```
[chore] : 무시 규칙과 clangd & VSCode 공통 설정
  .gitignore  .clangd  .vscode/{extensions,settings,tasks}.json

[build] : CMake 골격 - 모듈별 의존성 선언과 타깃별 프리셋 분리
  CMakeLists.txt  CMakePresets.json  cmake/CXXStandard.cmake  vcpkg.json
```

커밋 실행 시 주의:

- `git commit` 은 인덱스 **전체**를 커밋한다. 이전 세션에서 스테이징된 채 남은 항목이 섞여 들어갈 수 있으니
  첫 커밋 전에 `git status --porcelain -uall` 과 `git ls-files` 로 인덱스를 확인하라.
- 빈 파일(0 바이트)이 의도된 스켈레톤인지 미완성 산출물인지 구분하라. 후자는 커밋에서 빼고 사용자에게 알려라.
- 대용량 바이너리를 처음 커밋할 때는 크기를 먼저 재서 알려라. 히스토리에 들어가면 되돌리기 어렵다.

## 제목 쓰는 법

무엇을 바꿨는지가 아니라 **무엇이 가능해졌는지 / 왜 그렇게 했는지**가 드러나게 쓴다.
`git log --oneline` 은 파일 목록을 보여주지 않으므로, 제목이 유일한 단서다.

```
약함: [build] : CMakeLists.txt 수정
강함: [build] : app - panorama_gui 타깃, core 링크 금지 가드와 AUTORCC

약함: [feat] : 서버 구현
강함: [feat] : server - QTcpServer bind 방식 QHttpServer 부트스트랩과 GET /health

약함: [chore] : 설정 추가
강함: [chore] : 무시 규칙과 clangd & VSCode 공통 설정
```
