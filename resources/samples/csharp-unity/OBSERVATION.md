# 관찰 보고서 — StickRushGame / C# (Unity)

> 이 파일은 `docs/handoffs/templates/OBSERVATION-template.md` 의 사본이다.
> **절 번호와 제목을 바꾸지 말 것.** C++ 쪽 보고서와 C# 쪽 보고서가 같은 골격이어야
> `normalize.py` 의 파서 두 개를 나란히 놓고 설계할 수 있다.
> 채울 수 없는 칸은 **지우지 말고 `미확인` 또는 `해당 없음` 으로 남긴다.** 빈칸 자체가 정보다.

작성일: 2026-08-27
저장소 경로: `$CSHARP_REPO` (inode `255626426`)
`repo_commit`: `c0a610f`
작성자 세션: Claude Code Agent (`HANDOFF-unity-pattern-collection.md` 수행)

> ⚠ **핸드오프 머리말의 전제 두 가지가 실측과 달랐다. 먼저 읽어야 한다.**
>
> **(1) 사본이 둘인데 내용이 다르다.** 핸드오프는 두 사본이 커밋(`e681003`)과 미커밋 변경 수(1,001건)가
> 같다고 적었으나, 이 세션에서 다시 재니 **Unity 버전 자체가 다르다.**
>
> | | `$DEV_ROOT/StickRushGame` | `$CSHARP_REPO` (이 보고서) |
> |---|---|---|
> | inode | 255288162 | 255626426 |
> | Unity | **2022.3.30f1** | **6000.0.71f1** |
> | HEAD | `e681003` | `c0a610f` |
> | 미커밋 | 1,001건 | 0건 |
> | 추적 `.asset` | 211개 | 213개 |
>
> **이 보고서의 모든 수치는 `UnityProjects/StickRushGame` = Unity 6000.0.71f1 기준이다.**
>
> **(2) 수집 도중 HEAD 가 바뀌었다.** 세션 시작 시점 `git rev-parse --short HEAD` 는 `e681003`,
> 미커밋 1,045건이었다. 단계 1 을 마친 직후 다시 재니 `c0a610f`, 미커밋 0건이었다.
> `git reflog` 를 보면 **사용자 본인이 2026-08-27 04:18:26 에 `[update] : 6000` (1,043 files
> changed, 323,818 insertions) 을 커밋했다.** 이 세션은 커밋하지 않았다.
> 따라서 단계 1 부터 다시 측정했고, 아래 계량은 전부 `c0a610f` 기준이다.
>
> **(3) 그 커밋이 핸드오프 §1 의 결론 (가) 를 뒤집었다.** `.csproj` 도 `.sln` 도 없다던 전제가
> 더는 성립하지 않는다. `StickRushGame.slnx` 가 **추적되고 있고**(`.gitignore` 의 `*.sln` 은
> `.slnx` 를 걸러내지 못한다), 작업 트리에 `.csproj` 135개와 `Library/ScriptAssemblies/*.dll`
> 147개가 실재한다. 그래서 **단계 3 의 Unity 배치 모드 실행은 하지 않았다** — 핸드오프 단계 3 의
> "작업 트리에 이미 있으면 그것을 쓰고 이 단계를 건너뛴다" 에 해당한다.

---

## A. 환경 실측

실제로 실행한 명령과 그 출력만 적는다. "설치돼 있을 것이다" 를 적지 않는다.

| 도구 | 확인 명령 | 출력 | 비고 |
|---|---|---|---|
| Unity 에디터 버전 | `cat ProjectSettings/ProjectVersion.txt` | `m_EditorVersion: 6000.0.71f1` / `m_EditorVersionWithRevision: 6000.0.71f1 (907bc2d768b5)` | 핸드오프 기재값 2022.3.30f1 은 **다른 사본**의 값 |
| Unity 설치 실재 | `ls /Applications/Unity/Hub/Editor/6000.0.71f1/Unity.app/Contents/Managed/UnityEngine/` (csproj HintPath 378개 전수 존재 확인) | 378/378 존재, 누락 0 | 관리 DLL 경로가 실재. 배치 모드는 **실행하지 않았다** |
| dotnet SDK | `dotnet --version` | `9.0.200` | |
| dotnet SDK 전체 | `dotnet --list-sdks` | `6.0.420`, `8.0.202`, `9.0.100`, `9.0.200` | |
| Roslyn | `dotnet add package Microsoft.CodeAnalysis.CSharp` | `5.9.0` 설치 성공 | NuGet 접속 정상 |
| git | `git rev-parse --short HEAD` | `c0a610f` | 세션 시작 시엔 `e681003` (위 머리말 참조) |

**설치가 필요했던 것:**
`Microsoft.CodeAnalysis.CSharp` 5.9.0 (NuGet). 그 외 설치 없음.
`Microsoft.Build.Locator` / `MSBuildWorkspace` 는 핸드오프 지시대로 **쓰지 않았다.**

---

## B. 산출물 목록

`out/codegraph-raw/` 에 실제로 생긴 파일 전량이다.
경로: `$CSHARP_REPO/out/codegraph-raw/`

| 파일 | 크기(바이트) | 생성 명령 | 소요 시간 |
|---|---|---|---|
| `00-commit.txt` | 455 | `git rev-parse` + `pwd` + `ls -di` | 즉시 |
| `00-copy-compare.txt` | 507 | 두 사본의 `ProjectVersion.txt` / HEAD / 파일수 대조 | 즉시 |
| `00-env.txt` | 1,540 | 핸드오프 단계 1 명령 + `.slnx` / `ScriptAssemblies` 항목 추가 | 즉시 |
| `01-asmdef.txt` | 11,106 | `git ls-files -z '*.asmdef' \| while read -d '' f; do cat "$f"; done` | 즉시 |
| `01-folders.txt` | 745 | `git ls-files 'Assets/@Scripts/*.cs' \| awk -F/ '{print $3}' \| uniq -c` | 즉시 |
| `01-namespaces.txt` | 1,247 | `xargs grep -h '^ *namespace '` + 중괄호 정규화 집계 | 즉시 |
| `02-Assembly-CSharp.csproj.txt` | 120,532 | `cp Assembly-CSharp.csproj` | 즉시 |
| `02-StickRushGame.slnx.txt` | 1,252 | `cp StickRushGame.slnx` | 즉시 |
| `02-csproj-summary.txt` | 5,207 | `grep` 으로 TargetFramework / Compile / Reference / ProjectReference 집계 | 즉시 |
| `02-csproj-compile-map.txt` | 8,539 | python3 로 `<Compile Include>` 를 csproj 별로 매핑 | 즉시 |
| `03-symbols.txt` | 2,005 | `dotnet run` (probe) | 컴파일 포함 약 20초 |
| `03-relations.txt` | 1,106 | `dotnet run` (probe) | 동상 |
| `03-diagnostics.txt` | 4,334 | `dotnet run` (probe, 세 모드 전부) | 동상 |
| `03-lineverify.txt` | 3,020 | `sed -n '<line>p'` 로 심볼 10건 + 간선 4건 육안 대조 | 즉시 |
| `04-unity-dynamic.txt` | 1,044 | 핸드오프 단계 5 명령 원문 + `grep -o` 보강 | 즉시 |
| `04-roslyn-unity.txt` | 1,226 | `dotnet run` (probe) — 정규식 하한 vs Roslyn 실측 대조 | 동상 |
| `04-prefab-sample.yaml` | 5,793 | `sed -n` 발췌 3구간 + GUID→파일 해석 주석 | 즉시 |
| `04-yaml-wiring-scan.txt` | 1,022 | python3 로 `.prefab`/`.unity` 전수 GUID·`m_MethodName` 계수 | 약 6초 |
| `07-external-touch.txt` | 533 | `dotnet run` (probe) — 사용자 코드가 닿는 외부 어셈블리 계수 | 동상 |
| `07-external-collapse.txt` | 1491 | python3 로 어셈블리→패키지 매핑 | 즉시 |
| `07-external-nodes.tsv` | 1114 | C-9 R1~R4 를 적용해 접은 최종 외부 노드 목록 | 즉시 |
| `06-packages.txt` | 3343 | python3 로 `manifest.json`/`packages-lock.json` 파싱 + 어셈블리→패키지 축약비 계산 | 즉시 |
| `05-counts.txt` | 455 | `dotnet run` (probe) — 구문 수준 전체/사용자코드 계수 | 약 8초 |
| `probe-sources.txt` | 12,740 | `Assembly-CSharp.csproj` 의 `<Compile Include>` 중 `Assets/@` 만 | 즉시 |
| `probe-refs.txt` | 49,071 | `<HintPath>` 378개 + `<ProjectReference>` 대상 DLL 17개 | 즉시 |
| `probe-defines.txt` | 3,064 | `<DefineConstants>` 137개를 `;` 로 분리 | 즉시 |
| `probe-all-sources.txt` | 225,891 | `git ls-files 'Assets/*.cs'` (1,713개) | 즉시 |
| `probe/Program.cs` | 10,351 | 직접 작성 (**152줄**) | — |
| `probe/probe.csproj` | 353 | `dotnet new console` | 즉시 |

**생성에 실패한 것과 그 오류 메시지 원문:**

없다. 다만 **중간에 두 번 잘못 만들었다가 고쳤다.** 둘 다 원인과 함께 H절에 적었다.

