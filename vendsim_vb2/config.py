from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class VB2Config:
    starting_balance: float = 500.0
    daily_machine_fee: float = 2.0
    episode_days: int = 365
    bankruptcy_consecutive_negative_days: int = 10
    output_token_cost_per_million: float = 100.0
    storage_address: str = "1680 Mission St, San Francisco"
    machine_address: str = "1421 Bay St, San Francisco"
    restock_travel_time_minutes: int = 75
    supplier_message_time_minutes: int = 10
    delivery_check_time_minutes: int = 5
    minutes_per_day: int = 24 * 60
    machine_small_rows: int = 2
    machine_large_rows: int = 2
    machine_slots_per_row: int = 3
