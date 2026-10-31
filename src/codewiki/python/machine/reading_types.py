"""전수조사 원본 `terms-reading.json` 의 모양. `does` 와 `confidence` 만 선택이고 나머지는 모든 레코드에 있다."""
from typing import NotRequired, TypedDict


class Use(TypedDict):
    """`uses[]` 한 칸 — 이 용어가 무엇을 쓰는가."""
    to: str
    kind: str
    label: str
    where: str
    source: NotRequired[str]


class Term(TypedDict):
    """용어 하나. 열쇠 이름은 json 의 것 그대로다."""
    kind: str
    means: str
    module: str
    source: str
    where: str
    uses: list[Use]
    does: NotRequired[str]
    confidence: NotRequired[str]


# {용어 id: 레코드}. json 최상위가 이 모양이다.
Terms = dict[str, Term]
