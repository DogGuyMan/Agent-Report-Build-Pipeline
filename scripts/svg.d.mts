// scripts/svg.mjs 의 타입 선언.
// svg.mjs 는 순수 JavaScript 라 strict 모드에서 implicit any 가 된다.
// tsconfig paths 가 "report-builder/svg" 를 svg.mjs 로 보내므로
// TypeScript 는 같은 이름의 .d.mts 를 declaration 으로 집는다.
import type { InlinedSvg } from "../src/types.js";

export declare function inlineSvg(raw: string, idPrefix: string): InlinedSvg;
