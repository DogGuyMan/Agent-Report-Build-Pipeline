"""jsonio.py — JSON 파일을 같은 폴더의 임시 파일에 쓰고 `os.replace` 로 바꿔 끼운다. 도중에 끊겨도 옛 파일이 그대로 남는다."""
import json
import os
import tempfile


def write_json_atomic(path: str, obj: object, indent: int = 2, trailing_newline: bool = False,
                      sort_keys: bool = False) -> None:
    """`path` 를 `obj` 의 JSON 으로 바꿔 끼운다. 같은 입력이면 같은 바이트다. `sort_keys` 면 사전의 열쇠를 정렬해 쓴다."""
    folder = os.path.dirname(os.path.abspath(path))
    os.makedirs(folder, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=folder, prefix="." + os.path.basename(path) + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=indent, sort_keys=sort_keys)
            if trailing_newline:
                f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
