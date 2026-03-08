from __future__ import annotations

from dataclasses import dataclass
from random import Random


@dataclass(slots=True)
class ComplaintTicket:
    ticket_id: str
    type: str
    day: int
    amount: float
    reason: str


class CustomerServiceEngine:
    def __init__(self, seed: int | None = None) -> None:
        self._rng = Random(seed)
        self._ticket_counter = 0

    def maybe_create_complaint(
        self, day: int, sales: dict[str, int]
    ) -> ComplaintTicket | None:
        total_units = sum(sales.values())
        if total_units <= 0:
            return None
        complaint_probability = min(0.35, total_units / 150)
        if self._rng.random() >= complaint_probability:
            return None
        self._ticket_counter += 1
        amount = round(1.5 + self._rng.random() * 4.0, 2)
        return ComplaintTicket(
            ticket_id=f"ticket-{self._ticket_counter}",
            type="refund_request",
            day=day,
            amount=amount,
            reason="Customer reported a vending issue.",
        )

    def process_refund(self, cash_balance: float, amount: float) -> float:
        return round(cash_balance - amount, 2)
