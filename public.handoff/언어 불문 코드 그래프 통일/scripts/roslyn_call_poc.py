#!/usr/bin/env python3
"""roslyn-dump 사본의 Program.cs 에 호출 루프를 넣는다. 원본은 고치지 않는다.

    cp -R src/codewiki/csharp/roslyn-dump <임시>/roslyn-poc
    python3 roslyn_call_poc.py <임시>/roslyn-poc/Program.cs
    (cd <임시>/roslyn-poc && dotnet run -c Release -- "$CSHARP_REPO" <임시>/roslyn-poc.json)
"""
import sys

path = sys.argv[1]
with open(path, encoding="utf-8") as f:
    s = f.read()
head = "// ── depend 의 local·new — 구문을 걸어야 나온다 (심볼 테이블에는 없다)\n"
tail = "    }\n}\n\n// ── 부가 정보"
assert head in s and tail in s
s = s.replace(head, "int callOk = 0, callCandidate = 0, callNull = 0;\n" + head)
s = s.replace(tail, '''    }
    foreach (var inv in root.DescendantNodes().OfType<InvocationExpressionSyntax>())
    {
        var sid = EnclosingTypeId(inv);
        if (sid == null) continue;
        var info = sm.GetSymbolInfo(inv);
        var target = info.Symbol as IMethodSymbol;
        if (target == null && info.CandidateSymbols.Length > 0) { target = info.CandidateSymbols[0] as IMethodSymbol; callCandidate++; }
        if (target == null) { callNull++; continue; }
        callOk++;
        var (cf, cl) = Loc(inv);
        rels.Add(new RelRec { Kind = "call", Src = sid, Dst = Reg((target.ReducedFrom ?? target).ContainingType), Member = EnclosingMember(inv) + " -> " + target.Name, Origin = "invoke", File = cf, Line = cl });
    }
}

// ── 부가 정보''')
s = s.replace("File.WriteAllText(outPath,", 'Console.WriteLine($"call 해소 {callOk} · 후보만 {callCandidate} · 못 찾음 {callNull}");\nFile.WriteAllText(outPath,')
with open(path, "w", encoding="utf-8") as f:
    f.write(s)
