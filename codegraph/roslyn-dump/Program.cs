// codegraph/roslyn-dump — C# 원시 사실 덤프 (Track C Phase 7)
//
// 형식 명세: docs/handoffs/DECISION-csharp-intermediate-format.md (F1~F11)
// 원칙 F2 — 이 도구는 접기(R1~R7)·필터·모듈 배정을 하지 않는다. 정책은 전부 normalize.py 에 있다.
//   따라서 System.Object 로의 상속, enum 멤버(is_enum_member 플래그), 원시 타입으로의 depend 도
//   전부 그대로 낸다. 버리는 것은 normalize.py 의 R7/자기참조 규칙이다.
//
// 참조 구성은 모드 C — Unity 가 생성한 Assembly-CSharp.csproj 의 목록만 쓰고 호스트 런타임
// 어셈블리를 절대 섞지 않는다. 섞으면 CS0433/CS0518 이 수천 건 난다(관찰 보고서 F절 실측).
//
// 사용: dotnet run --project codegraph/roslyn-dump -- <Unity저장소> [출력경로]
//   출력 기본값: <Unity저장소>/out/codegraph-raw/roslyn-dump.json

using System.Diagnostics;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Xml.Linq;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;

if (args.Length < 1)
{
    Console.Error.WriteLine("사용법: roslyn-dump <Unity저장소> [출력경로]");
    return 1;
}

var repo = Path.GetFullPath(args[0]);
var outPath = args.Length > 1 ? Path.GetFullPath(args[1])
    : Path.Combine(repo, "out/codegraph-raw/roslyn-dump.json");

var csprojPath = Path.Combine(repo, "Assembly-CSharp.csproj");
if (!File.Exists(csprojPath))
{
    // F10 의 전제 — Unity 가 만든 .csproj 가 있어야 참조 395개를 그대로 쓸 수 있다.
    Console.Error.WriteLine($"에러 — {csprojPath} 가 없다. Unity 에디터가 생성해야 한다" +
        " (HANDOFF-unity-pattern-collection.md §3 단계 3).");
    return 1;
}

// ── Assembly-CSharp.csproj 파싱. MSBuild XML 이라 네임스페이스가 붙을 수 있어 LocalName 으로 찾는다.
var doc = XDocument.Load(csprojPath);
IEnumerable<XElement> Els(string local) => doc.Descendants().Where(e => e.Name.LocalName == local);
string Norm(string p) => p.Replace('\\', '/');

var hintPaths = Els("Reference")
    .SelectMany(r => r.Elements().Where(e => e.Name.LocalName == "HintPath"))
    .Select(e => Norm(e.Value.Trim()))
    .Select(p => Path.IsPathRooted(p) ? p : Path.GetFullPath(Path.Combine(repo, p)))
    .Where(File.Exists)
    .Distinct().ToList();

// ProjectReference 는 프로젝트가 아니라 Unity 가 이미 빌드해 둔 DLL 로 치환한다
// (관찰 보고서 H절 — 이 치환으로 ToolbarExtender 참조 오류가 0건이 됐다).
var projDlls = Els("ProjectReference")
    .Select(e => (string?)e.Attribute("Include"))
    .Where(v => v != null)
    .Select(v => Path.GetFileNameWithoutExtension(Norm(v!)))
    .Select(name => Path.Combine(repo, "Library/ScriptAssemblies", name + ".dll"))
    .Where(File.Exists)
    .Distinct().ToList();