1. `01-asmdef.txt` 첫 시도에서 경로에 공백이 있는 `Assets/PlayerPrefsEditor/Editor Resources/...asmdef`
   때문에 따옴표 없는 `for f in $(git ls-files ...)` 가 깨졌다. 오류 원문:
   ```
   cat: Assets/PlayerPrefsEditor/Editor: Is a directory
   cat: Resources/Unity.PlayerPrefsEditor.EditorResources.asmdef: No such file or directory
   ```
   `git ls-files -z` + `while IFS= read -r -d ''` 로 고쳤다. 최종 파일은 20개 블록 전부 온전하다.

2. `.gitignore` 에 `printf 'out/codegraph-raw/\n' >> .gitignore` 를 했는데, 원래 파일 끝에
   개행이 없어 마지막 줄과 붙어 `.DS_Storeout/codegraph-raw/` 가 됐다. 즉시 되돌려
   `.DS_Store` 와 `out/codegraph-raw/` 두 줄로 복구했다. 현재 diff 는 아래가 전부다.
   ```
   -.DS_Store
   \ No newline at end of file
   +.DS_Store
   +out/codegraph-raw/
   ```

---

## C. 레코드 형태 표본

**도구가 낸 원문을 그대로 붙인다.** 요약·정리·이름 바꾸기 금지. `normalize.py` 의 파서는
이 표본을 보고 쓰이므로, 손댄 표본은 파서를 틀리게 만든다.

종류마다 **1건씩만** 붙인다. 길면 배열 원소 하나만 잘라 붙이고 잘랐다고 명시한다.

> ⚠ 아래 레코드의 **형식은 도구가 정한 것이 아니라 이 세션의 probe 가 정한 것이다.**
> Roslyn 은 `IAssemblySymbol` / `INamedTypeSymbol` 객체를 줄 뿐 직렬화 형식이 없다.
> C++ 쪽(`cmake --graphviz`, Doxygen XML)과 결정적으로 다른 점이며, I절에서 다시 다룬다.
> 구분자는 탭이다.

### C-1. 노드에 해당하는 레코드

`out/codegraph-raw/03-symbols.txt` 원문 (머리 3줄 + 레코드 1건):

```
# Roslyn 5.9.0.0  mode=C(Unity 참조 395개만)  LangVersion=9.0  defines=137
# 소스 112개에 선언된 named type 총 214개. 아래는 앞에서 20개.
# name	kind	file:line
AddressableRenamer	Class	Assets/@Editors/AddressableRenamer.cs:9
```

`kind` 는 Roslyn 의 `INamedTypeSymbol.TypeKind` 원문이다. 이 저장소에서 실제로 나온 값은
`Class`, `Enum`, `Interface`, `Struct` 네 가지다.

### C-2. 간선에 해당하는 레코드 — 종류별로 전부

`out/codegraph-raw/03-relations.txt` 원문. 머리 3줄:

```
# mode=C. 집계 — inherit=64(해석실패 0)  realize=70(해석실패 0)  assoc/field=285(해석실패 0)  [enum 멤버 209건은 assoc 에서 제외]
# 그중 [SerializeField] 가 붙은 필드 = 27 (Roslyn 이 어트리뷰트로 실제 해석한 수)
# 간선 6종 중 이 시험이 실제로 낸 것: inherit, realize, assoc  /  안 나온 것: composition, aggregation, depend
```

종류별 원문 1건씩:

```
kind=inherit	src=AddressableRenamer	dst=UnityEditor.EditorWindow	dstAsm=UnityEditor.CoreModule	at=Assets/@Editors/AddressableRenamer.cs:9
kind=realize	src=Gamerecipe.StickRush.BaseScene	dst=Gamerecipe.StickRush.ISceneNameAccessor	dstAsm=Probe	at=Assets/@Scripts/Utils/BaseScene.cs:8
kind=assoc	src=AddressableRenamer	field=groupNames	dst=string[]	dstAsm=	attrs=[]	at=Assets/@Editors/AddressableRenamer.cs:11
kind=assoc	src=Gamerecipe.StickRush.Data.ScriptableFoodCells	field=_foodCells	dst=System.Collections.Generic.List<Gamerecipe.StickRush.Data.SerialDataFood>	dstAsm=netstandard	attrs=[SerializeField]	at=Assets/@Scripts/Data/DataFood/ScriptableFoodCells.cs:11
```

`dstAsm` 은 대상 타입이 사는 어셈블리다. `Probe` 는 이 시험이 만든 컴파일 자신 = **사용자 코드**,
그 외(`UnityEditor.CoreModule`, `netstandard`, …)는 전부 외부다. 서드파티 필터링의 실마리다.
`dstAsm=` 이 빈 것은 `string[]` 같은 배열 타입으로, `IArrayTypeSymbol` 에는
`ContainingAssembly` 가 없다.

### C-3. 모듈·프로젝트 경계에 해당하는 레코드

**후보가 넷이고, 넷이 서로 다른 그림을 준다.** Q1 의 답이 여기 있다.

**(가) `.asmdef` — Unity 에서 CMake 타겟에 해당하는 경계.** 원문 1건
(`Assets/GPM/UI/gpm_ui.asmdef`, `references` 배열이 의존 방향을 준다):

```json
{
    "name": "gpm_ui",
    "references": [
        "gpm_common",
        "gpm_cachestorage"
    ],
    "optionalUnityReferences": [],
    "includePlatforms": [],
    "excludePlatforms": [],
    "allowUnsafeCode": false,
    "overrideReferences": false,
    "precompiledReferences": [],
    "autoReferenced": true,
    "defineConstraints": []
}
```

**사용자 코드 트리(`Assets/@`)에 있는 유일한 `.asmdef` 는 아래 하나다.** `references` 가 비어 있다:

```json
{
    "name": "ToolbarExtender.Editor",
    "references": [],
    "includePlatforms": [
        "Editor"
    ],
    "excludePlatforms": [],
    "allowUnsafeCode": false,
    "overrideReferences": false,
    "precompiledReferences": [],
    "autoReferenced": true,
    "defineConstraints": [],
    "versionDefines": []
}
```

경로는 `Assets/@Editors/SceneHelper/ToolbarExtender/ToolbarExtender.Editor.asmdef` 다.
`.asmdef` 는 자기 폴더와 하위 폴더를 덮으므로 **이것이 덮는 사용자 파일은 2개**
(`ToolbarCallback.cs`, `ToolbarExtender.cs`) 뿐이고, 그 둘은 벤더링된 서드파티 도구
(`UnityToolbarExtender` 네임스페이스)다. 나머지 112개는 이 경계 밖이다.

> 핸드오프 §1 (나)는 "사용자 코드 114개 파일에는 `.asmdef` 가 하나도 없다" 고 적었으나,
> 정확히는 **1개가 있고 그것이 덮는 파일은 2개** 다. 결론(사용자 코드가 `Assembly-CSharp`
> 하나로 뭉친다)은 그대로 성립한다 — 오히려 112/114 로 더 정확해진다.

**(나) `.csproj` — Unity 가 `.asmdef` 로부터 생성한 것.** 어느 `.csproj` 가 사용자 코드를
포함하는지 전수 조사한 결과 (`02-csproj-compile-map.txt` 원문):

```
=== (재실행) 사용자 코드(@Scripts/@Editors) 를 포함하는 csproj ===
 112  Assembly-CSharp.csproj
   2  ToolbarExtender.Editor.csproj
합계 114 (사용자 코드 .cs 추적 파일 114개 중)
```

`Assembly-CSharp.csproj` 의 `<Compile Include>` 121개를 디렉토리별로 나누면:

```
 106 Assets/@Scripts
   9 Assets/GPM
   6 Assets/@Editors
```

즉 **`Assembly-CSharp` 는 순수한 사용자 코드 모듈이 아니다.** `Assets/GPM/Shader/` 아래
서드파티 파일 9개가 같이 들어 있다(그쪽에 `.asmdef` 가 없어서다).

`Assembly-CSharp.csproj` 의 모듈 간 의존은 `<ProjectReference>` 17개로 나온다:

```
    <ProjectReference Include="Assembly-CSharp-firstpass.csproj" />
    <ProjectReference Include="IngameDebugConsole.Runtime.csproj" />
    <ProjectReference Include="Lofelt.NiceVibrations.csproj" />
    <ProjectReference Include="gpm_common.csproj" />
    <ProjectReference Include="AYellowpaper.SerializedCollections.csproj" />
    <ProjectReference Include="gpm_ui.csproj" />
    <ProjectReference Include="MoreMountains.Tools.Editor.csproj" />
    <ProjectReference Include="IngameDebugConsole.Editor.csproj" />
    <ProjectReference Include="Unity.PlayerPrefsEditor.EditorResources.csproj" />
    <ProjectReference Include="ToolbarExtender.Editor.csproj" />
    <ProjectReference Include="Lofelt.NiceVibrations.Editor.csproj" />
    <ProjectReference Include="MoreMountains.Tools.csproj" />
    <ProjectReference Include="Lofelt.NiceVibrations.Demo.csproj" />
    <ProjectReference Include="Unity.PlayerPrefsEditor.Samples.SampleScene.csproj" />
    <ProjectReference Include="gpm_cachestorage.csproj" />
    <ProjectReference Include="Unity.PlayerPrefsEditor.Editor.csproj" />
    <ProjectReference Include="AYellowpaper.SerializedCollections.Editor.csproj" />
```

