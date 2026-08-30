// <include file="machine/comments.xml" path="//term[@id='lib.mjs']"/>
// 테스트가 읽을 수 있도록 src 를 한 덩이로 묶는 스크립트.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
// viz/lib.mjs
// viz/src/ 를 .tmp/lib.mjs 로 번들한다. test/ 가 이것을 import 한다.
// node --test 는 JSX 를 해석하지 못하므로 이 단계가 필요하다.
import { build } from "esbuild";

await build({
  entryPoints: ["viz/src/index.ts"],
  bundle: true,
  format: "esm",
  platform: "node",
  target: "node22",
  jsx: "automatic",
  external: ["react", "react-dom", "react/jsx-runtime"],
  outfile: ".tmp/lib.mjs",
  logLevel: "warning",
});

console.log(".tmp/lib.mjs 빌드 완료");
