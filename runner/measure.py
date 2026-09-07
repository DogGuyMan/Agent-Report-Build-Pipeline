#!/usr/bin/env python3
"""세 실행기가 함께 쓰는 재는 코드. 형 · 좁히기 도우미 · 표 그리기 · 하트비트.

**`machine/` 을 import 하지 않는다.** 여기를 import 하는 것만으로 해석기가 바뀌거나
무거운 라이브러리가 실리면 안 된다.

**`Any` 를 쓰지 않는다.** 바깥 프로그램이 꼴을 정하는 값은 `object` 로 받고 아래
좁히기 도우미로 하나씩 확인한다.
"""
from typing import NotRequired, TypedDict, cast

# `claude -p --output-format json` 이 stdout 으로 내는 객체 하나. 꼴을 정하는 것은 바깥
# 프로그램이라 칸을 못 박지 않는다. 값은 `object` 이므로 읽는 자리에서 좁힌다.
AgentResult = dict[str, object]

# 잰 값 한 묶음. 정수 여섯에 실수 하나(`cost_usd`)가 섞인 의도된 이종 사전이다.
# 값 타입을 `float` 으로 적는 것은 파이썬에서 정수가 실수의 부분형이라 둘 다 담기기 때문이다.
Usage = dict[str, float]


class StageRow(TypedDict):
    """측정 표의 한 줄. 세 실행기가 모두 이 꼴로 쌓고 `format_report` 가 읽는다.

    `skipped` 만 선택 항목이다 — 건너뛴 단계에만 붙는다.
    """

    stage: str
    seconds: float
    usage: Usage
    ok: bool
    why: str
    skipped: NotRequired[bool]


# ── 좁히기 도우미. `object` 를 쓸 수 있는 형으로 바꾸는 자리는 여기뿐이다 ──


def as_map(v: object) -> dict[str, object]:
    """열쇠가 문자열인 사전이면 그것을, 아니면 빈 사전을 낸다."""
    if not isinstance(v, dict):
        return {}
    items = cast(dict[object, object], v).items()
    return {k: x for k, x in items if isinstance(k, str)}


def as_int(v: object) -> int:
    """정수면 그것을, 아니면 0. `bool` 은 정수가 아니다 — 참/거짓이 수로 세어지면 안 된다."""
    return v if isinstance(v, int) and not isinstance(v, bool) else 0


def as_float(v: object) -> float:
    """정수나 실수면 실수로, 아니면 0.0. `bool` 은 제외한다."""
    if isinstance(v, bool):
        return 0.0
    return float(v) if isinstance(v, (int, float)) else 0.0


def as_str(v: object) -> str:
    """문자열이면 그것을, 아니면 빈 문자열."""
    return v if isinstance(v, str) else ""
