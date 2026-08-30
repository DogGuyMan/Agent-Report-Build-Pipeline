// <include file="machine/comments.xml" path="//term[@id='dispatch.mjs']"/>
// bin 진입점들이 같이 쓰는 명령 갈림길.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
// runner/dispatch.mjs — mode 별 bin 진입점이 공유하는 디스패처.
// 각 bin 은 자기 명령표(table)만 갖고 이 함수를 부른다.
import { spawnSync } from "node:child_process";
import { join } from "node:path";

/** 명령표에서 스크립트 상대경로를 찾는다. 없으면 null. */
export function resolveScript(table, cmd) {
  if (!cmd) return null;
  // Object.hasOwn — 프로토타입 체인(toString 등)을 명령으로 오인하지 않는다.
  if (!Object.hasOwn(table, cmd)) return null;
  return table[cmd];
}

// 부수효과(process.exit · spawnSync)는 이 함수 안에만 둔다.
// import 시에는 순수 함수만 노출한다(러너·시각축 .mjs 규약).
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
