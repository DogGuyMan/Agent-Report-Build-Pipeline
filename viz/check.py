import re

from typing import Union

def countScripts(html: str) -> dict[str, Union[int, bool]]:
    count = len(re.findall(r'<script\b', html, re.IGNORECASE))
    return {"count": count, "ok": count <= 1}

def linkIntegrity(decisionIds: list[str], reportHtml: str) -> dict[str, Union[bool, list[str]]]:
    sections = re.findall(r'<Section\s+title="([^"]+)"', reportHtml)
    sectionIds = []
    for s in sections:
        m = re.match(r'^([^—\s]+)', s)
        if m:
            sectionIds.append(m.group(1))
    
    missing = [d for d in decisionIds if d not in sectionIds]
    orphans = [s for s in sectionIds if s not in decisionIds]
    
    ok = len(missing) == 0 and len(orphans) == 0
    return {"ok": ok, "missingSections": missing, "orphanSections": orphans}

def versionMatch(dataVersion: str, builderVersion: str) -> dict[str, bool]:
    match = (dataVersion == builderVersion)
    return {"ok": True, "warn": not match}
