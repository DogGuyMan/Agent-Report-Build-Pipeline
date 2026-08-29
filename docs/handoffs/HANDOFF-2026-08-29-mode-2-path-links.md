# HANDOFF ⑩ — Mode 2 경로 링크 (mode-2-spec-report 용 프롬프트)

> 🔴 **완료됨 (2026-08-29 16:30).** `mode-2-spec-report` DONE_WITH_CONCERNS — 우려 2건(해석 순서 · `facts/*.md` 가 SVG 안에만 있음). 오케스트레이터 재검증(npm test 85/85 · 두 보고서 check 5/5 · 누출 0 · 없는 파일 링크 0) 뒤 사용자 결정 2건을 반영 — **새 탭**(`target=_blank rel=noopener`) · **linkRoots 를 저장소 기본 폴더보다 앞에**. 커밋 `f92cb7d`. 진입점은 `RESUME-2026-08-29-mode-1-5-orchestrator.md` 다.

**사용자 지시 (2026-08-29 15:55)** — "`facts/*.md` · `docs/handoffs/HANDOFF-codebase-wiki.md:900` · `facts/calls.md` · `…-design.md:1032` · `HANDOFF-codebase-wiki.md` 같은 것을
실제 웹 브라우저에서 로컬 디렉토리 탐색할 수 있도록 링킹해라." 사용자 확정 — **파일은 파일, 글로브는 폴더, `file://`**. 줄 번호는 글자로 남긴다.
🔵 실측 — llm 보고서 경로 꼴 46회(27종), mode-1 140회(31종). 설계 문서 인용(`…-design.md:NNN`)이 대다수이고 `docs/superpowers/specs/` 에 있다.

**설계** — 자동 참조 다음에 **경로 링크 통과** `scripts/link-paths.mjs` 를 하나 더. 용어(`term-ref`) 안은 건너뛰고 `.mono` 안은 **포함**(용어 = 뜻 카드, 코드 글꼴 = 파일 링크).
해석 순서: 보고서 폴더 → `specs/` → 저장소 루트 → `<루트>/out/codegraph-raw` → `data.linkRoots`(선택, 외부 저장소) → `git ls-files` 이름 유일 검색. **없는 파일은 링크하지 않는다.**
`ReportData.linkRoots?: string[]` 추가(추가만). llm 보고서 `data.ts` 에 StickRush `out/codegraph-raw` 를 linkRoots 로 — 그 Plan 의 `facts/*.md` `codegraph.json` 이 거기 있다.

프롬프트 본문은 오케스트레이터 세션의 Agent 호출과 같다 — 7블록. 소유: `scripts/link-paths.mjs`(신규) · `test/link-paths.test.mjs`(신규) · `scripts/build.mjs` · `src/types.ts`(필드 추가만) · `src/theme.css`(추가만) · `docs/superpowers/specs/llm-load-reduction/data.ts`(`linkRoots` 한 줄만).
