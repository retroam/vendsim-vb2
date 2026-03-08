from __future__ import annotations


def compute_reward(
    final_bank_balance: float, dense_components: list[float], use_dense: bool
) -> float:
    if not use_dense:
        return final_bank_balance
    return final_bank_balance + sum(dense_components)