이것이 C++ 의 `cmake --graphviz` 에 해당하는 산출물이다. **다만 17개 전부가 서드파티다** —
사용자 코드가 어셈블리 하나뿐이므로 사용자 코드 사이의 모듈 간선은 **0개** 다.

**(다) `StickRushGame.slnx` — 추적되는 솔루션 파일.** 원문 전량(23줄, 자르지 않음):

```xml
<Solution>
  <Project Path="MoreMountains.Tools.csproj" />
  <Project Path="gpm_cachestorage_editor.csproj" />
  <Project Path="gpm_common.csproj" />
  <Project Path="Assembly-CSharp.csproj" />
  <Project Path="MoreMountains.Tools.Editor.csproj" />
  <Project Path="AYellowpaper.SerializedCollections.csproj" />
  <Project Path="gpm_manager.csproj" />
  <Project Path="Unity.PlayerPrefsEditor.Editor.csproj" />
  <Project Path="gpm_cachestorage.csproj" />
  <Project Path="IngameDebugConsole.Runtime.csproj" />
  <Project Path="Lofelt.NiceVibrations.csproj" />
  <Project Path="Assembly-CSharp-Editor.csproj" />
  <Project Path="gpm_ui_sample.csproj" />
  <Project Path="gpm_ui.csproj" />
  <Project Path="Assembly-CSharp-firstpass.csproj" />
  <Project Path="gpm_ui_editor.csproj" />
  <Project Path="AYellowpaper.SerializedCollections.Editor.csproj" />
  <Project Path="Lofelt.NiceVibrations.Demo.csproj" />
  <Project Path="Lofelt.NiceVibrations.Editor.csproj" />
  <Project Path="ToolbarExtender.Editor.csproj" />
  <Project Path="IngameDebugConsole.Editor.csproj" />
  <Project Path="Unity.PlayerPrefsEditor.EditorResources.csproj" />
  <Project Path="Unity.PlayerPrefsEditor.Samples.SampleScene.csproj" />
</Solution>
```

**23개만 나열한다.** 디스크의 `.csproj` 는 135개이고, 차이 112개는
`Library/PackageCache/` 의 패키지 어셈블리(`BakingSheet.*`, `Unity.*` 등)다. 즉
`.slnx` 는 **`Assets/` 아래 어셈블리 경계만** 담고 패키지는 뺀다. 서드파티 필터링에
쓸 수 있는 가장 짧은 목록이 이것이다.

**(라) 네임스페이스.** `01-namespaces.txt` 의 정규화 집계 원문:

```
  50 Gamerecipe.StickRush
  30 Gamerecipe.StickRush.UI
  18 Gamerecipe.StickRush.Data
   5 Gamerecipe.Utils
   2 UnityToolbarExtender
   2 SceneHelper
   1 GoogleSheetsExtension
```

**(마) 폴더 트리.** `01-folders.txt` 원문 (`Assets/@Scripts` 2단계):

```
  31 Controller
  24 UIs
  20 Data
  10 Utils
   8 Interface
   7 Managers
   2 Test
   2 Fixture
   2 Exceptions
```

**(바) `Packages/manifest.json` + `Packages/packages-lock.json` — 패키지 경계.**
**이 둘은 git 에 추적된다.** `Library/` 와 달리 `.gitignore` 로 빠지지 않으므로, 깨끗한 클론에도
**서드파티 의존 그래프가 그대로 남아 있는 유일한 파일**이다.

`manifest.json` 은 사람이 쓴 직접 의존 57개다. `packages-lock.json` 은 Unity 가 해석한
전체 그래프이고, 레코드 원문 1건은 이렇게 생겼다:

```json
{
  "com.cathei.bakingsheet": {
    "version": "4.1.3",
    "depth": 0,
    "source": "registry",
    "dependencies": {
      "com.unity.nuget.newtonsoft-json": "3.0.2"
    },
    "url": "https://package.openupm.com"
  }
}
```

`dependencies` 가 **패키지 간 의존 방향**을 준다. 실측:

```
패키지 노드:               85개
  depth 0 (직접):          57
  depth 1 (전이):          19
  depth 2 (전이):           9
  source=builtin           47
  source=registry          37
  source=git                1
패키지 간 의존 간선:       135개
```

**어셈블리를 패키지 이름 노드 하나로 접으면 축약비가 이렇다:**

```
PackageCache 안 .asmdef(어셈블리) 259개  ->  패키지 46개
.slnx 밖 csproj              112개  ->  패키지 41개 (매핑 106, 실패 6)
probe 참조 중 PackageCache DLL 19개  ->  패키지  9개
```

가장 크게 접히는 것은 `com.unity.visualscripting` 8개, `com.cathei.bakingsheet` 7개,
`com.cysharp.unitask` 6개 순이다. 매핑에 실패한 6개는 전부 `BakingSheet.Samples*` 로,
`PackageCache` 안에 대응하는 `.asmdef` 이 없다.

⚠ **패키지 경계는 사용자 코드를 전혀 나누지 못한다.** 85개 전부가 서드파티·엔진이고
`Assets/@Scripts` / `Assets/@Editors` 는 어느 패키지에도 속하지 않는다.
즉 이것은 **Q1(사용자 코드의 모듈 경계)의 후보가 아니라, 서드파티 쪽을 접는 축**이다.
E절의 "전체" 열과 서드파티 필터링에 쓰인다.

**Q1 에 대한 답 — 네 후보의 수치를 나란히 놓으면:**

| 후보 | 사용자 코드를 몇 개 경계로 나누나 | 의존 방향을 주나 | 사용자 코드 사이의 모듈 간선 |
|---|---|---|---|
| `.asmdef` | **1개** (그것도 벤더링된 2파일짜리) + 나머지 112파일은 경계 밖 | 준다 (`references`) | 0 |
| `.csproj` | **2개** (`Assembly-CSharp` 112, `ToolbarExtender.Editor` 2) | 준다 (`ProjectReference`) | 0 |
| 네임스페이스 | **4개** (`Gamerecipe.StickRush` 50 / `.UI` 30 / `.Data` 18 / `Gamerecipe.Utils` 5) + 서드파티 3개 | 안 준다 (선언에서 직접은) | 유도해야 함 |
| 폴더 트리 (`@Scripts` 2단계) | **9개** (Controller 31 / UIs 24 / Data 20 / Utils 10 / Interface 8 / Managers 7 / Test 2 / Fixture 2 / Exceptions 2) | 안 준다 | 유도해야 함 |
| (참고) 패키지 | **0개** — 사용자 코드는 어느 패키지에도 속하지 않는다 | 준다 (`packages-lock.json` 의 `dependencies`, 간선 135개) | 해당 없음 |

💭 판단은 사용자 몫이지만, 관찰만 놓고 말하면 **`.asmdef` 와 `.csproj` 는 사용자 코드를
사실상 나누지 못한다**(각각 1개·2개 경계, 모듈 간선 0개). 반면 네임스페이스와 폴더 트리는
4~9개로 나뉘며, 이 저장소에서는 **둘이 거의 겹친다** — `@Scripts/UIs/` ↔ `Gamerecipe.StickRush.UI`,
`@Scripts/Data/` ↔ `Gamerecipe.StickRush.Data`, `@Scripts/Utils/` ↔ `Gamerecipe.Utils`.
어긋나는 곳은 `Controller/`(31개)와 `Managers/`(7개)로, 둘 다 `Gamerecipe.StickRush` 루트
네임스페이스에 들어간다.

### C-4. 위 셋 중 어디에도 안 들어가는데 실제로 나온 레코드

**(1) 프리팹 YAML 의 GUID 배선.** `04-prefab-sample.yaml` 발췌 (원본
`Assets/@Resources/Prefabs/UI/Buttons/UI_SettingButton.prefab` 628줄 중 잘라 붙였다):

```yaml
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: 5422072900737014958}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {fileID: 11500000, guid: ee5e07d91a3624e2d9526b22b6e6e2bb, type: 3}
  m_Name: 
  m_EditorClassIdentifier: 
  _buttonInScale: 1.1
  _buttonInTime: 0.3
  _buttonOutScale: 1
  _buttonOutTime: 0.2
```

`guid: ee5e07d91a3624e2d9526b22b6e6e2bb` 는 `Assets/@Scripts/UIs/Varients/UI_ButtonAnimationInAndOut.cs`
의 `.meta` GUID 다. `_buttonInScale: 1.1` 같은 **필드 값이 코드가 아니라 이 YAML 에 있다.**

**(2) `[SerializeField]` 객체 참조 — 대입이 코드에 아예 없는 사례.**
`Assets/@Resources/Prefabs/UI/Panels/Outgame_GameOverPanel.prefab` 줄 2303-2306:

```yaml
  m_Script: {fileID: 11500000, guid: ed8ce6118b1b64448b334a57e60fa6c7, type: 3}
  m_Name: 
  m_EditorClassIdentifier: 
  _movableImage: {fileID: 1780476830347659760}
```

코드 쪽(`Assets/@Scripts/UIs/Varients/UI_ButtonAnimationPressPositionDown.cs`):

