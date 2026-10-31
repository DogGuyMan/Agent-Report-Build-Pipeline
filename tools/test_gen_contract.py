"""계약 리소스가 Mode 1 의 형에서 나온 것과 같은지, 이름 떼기가 스키마의 이름만 떼는지 본다."""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_contract as G  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_계약_파일이_형과_같다():
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "gen_contract.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_strip_names_는_스키마의_title_description_만_뗀다():
    got = G.strip_names({"title": "A", "description": "d", "type": "object",
                         "properties": {"title": {"type": "string", "description": "칸"}}})
    assert got == {"type": "object", "properties": {"title": {"type": "string"}}}
