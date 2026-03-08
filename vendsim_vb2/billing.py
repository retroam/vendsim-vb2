from __future__ import annotations


def apply_weekly_costs(
    cash_balance: float,
    weekly_output_tokens: int,
    token_cost_per_million: float,
    daily_fee: float,
    days_in_week: int,
) -> float:
    token_cost = (weekly_output_tokens / 1_000_000) * token_cost_per_million
    total_cost = token_cost + (daily_fee * days_in_week)
    return round(cash_balance - total_cost, 2)
