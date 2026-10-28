"""Bucket glossary entries: S2 design/SE, S1 general programming/CS, P platform/product/API, G general IT domain."""
import sys, json, re
r = json.load(open(sys.argv[1], encoding="utf-8"))

S2 = {  # language-agnostic design / architecture / pattern / SE-process vocabulary
 "mdn": {"Abstraction","Encapsulation","Inheritance","Polymorphism","Idempotent","Modularity","MVC","Mixin","OOP",
         "State machine","Principle of least privilege","Graceful degradation","Progressive Enhancement","Middleware",
         "CRUD","REST","DSL/Domain_specific_language","Smoke Test","Fuzzing","Wrapper","Shim","Prototype-based programming",
         "Pseudocode","Information architecture","Fork","Repo","SCM","Specification","Normative","Non-normative",
         "Placeholder names","Camel case","Kebab case","Snake case","SDK","IDE","API"},
 "pyko": {"abstract base class","duck-typing","EAFP","LBYL","generic function","single dispatch","provisional API",
          "soft deprecated","immutable","mutable","method resolution order"},
 "k8s": set(),
}
S1 = {  # language-agnostic general programming / CS concept (not design vocabulary per se)
 "mdn": {"Algorithm","Argument","Array","Asynchronous","Binding","Bitwise flags","Boolean","Buffer","Cache","Call stack",
         "Callback function","Class","Closure","Code point","Code unit","Compile","Compile time","Computer Programming",
         "Conditional","Constant","Constructor","Control flow","Data structure","Debounce","Deep copy","Deserialization",
         "Dynamic typing","Endianness","Exception","First-class Function","Function","Garbage collection","Global scope",
         "Global variable","Hash function","High-level programming language","Identifier","Immutable","Instance","Interpolation",
         "Key","Keyword","Lazy load","Literal","Local scope","Local variable","Loop","Method","Mutable","Namespace","Null",
         "Object","Object reference","Operand","Operator","Parameter","Parent object","Parse","Parser","Primitive","Recursion",
         "Regular expression","Scope","Serialization","Shallow copy","Signature/Function","Statement","Static method",
         "Static typing","String","Synchronous","Syntax","Syntax error","Thread","Main thread","Throttle","Type",
         "Type coercion","Type Conversion","Value","Variable","Entity","Enumerated","Character encoding","Character set",
         "Character","Unicode","Database","Plugin","Native","Event","Encryption","Decryption","Cipher","Ciphertext",
         "Plaintext","Cryptography","Cryptanalysis","Public-key cryptography","Symmetric-key cryptography","Hoisting",
         "Delta","Locale","Localization","Internationalization","Metadata","Protocol","Prototype","Truthy","Falsy","Nullish",
         "Sloppy mode","Strict mode","Undefined","NaN","Number","BigInt","Engine","Codec","Lossless compression",
         "Lossy compression","Whitespace","Block/Scripting","Block","Long task","Minification","Code splitting","Tree shaking",
         "Polyfill","Global object","Property","Property/JavaScript","Serializable object","Stringifier","Expando","Enumerated",
         "Validator","Semantics","Markup","Server","Latency","Bandwidth","Packet","Signature","Signature/Security","Domain",
         "Domain/Digital","Pixel","Raster image","Quaternion","Bezier curve","Vendor Prefix","RNG","UUID","Unix time"},
 "pyko": {"argument","attribute","binary file","bytecode","callable","callback","class","class variable","closure variable",
          "complex number","context","coroutine","coroutine function","decorator","dictionary","expression","free variable",
          "function","garbage collection","generator","generic type","hashable","interactive","interpreted","iterable","iterator",
          "keyword argument","lambda","lexical analyzer","list","mapping","metaclass","method","module","namespace",
          "nested scope","object","package","parameter","positional argument","qualified name","reference count","sequence",
          "slice","statement","static type checker","strong reference","text encoding","text file","token","type",
          "type alias","type hint","virtual environment","virtual machine","asynchronous iterator","asynchronous iterable",
          "asynchronous generator","annotation","function annotation","variable annotation","immortal","contiguous",
          "special method","magic method","floor division","key function","free threading","importing","importer","loader",
          "finder","descriptor","awaitable","generator expression","dictionary comprehension","list comprehension",
          "set comprehension","current context","context variable","context manager","file object","locale encoding",
          "interpreter shutdown","standard library","thread state"},
 "k8s": {"Garbage Collection","Object","Name","Namespace","Event","Logging","Proxy","uid"},
}
BRANDS = r"Chrome|Firefox|Safari|Edge|Explorer|Gecko|Blink|WebKit|Presto|Trident|Netscape|Opera|Java\b|JavaScript|ECMAScript|Python|PHP|Ruby|Bun|Node\.js|Git\b|Rsync|Houdini|Khronos|Three js|Adobe|Arpanet|Firefox OS|Mozilla|Google|Microsoft|Apple|Usenet|OpenGL|OpenSSL|WebGL|WebAssembly|WebRTC|WebSockets|WebVTT|WebM|WebP|WebExtensions|WebIDL|WebDAV|IndexedDB|XMLHttpRequest|WindowProxy|Docker|Dockershim|etcd|istio|Helm|kube|Kube|minikube|kubectl|kubeadm|kubelet|sysctl|cgroup|CPython|IDLE|Zen of Python|Python 3000|Pythonic|BDFL|__"
PREFIX = r"^(CSS|HTML|HTTP|DOM|ARIA|Grid|Flex|CORS|TCP|Baseline|Fetch|Table|Payload|Request header|Response header|Entity header|General header|Representation header|Forbidden|First |Largest|Time to|Speed index|Page |Layout|Visual Viewport|Viewport|Pseudo|Scroll|Snap|Stacking|Style|Submit|Void element|Script-supporting|Block-level|Inline-level|Ink overflow|Fragmentainer|Alignment|Fallback Alignment|Main Axis|Cross Axis|Intrinsic|Advance measure|Browsing context|Secure Context|Same-origin|Origin|Sticky|Transient|Top layer|Shadow tree|Accessibility tree|Accessible name|Document |Navigation directive|Reporting directive|Fetch directive|Hotlink|Prefetch|Prerender|Preflight|Render blocking|Reflow|Repaint|Jank|Speculative|Media|Tag|Element|Attribute|Doctype|Head$|Quality values|Effective connection|Perceived|Real User|Synthetic|RAIL|Server Timing|Resource Timing|Beacon|Favicon|Slug|Site|Registrable|Domain sharding|Hyperlink|Hypertext|World Wide Web|Web |Responsive|Mobile First|Progressive web|SPA|SSG|Lazy|Canvas|Caret|Breadcrumb|Card sorting|Color wheel|Gamut|RGB|Glyph|Ligature|Accent|Texel|Composite operation|Bounding box|Continuous Media|Gutters|Boolean/|Property/CSS|Block/CSS|Safe|Cacheable|Certified|Privileged|Dominator|Challenge|Application context|Canonical order|Placeholder|Input method editor|Screen reader|Accessibility|User agent|Browser|Developer Tools|Search engine|Crawler|Robots|Site map|Network throttling|Round Trip|Brotli|gzip|Percent-encoding|Base64|Mixin$)"
def bucket(src, g):
    en = g["en"] + ("/" + g["qual"] if g.get("qual") else "")
    if src == "pyko" and not g.get("is_term", True): return None
    if src == "pyko" and (en.startswith(("``", ":")) or en in {"Glossary","callable(argument1, argument2, argumentN)","count: int = 0","magic","special","ellipsis literal","C-contiguous","Fortran contiguous","REPL","stdlib"}): return "X"
    if en in S2[src] or g["en"] in S2[src]: return "S2"
    if en in S1[src] or g["en"] in S1[src]: return "S1"
    if src == "k8s":
        if set(g["tags"]) & {"core-object","tool","community","cri","workload","extension","pod","container","storage","security","networking","operation","user-type","architecture"} or re.search(r"[a-z][A-Z]", g["en"]) or re.search(BRANDS, g["en"]) or re.match(r"(Pod|Container|Kubernetes|API|Cloud|Cluster|Mirror|Static|Init|Ephemeral|Device|Dynamic|Data Plane|Control Plane)", g["en"]):
            return "P"
        return "G"
    if re.fullmatch(r"[A-Z0-9][A-Z0-9 .\-/_]*", g["en"]) and sum(c.isupper() for c in g["en"]) >= 2: return "P"
    if re.search(BRANDS, en) or re.search(PREFIX, en): return "P"
    if src == "pyko":
        return "P"   # remaining Python terms are Python-defined mechanisms/names
    return "G"

out = {}
for src in ["k8s", "mdn", "pyko"]:
    from collections import defaultdict
    b = defaultdict(list)
    for g in r[src]["glossary"]:
        k = bucket(src, g)
        if k: b[k].append(g["en"] + ("/" + g["qual"] if g.get("qual") else ""))
    out[src] = b
    tot = sum(len(v) for k, v in b.items() if k != "X")
    print(f"== {src}: total(valid)={tot}", {k: len(v) for k, v in sorted(b.items())},
          {k: f"{100*len(v)/tot:.1f}%" for k, v in sorted(b.items()) if k != "X"})
    for k in ["S2", "G"] + (["X"] if src == "pyko" else []):
        print(f"  {k}: " + " | ".join(b.get(k, [])))
json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