var defines = Els("DefineConstants")
    .SelectMany(e => e.Value.Split(';', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
    .Distinct().ToList();

var langRaw = Els("LangVersion").Select(e => e.Value.Trim()).FirstOrDefault() ?? "9.0";
LanguageVersionFacts.TryParse(langRaw, out var langVersion);
var allowUnsafe = Els("AllowUnsafeBlocks").Any(e => e.Value.Trim().Equals("true", StringComparison.OrdinalIgnoreCase));

// F10 — 사용자 코드만. csproj 의 Compile 목록(=Unity 의 어셈블리 배정 결과)과
// 사용자 경로(Assets/@Scripts, Assets/@Editors)의 교집합을 소스로 쓴다.
// ToolbarExtender 2파일은 자체 .asmdef 로 다른 csproj 에 가 있으므로 자동으로 빠진다.
var sources = Els("Compile")
    .Select(e => (string?)e.Attribute("Include"))
    .Where(v => v != null)
    .Select(v => Norm(v!))
    .Where(p => p.StartsWith("Assets/@Scripts/") || p.StartsWith("Assets/@Editors/"))
    .Select(p => Path.Combine(repo, p))
    .Where(File.Exists)
    .OrderBy(p => p, StringComparer.Ordinal)
    .ToList();

Console.Error.WriteLine($"소스 {sources.Count}개 / HintPath 참조 {hintPaths.Count}개 / ScriptAssemblies 치환 {projDlls.Count}개 / defines {defines.Count} / LangVersion {langVersion}");

var parseOpts = new CSharpParseOptions(langVersion).WithPreprocessorSymbols(defines);
var trees = sources.Select(p => CSharpSyntaxTree.ParseText(File.ReadAllText(p), parseOpts, path: p)).ToList();
var refs = hintPaths.Concat(projDlls).Select(p => (MetadataReference)MetadataReference.CreateFromFile(p)).ToList();

var compilation = CSharpCompilation.Create(
    "Assembly-CSharp", trees, refs,
    new CSharpCompilationOptions(OutputKind.DynamicallyLinkedLibrary, allowUnsafe: allowUnsafe));

var diags = compilation.GetDiagnostics();
var errors = diags.Where(d => d.Severity == DiagnosticSeverity.Error).ToList();
if (errors.Count > 0)
    foreach (var d in errors.Take(5)) Console.Error.WriteLine("  " + d);

// ── 이름 형식. R7 매칭을 위해 키워드가 아니라 정식 이름을 쓴다 — "string" 이 아니라 "System.String".
var NameFmt = new SymbolDisplayFormat(
    globalNamespaceStyle: SymbolDisplayGlobalNamespaceStyle.Omitted,
    typeQualificationStyle: SymbolDisplayTypeQualificationStyle.NameAndContainingTypesAndNamespaces,
    genericsOptions: SymbolDisplayGenericsOptions.IncludeTypeParameters);

// ── 타입 레지스트리 — F3: 외부 타입도 전부 types[] 에 들어가고 관계는 id → id 다.
var ids = new Dictionary<ITypeSymbol, string>(SymbolEqualityComparer.Default);
var typeRecs = new List<TypeRec>();
int unresolved = 0;

string RelFile(Location loc) => Path.GetRelativePath(repo, loc.SourceTree!.FilePath).Replace('\\', '/');

(string? file, int? line) SrcLoc(ISymbol s)
{
    var loc = s.Locations.Where(l => l.IsInSource)
        .OrderBy(l => l.SourceTree!.FilePath, StringComparer.Ordinal)
        .ThenBy(l => l.GetLineSpan().StartLinePosition.Line)
        .FirstOrDefault();
    if (loc == null) return (null, null);
    return (RelFile(loc), loc.GetLineSpan().StartLinePosition.Line + 1);
}

string Reg(ITypeSymbol t)
{
    if (ids.TryGetValue(t, out var have)) return have;
    var id = "T" + (typeRecs.Count + 1);
    ids[t] = id;                       // 재귀(제네릭 인자 → 자기 자신) 대비 먼저 등록
    var rec = new TypeRec { Id = id };
    typeRecs.Add(rec);

    switch (t)
    {
        case IArrayTypeSymbol arr:
            // F4 — 배열도 제네릭과 같은 자리로 표현한다. generic_def "[]" + type_args [원소]
            rec.Name = arr.ToDisplayString(NameFmt);
            rec.Kind = "Array";
            rec.GenericDef = "[]";
            rec.TypeArgs = new() { Reg(arr.ElementType) };
            break;
        case ITypeParameterSymbol tp:
            rec.Name = tp.Name;
            rec.Kind = "TypeParameter";
            break;
        case INamedTypeSymbol n:
            rec.Name = n.ToDisplayString(NameFmt);
            rec.Kind = n.TypeKind == TypeKind.Error ? "Error" : n.TypeKind.ToString();
            if (n.TypeKind == TypeKind.Error) unresolved++;
            rec.Assembly = n.ContainingAssembly?.Name;
            (rec.File, rec.Line) = SrcLoc(n);
            if (n.ContainingType != null) rec.NestedIn = Reg(n.ContainingType);
            rec.PartialDecls = n.DeclaringSyntaxReferences.Length;
            // 구성된 제네릭(List<Foo>)만 분해한다. 정의 자체(List<T>)는 분해할 것이 없다.
            if (n.IsGenericType && !SymbolEqualityComparer.Default.Equals(n, n.OriginalDefinition))
            {
                var od = n.OriginalDefinition;
                var ns = od.ContainingNamespace != null && !od.ContainingNamespace.IsGlobalNamespace
                    ? od.ContainingNamespace.ToDisplayString() + "." : "";
                var outer = od.ContainingType != null ? od.ContainingType.ToDisplayString(NameFmt) + "." : "";
                rec.GenericDef = ns + outer + od.MetadataName;   // 예: System.Collections.Generic.List`1
                rec.TypeArgs = n.TypeArguments.Select(Reg).ToList();
            }
            break;
        default:
            rec.Name = t.ToDisplayString(NameFmt);
            rec.Kind = t.TypeKind.ToString();
            rec.Assembly = t.ContainingAssembly?.Name;
            break;
    }
    return id;
}

// ── 소스에 선언된 타입 전량 (중첩 포함). 파일·줄 순서로 id 를 결정적으로 만든다.
IEnumerable<INamedTypeSymbol> AllTypes(INamespaceSymbol ns)
{
    foreach (var m in ns.GetNamespaceMembers())
        foreach (var t in AllTypes(m)) yield return t;
    foreach (var t in ns.GetTypeMembers())
        foreach (var x in WithNested(t)) yield return x;

    static IEnumerable<INamedTypeSymbol> WithNested(INamedTypeSymbol t)
    {
        yield return t;
        foreach (var n in t.GetTypeMembers())
            foreach (var x in WithNested(n)) yield return x;
    }
}

var srcTypes = AllTypes(compilation.Assembly.GlobalNamespace)
    .Where(t => t.Locations.Any(l => l.IsInSource))
    .Select(t => (t, loc: SrcLoc(t)))
    .OrderBy(x => x.loc.file, StringComparer.Ordinal).ThenBy(x => x.loc.line)
    .Select(x => x.t).ToList();
foreach (var t in srcTypes) Reg(t);

// ── v2 살 채우기 (D1~D4). 관계 추출과 독립이고 srcTypes 만 대상이다.
//    ⚠ 걸러내기(표시 정책)는 하지 않는다 — 렌더러 몫이다(F2).
{
    string Acc(Accessibility a) => a switch {
        Microsoft.CodeAnalysis.Accessibility.Public => "public",
        Microsoft.CodeAnalysis.Accessibility.Private => "private",
        Microsoft.CodeAnalysis.Accessibility.Protected => "protected",
        Microsoft.CodeAnalysis.Accessibility.Internal => "internal",
        Microsoft.CodeAnalysis.Accessibility.ProtectedOrInternal => "protected internal",
        Microsoft.CodeAnalysis.Accessibility.ProtectedAndInternal => "private protected",
        _ => "unknown" };
    string AttrName(AttributeData a) {
        var n = a.AttributeClass?.Name ?? "?";
        return n.EndsWith("Attribute") && n.Length > 9 ? n[..^9] : n; }
    // D4 — BaseType 을 타고 올라가며 전이 파생을 판정한다. 정규식이 못 하는 것이 이것이다.
    bool DerivesFrom(INamedTypeSymbol t, string full) {
        for (var b = t.BaseType; b != null; b = b.BaseType)
            if (b.OriginalDefinition.ToDisplayString(NameFmt) == full || b.ToDisplayString(NameFmt) == full) return true;
        return false; }

    foreach (var st in srcTypes)
    {
        var rec = typeRecs[int.Parse(ids[st].Substring(1)) - 1];
        rec.IsAbstract = st.IsAbstract;                                   // D3
        rec.Accessibility = Acc(st.DeclaredAccessibility);
        rec.Unity = new UnityRec {                                        // D4
            IsMonoBehaviour = DerivesFrom(st, "UnityEngine.MonoBehaviour"),
            IsScriptableObject = DerivesFrom(st, "UnityEngine.ScriptableObject") };

        var mems = new List<MemberRec>();
        var meths = new List<MethodRec>();
        foreach (var mem in st.GetMembers())
        {
            if (mem.IsImplicitlyDeclared) continue;                       // 컴파일러 생성 제외
            switch (mem)
            {
                case IFieldSymbol f: {                                    // D1
                    var (ff, fl) = SrcLoc(f);
                    mems.Add(new MemberRec {
                        Name = f.Name, Type = f.Type.ToDisplayString(NameFmt), Access = Acc(f.DeclaredAccessibility),
                        IsStatic = f.IsStatic, IsProperty = false,
                        IsEnumMember = st.TypeKind == TypeKind.Enum && f.IsConst,
                        Attrs = f.GetAttributes().Select(AttrName).ToList(), File = ff, Line = fl });
                    break; }
                case IPropertySymbol pr: {                                // D1 — is_property 로 구분
                    var (pf, pl) = SrcLoc(pr);
                    mems.Add(new MemberRec {
                        Name = pr.Name, Type = pr.Type.ToDisplayString(NameFmt), Access = Acc(pr.DeclaredAccessibility),
                        IsStatic = pr.IsStatic, IsProperty = true, IsEnumMember = false,
                        Attrs = pr.GetAttributes().Select(AttrName).ToList(), File = pf, Line = pl });
                    break; }
                case IMethodSymbol m when m.AssociatedSymbol == null      // D2 — 접근자(get/set) 제외
                        && (m.MethodKind == MethodKind.Ordinary || m.MethodKind == MethodKind.Constructor): {
                    var (mf, ml) = SrcLoc(m);
                    meths.Add(new MethodRec {
                        Name = m.Name, Access = Acc(m.DeclaredAccessibility), IsStatic = m.IsStatic,
                        IsAbstract = m.IsAbstract, IsVirtual = m.IsVirtual, IsOverride = m.IsOverride,
                        IsCtor = m.MethodKind == MethodKind.Constructor,
                        ParamCount = m.Parameters.Length,
                        Returns = m.MethodKind == MethodKind.Constructor ? null : m.ReturnType.ToDisplayString(NameFmt),
                        File = mf, Line = ml });
                    break; }
            }
        }
        rec.Members = mems;
        rec.Methods = meths;
    }
}

// ── 관계
var rels = new List<RelRec>();
string ShortAttr(AttributeData a)
{
    var n = a.AttributeClass?.Name ?? "?";
    return n.EndsWith("Attribute") && n.Length > 9 ? n[..^9] : n;
}

foreach (var st in srcTypes)
{
    var sid = ids[st];
    var (tf, tl) = SrcLoc(st);

    // inherit — System.Object/ValueType/Enum 포함 (F2: R7 은 normalize.py 몫)
    if (st.BaseType != null)
        rels.Add(new RelRec { Kind = "inherit", Src = sid, Dst = Reg(st.BaseType), File = tf, Line = tl });

    // realize — 선언된 직접 인터페이스만 (probe 와 같은 기준)
    foreach (var i in st.Interfaces)
        rels.Add(new RelRec { Kind = "realize", Src = sid, Dst = Reg(i), File = tf, Line = tl });

    foreach (var mem in st.GetMembers())
    {
        switch (mem)
        {
            // assoc — 명시 선언 필드만. enum 멤버는 버리지 않고 플래그(F8)
            case IFieldSymbol f when !f.IsImplicitlyDeclared:
                var (ff, fl) = SrcLoc(f);
                rels.Add(new RelRec
                {
                    Kind = "assoc", Src = sid, Dst = Reg(f.Type), Member = f.Name,
                    Attrs = f.GetAttributes().Select(ShortAttr).ToList(),
                    IsEnumMember = st.TypeKind == TypeKind.Enum && f.IsConst,
                    File = ff, Line = fl,
                });
                break;

            // depend (F11) — 파라미터·반환형. 접근자(get/set)와 컴파일러 생성 멤버는 제외.
            // void 반환은 내지 않는다 — 타입 참조가 아니라 값의 부재다(기계적 제외, 정책 아님).
            case IMethodSymbol m when !m.IsImplicitlyDeclared && m.AssociatedSymbol == null
                                      && (m.MethodKind == MethodKind.Ordinary || m.MethodKind == MethodKind.Constructor):
                foreach (var p in m.Parameters)
                {
                    var (pf, pl) = SrcLoc(p);
                    rels.Add(new RelRec
                    {
                        Kind = "depend", Src = sid, Dst = Reg(p.Type), Member = m.Name,
                        Origin = "parameter", File = pf ?? tf, Line = pl ?? tl,
                    });
                }
                if (m.MethodKind == MethodKind.Ordinary && !m.ReturnsVoid)
                {
                    var (mf, ml) = SrcLoc(m);
                    rels.Add(new RelRec
                    {
                        Kind = "depend", Src = sid, Dst = Reg(m.ReturnType), Member = m.Name,
                        Origin = "return", File = mf, Line = ml,
                    });
                }
                break;
        }
    }
}

// ── depend 의 local·new — 구문을 걸어야 나온다 (심볼 테이블에는 없다)
foreach (var tree in trees)
{
    var sm = compilation.GetSemanticModel(tree);
    var root = tree.GetRoot();

    string? EnclosingTypeId(SyntaxNode node)
    {
        var td = node.FirstAncestorOrSelf<TypeDeclarationSyntax>();
        if (td == null) return null;
        var sym = sm.GetDeclaredSymbol(td) as ITypeSymbol;
        return sym != null && ids.TryGetValue(sym, out var id) ? id : null;
    }
    string EnclosingMember(SyntaxNode node) =>
        node.FirstAncestorOrSelf<MemberDeclarationSyntax>() switch
        {
            MethodDeclarationSyntax m => m.Identifier.Text,
            ConstructorDeclarationSyntax c => c.Identifier.Text,
            PropertyDeclarationSyntax p => p.Identifier.Text,
            _ => "?",
        };
    (string, int) Loc(SyntaxNode node)
    {
        var sp = node.GetLocation().GetLineSpan();
        return (RelFile(node.GetLocation()), sp.StartLinePosition.Line + 1);
    }

    foreach (var decl in root.DescendantNodes().OfType<LocalDeclarationStatementSyntax>())
    {
        var t = sm.GetTypeInfo(decl.Declaration.Type).Type;   // var 도 여기서 풀린다
        var sid = EnclosingTypeId(decl);
        if (t == null || sid == null) { if (t == null) unresolved++; continue; }
        var (df, dl) = Loc(decl);
        rels.Add(new RelRec
        {
            Kind = "depend", Src = sid, Dst = Reg(t), Member = EnclosingMember(decl),
            Origin = "local", File = df, Line = dl,
        });
    }
    // BaseObjectCreation = new Foo() + C# 9 대상 타입 new(). foo.Bar() 호출은 내지 않는다 —
    // 그것은 calls[] 이고 Track C §7 이 "나중에 붙일 자리" 로 못박았다.
    foreach (var nu in root.DescendantNodes().OfType<BaseObjectCreationExpressionSyntax>())
    {
        var t = sm.GetTypeInfo(nu).Type;
        var sid = EnclosingTypeId(nu);
        if (t == null || sid == null) { if (t == null) unresolved++; continue; }
        var (nf, nl) = Loc(nu);
        rels.Add(new RelRec
        {
            Kind = "depend", Src = sid, Dst = Reg(t), Member = EnclosingMember(nu),
            Origin = "new", File = nf, Line = nl,
        });
    }
}

// ── 부가 정보
string? unity = null;
var pv = Path.Combine(repo, "ProjectSettings/ProjectVersion.txt");
if (File.Exists(pv))
    unity = File.ReadLines(pv).FirstOrDefault()?.Replace("m_EditorVersion:", "").Trim();

string? commit = null;
try
{
    var psi = new ProcessStartInfo("git", "rev-parse --short HEAD")
    { WorkingDirectory = repo, RedirectStandardOutput = true };
    using var proc = Process.Start(psi)!;
    commit = proc.StandardOutput.ReadToEnd().Trim();
    proc.WaitForExit();
}
catch { /* git 없으면 null */ }

var roslynVer = typeof(CSharpCompilation).Assembly.GetName().Version?.ToString(3) ?? "?";
var dump = new Dump
{
    FormatVersion = 2,
    Tool = $"roslyn-dump 0.1 (Microsoft.CodeAnalysis.CSharp {roslynVer})",
    RepoCommit = commit,
    Engine = new EngineRec { Unity = unity, LangVersion = langVersion.ToDisplayString(), Defines = defines.Count },
    Compilation = new CompRec
    {
        Assembly = "Assembly-CSharp",
        Sources = trees.Count,
        References = refs.Count,
        Errors = errors.Count,
        UnresolvedTypes = unresolved,
    },
    Types = typeRecs,
    Relations = rels,
};

Directory.CreateDirectory(Path.GetDirectoryName(outPath)!);
File.WriteAllText(outPath, JsonSerializer.Serialize(dump, new JsonSerializerOptions
{
    WriteIndented = true,
    Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
}));

// ── 요약 — 정규화 전 원시 수치. probe 실측과의 대사는 normalize 쪽에서 한다.
var byKind = rels.GroupBy(r => r.Kind).ToDictionary(g => g.Key, g => g.Count());
var byOrigin = rels.Where(r => r.Origin != null).GroupBy(r => r.Origin!).ToDictionary(g => g.Key, g => g.Count());
Console.WriteLine($"{outPath}");
Console.WriteLine($"  compilation — errors {errors.Count} / unresolved {unresolved}  (F5: 둘 다 0 이어야 normalize 가 받는다)");
Console.WriteLine($"  types {typeRecs.Count} (소스 {srcTypes.Count} + 외부 {typeRecs.Count - srcTypes.Count})");
Console.WriteLine($"  relations {rels.Count} — " + string.Join(" · ", byKind.Select(kv => $"{kv.Key} {kv.Value}")));
Console.WriteLine($"  depend origin — " + string.Join(" · ", byOrigin.Select(kv => $"{kv.Key} {kv.Value}")));
Console.WriteLine($"  enum 멤버 플래그 {rels.Count(r => r.IsEnumMember)} / [SerializeField] {rels.Count(r => r.Attrs != null && r.Attrs.Contains("SerializeField"))}");
Console.WriteLine($"  v2 살 — members {typeRecs.Sum(t => t.Members?.Count ?? 0)} · methods {typeRecs.Sum(t => t.Methods?.Count ?? 0)}"
    + $" · is_abstract=true {typeRecs.Count(t => t.IsAbstract == true)}"
    + $" · MonoBehaviour {typeRecs.Count(t => t.Unity?.IsMonoBehaviour == true)}"
    + $" · ScriptableObject {typeRecs.Count(t => t.Unity?.IsScriptableObject == true)}");
return errors.Count > 0 ? 2 : 0;

// ── 레코드 (형식 명세 §3 의 키 이름 그대로)
class Dump
{
    [JsonPropertyName("format_version")] public int FormatVersion { get; set; }
    [JsonPropertyName("tool")] public string? Tool { get; set; }
    [JsonPropertyName("repo_commit")] public string? RepoCommit { get; set; }
    [JsonPropertyName("engine")] public EngineRec? Engine { get; set; }
    [JsonPropertyName("compilation")] public CompRec? Compilation { get; set; }
    [JsonPropertyName("types")] public List<TypeRec>? Types { get; set; }
    [JsonPropertyName("relations")] public List<RelRec>? Relations { get; set; }
}
class EngineRec
{
    [JsonPropertyName("unity")] public string? Unity { get; set; }
    [JsonPropertyName("lang_version")] public string? LangVersion { get; set; }
    [JsonPropertyName("defines")] public int Defines { get; set; }
}
class CompRec
{
    [JsonPropertyName("assembly")] public string? Assembly { get; set; }
    [JsonPropertyName("sources")] public int Sources { get; set; }
    [JsonPropertyName("references")] public int References { get; set; }
    [JsonPropertyName("errors")] public int Errors { get; set; }
    [JsonPropertyName("unresolved_types")] public int UnresolvedTypes { get; set; }
}
class TypeRec
{
    [JsonPropertyName("id")] public string Id { get; set; } = "";
    [JsonPropertyName("name")] public string? Name { get; set; }
    [JsonPropertyName("kind")] public string? Kind { get; set; }
    [JsonPropertyName("assembly")] public string? Assembly { get; set; }
    [JsonPropertyName("file")] public string? File { get; set; }
    [JsonPropertyName("line")] public int? Line { get; set; }
    [JsonPropertyName("nested_in")] public string? NestedIn { get; set; }
    [JsonPropertyName("partial_decls")] public int PartialDecls { get; set; }
    [JsonPropertyName("generic_def")] public string? GenericDef { get; set; }
    [JsonPropertyName("type_args")] public List<string> TypeArgs { get; set; } = new();

    // v2 (F12·F13·F14) — 소스 선언 타입에만 채운다. 외부 타입은 null 이다.
    [JsonPropertyName("is_abstract")] public bool? IsAbstract { get; set; }
    [JsonPropertyName("accessibility")] public string? Accessibility { get; set; }
    [JsonPropertyName("unity")] public UnityRec? Unity { get; set; }
    [JsonPropertyName("members")] public List<MemberRec>? Members { get; set; }
    [JsonPropertyName("methods")] public List<MethodRec>? Methods { get; set; }
}
class UnityRec
{
    [JsonPropertyName("is_monobehaviour")] public bool IsMonoBehaviour { get; set; }
    [JsonPropertyName("is_scriptable_object")] public bool IsScriptableObject { get; set; }
}
class MemberRec
{
    [JsonPropertyName("name")] public string Name { get; set; } = "";
    [JsonPropertyName("type")] public string? Type { get; set; }
    [JsonPropertyName("access")] public string? Access { get; set; }
    [JsonPropertyName("is_static")] public bool IsStatic { get; set; }
    [JsonPropertyName("is_property")] public bool IsProperty { get; set; }
    [JsonPropertyName("is_enum_member")] public bool IsEnumMember { get; set; }
    [JsonPropertyName("attrs")] public List<string>? Attrs { get; set; }
    [JsonPropertyName("file")] public string? File { get; set; }
    [JsonPropertyName("line")] public int? Line { get; set; }
}
class MethodRec
{
    [JsonPropertyName("name")] public string Name { get; set; } = "";
    [JsonPropertyName("access")] public string? Access { get; set; }
    [JsonPropertyName("is_static")] public bool IsStatic { get; set; }
    [JsonPropertyName("is_abstract")] public bool IsAbstract { get; set; }
    [JsonPropertyName("is_virtual")] public bool IsVirtual { get; set; }
    [JsonPropertyName("is_override")] public bool IsOverride { get; set; }
    [JsonPropertyName("is_ctor")] public bool IsCtor { get; set; }
    [JsonPropertyName("param_count")] public int ParamCount { get; set; }
    [JsonPropertyName("returns")] public string? Returns { get; set; }
    [JsonPropertyName("file")] public string? File { get; set; }
    [JsonPropertyName("line")] public int? Line { get; set; }
}
class RelRec
{
    [JsonPropertyName("kind")] public string Kind { get; set; } = "";
    [JsonPropertyName("src")] public string Src { get; set; } = "";
    [JsonPropertyName("dst")] public string Dst { get; set; } = "";
    [JsonPropertyName("member")] public string? Member { get; set; }
    [JsonPropertyName("attrs")] public List<string>? Attrs { get; set; }
    [JsonPropertyName("is_enum_member")] public bool IsEnumMember { get; set; }
    [JsonPropertyName("origin")] public string? Origin { get; set; }
    [JsonPropertyName("file")] public string? File { get; set; }
    [JsonPropertyName("line")] public int? Line { get; set; }
}
