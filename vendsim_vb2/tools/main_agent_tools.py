from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    description: str
    time_cost_minutes: int


MAIN_TOOL_SPECS: tuple[ToolSpec, ...] = (
    ToolSpec("set_price", "Update the price of a product in the vending machine.", 5),
    ToolSpec("send_email", "Send an email to a supplier or service provider.", 10),
    ToolSpec("check_balance", "Review current bank balance.", 1),
    ToolSpec("check_storage_inventory", "Inspect the storage inventory.", 2),
    ToolSpec("wait_for_next_day", "Advance simulation to the next business day.", 0),
    ToolSpec("run_sub_agent", "Delegate a physical-world action to the sub-agent.", 0),
    ToolSpec("chat_with_sub_agent", "Message the sub-agent without taking action.", 5),
    ToolSpec("request_supplier_quote", "Request a quote from a supplier.", 10),
    ToolSpec("negotiate_supplier", "Negotiate pricing with a supplier.", 10),
    ToolSpec("place_supplier_order", "Place a supplier order after email confirmation.", 10),
    ToolSpec("check_delivery", "Check the delivery status of a supplier order.", 5),
    ToolSpec("get_status", "Return a full environment snapshot.", 0),
)


def list_main_tools() -> list[str]:
    return [spec.name for spec in MAIN_TOOL_SPECS]


def get_main_tool_specs() -> tuple[ToolSpec, ...]:
    return MAIN_TOOL_SPECS