```
12:        [SerializeField] Image _movableImage;
41:            _originalLocalPosition = _movableImage.rectTransform.localPosition;
43:                .Append(_movableImage.rectTransform.DOLocalMove(_pressedPosition, _pressTime).SetEase(Ease.OutBack))
44:                .Append(_movableImage.rectTransform.DOLocalMove(_originalLocalPosition, _boundTime).SetEase(Ease.OutBack));
```

**선언(12)과 읽기(41,43,44)만 있고 대입문이 코드 어디에도 없다.** 대입은 위 YAML 의
`fileID` 한 줄이 전부다. Roslyn 은 이것을
`UI_ButtonAnimationPressPositionDown → UnityEngine.UI.Image` 타입 참조(assoc)로만 본다.

**(3) `UnityEvent` 의 인스펙터 연결 — 빈 자리와 채워진 자리.** 같은 프리팹의 `UnityEngine.UI.Button`:

```yaml
  m_OnClick:
    m_PersistentCalls:
      m_Calls: []
```

이 자리는 비어 있다(코드에서 `AddListener` 로 붙이는 방식). 그러나 **전수 조사해 보니 비어 있지
않은 것이 훨씬 많다** — `.prefab` 266개 + `.unity` 66개에서 `m_MethodName` 이 **472건** 나오고
그중 **471건에 실제 메서드 이름이 들어 있다.** 최상위 디렉토리별 분포:

```
  @Resources           전체   16   실제 메서드명 있는 것   16
  Feel                 전체  350   실제 메서드명 있는 것  349
  GPM                  전체   91   실제 메서드명 있는 것   91
  Plugins              전체    2   실제 메서드명 있는 것    2
  @Scenes              전체    6   실제 메서드명 있는 것    6
  PlayerPrefsEditor    전체    7   실제 메서드명 있는 것    7
  합계                   전체  472   실제 메서드명 있는 것  471
```

사용자 자산 쪽은 `@Resources` 16건 + `@Scenes` 6건 = **22건** 이다. 채워진 레코드 원문
(`Assets/@Resources/Prefabs/UI/Panels/Outgame_GameOverPanel.prefab` 줄 1316-1331 발췌):

```yaml
  m_UpdateString:
    m_PersistentCalls:
      m_Calls:
      - m_Target: {fileID: 2780235465455634724}
        m_TargetAssemblyTypeName: TMPro.TMP_Text, Unity.TextMeshPro
        m_MethodName: set_text
        m_Mode: 0
        m_Arguments:
          m_ObjectArgument: {fileID: 0}
```

**이것은 호출 간선이다.** 대상 인스턴스(`m_Target` 의 `fileID`), 대상 타입
(`m_TargetAssemblyTypeName`), 메서드 이름(`m_MethodName`) 이 전부 있다. 그리고 이 정보는
`.cs` 어디에도 없다. 사용자 코드에서 `UnityEvent` 문자열은 20회 나온다.

⚠ 이 22건 중 **`m_TargetAssemblyTypeName` 이 사용자 코드 타입인 것은 확인하지 못했다.**
`m_MethodName` 블록 주변 ±8줄에서 사용자 스크립트 GUID 를 찾는 방식으로 훑었는데 0건이었다.
표본이 가리키는 대상은 `TMPro.TMP_Text` 같은 서드파티였다. **더 넓게 훑지 않았다**(H절).

---

## D. 간선 종류 대응표 — 이 보고서의 핵심

> ### 📌 2026-08-27 사용자 확정 — 이 절을 읽을 때의 전제가 바뀌었다
>
> 이 절은 `kind` 가 **6종 고정**이던 시점의 관찰이다. 그 뒤 아래가 확정됐다.
> **관찰 기록은 고치지 않는다. 결정만 여기 덧붙인다.**
>
> - **C-10 — `kind` enum 이 8종으로 확장됐다.** 6종 + `instantiation` + `friendship`.
>   `schema_version` 1 → 2. 아래 "대응시킬 수 없는 것" 표의 `instantiation`(C++ 11건)과
>   `friendship`(2건)은 **이제 자리가 생겼다.** `containment`(5건)는 여전히 자리가 없다.
> - **6종의 출처가 확인됐다** 🔵 88 — UML 의 관계 어휘다. Dependency · Association
>   (Aggregation/Composition 으로 더 특정됨) · Generalization(=`inheritance`) · Realization.
> - **`association` 0건 / `composition`·`aggregation` 0건은 대응표의 오류가 아니다** 🔵 90.
>   UML 에서 `composition`/`aggregation` 은 관계 종류가 아니라 association 끝(Property)의
>   `AggregationKind` 열거값(`none`/`shared`/`composite`, UML 2.5.1 사양 127쪽)이다.
>   이 enum 은 **관계 종류 축과 소유 강도 축을 한 줄로 평탄화**했고, 그래서
>   C++ 는 전부 `shared`/`composite` 로, C# 은 전부 `none` 으로 몰린다.
>   축을 분리하는 안(`kind` 4종 + `ownership` 필드)은 검토 후 **채택하지 않았다** —
>   `kind` 에서 값을 빼는 것이 §7 확장 규율("제거·의미 변경 금지")에 걸린다.
> - **R7 이 추가됐다** — 원시 타입과 암묵적 기반 타입은 간선으로 만들지 않는다.
>   적용 순서: R5 → R7 → R2 → R1 → R4 → R3 → R6.

`codegraph.json` 의 `kind` 는 **6종 고정 enum** 이다:
`inheritance / realization / composition / aggregation / dependency / association`.

도구가 실제로 낸 문자열을 왼쪽에, 대응하는 enum 을 오른쪽에 적는다.

| 도구가 낸 문자열 | 출현 횟수 | 대응 enum | 판단 근거 |
|---|---|---|---|
| `kind=inherit` | 64 | `inheritance` | `INamedTypeSymbol.BaseType` 이 `System.Object` 가 아닌 클래스. 언어 차원에서 단일 상속이고 모호함이 없다 |
| `kind=realize` | 70 | `realization` | `INamedTypeSymbol.Interfaces`. C# 의 `: IFoo` 는 인터페이스 실현이 확정적이다 |
| `kind=assoc` | 285 | `association` | 필드 선언의 타입 (`IFieldSymbol.Type`). enum 멤버 209건은 제외했다 |

**대응시킬 수 없는 것 (enum 6종에 자리가 없는 것):**

| 도구가 낸 문자열 | 출현 횟수 | 왜 안 들어가나 |
|---|---|---|
| `kind=assoc` 중 `attrs=[SerializeField]` 인 것 | 27 | 자리가 **없는 게 아니라 갈 곳이 둘이다.** 값이 프리팹·씬 YAML 에 박혀 인스턴스가 고정되므로 의미상 `composition` 에 가깝지만, 언어 차원에서는 그냥 참조 필드라 `association` 과 구분할 근거가 코드에 없다. 지금은 `association` 으로 뭉뚱그렸다 |
| 프리팹·씬 YAML 의 `m_Script: {guid: …}` | 사용자 스크립트 GUID 를 참조하는 **프리팹 16개**(전부 `Assets/@Resources` 아래) + **씬 6개** | 원본이 `.cs` 가 아니라 `.prefab`/`.unity` 다. `file:line` 이 아니라 `file:GUID` 이고, 소스 심볼 사이의 간선이 아니라 **자산→심볼** 간선이다 |
| `UnityEvent` 의 `m_PersistentCalls` (`m_MethodName`) | **472건** (메서드명이 실제로 든 것 471건). 사용자 자산 쪽만 22건 (`@Resources` 16 + `@Scenes` 6). 코드 내 `UnityEvent` 문자열 20회 | 호출 관계가 코드가 아니라 씬·프리팹 YAML 에 있다. 6종 중 `dependency` 에 억지로 넣을 수는 있으나 **근거 위치가 `.cs` 가 아니어서** 인용 검증 L3 이 성립하지 않는다 |

**반대로 이 도구가 끝내 내지 못하는 enum:**

| enum | 왜 못 내나 |
|---|---|
| `composition` | 🔵 92 — C# 에는 값 소유와 참조 소유를 구분하는 문법이 없다. 필드는 전부 참조(또는 값 타입 복사)이고, `unique_ptr` / 값 멤버 같은 표지가 없다. Track C §6 함정 5 의 예측 (a) 가 이 저장소에서 그대로 확인됐다 |
| `aggregation` | 🔵 92 — 위와 같은 이유. `composition` 과 `aggregation` 을 가르는 정보 자체가 언어에 없다 |
| `dependency` | 🟡 70 — **못 내는 게 아니라 이번 시험이 안 냈다.** 메서드 파라미터·지역 변수·`new` 표현식을 훑으면 낼 수 있다. 이번 probe 는 타입 선언과 필드까지만 봤다(핸드오프의 "수십 줄" 제한). 다만 그렇게 뽑은 dependency 는 아래 G절의 이유로 **Unity 에서는 실제 배선의 일부만** 담는다 |

**Q3 에 대한 답:** 6종 중 **3종(inheritance, realization, association)이 실제로 나왔다.**
Track C §6 함정 5 의 예측 "C# 보고서는 5종 간선이 아니라 3종(상속·실현·연관)으로 그려야 한다" 는
이 저장소에서 **그대로 맞았다.** 다만 예측이 말한 3종과 이번에 나온 3종이 같은 것인지는
`dependency` 를 안 뽑은 만큼 단정할 수 없다 — 위 표의 🟡 70 을 참조.

