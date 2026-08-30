// <include file="machine/comments.xml" path="//term[@id='runner/wiki/paths.mjs']"/>
// 위키 세 명령이 함께 보는 경로 규약.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
// Mode 1 위키의 경로 규약 한 곳. prep · build · check 세 명령이 전부 이것만 본다.
// 순수 함수만 노출한다 — CLI 본체가 없으므로 직접 실행 가드도 없다.
import { join } from "node:path";

// <include file="machine/comments.xml" path="//term[@id='wikiPaths']"/>
// 대상 저장소 하나의 여러 경로를 한 덩이로 만든다.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
/**
 * 대상 저장소 하나에 대한 경로 규약.
 *
 * W1 — 산문(`wiki`)은 대상 저장소의 **추적 경로**에 산다. LLM 이 쓴 원고이기 때문이다.
 * W3 — 파생물(`raw`·`built`·`site`)은 `out/` 아래에 둔다. 결정론으로 재생성되므로 추적하지 않는다.
 */
export function wikiPaths(repo) {
  const raw = join(repo, "out", "codegraph-raw");
  return {
    repo,
    raw,
    wiki: join(repo, "docs", "wiki"),
    built: join(raw, "wiki-built"),
    site: join(raw, "wiki-site"),
    codegraph: join(raw, "codegraph.json"),
  };
}

// <include file="machine/comments.xml" path="//term[@id='collectorFor']"/>
// 저장소 최상위를 보고 어느 정적 수집기를 쓸지 고른다.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
/**
 * 저장소 최상위 항목 목록을 보고 정적 수집기를 고른다.
 *
 * 수집기는 2종 고정이다 — 레지스트리를 만들지 않는다(거울 함정).
 * C# 을 먼저 보는 이유: Unity 저장소는 네이티브 플러그인 때문에 `CMakeLists.txt` 를
 * 함께 가질 수 있으나, 사용자 코드는 `.cs` 다.
 */
export function collectorFor(entries) {
  const has = (suffix) => entries.some((f) => f.endsWith(suffix));
  if (has(".csproj") || has(".slnx") || has(".sln")) return "roslyn-dump";
  if (entries.includes("CMakeLists.txt")) return "clang-uml";
  return "none";
}
