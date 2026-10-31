"""Print contexts for strict matches; count loose parenthetical and raw English/Korean occurrences."""
import sys, re, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv = [sys.argv[0], sys.argv[1], "/dev/null"]
import importlib.util
spec = importlib.util.spec_from_file_location("m", os.path.join(os.path.dirname(os.path.abspath(__file__)), "measure_lib.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
KO = ["부작용","부수 효과","부수효과","사전 조건","사후 조건","불변식","불변 조건","단일 진실 공급원","단일 책임 원칙","개방 폐쇄 원칙","개방-폐쇄 원칙",
      "리스코프 치환 원칙","인터페이스 분리 원칙","의존성 역전 원칙","의존 관계 역전 원칙","의존성 주입","의존성 삽입","제어의 역전","제어 역전","결합도","응집도",
      "캡슐화","정보 은닉","추상화","다형성","상속","합성","컴포지션","인터페이스","계층","레이어","관심사 분리","관심사의 분리","순환 의존","순환 참조",
      "의존성 그래프","호출 그래프","호출자","피호출자","데이터 흐름","결정적","결정론적","멱등","세분성","입도","테스트 용이성","테스트 가능성",
      "디자인 패턴","설계 패턴","싱글톤","팩토리 메서드","옵저버","관찰자","전략 패턴","어댑터","퍼사드","데코레이터","방문자","비지터","코드 스멜","코드 냄새",
      "리팩터링","리팩토링","기술 부채","기술 부채","컨벤션","관례","규약","바운디드 컨텍스트","유비쿼터스 언어","프로덕션 코드","테스트 코드","선행 조건",
      "전제 조건","엣지","에지","간선","노드","정점","꼭짓점","트리","스테이지","파이프라인"]
KO = list(dict.fromkeys(KO))
for name in ["k8s", "mdn", "pyko"]:
    print("=====", name)
    loose = collections.Counter(); raw_en = collections.Counter(); raw_ko = collections.Counter()
    for fp, text in m.prose_docs(name):
        for p in m.PROBE:
            e = m.eng_regex(p)
            pf, _ = m.PAT[p]
            for mm in pf.finditer(text):
                s = max(0, mm.start() - 40); print(f"  [{p}] {os.path.relpath(fp, m.ROOT)}: ...{text[s:mm.end()+10]!r}")
            loose[p] += len(re.findall(r"[가-힣][ ]?\([ ]*" + e + r"[ ]*[,;/)]", text, re.I))
            raw_en[p] += len(re.findall(r"(?<![A-Za-z])" + e + r"(?![A-Za-z])", text, re.I))
        for k in KO:
            raw_ko[k] += len(re.findall(r"(?<![가-힣])" + re.escape(k), text))
    print("LOOSE:", {k: v for k, v in loose.items() if v})
    print("RAW_EN:", {k: v for k, v in raw_en.items() if v})
    print("RAW_KO(prefix-boundary only):", {k: v for k, v in raw_ko.items() if v})
