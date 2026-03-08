from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Any

from vendsim_vb2.billing import apply_weekly_costs
from vendsim_vb2.config import VB2Config
from vendsim_vb2.customer_service import CustomerServiceEngine
from vendsim_vb2.demand import (
    PRODUCTS,
    compute_daily_sales,
    day_of_week_for_day,
    season_for_day,
    weather_for_day,
)
from vendsim_vb2.state import SimulationState
from vendsim_vb2.subagent import SubAgent
from vendsim_vb2.suppliers import SupplierEngine
from vendsim_vb2.tools.main_agent_tools import get_main_tool_specs
from vendsim_vb2.tools.memory_tools import get_memory_tool_specs


@dataclass(slots=True)
class ToolCallResult:
    status: str
    payload: dict[str, Any]


class VendingBench2Environment:
    def __init__(
        self,
        config: VB2Config | None = None,
        seed: int | None = None,
        use_dense_rewards: bool = False,
    ) -> None:
        self.config = config or VB2Config()
        self._seed = seed
        self._rng = Random(seed)
        self.use_dense_rewards = use_dense_rewards
        self.suppliers = SupplierEngine(seed=seed)
        self.customer_service = CustomerServiceEngine(seed=seed)
        self.subagent = SubAgent(config=self.config)
        self.state = self.reset()

    def reset(self) -> SimulationState:
        self._rng = Random(self._seed)
        self.suppliers = SupplierEngine(seed=self._seed)
        self.customer_service = CustomerServiceEngine(seed=self._seed)
        self.subagent = SubAgent(config=self.config)
        self.state = SimulationState.new_episode(self.config)
        self.state.prices = {
            product: float(spec["ideal_price"]) for product, spec in PRODUCTS.items()
        }
        return self.state

    def tool_registry(self) -> dict[str, list[str]]:
        return {
            "main": [spec.name for spec in get_main_tool_specs()],
            "memory": [spec.name for spec in get_memory_tool_specs()],
            "subagent": list(self.subagent.specs()["tools"]),
        }

    def _log_email(
        self,
        *,
        sender: str,
        recipient: str,
        subject: str,
        body: str,
        category: str = "email",
    ) -> None:
        self.state.email_log.append(
            {
                "day": self.state.day_index,
                "minute_of_day": self.state.minute_of_day,
                "sender": sender,
                "recipient": recipient,
                "subject": subject,
                "body": body,
                "category": category,
            }
        )

    def resolve_delivery(self, order_id: str) -> ToolCallResult:
        """Check delivery status; on success, add items to storage and charge cost."""
        delivery = self.suppliers.simulate_delivery(order_id)
        order = self.suppliers._orders[order_id]
        if delivery.status in {"delivered", "delayed", "partial"} and delivery.delivered_qty > 0:
            product = order.product
            self.state.storage_inventory[product] = (
                self.state.storage_inventory.get(product, 0) + delivery.delivered_qty
            )
            cost = round(delivery.final_unit_price * delivery.delivered_qty, 2)
            self.state.cash_balance = round(self.state.cash_balance - cost, 2)
        self.state.advance_minutes(self.config.delivery_check_time_minutes)
        self._log_email(
            sender=order.supplier_name,
            recipient="charles.paxton",
            subject=f"Delivery update for {order.order_id}",
            body=(
                f"Status={delivery.status}; delivered_qty={delivery.delivered_qty}; "
                f"days_late={delivery.days_late}; final_unit_price={delivery.final_unit_price}"
            ),
            category="supplier_delivery",
        )
        return ToolCallResult(
            delivery.status,
            {
                "order_id": delivery.order_id,
                "delivered_qty": delivery.delivered_qty,
                "days_late": delivery.days_late,
                "final_unit_price": delivery.final_unit_price,
            },
        )

    def set_price(self, product: str, price: float) -> ToolCallResult:
        self.state.prices[product] = round(price, 2)
        self.state.advance_minutes(5)
        return ToolCallResult(
            "ok", {"product": product, "price": self.state.prices[product]}
        )

    def send_email(self, recipient: str, subject: str, body: str) -> ToolCallResult:
        self._log_email(
            sender="charles.paxton",
            recipient=recipient,
            subject=subject,
            body=body,
            category="manual_email",
        )
        self.state.advance_minutes(self.config.supplier_message_time_minutes)
        return ToolCallResult("ok", {"recipient": recipient, "queued": True})

    def check_balance(self) -> ToolCallResult:
        self.state.advance_minutes(1)
        return ToolCallResult("ok", {"cash_balance": round(self.state.cash_balance, 2)})

    def check_storage_inventory(self) -> ToolCallResult:
        self.state.advance_minutes(2)
        return ToolCallResult(
            "ok", {"storage_inventory": dict(self.state.storage_inventory)}
        )

    def chat_with_sub_agent(self, message: str) -> ToolCallResult:
        self.state.subagent_chat_log.append(message)
        self.state.advance_minutes(5)
        return ToolCallResult("ok", {"message": message})

    def request_supplier_quote(self, product: str, qty: int) -> ToolCallResult:
        quote = self.suppliers.request_quote(product, qty)
        subject = f"Quote request for {qty} units of {product}"
        self._log_email(
            sender="charles.paxton",
            recipient=quote.supplier_name,
            subject=subject,
            body=f"Please quote {qty} units of {product}.",
            category="supplier_quote_request",
        )
        self.state.advance_minutes(self.config.supplier_message_time_minutes)
        self._log_email(
            sender=quote.supplier_name,
            recipient="charles.paxton",
            subject=f"Quote response for {product}",
            body=(
                f"quote_id={quote.quote_id}; qty={quote.qty}; "
                f"unit_price={quote.unit_price}; fair_unit_price={quote.fair_unit_price}"
            ),
            category="supplier_quote_response",
        )
        return ToolCallResult(
            "ok",
            {
                "quote_id": quote.quote_id,
                "product": quote.product,
                "qty": quote.qty,
                "unit_price": quote.unit_price,
                "supplier_name": quote.supplier_name,
            },
        )

    def negotiate_supplier(
        self, quote_id: str, proposed_unit_price: float
    ) -> ToolCallResult:
        quote = self.suppliers._quotes[quote_id]
        response = self.suppliers.negotiate(quote_id, proposed_unit_price)
        self._log_email(
            sender="charles.paxton",
            recipient=quote.supplier_name,
            subject=f"Counteroffer for {quote.product}",
            body=(
                f"quote_id={quote_id}; proposed_unit_price={round(proposed_unit_price, 2)}"
            ),
            category="supplier_negotiation_request",
        )
        self.state.advance_minutes(self.config.supplier_message_time_minutes)
        self._log_email(
            sender=quote.supplier_name,
            recipient="charles.paxton",
            subject=f"Negotiation response for {quote.product}",
            body=(
                f"quote_id={response.quote_id}; status={response.status}; "
                f"unit_price={response.unit_price}; message={response.message}"
            ),
            category="supplier_negotiation_response",
        )
        return ToolCallResult(
            response.status,
            {
                "quote_id": response.quote_id,
                "unit_price": response.unit_price,
                "message": response.message,
            },
        )

    def place_supplier_order(self, product: str, qty: int) -> ToolCallResult:
        order = self.suppliers.place_email_confirmed_order(product, qty)
        self._log_email(
            sender="charles.paxton",
            recipient=order.supplier_name,
            subject=f"Purchase order for {product}",
            body=f"Please ship {qty} units of {product}.",
            category="supplier_order_request",
        )
        self.state.advance_minutes(self.config.supplier_message_time_minutes)
        self._log_email(
            sender=order.supplier_name,
            recipient="charles.paxton",
            subject=f"Order confirmation for {product}",
            body=(
                f"order_id={order.order_id}; qty={order.qty}; unit_price={order.unit_price}; "
                f"may_bait_and_switch={order.may_bait_and_switch}"
            ),
            category="supplier_order_confirmation",
        )
        return ToolCallResult(
            order.status,
            {
                "order_id": order.order_id,
                "product": order.product,
                "qty": order.qty,
                "unit_price": order.unit_price,
                "supplier_name": order.supplier_name,
            },
        )

    def run_sub_agent(self, tool_name: str, **kwargs: Any) -> ToolCallResult:
        if tool_name == "restock_machine":
            product = str(kwargs["product"])
            qty = int(kwargs["qty"])
            available = self.state.storage_inventory.get(product, 0)
            if available < qty:
                return ToolCallResult(
                    "rejected",
                    {
                        "message": f"insufficient storage inventory for {product}",
                        "available": available,
                    },
                )
            result = self.subagent.restock_machine(product, qty)
            if result.get("status") == "ok":
                self.state.storage_inventory[product] = available - qty
                if self.state.storage_inventory[product] == 0:
                    del self.state.storage_inventory[product]
                self.state.machine_inventory = dict(self.subagent.machine_inventory)
                self.state.advance_minutes(int(result["time_cost_minutes"]))
            return ToolCallResult(str(result["status"]), dict(result))
        if tool_name == "collect_cash":
            self.subagent.machine_cash = self.state.machine_cash
            result = self.subagent.collect_cash()
            self.state.machine_cash = self.subagent.machine_cash
            self.state.cash_balance = round(
                self.state.cash_balance + float(result["amount_collected"]), 2
            )
            self.state.advance_minutes(int(result["time_cost_minutes"]))
            return ToolCallResult("ok", dict(result))
        if tool_name == "get_machine_inventory":
            return ToolCallResult(
                "ok", {"machine_inventory": self.subagent.get_machine_inventory()}
            )
        raise KeyError(f"unknown sub-agent tool: {tool_name}")

    def write_scratchpad(self, note: str) -> ToolCallResult:
        self.state.scratchpad.append(note)
        self.state.notes.append(note)
        return ToolCallResult("ok", {"note_count": len(self.state.scratchpad)})

    def read_scratchpad(self) -> ToolCallResult:
        return ToolCallResult("ok", {"scratchpad": list(self.state.scratchpad)})

    def search_notes(self, query: str) -> ToolCallResult:
        query_lower = query.lower()
        matches = [note for note in self.state.notes if query_lower in note.lower()]
        return ToolCallResult("ok", {"matches": matches})

    def set_reminder(self, day: int, message: str) -> ToolCallResult:
        self.state.add_reminder(day, message)
        return ToolCallResult("ok", {"day": day, "message": message})

    def record_output_tokens(self, count: int) -> None:
        self.state.weekly_output_tokens += count

    def wait_for_next_day(self, output_tokens: int = 0) -> ToolCallResult:
        self.record_output_tokens(output_tokens)
        weather = weather_for_day(self.state.day_index)
        season = season_for_day(self.state.day_index)
        day_of_week = day_of_week_for_day(self.state.day_index)
        sales_result = compute_daily_sales(
            products=list(self.state.machine_inventory),
            prices=self.state.prices,
            weather=weather,
            season=season,
            day_of_week=day_of_week,
            inventory=self.state.machine_inventory,
            seed=self._rng.randint(0, 1_000_000),
        )
        for product, sold in sales_result.units_sold.items():
            if product in self.subagent.machine_inventory:
                remaining = self.subagent.machine_inventory[product] - sold
                if remaining > 0:
                    self.subagent.machine_inventory[product] = remaining
                else:
                    del self.subagent.machine_inventory[product]
        self.state.machine_inventory = dict(self.subagent.machine_inventory)
        # Revenue goes into the machine coin box only — collected via collect_cash
        self.state.machine_cash = round(
            self.state.machine_cash + sales_result.revenue, 2
        )
        complaint = self.customer_service.maybe_create_complaint(
            self.state.day_index, sales_result.units_sold
        )
        refund_amount = 0.0
        if complaint is not None:
            refund_amount = complaint.amount
            self.state.cash_balance = self.customer_service.process_refund(
                self.state.cash_balance, complaint.amount
            )
        self.state.cash_balance = round(
            self.state.cash_balance - self.config.daily_machine_fee, 2
        )
        if self.state.cash_balance < 0:
            self.state.consecutive_negative_days += 1
        else:
            self.state.consecutive_negative_days = 0
        if self.state.day_index % 7 == 0:
            self.state.cash_balance = apply_weekly_costs(
                cash_balance=self.state.cash_balance
                + (self.config.daily_machine_fee * 7),
                weekly_output_tokens=self.state.weekly_output_tokens,
                token_cost_per_million=self.config.output_token_cost_per_million,
                daily_fee=self.config.daily_machine_fee,
                days_in_week=7,
            )
            self.state.weekly_output_tokens = 0
        self.suppliers.tick_supplier_health(days=1)
        self.state.daily_sales_history.append(
            {
                "day": self.state.day_index,
                "weather": weather,
                "season": season,
                "day_of_week": day_of_week,
                "sales": dict(sales_result.units_sold),
                "revenue": sales_result.revenue,
                "refund_amount": refund_amount,
                "debug": dict(sales_result.debug),
            }
        )
        self.state.day_index += 1
        self.state.minute_of_day = 0
        return ToolCallResult(
            "ok",
            {
                "sales": dict(sales_result.units_sold),
                "revenue": sales_result.revenue,
                "weather": weather,
                "refund_amount": refund_amount,
            },
        )

    def final_score(self) -> float:
        """Score is final bank balance only (per spec)."""
        return round(self.state.cash_balance, 2)

    def is_done(self) -> bool:
        return (
            self.state.day_index > self.config.episode_days
            or self.state.consecutive_negative_days
            >= self.config.bankruptcy_consecutive_negative_days
        )

    def snapshot(self) -> dict[str, Any]:
        data = self.state.snapshot()
        data["tools"] = self.tool_registry()
        data["done"] = self.is_done()
        return data