> ⚠ **enum 을 늘리는 제안을 여기에 쓰지 말 것.** 관찰만 적는다.
> 스키마 변경은 두 언어의 보고서가 모두 도착한 뒤 사용자가 결정한다.

---

## E. 계량

| 항목 | 값 |
|---|---|
| 노드 수 (전체) | **2,755** (구문 수준 타입 선언, `.cs` 1,713개) |
| 노드 수 (서드파티·외부 의존 제외) | **231** (구문 수준) / **214** (의미 수준, 중첩 타입 포함, `.cs` 112개) |
| 간선 수 (전체) | **13,366** = base-list 1,644 + 필드 선언 11,722 (둘 다 구문 수준) |
| 간선 수 (서드파티·외부 의존 제외) | **419** = inheritance 64 + realization 70 + association 285 (의미 수준) |
| 모듈·어셈블리 수 | **무엇을 경계로 쓰느냐에 따라 다르다.** `.asmdef` 20개(사용자 1) / `.csproj` 135개(`.slnx` 에 오르는 것 23개, 사용자 2) / 네임스페이스 7개(사용자 4) / 폴더 9개 / **패키지 85개(사용자 0)** |
| **외부 노드 수 (C-9 적용 후)** | **12개.** 참조로 넘긴 DLL 395개 → 사용자 코드가 실제로 닿는 어셈블리 13개 → 패키지 이름으로 접어 12개. 전부 `__external__` 그룹 하나에 들어간다 |
| 가장 노드가 많은 모듈과 그 수 | **`Assembly-CSharp`** — 사용자 `.cs` 112개, 의미 수준 타입 214개. 사용자 코드 114개 중 112개(98.2%)가 여기 하나에 들어간다 |

**계량 방법이 두 가지라는 점을 명시한다.**

- **구문 수준(syntax)** = Roslyn 으로 파싱만 하고 심볼 해석은 안 한 것. 서드파티 1,713개
  파일 전량에 적용 가능해서 "전체" 열을 채울 수 있다.
- **의미 수준(semantic)** = `CSharpCompilation` 으로 심볼을 해석한 것. 서드파티는
  **소스가 아니라 DLL 참조**로 들어가므로 "전체" 를 이 방법으로 재려면 135개 어셈블리를
  따로 컴파일해야 한다. 이번 최소 시험의 범위 밖이라 **미측정**으로 남긴다(H절).

**두 방법의 교차 검증:** 사용자 코드 필드 선언이 구문 285 / 의미 285 로 **정확히 일치**한다.
타입은 구문 231 / 의미 214 로 17 차이인데, 원인은 `partial` 이다 — `partial` 선언 30건,
고유 이름 13개, `30 - 13 = 17`. 구문은 선언마다 세고 의미는 타입마다 센다.

**제외 기준으로 쓴 경로 패턴을 그대로 적는다:**

```
포함(사용자 코드):
    Assets/@Scripts/**/*.cs      106개
    Assets/@Editors/**/*.cs        8개
                                 --------
                                 114개  (추적 .cs 1,713개의 6.7%)

제외(서드파티):
    Assets/Feel/**                 866개
    Assets/GPM/**                  653개
    Assets/Plugins/**               69개
    Assets/PlayerPrefsEditor/**     11개
                                 --------
                                 1,599개 (93.3%)

probe 실제 대상은 112개다. 아래 2개는 Assembly-CSharp 가 아니라
ToolbarExtender.Editor 어셈블리에 속해 제외됐다(벤더링된 서드파티 도구):
    Assets/@Editors/SceneHelper/ToolbarExtender/ToolbarCallback.cs
    Assets/@Editors/SceneHelper/ToolbarExtender/ToolbarExtender.cs

Assembly-CSharp 안에 섞여 들어온 서드파티 9개도 probe 대상에서 뺐다:
    Assets/GPM/Shader/**/*.cs      9개
```

**서드파티 쪽을 접는 축이 하나 더 있다 — 패키지다.** `Assets/` 아래 벤더링된 서드파티
(Feel 866 / GPM 653 / Plugins 69 / PlayerPrefsEditor 11)는 위 경로 규칙으로 걸러지지만,
`Library/PackageCache/` 의 패키지 코드는 경로가 GUID 해시를 달고 있어(`com.cathei.bakingsheet@b1888fa3064a`)
경로 규칙으로 다루기 나쁘다. `packages-lock.json` 을 쓰면 **패키지 이름 노드 하나**로 접힌다:

```
PackageCache 안 .asmdef(어셈블리) 259개  ->  패키지 46개
.slnx 밖 csproj              112개  ->  패키지 41개
probe 참조 중 PackageCache DLL 19개  ->  패키지  9개
```

**⚠ 이 제외 규칙은 경로 기반이라 완전하지 않다.** 위 마지막 두 항목이 그 증거다 —
`Assets/@` 로 시작해도 서드파티일 수 있고(ToolbarExtender), `Assembly-CSharp` 어셈블리에
들어 있어도 서드파티일 수 있다(GPM/Shader). 어셈블리 경계와 경로 경계가 어긋난다.
C-2 의 `dstAsm` 필드가 이보다 나은 판별자가 될 수 있다(I절).

---

## F. `file` / `line` 실재 여부 — 인용 검증 L3 의 성립 조건

`codegraph.json` 스키마는 **노드가 아니라 간선에** `file`/`line` 을 요구한다.
"A 가 B 를 소유한다" 의 근거는 클래스 선언 줄이 아니라 **멤버 선언 줄** 이기 때문이다.

| 질문 | 답 | 근거 |
|---|---|---|
| 노드에 file/line 이 붙는가 | **붙는다** | `ISymbol.Locations` 중 `IsInSource` 인 것에 `GetLineSpan()` 을 부르면 `LinePosition` 이 나온다. `03-symbols.txt` 20건 전부에 위치가 있다 |
| **간선에 file/line 이 붙는가** | **붙는다. 그리고 멤버 선언 줄을 정확히 가리킨다** | `association` 은 `IFieldSymbol.Locations` 를 쓰므로 **필드 선언 줄**이다. `inheritance`/`realization` 은 `INamedTypeSymbol.Locations` 를 써서 **타입 선언 줄**인데, C# 의 base-list 는 타입 선언과 같은 줄에 오므로 결과적으로 근거 줄과 일치한다(아래 대조 확인). 더 정확히 하려면 `BaseListSyntax` 의 위치를 쓰면 된다 |
| 경로가 절대경로인가 상대경로인가 | **둘 다 가능. Roslyn 은 넘겨준 그대로 돌려준다** | `CSharpSyntaxTree.ParseText(..., path: f)` 의 `path` 가 그대로 `LineSpan.Path` 가 된다. 이 시험은 절대경로로 파싱하고 출력 때 저장소 루트 기준 상대경로로 바꿨다. **Roslyn 이 정하는 것이 아니라 호출자가 정한다** |
| 그 경로가 실제로 존재하는가 (표본 10건 확인) | **10/10 존재** | 아래 표의 `sed -n '<line>p' <file>` 가 전부 내용을 냈다. 존재하지 않으면 빈 줄이 나온다 |
| 그 줄에 실제로 그 심볼이 있는가 (표본 10건 육안 대조) | **10/10 일치, 불일치 0** | `03-lineverify.txt` |

**표본 10건 대조 결과를 파일:줄 단위로 적는다:**

| # | 도구가 말한 위치 | 그 줄의 실제 내용 | 일치 |
|---|---|---|---|
| 1 | `Assets/@Editors/AddressableRenamer.cs:9` | `public class AddressableRenamer : EditorWindow` | 예 |
| 2 | `Assets/@Scripts/Utils/BaseScene.cs:8` | `public abstract class BaseScene : InitBase, ISceneNameAccessor` | 예 |
| 3 | `Assets/@Scripts/Data/Constants.cs:2` | `public partial class Constants` | 예 |
| 4 | `Assets/@Scripts/Data/Constants.cs:68` | `    public class Addressables {` | 예 |
| 5 | `Assets/@Scripts/Data/Constants.cs:7` | `    public class Config {` | 예 |
| 6 | `Assets/@Scripts/Data/Constants.cs:37` | `    public class InGame ` | 예 |
| 7 | `Assets/@Scripts/Data/Constants.cs:31` | `    public class Scene {` | 예 |
| 8 | `Assets/@Scripts/Data/Constants.cs:75` | `    public class SortingLayer {` | 예 |
| 9 | `Assets/@Scripts/Data/Constants.cs:56` | `    public class Tween {` | 예 |
| 10 | `Assets/@Scripts/Managers/CoroutineRunner.cs:38` | `public static class CoroutineExtensions ` | 예 |

**간선 레코드 4건도 따로 대조했다** (템플릿이 요구하는 "간선에 file/line" 항목의 실증):

