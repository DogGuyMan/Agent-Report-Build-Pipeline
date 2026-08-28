# HANDOFF ② — CLI 빌드 타깃 분리 (Task 0.1 · 0.2 · 0.3 의 붙여넣기용 프롬프트)

> 아래 ``` 블록을 새 세션에 그대로 붙여넣는다. 자기완결이다.
> 정본 참조(읽지 않아도 됨): `docs/superpowers/plans/2026-08-29-mode-1-5-term-benchmark.md` Phase 0

이 핸드오프는 **Task 0.1 하나**를 담는다. 0.2 와 0.3 은 0.1 이 끝난 뒤 같은 형식으로 오케스트레이터가 만든다 —
0.2 의 코드는 계획서 Task 0.2 에, 0.3 의 표는 계획서 Task 0.3 에 그대로 있다.

```
[ROLE]
당신은 $REPO_ROOT (브랜치 feat/report-builder) 의 구현 에이전트다.
목표: mode 별 bin 진입점 세 개가 공유할 디스패처 함수를 scripts/dispatch.mjs 로 분리한다.
이 Task 는 의도적으로 "연결 안 된 상태" 로 끝난다 — bin/* 을 고치는 것은 다음 Task(0.2) 다.
당신은 함수와 테스트만 만든다.

[HARD RULES]
- 커밋하지 않는다. git add 도 하지 않는다. 구현 + 검증 + 보고까지만. 커밋은 오케스트레이터가 사용자 승인 후 한다.
- TDD 를 지킨다. 순서: 실패하는 테스트 작성 → 실패 확인 → 최소 구현 → 통과 확인. 순서를 바꾸지 않는다.
- 주석은 한국어. 기술 용어는 영문 병기 가능.
- scripts/*.mjs 규약: import 시에는 순수 함수만 노출한다. 부수효과(process.exit 등)는 함수 안에 두고, 모듈 최상위에서 실행하지 않는다.
- "검증됨" "입증" "증명" 이라는 단어를 쓰지 않는다.
- 이 저장소의 npm test 는 pretest 로 esbuild 번들을 만든 뒤 node --test 를 인자 없이 돌린다. `node --test test/` 처럼 디렉토리 인자를 주면 Node 25 에서 죽는다.

[BOUNDARIES]
- 당신이 소유하는 파일 = 정확히 2개: scripts/dispatch.mjs (신규), test/dispatch.test.mjs (신규).
- bin/report 는 건드리지 않는다 — Task 0.2 가 소유한다.
- scripts/build.mjs · scripts/check.mjs · scripts/init.mjs 를 건드리지 않는다 — Mode 2 의 완성된 부분이다.
- test/ 의 다른 파일을 건드리지 않는다.
- CLAUDE.md 를 건드리지 않는다 — Task 0.3 이 소유한다.

[VERIFIED FACTS — 2026-08-29 실측]
- bin/report 의 현재 디스패치 로직은 bin/report:10-22 에 있다. SCRIPTS 객체 + Object.hasOwn 검사 + spawnSync. 당신이 만드는 함수는 이것을 일반화한 것이다.
- 기존 테스트 파일은 test/check.test.mjs · components.test.mjs · init.test.mjs · svg.test.mjs 4개. 44개 테스트가 통과 중이다.
- 테스트 파일 규약(test/check.test.mjs:1-3 참고): `import { test } from "node:test"; import assert from "node:assert/strict";` 로 시작한다.
- 이 보고를 믿지 말고 시작 전에 `git log --oneline -1` 과 `npm test` 로 상태를 재확인하라. HEAD 는 dccced5 여야 한다.

========================================================================
[STEP 1] 실패하는 테스트를 쓴다 — test/dispatch.test.mjs

import { test } from "node:test";
import assert from "node:assert/strict";
import { resolveScript } from "../scripts/dispatch.mjs";

test("resolveScript 는 등록된 명령을 스크립트 경로로 바꾼다", () => {
  const table = { init: "scripts/init.mjs", build: "scripts/build.mjs" };
  assert.equal(resolveScript(table, "init"), "scripts/init.mjs");
});

test("resolveScript 는 없는 명령에 null 을 낸다", () => {
  const table = { init: "scripts/init.mjs" };
  assert.equal(resolveScript(table, "nope"), null);
});

test("resolveScript 는 명령이 없으면 null 을 낸다", () => {
  assert.equal(resolveScript({ init: "x" }, undefined), null);
});

test("resolveScript 는 프로토타입 오염을 통과시키지 않는다", () => {
  assert.equal(resolveScript({ init: "x" }, "toString"), null);
});

[STEP 2] 실패를 확인한다
  실행: node --test test/dispatch.test.mjs
  기대: FAIL — Cannot find module '.../scripts/dispatch.mjs'
  (실패하지 않으면 무언가 잘못됐다. 멈추고 보고하라.)

[STEP 3] 최소 구현 — scripts/dispatch.mjs

// scripts/dispatch.mjs — mode 별 bin 진입점이 공유하는 디스패처.
// 각 bin 은 자기 명령표만 갖고 이 함수를 부른다.
import { spawnSync } from "node:child_process";
import { join } from "node:path";

/** 명령표에서 스크립트 상대경로를 찾는다. 없으면 null. */
export function resolveScript(table, cmd) {
  if (!cmd) return null;
  if (!Object.hasOwn(table, cmd)) return null;
  return table[cmd];
}

