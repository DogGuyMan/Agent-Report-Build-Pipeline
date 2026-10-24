<!-- section: batch -->
너는 코드베이스 전수조사의 배치 {{bid}} 담당이다. 대상 저장소 {{repo}}. 도구 저장소 {{root}}.
사람에게 묻지 않는다 — 이 세션은 헤드리스라 되묻는 순간 막힌다. 막히면 무엇이 없어 막혔는지 적고 끝낸다.

## 너보다 아래층은 이미 끝났다 — 다시 조사하지 마라

{{deps}}

## 네가 맡은 심볼 {{n}}개 — 이것만 한다

{{syms}}

## 읽는 법 — 순서를 지킨다

1. 담당 파일마다 통독 캐시를 먼저 본다:
     {{root}}/.venv/bin/python {{root}}/machine/file_cache.py get {{repo}} <파일경로>
   - 있으면: 개요를 읽고 **네 심볼의 줄 범위만** 실제로 연다.
   - 없으면: 파일을 통독하고, 끝나면 개요를 **JSON 파일로 먼저 쓴 뒤** 그 경로를 넘긴다:
     {{root}}/.venv/bin/python {{root}}/machine/file_cache.py put {{repo}} <파일경로> <개요json의_파일경로>
     넷째 인자는 JSON 문자열이 아니라 **파일 경로**다. 문자열을 넣으면 죽는다.
     개요 꼴 — 심볼마다 {name, kind, line, end_line, signature, one_line} 에
     파일의 imports 와 head_comment 를 더한 객체.
2. **네 심볼은 캐시로 때우지 않는다.** 반드시 그 줄 범위를 실제로 읽는다.
   캐시는 남의 심볼을 uses[].to 로 가리킬 때만 쓴다.

## 레코드 계약

{kind, module, where, means, does, uses[], confidence, source:"reading"}
정확한 꼴은 {{repo}}/out/codegraph-raw/record-schema.json (읽기 전용 JSON Schema, examples 에 견본) 이다.
칸을 빼거나 어휘 밖의 값을 쓰면 기계가 그 샤드를 통째로 되돌린다 — 네 배치가 없던 일이 된다.
- where = `경로:줄` (필수. 기계가 L1 파일 / L2 줄 / L3 근처에 이름 으로 검사한다)
- means = 무엇인가, 한 문장. **객체지향을 갓 배운 대학 1학년 눈높이.** 어려운 용어로 설명하지 않는다
- does  = 무엇을 하는가, 한두 문장
- uses[] = {to, kind, label, where}. kind 는 dependency inheritance aggregation composition
  association realization 중 하나
- **uses[].to 는 이 저장소 안 심볼의 레코드 키다** — 위 심볼 목록과 아래층 발췌에 적힌 이름 **그대로**.
  `C218` 같은 id 나 `GraphNode` 같은 짧은 이름을 쓰지 않는다. 표준 라이브러리·서드파티
  (`subprocess.run`, `networkx`)는 uses 에 넣지 않는다 — 기계가 떼어 내고 기록만 남긴다.
- confidence = HIGH(코드를 읽고 썼다) / MEDIUM(일부 읽고 나머지는 추론) / LOW(이름·구조에서 추론)
  **전부 HIGH 로 적으면 그 칸이 장식이 된다.**

## 금지 — 이 말이 떠오르면 멈추고 읽는다

  "이건 아마 …할 것이다"  -> 그 함수를 열어 실제로 무엇을 하는지 적는다
  "이름으로 보아 …"       -> 이름은 거짓말한다. 구현을 확인한다
  "보통 이런 건 …"        -> 이 코드베이스를 읽는다. 관례에 대지 않는다
  "…에 연결될 것 같다"    -> import 나 호출을 실제로 따라간다
  "읽지 않았지만 …"       -> confidence LOW 로 적거나 아예 쓰지 않는다

## 쓰는 곳 — 여기 말고 아무 데도 쓰지 않는다

  {{repo}}/out/codegraph-raw/_shards/{{bid}}.json      꼴은 {"키": 레코드}

**terms-reading.json 을 열지도 고치지도 않는다.** 지금 다른 배치들이 동시에 돌고 있다.
키가 다른 파일과 겹칠 것 같아도 **네가 고치지 않는다** — 층이 끝날 때 일괄 해소된다. 보고에 적기만 한다.
**커밋하지 않는다.**

## 끝내기 전에

