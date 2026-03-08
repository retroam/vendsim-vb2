from __future__ import annotations

from dataclasses import dataclass
from random import Random

from vendsim_vb2.demand import PRODUCTS


@dataclass(slots=True)
class Quote:
    quote_id: str
    product: str
    qty: int
    unit_price: float
    fair_unit_price: float
    supplier_name: str


@dataclass(slots=True)
class NegotiationResponse:
    quote_id: str
    status: str
    unit_price: float
    message: str


@dataclass(slots=True)
class SupplierOrder:
    order_id: str
    product: str
    qty: int
    unit_price: float
    supplier_name: str
    may_bait_and_switch: bool
    status: str = "confirmed"


@dataclass(slots=True)
class DeliveryTimeline:
    order_id: str
    status: str
    delivered_qty: int
    days_late: int
    final_unit_price: float


class SupplierEngine:
    def __init__(self, seed: int | None = None) -> None:
        self._rng = Random(seed)
        self._quotes: dict[str, Quote] = {}
        self._orders: dict[str, SupplierOrder] = {}
        self._resolved_deliveries: dict[str, DeliveryTimeline] = {}
        self._quote_counter = 0
        self._order_counter = 0
        self._health = "active"

    def request_quote(self, product: str, qty: int) -> Quote:
        fair_price = float(PRODUCTS.get(product, {}).get("wholesale_price", 1.0))
        markup = 0.85 + (self._rng.random() * 1.4)
        quoted_price = round(fair_price * markup, 2)
        self._quote_counter += 1
        quote = Quote(
            quote_id=f"quote-{self._quote_counter}",
            product=product,
            qty=qty,
            unit_price=quoted_price,
            fair_unit_price=round(fair_price, 2),
            supplier_name=f"supplier-{self._rng.randint(1, 5)}",
        )
        self._quotes[quote.quote_id] = quote
        return quote

    def negotiate(
        self, quote_id: str, proposed_unit_price: float
    ) -> NegotiationResponse:
        quote = self._quotes[quote_id]
        floor_price = round(quote.fair_unit_price * 0.9, 2)
        if proposed_unit_price >= quote.unit_price:
            return NegotiationResponse(
                quote_id=quote_id,
                status="accepted",
                unit_price=round(proposed_unit_price, 2),
                message="Accepted at your proposed price.",
            )
        if proposed_unit_price >= floor_price:
            if self._rng.random() < 0.55:
                return NegotiationResponse(
                    quote_id=quote_id,
                    status="accepted",
                    unit_price=round(proposed_unit_price, 2),
                    message="Accepted after negotiation.",
                )
            counter_price = round((proposed_unit_price + quote.unit_price) / 2, 2)
            return NegotiationResponse(
                quote_id=quote_id,
                status="countered",
                unit_price=counter_price,
                message="Counteroffer issued.",
            )
        return NegotiationResponse(
            quote_id=quote_id,
            status="rejected",
            unit_price=quote.unit_price,
            message="Offer too low.",
        )

    def place_email_confirmed_order(self, product: str, qty: int) -> SupplierOrder:
        fair_price = float(PRODUCTS.get(product, {}).get("wholesale_price", 1.0))
        unit_price = round(fair_price * (0.95 + self._rng.random() * 0.5), 2)
        self._order_counter += 1
        order = SupplierOrder(
            order_id=f"order-{self._order_counter}",
            product=product,
            qty=qty,
            unit_price=unit_price,
            supplier_name=f"supplier-{self._rng.randint(1, 5)}",
            may_bait_and_switch=self._rng.random() < 0.35,
        )
        self._orders[order.order_id] = order
        return order

    def simulate_delivery(self, order_id: str) -> DeliveryTimeline:
        # Return cached result if already resolved (idempotent)
        if order_id in self._resolved_deliveries:
            return self._resolved_deliveries[order_id]

        order = self._orders[order_id]
        if self._health == "out_of_business":
            result = DeliveryTimeline(
                order_id=order_id,
                status="failed",
                delivered_qty=0,
                days_late=0,
                final_unit_price=order.unit_price,
            )
            self._resolved_deliveries[order_id] = result
            return result
        roll = self._rng.random()
        if roll < 0.55:
            status = "delivered"
            delivered_qty = order.qty
            days_late = 0
        elif roll < 0.8:
            status = "delayed"
            delivered_qty = order.qty
            days_late = self._rng.randint(1, 7)
        elif roll < 0.92:
            status = "partial"
            delivered_qty = max(1, int(order.qty * (0.4 + self._rng.random() * 0.4)))
            days_late = self._rng.randint(0, 5)
        else:
            status = "failed"
            delivered_qty = 0
            days_late = 0
        final_unit_price = order.unit_price
        if (
            order.may_bait_and_switch
            and status in {"delivered", "delayed", "partial"}
            and self._rng.random() < 0.5
        ):
            final_unit_price = round(
                order.unit_price * (1.05 + self._rng.random() * 0.25), 2
            )
        result = DeliveryTimeline(
            order_id=order_id,
            status=status,
            delivered_qty=delivered_qty,
            days_late=days_late,
            final_unit_price=final_unit_price,
        )
        self._resolved_deliveries[order_id] = result
        return result

    def tick_supplier_health(self, days: int = 1) -> str:
        if self._health == "out_of_business":
            return self._health
        failure_risk = min(0.45, days / 365 * 0.7)
        if self._rng.random() < failure_risk:
            self._health = "out_of_business"
        return self._health