// 직접 실행 가드 — import 시에는 순수 함수만 노출한다(scripts/*.mjs 규약).
export function runDispatch({ root, table, argv, usage }) {
  const [cmd, ...rest] = argv;
  const script = resolveScript(table, cmd);
  if (!script) {
    console.error(usage);
    process.exit(1);
  }
  const r = spawnSync(process.execPath, [join(root, script), ...rest], { stdio: "inherit" });
  process.exit(r.status ?? 1);
}

[STEP 4] 통과를 확인한다
  실행: node --test test/dispatch.test.mjs
  기대: 4 tests, 4 pass

[STEP 5] 전체 회귀
  실행: npm test
  기대: ℹ tests 48 / ℹ pass 48 / ℹ fail 0   (기존 44 + 새 4)
  실행: npm run typecheck
  기대: 출력 없이 종료 (tsc --noEmit 통과)

========================================================================
[SELF-REVIEW — 보고 전에 확인]
- [ ] 테스트를 먼저 썼고 실패를 실제로 봤는가
- [ ] scripts/dispatch.mjs 의 모듈 최상위에 process.exit 이나 spawnSync 호출이 없는가 (함수 안에만)
- [ ] 소유 파일 2개 외에 아무것도 바꾸지 않았는가 (`git status --porcelain` 으로 확인)
- [ ] npm test 가 48/48 인가
- [ ] 커밋하지 않았는가

[REPORT — 이 형식으로]
상태: DONE | DONE_WITH_CONCERNS | BLOCKED
변경 파일: (경로 나열)
검증 출력: (npm test 마지막 8줄, npm run typecheck 결과)
미룬 것 / 우려: (없으면 "없음")
커밋: 하지 않았다 (확인)
```

## Notes (오케스트레이터용 — 펜스 밖)

- 돌아오면 `npm test` 를 **직접 다시 돌려** 48/48 을 눈으로 확인한다. 보고를 믿지 않는다.
- 통과하면 사용자에게 커밋 승인을 묻는다. 권장 메시지:
  `[refactor] : mode 별 bin 이 공유할 디스패처를 함수로 분리`
  경로 범위: `git add scripts/dispatch.mjs test/dispatch.test.mjs` (`-A` 금지)
- 커밋 후 **L1 세 개(0.2 · 1.1 · 2.1)를 한 메시지에서 동시에** 띄운다. 0.2 프롬프트는 이 문서와 같은 형식으로,
  코드는 계획서 Task 0.2 Step 1~4 를 통째로 복사한다. `[VERIFIED FACTS]` 에 "scripts/dispatch.mjs 가 이제 존재하며
  runDispatch({root, table, argv, usage}) 를 export 한다" 를 추가한다.
- 0.2 의 `[VERIFY]` 는 계획서 Task 0.2 Step 6 그대로 — `report check` 와 `report-spec check` 가 같은 4줄을 내는지.