- 심볼 {{n}}개에 레코드가 {{n}}개 있는가
- where 의 줄 번호를 실제로 열어 확인했는가
- confidence 가 전부 HIGH 는 아닌가
- 샤드 파일 하나만 만들었는가
- **기계 검문을 통과했는가** — 다음을 돌려 `통과` 가 나올 때까지 고친다. 통과 전에는 끝내지 않는다:
    {{root}}/.venv/bin/python {{root}}/runner/check_shard.py {{repo}}/out/codegraph-raw/_shards/{{bid}}.json
  (JSON 문법 · 필수 칸 · 어휘 · where 를 본다. 이것이 층 끝 검문과 같은 검사기다)

보고: 레코드 수 · confidence 분포 · 통독한 파일과 캐시로 때운 파일 · 키 충돌 후보 · 읽지 못한 것과 이유.

<!-- section: batch-symbol -->
  - {{name}} ({{kind}}) {{file}}:{{line}}   의존 -> {{deps}}

<!-- section: batch-symbol-no-deps -->
없음

<!-- section: batch-dep -->
  - {{name}} — {{means}}

<!-- section: batch-dep-no-means -->
(뜻 없음)

<!-- section: batch-no-deps -->
  (없음 — 너는 최하층이다)

<!-- section: scope -->
## 범위 — 증분 조사다. 저장소 전량을 읽지 마라

지난 조사 결과가 {{reading}} 에 이미 있다. 그중
**아래 {{count}}개 파일에 걸린 레코드만** 다시 만든다. 추적 파일 {{total}}개 중 {{count}}개다.

{{targets}}

- **이 목록에 없는 파일은 읽지 마라.** 나머지 레코드는 그대로 살아 있고, 손대면 안 된다.
- 목록 밖의 이름이 필요하면 소스가 아니라 **기존 terms-reading.json 과 codegraph.json**
  을 근거로 쓴다.
- 목록의 파일이 사라졌거나 읽을 수 없으면 **지어내지 말고** 보고에 적는다.

<!-- section: pending -->
## 아직 조사되지 않은 의존 대상 — 열지 마라

{{pending}}

이것들의 모듈을 **열지 않는다.** 이름·종류·시그니처(호출 자리에서 보이는 것)만으로 **얕게** 쓴다.
그렇게 쓴 레코드에는 `"shallow": ["위 목록의 이름 그대로"]` 을 적는다 — 기계가 모아 두었다가, 그 대상이 조사된 뒤
**너 대신 다른 세션이** does 와 uses[].label 을 다듬는다. means 와 where 는 네 코드만 보면 되니 지금 정확히 쓴다.
뜻을 지어내지 마라 — does 에는 코드에서 보이는 사실만.

<!-- section: retry -->
## 지난 시도가 되돌려졌다 — 같은 실수를 하지 마라

이 배치는 한 번 돌았고, 기계 검문이 그 샤드에서 결함 {{count}}개를 찾아 되돌렸다:

{{faults}}

- 되돌린 샤드는 {{bad}} 에 그대로 있다. **결함의 자리를 열어 무엇이 깨졌는지 먼저 본다.**
- 읽은 내용을 다시 쓰되, **끝내기 전에 검문 명령을 반드시 돌려 `통과` 를 본다.**

<!-- section: nonnode -->
너는 코드베이스 전수조사의 **마지막 층** 담당이다. 대상 저장소 {{repo}}. 도구 저장소 {{root}}.
사람에게 묻지 않는다 — 헤드리스 세션이다. 막히면 무엇이 없어 막혔는지 적고 끝낸다.

## 심볼은 이미 전부 끝났다

  {{reading}}   앞선 층들이 합쳐 놓은 심볼 레코드

이 파일을 **읽기만** 한다. 고치지 않는다.

## 네가 맡은 것 — 코드 지도의 노드가 아닌 용어 다섯 종류

| kind | 무엇 | where 는 어디 |
|---|---|---|
| `file` | 소스 파일 하나 | `경로:1` |
| `module` | 디렉토리 하나 | 없어도 된다 |
| `artifact` | 이 저장소가 **만들어 내는** 파일 | 그 파일을 **쓰는** 줄 |
| `key` | 설정·JSON 의 이름난 칸 | 그 키를 **채우는** 줄 |
| `concept` | 코드에 글자로 있는 낱말 | 그 낱말이 있는 줄 |