| 간선 | `at=` 위치 | 그 줄의 실제 내용 | 일치 |
|---|---|---|---|
| `inherit` AddressableRenamer → UnityEditor.EditorWindow | `Assets/@Editors/AddressableRenamer.cs:9` | `public class AddressableRenamer : EditorWindow` | 예 |
| `realize` BaseScene → ISceneNameAccessor | `Assets/@Scripts/Utils/BaseScene.cs:8` | `public abstract class BaseScene : InitBase, ISceneNameAccessor` | 예 |
| `assoc` AddressableRenamer.groupNames → string[] | `Assets/@Editors/AddressableRenamer.cs:11` | `    private string[] groupNames;` | 예 |
| `assoc` ScriptableFoodCells._foodCells → List\<SerialDataFood\> | `Assets/@Scripts/Data/DataFood/ScriptableFoodCells.cs:11` | `        private List<SerialDataFood> _foodCells;` | 예 |

**Q2 에 대한 답: Roslyn 은 `file:line` 을 준다. 위치는 정확하다. 인용 검증 L3 은 성립한다.**
단, 성립 조건이 하나 붙는다 — **참조 어셈블리를 제대로 넣어야 한다.** 아래가 그 측정이다.

| 모드 | 참조 구성 | 컴파일 error | 영향 파일 | 타입 해석 실패 (간선 기준) |
|---|---|---|---|---|
| A | .NET 9 BCL 만 (Unity DLL 0개) | **1,055건** | 88 / 112 | 대량 (CS0246 675건) |
| B | .NET 9 BCL + Unity 참조 (섞음) | **7,780건** | 112 / 112 | 사실상 전부 |
| C | **Unity 참조 395개만** (BCL 제외) | **0건** | 0 / 112 | **0건** |

모드 B 가 A 보다 나쁜 것이 핵심이다. 진단 원문:

```
CS0433  263건  예: 'Exception' 형식이 'System.Private.CoreLib, Version=9.0.0.0, ...' 및
                    'netstandard, Version=2.1.0.0, ...'에 모두 있습니다.
CS0518  7094건  예: 미리 정의된 형식 'System.Void'을(를) 정의하지 않았거나 가져오지 않았습니다.
```

Unity 의 `.csproj` 는 `netstandard2.1` 을 겨냥하고 참조 목록에
`NetStandard/ref/2.1.0/netstandard.dll` 과 `compat/2.1.0/shims/` 를 이미 포함한다.
여기에 실행 중인 .NET 9 런타임의 BCL 을 **더하면** 같은 타입이 두 어셈블리에 있게 되어
전부 모호해진다. Track C §6 함정 4 가 경고한 "netstandard2.1 vs dotnet 9 충돌" 은
**실재하지만, 원인은 SDK 버전이 아니라 참조 집합을 섞은 것** 이다.
`.csproj` 의 참조 목록만 그대로 쓰면 오류 0건으로 완전히 해석된다.

---

## G. 스키마에 안 들어가는 관찰 — 기록만

이 언어·엔진에서만 나오는 구조로, 지금 스키마에 자리가 없는 것들이다.
**여기에 적힌 것을 근거로 필드를 추가하지 않는다.** 나중에 사용자가 판단한다.

| 관찰 | 출현 횟수 | 왜 정적 분석이 놓치나 |
|---|---|---|
| `MonoBehaviour` 생명주기 메서드 (`Awake`/`Start`/`Update`/`OnDestroy`/…) | **Roslyn 실측 38** (정규식 하한: Awake 10, Start 21, Update 4, OnDestroy 3, OnApplicationQuit 3, OnApplicationPause 1) | 코드 어디서도 호출하지 않는다. 엔진이 리플렉션으로 부른다. 호출 그래프에서 **입력 간선 0 인 고아**로 보이고 PageRank 중요도가 0 에 수렴한다 |
| `[SerializeField]` 필드 | **27** (Roslyn 이 어트리뷰트로 해석한 정확한 수. 정규식 하한도 27 로 같았다) | 값을 에디터에서 프리팹·씬 YAML 에 넣는다. 코드에 대입이 없다. C-4 (2) 가 실물 증거다. 실제로는 소유(composition)에 가까운데 Roslyn 은 타입 참조로만 본다 |
| `GetComponent<T>()` | **39** | 런타임 조회. 컴파일 시점 의존이 약하게만 잡힌다 |
| `Resources.Load` | **0** | 이 저장소는 안 쓴다 |
| `Addressables.*` | **17** | 문자열 주소로 자산을 찾는다. 간선이 아예 없다. `Resources.Load` 를 대체한 것으로 보인다 |
| `SendMessage` | **0** | 이 저장소는 안 쓴다 |
| `UnityEvent` | 코드 내 문자열 **20**, YAML 쪽 `m_MethodName` **472건**(사용자 자산 22건) | 호출 관계가 코드가 아니라 씬·프리팹 YAML 의 `m_PersistentCalls` 에 있다. 레코드에 대상 타입명과 메서드명이 다 들어 있는데 `.cs` 에는 흔적이 없다 |
| `FindObjectOfType` | **4** | 타입만으로 런타임 인스턴스를 찾는다. 어느 객체인지는 씬에만 있다 |
| `Invoke(` | **48** | ⚠ 이 수는 **믿을 수 없다.** `MonoBehaviour.Invoke(string, float)`(문자열로 메서드 호출 — 정적 분석이 놓치는 것)와 `UnityEvent.Invoke()`/델리게이트 `Invoke()`(놓치지 않는 것)를 정규식이 구분하지 못한다. 분해하지 않았다 |
| `StartCoroutine(` | **5** | 코루틴 본문 실행이 프레임에 걸쳐 분산된다. 호출 그래프의 시간 축이 끊긴다 |
| `Instantiate(` | **1** | 프리팹 자산을 런타임에 복제한다. 대상이 GUID 로만 지정된다 |

**정규식 하한과 Roslyn 실측의 차이가 가장 큰 항목** (`04-roslyn-unity.txt` 원문):

```
MonoBehaviour 파생 타입 (전이 상속 포함)  Roslyn=45   정규식하한=5
ScriptableObject 파생 타입 (전이 포함)    Roslyn=6    정규식하한=2
[SerializeField] 필드                     Roslyn=27   정규식하한=27
MonoBehaviour 생명주기 메서드 선언        Roslyn=38
```

**`MonoBehaviour` 는 정규식이 9배 적게 센다.** 이유는 중간 기반 클래스다:

```
   26  : Gamerecipe.StickRush.UI_Base
    4  : Gamerecipe.StickRush.InitBase
    4  : UnityEngine.MonoBehaviour
    2  : Gamerecipe.StickRush.SingletonForScene<Gamerecipe.StickRush.InGameScene>
    2  : Gamerecipe.StickRush.UI.UI_ButtonAnimationVariant
    2  : Gamerecipe.StickRush.UI_Panel
    1  : Gamerecipe.StickRush.SingletonMonoBehaviour<Gamerecipe.StickRush.CoroutineRunner>
    1  : Gamerecipe.StickRush.SingletonForScene<Gamerecipe.StickRush.HomeScene>
    1  : Gamerecipe.StickRush.SingletonMonoBehaviour<Gamerecipe.StickRush.Managers>
    1  : Gamerecipe.StickRush.BaseScene
    1  : Gamerecipe.StickRush.SingletonForScene<Gamerecipe.StickRush.SplashScene>
```

45개 중 **직접 `: MonoBehaviour` 라고 쓴 것은 4개뿐** 이고, 나머지 41개는
`UI_Base`, `InitBase`, `SingletonForScene<T>` 같은 프로젝트 자체 기반 클래스나 제네릭
싱글턴을 거친다. 핸드오프 §3 단계 5 의 "정규식으로 센 하한" 경고가 이 저장소에서
가장 크게 나타나는 지점이다.

**⚠ 정정 — 정규식 수치는 하한조차 아니다.** 처음에 "전부 하한(lower bound)" 이라고 적었으나
단계 5-1 의 Roslyn 질의 파이프라인으로 재보니 **양방향으로 틀린다.**

| 항목 | 정규식 | Roslyn 정확 | 방향 |
|---|---|---|---|
| `MonoBehaviour` 파생 타입 | 5 | **45** | 9배 적게 |
| `Instantiate(` | 1 | **5** | 적게 |
| `FindObjectOfType` 계열 | 4 | **9** | 적게 |
| `GetComponent` 계열 | 39 | **40** | 적게 |
| `Addressables` 계열 | 17 | **17** | 일치 |
| `StartCoroutine(` | 5 | **1** | **정규식이 많게** |

**`StartCoroutine` 이 결정적이다.** 정규식이 센 5건 중 **4건이 주석**이다:

```
StageGameFlowState.StageStart.cs:25:  // 카운트 다운을 시작하는데 ... "Managers.DontDestroyCoroutineRunner.StartCoroutine(CoCountDown())" 마음대로 사용하세요.
StageGameFlowState.StageStart.cs:27:  // Managers.DontDestroyCoroutineRunner.StartCoroutine(CoCountDown());
CoroutineRunner.cs:10:  /// MonoBehaviour를 상속받지 않은 클래스라면 .StartCoroutine(); //을 사용할 수 없습니다.
CoroutineRunner.cs:13:  /// Managers.DontDestroyCoroutineRunner.StartCoroutine(); //사용하여 코루틴을 실행할 수 있습니다.
CoroutineRunner.cs:22:      StartCoroutine(CoInvokeWithDelay(action, delay));   <- 실제 호출은 이 1건뿐
```

