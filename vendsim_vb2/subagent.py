from __future__ import annotations

from dataclasses import dataclass, field

from vendsim_vb2.config import VB2Config
from vendsim_vb2.demand import PRODUCTS

MACHINE_LAYOUT = {
    "small_rows": 2,
    "large_rows": 2,
    "slots_per_row": 3,
    "total_slots": 12,
}

RESTOCK_TRAVEL_TIME_MINUTES = 75


@dataclass(slots=True)
class SubAgent:
    config: VB2Config = field(default_factory=VB2Config)
    machine_inventory: dict[str, int] = field(default_factory=dict)
    machine_cash: float = 0.0

    def specs(self) -> dict[str, object]:
        return {
            "name": "physical-ops-sub-agent",
            "tools": ["restock_machine", "collect_cash", "get_machine_inventory"],
        }

    def machine_layout(self) -> dict[str, int]:
        return dict(MACHINE_LAYOUT)

    def restock_machine(self, product: str, qty: int) -> dict[str, object]:
        if qty <= 0:
            return {"status": "rejected", "message": "qty must be positive"}
        size = str(PRODUCTS.get(product, {}).get("size", "small"))
        max_slots = MACHINE_LAYOUT[f"{size}_rows"] * MACHINE_LAYOUT["slots_per_row"]
        current = sum(
            units
            for stocked_product, units in self.machine_inventory.items()
            if str(PRODUCTS.get(stocked_product, {}).get("size", "small")) == size
        )
        if current + qty > max_slots:
            return {"status": "rejected", "message": f"{size} slots full"}
        self.machine_inventory[product] = self.machine_inventory.get(product, 0) + qty
        return {
            "status": "ok",
            "time_cost_minutes": self.config.restock_travel_time_minutes,
            "machine_inventory": dict(self.machine_inventory),
        }

    def collect_cash(self) -> dict[str, object]:
        collected = round(self.machine_cash, 2)
        self.machine_cash = 0.0
        return {
            "status": "ok",
            "amount_collected": collected,
            "time_cost_minutes": self.config.restock_travel_time_minutes,
        }

    def get_machine_inventory(self) -> dict[str, int]:
        return dict(self.machine_inventory)
