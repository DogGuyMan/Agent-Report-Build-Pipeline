// <include file="docs/codegraph/comments.xml" path="//term[@id='patch-legacy.mjs']"/>
// 옛 HTML 보고서에 새 스타일과 확대 토글을 덧대 보던 일회용 스크립트.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
// scripts/patch-legacy.mjs
// Phase 1 검증 전용 — 기존 정본 HTML의 <style> 블록을 src/theme.css 로 교체하고
// .diagram-grid 앞에 zoom 토글 마크업을 삽입한다.
// 이후 정식 파이프라인이 재생성하면 이 스크립트는 제거 대상이다.
import { readFileSync, writeFileSync } from "node:fs";
import { basename } from "node:path";

const theme = readFileSync(new URL("../src/theme.css", import.meta.url), "utf8");

for (const file of process.argv.slice(2)) {
  let html = readFileSync(file, "utf8");

  const start = html.indexOf("<style>");
  const end = html.indexOf("</style>");
  if (start === -1 || end === -1) throw new Error(`<style> 블록 없음: ${file}`);
  html = html.slice(0, start) + "<style>\n" + theme + "\n    </style>" + html.slice(end + "</style>".length);

  let n = 0;
  html = html.replaceAll('<div class="diagram-grid">', () => {
    const id = `zoom-${++n}`;
    return `<input type="checkbox" class="zoom-toggle" id="${id}">`
      + `<label class="zoom-label" for="${id}"></label>`
      + `<div class="diagram-grid">`;
  });
  if (n === 0) throw new Error(`.diagram-grid 없음: ${file}`);

  // width/height 속성 제거 + --svg-w 주입
  let svgIdx = 0;
  html = html.replace(/<svg\s+width="([\d.]+)pt"\s+height="([\d.]+)pt"/g, (_, w, h) => {
    svgIdx++;
    const px = Math.round(Number(w) * 4 / 3);
    return `<svg style="--svg-w:${px}px"`;
  });

  const out = file.replace(/\.html$/, ".b1.html");
  writeFileSync(out, html);
  console.log(`${basename(out)} — 토글 ${n}개, SVG ${svgIdx}개`);
}
