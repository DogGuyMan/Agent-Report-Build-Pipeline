// scripts/lib.mjs
// src/ 를 .tmp/lib.mjs 로 번들한다. test/ 가 이것을 import 한다.
// node --test 는 JSX 를 해석하지 못하므로 이 단계가 필요하다.
import { build } from "esbuild";

await build({
  entryPoints: ["src/index.ts"],
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