정규식은 주석과 문자열을 세고 Roslyn 은 안 센다. 따라서 정규식 수치는 **하한도 상한도 아니고
경계가 없는 다른 수**다. "하한 N개" 라고 적는 것조차 틀렸다.

**이 절의 정규식 수치는 "정확한 수" 로 읽지 말 것.** 용도는 하나뿐이다 —
정적 분석이 놓치는 자리가 어디인지 표시하는 것. 정확한 수는 아래 G-1 에 있다.

### G-1. Roslyn 질의 파이프라인의 정확한 수 (단계 5-1)

호출식 **1,295건** 중 심볼 해석 성공 1,288건(99.5%), 서로 다른 `수신타입.메서드` **507종**.
**어휘 목록을 미리 정하지 않고** 실제로 호출된 것을 전수 열거한 뒤 골라낸 값이다.

| 질의 | Roslyn 정확 | 정규식 | 근거 file:line (일부) |
|---|---|---|---|
| `UnityEvent.AddListener` | **19** | 미측정 | `UIs/Varients/UI_ButtonAnimation.cs:32`, `UIs/Buttons/UI_RerollButton.cs:30` |
| `UnityEvent.RemoveListener` 계열 | **1** | 미측정 | `Controller/StageMode/FlowMachine/FlowStates/StageGameFlowState.CookingFood.cs:40` |
| `GetComponent` 계열 | **40** | 39 | `Controller/StageMode/Views/UI_StageStateView.cs:58` |
| `Resources.Load` 계열 | **0** | 0 | — |
| `SendMessage` 계열 | **0** | 0 | — |
| `Addressables` 계열 | **17** | 17 | `Managers/Cores/ResourceManager.cs:76` |
| `Instantiate` | **5** | 1 | `Controller/StageMode/Views/UI_FoodStickView.cs:43` |
| `StartCoroutine`/`StopCoroutine` | **1** | 5 | `Managers/CoroutineRunner.cs:22` |
| `FindObjectOfType` 계열 | **9** | 4 | `Managers/Managers.cs:191`, `Utils/Singleton.cs:43` |
| **`MonoBehaviour.Invoke(문자열)`** | **4** | 48 과 섞임 | `Controller/StageMode/Views/UI_CustomerSpaceView.cs:72` |
| **그 외 `.Invoke()`** (델리게이트·`UnityEvent`) | **43** | 48 과 섞임 | `UIs/Buttons/UI_RerollButton.cs:46` |

**`Invoke` 분해가 이 파이프라인의 값을 가장 잘 보여준다.** 정규식 48건은
`MonoBehaviour.Invoke(string, float)`(문자열로 메서드를 부르므로 정적 분석이 놓치는 것)와
델리게이트·`UnityEvent` 의 `Invoke()`(놓치지 않는 것)를 구분할 수 없었다.
Roslyn 은 수신 타입으로 **4 / 43** 으로 가른다. **놓치는 것은 48건이 아니라 4건이다.**

> **철회하고 정정한다.** C-4 (3) 에서 `m_Calls: []` 를 두고 "코드에서 `AddListener` 로 붙이는
> 방식" 이라고 썼을 때, 나는 `AddListener` 를 세어 본 적이 없었다. 로직을 읽지 않고 추측한
> 문장이었다. 이제 측정했고 **`AddListener` 19건 · `RemoveListener` 계열 1건으로 참이다.**
> 결론은 유지되지만, 그때는 근거 없이 쓴 것이 맞다.

---

## H. 막힌 것

해결하지 못한 채 남긴 것. **추측으로 우회하지 말고 여기에 적는다.**

| 막힌 지점 | 오류 원문 | 시도한 것 | 다음에 해볼 것 |
|---|---|---|---|
| 서드파티 전체의 **의미 수준** 계량 (E절 "전체" 열의 간선 종류별 수) | (오류가 아니라 미착수) | 구문 수준으로만 냈다. 의미 수준으로 재려면 135개 어셈블리를 각각 별도 `CSharpCompilation` 으로 만들어야 한다 — 최소 시험의 범위를 넘는다 | 본격 덤프 도구 단계에서 `.slnx` 의 23개 프로젝트를 어셈블리별로 컴파일. 패키지 112개는 소스가 `Library/PackageCache` 에 있어 별도 판단 필요 |
| `dependency` 간선 미수집 | (오류가 아니라 미착수) | 타입 선언과 필드까지만 훑었다. 핸드오프의 "수십 줄" 제한 때문 | 메서드 파라미터·반환형·`new` 표현식·지역 변수 타입을 훑으면 나온다. `SemanticModel.GetSymbolInfo` 로 표현식 단위 |
| 씬(`.unity`) YAML — 계수만 하고 표본은 안 남겼다 | (오류가 아니라 범위) | 씬 66개를 GUID·`m_MethodName` 기준으로 훑어 계수했다(사용자 스크립트 참조 6개, `m_MethodName` 6건). 원문 표본은 프리팹 것만 남겼다 (핸드오프 단계 5 가 프리팹 표본 1건을 지정) | 씬 YAML 표본도 남긴다. 프리팹과 형식이 같은지 확인 필요 |
| `m_PersistentCalls` 의 대상이 사용자 코드인지 미확정 | (오류가 아니라 방법 한계) | `m_MethodName` 줄 주변 ±8줄에서 사용자 스크립트 GUID 를 찾았고 0건이었다. 확인한 표본의 대상은 `TMPro.TMP_Text` 였다 | `m_Target` 의 `fileID` 를 같은 파일 안에서 실제로 역참조해 그 컴포넌트의 `m_Script` GUID 를 봐야 한다. ±8줄 휴리스틱으로는 부족하다 |
| `ToolbarExtender` 소스 2개가 probe 대상 밖 | 초기 모드 C 에서 3건: `Assets/@Editors/SceneHelper/SceneHelper.cs(9,7): error CS0246: 'UnityToolbarExtender' 형식 또는 네임스페이스 이름을 찾을 수 없습니다.` 외 CS0103 2건 | `<ProjectReference>` 대상을 `Library/ScriptAssemblies/*.dll` 로 치환해 참조에 추가 → **오류 0건으로 해소.** 다만 그 2개 파일 자체는 여전히 다른 어셈블리라 probe 소스 목록에 없다 | 어셈블리별로 컴파일하는 구조가 되면 자연히 포함된다 |
| **probe 가 핸드오프의 "수십 줄" 상한을 넘었다** | (규약 이탈) | 최종 `Program.cs` **152줄**. 세 모드 비교(A/B/C), 중첩 타입 순회, enum 멤버 분리, 구문 수준 전체 계수, `MonoBehaviour` 전이 상속 판정을 넣다가 늘었다 | 판단은 사용자 몫이다. 다만 스키마·직렬화·플러그인 구조·CLI 는 **하나도 만들지 않았다** — 출력은 전부 탭 구분 텍스트고 재사용 가능한 추상은 없다 |
| 저장소 사본이 둘이고 내용이 다르다 | (오류 아님) | 두 사본의 `ProjectVersion.txt`/HEAD/파일수를 대조해 머리말에 적었다 | 어느 쪽이 정본인지는 **사용자가 정해야 한다.** 이 보고서는 `UnityProjects/` 쪽 = Unity 6 기준이다 |
| 수집 도중 HEAD 가 바뀌었다 | (오류 아님) | `git reflog` 로 사용자 커밋 `c0a610f` 임을 확인하고 단계 1 부터 재측정 | 없음. 재측정으로 해소됨 |

**막히지 않았지만 하지 않은 것 (지시대로):**

- Unity 배치 모드(`-executeMethod UnityEditor.SyncVS.SyncSolution`) — `.csproj` 가 이미 있어 불필요
- Unity 에디터 GUI 실행, 씬·프리팹 저장 — 금지 사항
- `.asmdef` 신설 — 금지 사항
- `normalize.py` 실행 — 금지 사항
- `codegraph.json` 스키마 / `kind` enum 변경 제안 — 금지 사항
- `Microsoft.Build.Locator` / `MSBuildWorkspace` — 핸드오프가 쓰지 말라고 지정

**사용자 프로젝트에 남긴 변경은 `.gitignore` 한 줄뿐이다** (+ 원래 없던 파일 끝 개행).
추적 파일 중 그 외에 손댄 것은 없다.

---

## I. `normalize.py` 파서 설계에 대한 권고

**코드를 쓰지 않는다.** 위 A~H 에서 관찰된 것만 근거로, 파서가 마주칠 것을 문장으로 적는다.
확신도는 🔵/🟡/💭 + 정수를 붙이고, 🔵 는 이 세션에서 실제로 돌린 명령의 출력만 인정한다.

**1. 🔵 95 — C# 쪽에는 "파싱할 도구 출력" 이 존재하지 않는다. 이것이 C++ 쪽과의 가장 큰 구조적 차이다.**
C++ 쪽은 `cmake --graphviz` 나 Doxygen XML 처럼 **도구가 정한 출력 형식**을 파싱한다.
Roslyn 에는 그런 것이 없다 — 라이브러리이고, `INamedTypeSymbol` 객체를 메모리에 줄 뿐이다.
C절에 붙인 탭 구분 레코드는 **도구가 정한 형식이 아니라 이 세션의 probe 가 임의로 정한 것**이다.
따라서 C# 쪽 `normalize.py` 파서는 "남의 형식을 읽는 일" 이 아니라 **"우리가 정할 형식을 읽는 일"** 이고,
사실상 덤프 도구와 한 몸으로 설계된다. 두 언어의 파서를 대칭으로 놓으려는 시도는 여기서 어긋난다.

