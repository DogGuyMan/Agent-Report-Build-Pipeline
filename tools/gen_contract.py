#!/usr/bin/env python3
"""계약 리소스 `contracts/mode1-artifacts.v1.json` 과 지문 `.sha256` 을 Mode 1 의 형에서 낸다.

두 저장소에 같은 사본으로 산다. report-builder 는 이 파일에서 자기 형을 생성한다(`tools/gen_contract_types.py`).
`title` · `description`(클래스 이름 · 독스트링)은 뗀다. `types` 가 파일마다의 최상위 형 이름을 알려 준다.

    python tools/gen_contract.py            # 쓴다
    python tools/gen_contract.py --check    # 낡았으면 exit 1
"""
import argparse
import hashlib
import json
import os
import sys
from collections.abc import Sequence
from typing import cast

import msgspec

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "machine"))
import manifest as MF  # noqa: E402
import terms_db  # noqa: E402

JSON_PATH = os.path.join(ROOT, "contracts", "mode1-artifacts.v1.json")
SHA_PATH = os.path.join(ROOT, "contracts", "mode1-artifacts.v1.sha256")


def strip_names(node: object) -> object:
    """스키마 객체에서 `title` · `description` 을 뗀다. `properties` · `$defs` 안의 칸 이름은 남긴다."""
    if isinstance(node, list):
        return [strip_names(v) for v in cast(list[object], node)]
    if not isinstance(node, dict):
        return node
    out: dict[str, object] = {}
    for k, v in cast(dict[str, object], node).items():
        if k in ("title", "description"):
            continue
        if k in ("properties", "$defs") and isinstance(v, dict):
            out[k] = {name: strip_names(sub) for name, sub in cast(dict[str, object], v).items()}
        else:
            out[k] = strip_names(v)
    return out


def contract_text() -> str:
    """계약 JSON 본문. 열쇠를 정렬해 같은 형이면 같은 바이트다."""
    doc = {"contract": MF.CONTRACT, "version": MF.VERSION,
           "types": {"terms-db.json": "TermsDb", "manifest.json": "ArtifactManifest"},
           "schemas": {"terms-db.json": strip_names(msgspec.json.schema(terms_db.TermsDb)),
                       "manifest.json": strip_names(msgspec.json.schema(MF.ArtifactManifest))}}
    return json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def sha_text(text: str) -> str:
    """`sha256sum -c` 가 읽는 한 줄 — 계약 본문의 지문과 파일 이름."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest() + "  " + os.path.basename(JSON_PATH) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    """계약 리소스와 지문을 쓴다. `--check` 면 쓰지 않고 파일이 형과 같은지만 본다."""
    ap = argparse.ArgumentParser(description="계약 리소스를 형에서 낸다")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    text = contract_text()
    if a.check:
        try:
            with open(JSON_PATH, encoding="utf-8") as f1, open(SHA_PATH, encoding="utf-8") as f2:
                same = f1.read() == text and f2.read() == sha_text(text)
        except OSError:
            same = False
        if not same:
            print("계약 리소스가 형과 다르다 — python tools/gen_contract.py 로 다시 낸다. "
                  "열쇠를 빼거나 뜻을 바꿨다면 v2 로 판을 올린다", file=sys.stderr)
            return 1
        return 0
    os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        f.write(text)
    with open(SHA_PATH, "w", encoding="utf-8") as f:
        f.write(sha_text(text))
    print(JSON_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
