"""측정 표의 행을 스스로 내는 단계의 믹스인."""
import time

import measure as M


class Measured:
    """측정 표의 행(`measure.StageRow`) 하나를 스스로 내는 단계 — 토큰 0, 자기 이름, 경과 초.

    기계 단계는 `MachineStage.perform` 이, LLM 단계는 `LlmStage.harvest` 가 행을 만든다.
    같은 프로세스의 파이썬 단계와, `perform` 을 앞에서 가로채 실패나 건너뜀을 내는
    LLM 단계는 스스로 만들어야 하므로 이것을 상속한다.
    """
    name: str = ""

    def row(self, t0: float, ok: bool, why: str = "") -> M.StageRow:
        return {"stage": self.name, "seconds": time.monotonic() - t0,
                "usage": M.normalize_usage(None), "ok": ok, "why": why}
