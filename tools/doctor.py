def line(name: str, version: str | None, required: bool) -> str:
    if version:
        return f"OK      {name:15} {version}"
    else:
        return f"{'없음(필수)' if required else '선택'}    {name:15} (설치되지 않음)"