**`file` `module` `artifact` `key` `concept` 는 이름이 그 줄에 글자 그대로 있어야 한다** —
기계가 L3(근처에 그 이름) 으로 검사한다.

`file` 레코드는 **그 파일 안 심볼들의 완성된 means/does 를 재료로** 쓴다. 다시 통독하지 않는다.
`concept` 은 **코드에 글자로 없는 것을 만들지 않는다** — 계획서에만 있는 개념은 여기 싣지 않는다.

## 금지 — 이 말이 떠오르면 멈추고 읽는다

  "이건 아마 …할 것이다"  -> 그 자리를 열어 실제로 무엇을 하는지 적는다
  "이름으로 보아 …"       -> 이름은 거짓말한다. 구현을 확인한다
  "보통 이런 건 …"        -> 이 코드베이스를 읽는다. 관례에 대지 않는다
  "읽지 않았지만 …"       -> confidence LOW 로 적거나 아예 쓰지 않는다

## 레코드 계약과 쓰는 곳

{kind, module, where, means, does, uses[], confidence, source:"reading"} 이고
정확한 꼴은 {{repo}}/out/codegraph-raw/record-schema.json (읽기 전용 JSON Schema) 이다.
칸을 빼거나 어휘 밖의 값을 쓰면 기계가 이 샤드를 통째로 되돌린다.
쓰는 곳은 **여기 하나뿐**이다:

  {{repo}}/out/codegraph-raw/_shards/NONNODE.json      꼴은 {"키": 레코드}

**terms-reading.json 을 고치지 않는다. 커밋하지 않는다.**

끝내기 전에 기계 검문을 돌려 `통과` 가 나올 때까지 고친다:
  {{root}}/.venv/bin/python {{root}}/runner/check_shard.py {{repo}}/out/codegraph-raw/_shards/NONNODE.json

보고: 종류별 레코드 수 · confidence 분포 · 근거를 못 찾아 뺀 것과 이유.

<!-- section: pass2 -->
너는 코드베이스 전수조사의 **2패스** 담당이다. 대상 저장소 {{repo}}. 도구 저장소 {{root}}. 파일 {{file}}.
사람에게 묻지 않는다 — 헤드리스 세션이다.

## 소스를 열지 않는다

이 세션은 파일을 **읽지 않는다.** 1패스가 이 파일을 이미 읽었다. 네가 받은 것은 둘뿐이다:

### 1패스가 얕게 쓴 레코드 (의존 대상의 뜻을 모른 채 썼다)

{{mine}}

### 그 의존 대상들 — 이제 조사가 끝났다

{{theirs}}

## 할 일

레코드마다 `does` 와 `uses[].label` 을 **의존 대상의 뜻을 알게 된 지금** 다시 쓴다.
`means` `where` `kind` `confidence` 와 `uses[].to` `uses[].where` 는 그대로 둔다. `shallow` 칸은 **뗀다.**
새 레코드를 만들지 않는다 — 받은 키만 낸다.

## 쓰는 곳 — 여기 하나뿐

  {{repo}}/out/codegraph-raw/_shards/_pass2/{{bid}}.json      꼴은 {"키": 레코드}

정확한 꼴은 {{repo}}/out/codegraph-raw/record-schema.json 이다. 끝내기 전에 검문한다:
  {{root}}/.venv/bin/python {{root}}/runner/check_shard.py {{repo}}/out/codegraph-raw/_shards/_pass2/{{bid}}.json

<!-- section: pass2-dep -->
  - {{name}} — {{means}} / {{does}}

<!-- section: pass2-no-deps -->
  (없음)

<!-- section: fix-missing -->
샤드 파일이 없다. 지정된 자리에 {"키": 레코드} 꼴로 하나 만든다.

<!-- section: fix-malformed -->
JSON 문법이 깨졌다. 그 바이트 자리를 연다 — 문자열 안 따옴표는 \" 로, 줄바꿈은 \n 으로 쓴다.

<!-- section: fix-schema -->
필수 칸이 빠졌거나 어휘 밖의 값이다. record-schema.json 의 required 와 enum 에 맞춘다.

<!-- section: fix-where -->
where = `경로:줄` 을 넣는다. module 과 external 만 생략할 수 있다.

<!-- section: fix-coverage -->
네 배치의 심볼 목록과 샤드의 키를 하나씩 대조한다. 빠진 것은 읽어 넣고, 목록 밖의 것은 뺀다.