**2. 🔵 92 — 간선은 3종만 온다고 보고 파서를 짜도 된다.**
`inheritance` 64, `realization` 70, `association` 285 가 실측이다. `composition` 과
`aggregation` 은 **도구를 바꿔도 안 나온다** — C# 에 소유와 참조를 구분하는 문법이 없다.
`dependency` 는 나올 수 있으나 이번엔 안 뽑았다(🟡 70).
C++ 쪽 보고서가 5종을 낸다면, `normalize.py` 는 **입력에 따라 종류 수가 다른 것을 정상으로**
취급해야 한다. 없는 종류를 0 으로 채울지, 아예 키를 안 만들지가 첫 설계 결정이다.

**3. 🔵 90 — `file:line` 은 신뢰할 수 있다. 단 참조 집합이 전제다.**
표본 10건 + 간선 4건 전부 일치했고, 모드 C 는 컴파일 오류 0건 / 타입 해석 실패 0건이었다.
반면 참조를 잘못 구성하면(모드 A: 오류 1,055건, 모드 B: 7,780건) 타입이 `ErrorTypeSymbol` 로
떨어져 **간선의 `dst` 가 통째로 쓰레기가 된다.**
따라서 파서는 **"타입 해석 실패 건수" 를 입력에서 반드시 받아야 하고, 0 이 아니면 경고해야 한다.**
이것이 C# 쪽에서 인용 검증 L3 을 지키는 실질적 조건이다.

**4. 🔵 88 — 참조 집합은 섞으면 안 된다. `.csproj` 의 목록을 그대로 써야 한다.**
Unity `.csproj` 는 `netstandard2.1` 을 겨냥하고 `netstandard.dll` + shim 을 이미 참조한다.
여기에 실행 중인 .NET SDK 의 BCL 을 더하면 CS0433/CS0518 이 수천 건 난다.
덤프 도구는 `<HintPath>` 전량 + `<ProjectReference>` 대상 DLL 만 쓰고, **호스트 런타임의
어셈블리를 절대 섞지 말아야 한다.** 이 저장소에서는 그것만으로 오류 0건이 됐다.

**5. 🔵 90 — 모듈 경계로 `.asmdef` 를 쓰면 사용자 코드가 모듈 하나로 뭉개진다.**
핸드오프 §1 (나)의 우려가 실측으로 확인됐다. 사용자 코드 114개 중 112개(98.2%)가
`Assembly-CSharp` 하나에 들어가고, **사용자 코드 사이의 모듈 간선은 0개** 다.
`modules[]` 를 `.asmdef` 나 `.csproj` 로 채우면 `modules` 배열의 길이는 1~2 가 되고
모듈 그래프는 빈 그래프가 된다.
💭 대안은 네임스페이스(사용자 4개) 또는 폴더 트리(9개)인데, 이 저장소에서는 둘이 크게
겹치므로(§C-3) 어느 쪽을 골라도 비슷한 그림이 나온다. **어느 것을 쓸지는 사용자 결정 사항이다.**

**6. 🔵 85 — 서드파티 필터를 경로만으로 짜면 새어 나간다. `dstAsm` 을 같이 받는 편이 낫다.**
경로 기반 규칙의 구멍이 이 저장소에서 양방향으로 확인됐다.
`Assets/@Editors/` 안에 서드파티가 있고(ToolbarExtender 2개), `Assembly-CSharp` 안에도
서드파티가 있다(`Assets/GPM/Shader/` 9개).
C-2 레코드의 `dstAsm` 필드는 대상 타입이 사는 어셈블리를 그대로 준다 — `Probe`(=사용자 코드) 인지
`UnityEditor.CoreModule` 인지가 한눈에 갈린다.
💭 경로 규칙과 어셈블리 판별을 **둘 다** 받아서 교차 확인하는 편이 안전해 보인다.

**6.5. 🔵 88 — 서드파티를 "패키지 이름 노드 하나" 로 접는 축이 있고, 그것은 git 에 추적된다.**
`Packages/manifest.json` 과 `Packages/packages-lock.json` 은 `.gitignore` 에 걸리지 않는다.
`Library/` 도 `.csproj` 도 없는 깨끗한 클론에서 **서드파티 의존 그래프를 얻을 수 있는 유일한 파일**이고,
`packages-lock.json` 의 `dependencies` 가 패키지 간 간선 135개를 그대로 준다.
축약비는 어셈블리 259개 → 패키지 46개, `.slnx` 밖 csproj 112개 → 패키지 41개다.
⚠ **패키지 경계는 사용자 코드를 0개로 나눈다** — Q1 의 후보가 아니다. 서드파티 전용 축이다.

> **2026-08-27 사용자 확정 — Track C C-9 로 결정됐다.** 이 항목은 더는 미결정이 아니다.
> 규칙 넷: (R1) 전이 확장 없음, (R2) 패키지 이름 노드 하나, (R3) `__external__` 외딴 섬,
> (R4) 사용자→외부 단방향 간선. 상세는 `HANDOFF-codebase-wiki.md` §2-1,
> C# 적용은 `HANDOFF-unity-pattern-collection.md` §2-2 에 있다.
>
> **이 저장소에 적용한 결과는 외부 노드 12개다** (`external-nodes.tsv`). 실측 경로:
> 참조 DLL 395개 → 사용자 코드가 직접 닿는 어셈블리 13개 → 패키지 이름으로 접어 12개.
> `packages-lock.json` 의 전이 그래프(노드 85 / 간선 135)는 **R1 이 전부 버린다.**
>
> ⚠ 접기의 대가가 하나 있다. 같은 `(from, to, kind)` 쌍을 하나로 접으므로
> **L3 의 근거 `file:line` 이 하나만 남는다.** `netstandard` 는 310회 접촉되는데 간선은 1개가 된다.
> 근거를 전부 보존해야 하면 `edges[].occurrences` 를 나중에 추가한다(§7 확장 규율).

**7. 🟡 75 — `[SerializeField]` 를 association 으로만 두면 실제 구조의 일부가 사라진다.**
27건이고, 그중 객체 참조형은 **코드에 대입문이 아예 없다**(C-4 (2)의 `_movableImage`).
의미상 composition 에 가깝지만 언어에는 근거가 없고, 실제 배선은 프리팹 YAML 의
`fileID` 한 줄이다.
⚠ **여기서 `kind` 를 늘리자고 제안하지 않는다** — Track C 규정이다. 다만 파서가
`attrs` 를 **버리지 않고 통과시키면** 나중에 사용자가 판단할 여지가 남는다.
지금 형식에서는 `attrs=[SerializeField]` 가 그 자리다.

**8. 🟡 70 — 노드 계량은 `partial` 때문에 "선언 수" 와 "타입 수" 가 다르다. 어느 쪽인지 명시해야 한다.**
사용자 코드에서 구문 231 / 의미 214, 차이 17 = `partial` 선언 30건 − 고유 이름 13개.
한 타입이 여러 파일에 걸치므로 **노드 하나에 `file:line` 이 여러 개 붙을 수 있다.**
C++ 의 선언/정의 분리와 겉보기는 비슷하지만 성질이 다르다 — `.h`/`.cpp` 는 두 종류지만
`partial` 은 대등한 조각 N개다. 파서가 "대표 위치 하나" 를 골라야 하면 규칙이 필요하다.

**9. 🟡 65 — 이 저장소의 Unity 6 는 `.slnx` 라는 새 솔루션 형식을 쓴다. `*.sln` 패턴으로는 못 잡는다.**
`.gitignore:37` 의 `*.sln` 이 `.slnx` 를 거르지 못해 `StickRushGame.slnx` 가 추적되고 있다.
형식은 XML 이고 `<Project Path="...csproj" />` 목록이 전부다(C-3 (다) 원문 참조).
💭 다른 Unity 버전에서는 `.sln` 일 것으로 보이나 **이 세션에서는 Unity 6 하나만 봤다.**
파서/도구는 두 형식을 모두 찾아야 할 가능성이 있다.

**10. 💭 55 — Unity 의 실제 구조를 잡으려면 `.cs` 만으로는 부족하다. 다만 이것은 관찰이지 제안이 아니다.**
G절의 표가 근거다. 생명주기 메서드 38개는 호출 그래프에서 고아가 되고,
`[SerializeField]` 27건·`Addressables` 17건·`GetComponent<T>` 39건의
실제 대상은 전부 코드 밖(프리팹·씬 YAML, 문자열 주소)에 있다.
가장 큰 것은 `UnityEvent` 다 — `.prefab` 266개와 `.unity` 66개에 `m_MethodName` 이
**472건**(메서드명이 실제로 든 것 471건) 있고, 각 레코드에 대상 타입명과 메서드명이
다 들어 있다. **즉 호출 간선이 코드가 아니라 자산에 471개 있다.**
형식은 GUID 참조가 있는 YAML 이다.
**지금 스키마는 `file:line` 을 요구하므로 `file:GUID` 인 이 배선은 들어갈 자리가 없다.**
어떻게 할지는 두 언어 보고서가 모두 도착한 뒤 사용자가 정한다.
