"""Share of product-bound entries in an MS glossary xlsx by deterministic markers."""
import sys, re, collections, importlib.util, os
spec = importlib.util.spec_from_file_location("x", os.path.join(os.path.dirname(os.path.abspath(__file__)), "msxlsx_lib.py"))
x = importlib.util.module_from_spec(spec); spec.loader.exec_module(x)
PROD = r"\b(Microsoft|Azure|Dynamics|Office|Windows|SharePoint|Exchange|Xbox|XBOX|Teams|Visual Studio|Skype|Outlook|Excel|PowerPoint|OneDrive|OneNote|Bing|SQL Server|Power BI|Power Apps|Power Automate|Lync|Intune|Entra|Copilot|Cortana|Edge|Hyper-V|Active Directory|Yammer|Visio|Access|Publisher|InfoPath|Project Online|Viva|Defender|Sentinel|Purview|Fabric|Surface|HoloLens|Kinect|MSN|Hotmail|Live|Zune|Silverlight|\.NET|ASP\.NET|Win32|COM\+?|DirectX|WPF|UWP|BizTalk|System Center|Forefront|SCCM|Dataverse|LinkedIn|GitHub|Minecraft)\b"
for path in sys.argv[1:]:
    rs = list(x.rows(path))[1:]
    pos = collections.Counter(r.get("D", "").replace("en-US-partOfSpeech: ", "") for r in rs)
    n = len(rs)
    prod_def = sum(1 for r in rs if re.search(PROD, r.get("C", "")))
    prod_term = sum(1 for r in rs if re.search(PROD, r.get("A", "")))
    proper = pos.get("Proper Noun", 0)
    any_marker = sum(1 for r in rs if re.search(PROD, r.get("C", "")) or re.search(PROD, r.get("A", "")) or "Proper Noun" in r.get("D", ""))
    print(path.split("/")[-1], "n", n, "pos", dict(pos.most_common(6)))
    print(f"  proper noun {proper} ({100*proper/n:.1f}%) | def mentions MS product {prod_def} ({100*prod_def/n:.1f}%) | term contains product {prod_term} ({100*prod_term/n:.1f}%) | any marker {any_marker} ({100*any_marker/n:.1f}%)")
    # definitions mentioning programming/software-engineering words
    se = sum(1 for r in rs if re.search(r"\b(object-oriented|class|method|subroutine|function|module|programming|compiler|source code|software design|design pattern|algorithm|data structure)\b", r.get("C", ""), re.I))
    print(f"  def mentions programming vocabulary {se} ({100*se/n:.1f}%)")
