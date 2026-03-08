from __future__ import annotations

from dataclasses import dataclass, field

from vendsim_vb2.config import VB2Config


@dataclass(slots=True)
class Reminder:
    day: int
    message: str


@dataclass(slots=True)
class SimulationState:
    day_index: int
    minute_of_day: int
    cash_balance: float
    storage_inventory: dict[str, int] = field(default_factory=dict)
    machine_inventory: dict[str, int] = field(default_factory=dict)
    machine_cash: float = 0.0
    weekly_output_tokens: int = 0
    consecutive_negative_days: int = 0
    scratchpad: list[str] = field(default_factory=list)
    reminders: list[Reminder] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    email_log: list[dict[str, object]] = field(default_factory=list)
    subagent_chat_log: list[str] = field(default_factory=list)
    daily_sales_history: list[dict[str, object]] = field(default_factory=list)
    prices: dict[str, float] = field(default_factory=dict)

    @classmethod
    def new_episode(cls, config: VB2Config | None = None) -> "SimulationState":
        cfg = config or VB2Config()
        return cls(day_index=1, minute_of_day=0, cash_balance=cfg.starting_balance)

    def advance_minutes(self, minutes: int) -> None:
        if minutes < 0:
            raise ValueError("minutes must be non-negative")
        total = self.minute_of_day + minutes
        self.day_index += total // (24 * 60)
        self.minute_of_day = total % (24 * 60)

    def add_reminder(self, day: int, message: str) -> None:
        self.reminders.append(Reminder(day=day, message=message))

    def snapshot(self) -> dict[str, object]:
        return {
            "day_index": self.day_index,
            "minute_of_day": self.minute_of_day,
            "cash_balance": round(self.cash_balance, 2),
            "storage_inventory": dict(self.storage_inventory),
            "machine_inventory": dict(self.machine_inventory),
            "machine_cash": round(self.machine_cash, 2),
            "weekly_output_tokens": self.weekly_output_tokens,
            "consecutive_negative_days": self.consecutive_negative_days,
            "scratchpad": list(self.scratchpad),
            "reminders": [{"day": r.day, "message": r.message} for r in self.reminders],
            "notes": list(self.notes),
            "email_log": [dict(entry) for entry in self.email_log],
            "subagent_chat_log": list(self.subagent_chat_log),
            "prices": dict(self.prices),
        }
