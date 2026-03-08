from __future__ import annotations

from typing import Any, Optional

from fastmcp import FastMCP

from openenv.core.env_server.mcp_environment import MCPEnvironment
from openenv.core.env_server.mcp_types import CallToolAction, CallToolObservation
from openenv.core.env_server.types import Action, Observation

from vendsim_vb2.config import VB2Config
from vendsim_vb2.environment import VendingBench2Environment


class VB2MCPEnvironment(MCPEnvironment):
    """OpenEnv MCP wrapper around VendingBench2Environment."""

    def __init__(
        self,
        config: VB2Config | None = None,
        seed: int | None = None,
        use_dense_rewards: bool = False,
    ) -> None:
        self._config = config or VB2Config()
        self._seed = seed
        self._use_dense_rewards = use_dense_rewards
        self._inner_env: VendingBench2Environment | None = None
        self._prev_score: float = 0.0

        mcp = FastMCP("vending-bench-2")
        self._register_tools(mcp)
        super().__init__(mcp)

    # ------------------------------------------------------------------
    # Tool registration
    # ------------------------------------------------------------------

    def _register_tools(self, mcp: FastMCP) -> None:
        env_ref = self

        @mcp.tool()
        def set_price(product: str, price: float) -> dict:
            """Update the price of a product in the vending machine."""
            r = env_ref._inner_env.set_price(product, price)
            return {"status": r.status, **r.payload}

        @mcp.tool()
        def send_email(recipient: str, subject: str, body: str) -> dict:
            """Send an email to a supplier or service provider."""
            r = env_ref._inner_env.send_email(recipient, subject, body)
            return {"status": r.status, **r.payload}

        @mcp.tool()
        def check_balance() -> dict:
            """Review current bank balance."""
            r = env_ref._inner_env.check_balance()
            return {"status": r.status, **r.payload}

        @mcp.tool()
        def check_storage_inventory() -> dict:
            """Inspect the storage inventory."""
            r = env_ref._inner_env.check_storage_inventory()
            return {"status": r.status, **r.payload}

        @mcp.tool()
        def wait_for_next_day(output_tokens: int = 0) -> dict:
            """Advance simulation to the next business day."""
            r = env_ref._inner_env.wait_for_next_day(output_tokens)
            return {"status": r.status, **r.payload}

        @mcp.tool()
        def run_sub_agent(tool_name: str, arguments: dict[str, Any] | None = None) -> dict:
            """Delegate a physical-world action to the sub-agent."""
            r = env_ref._inner_env.run_sub_agent(tool_name, **(arguments or {}))
            return {"status": r.status, **r.payload}

        @mcp.tool()
        def chat_with_sub_agent(message: str) -> dict:
            """Message the sub-agent without taking action."""
            r = env_ref._inner_env.chat_with_sub_agent(message)
            return {"status": r.status, **r.payload}

        @mcp.tool()
        def write_scratchpad(note: str) -> dict:
            """Append a note to working memory."""
            r = env_ref._inner_env.write_scratchpad(note)
            return {"status": r.status, **r.payload}

        @mcp.tool()
        def read_scratchpad() -> dict:
            """Read the working-memory scratchpad."""
            r = env_ref._inner_env.read_scratchpad()
            return {"status": r.status, **r.payload}

        @mcp.tool()
        def search_notes(query: str) -> dict:
            """Search saved notes for a keyword."""
            r = env_ref._inner_env.search_notes(query)
            return {"status": r.status, **r.payload}

        @mcp.tool()
        def set_reminder(day: int, message: str) -> dict:
            """Schedule a future reminder."""
            r = env_ref._inner_env.set_reminder(day, message)
            return {"status": r.status, **r.payload}

        @mcp.tool()
        def request_supplier_quote(product: str, qty: int) -> dict:
            """Request a price quote from a supplier for a product."""
            r = env_ref._inner_env.request_supplier_quote(product, qty)
            return {"status": r.status, **r.payload}

        @mcp.tool()
        def negotiate_supplier(quote_id: str, proposed_unit_price: float) -> dict:
            """Negotiate a supplier quote with a proposed unit price."""
            r = env_ref._inner_env.negotiate_supplier(quote_id, proposed_unit_price)
            return {"status": r.status, **r.payload}

        @mcp.tool()
        def place_supplier_order(product: str, qty: int) -> dict:
            """Place a confirmed order with a supplier."""
            r = env_ref._inner_env.place_supplier_order(product, qty)
            return {"status": r.status, **r.payload}

        @mcp.tool()
        def check_delivery(order_id: str) -> dict:
            """Check delivery status. On success, items are added to storage and cost is charged."""
            r = env_ref._inner_env.resolve_delivery(order_id)
            return {"status": r.status, **r.payload}

        @mcp.tool()
        def get_status() -> dict:
            """Return a full snapshot of the current environment state."""
            return env_ref._inner_env.snapshot()

    # ------------------------------------------------------------------
    # MCPEnvironment interface
    # ------------------------------------------------------------------

    def step(
        self,
        action: Action,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> Observation:
        """Override step to propagate reward/done on the Observation object."""
        obs = super().step(action, timeout_s=timeout_s, **kwargs)
        if not isinstance(obs, CallToolObservation) or self._inner_env is None:
            return obs

        done = self._inner_env.is_done()
        obs.done = done

        if isinstance(action, CallToolAction) and action.tool_name == "wait_for_next_day":
            if self._use_dense_rewards:
                # Dense: per-day delta of bank balance
                new_score = self._inner_env.final_score()
                obs.reward = round(new_score - self._prev_score, 2)
                self._prev_score = new_score
            elif done:
                # Sparse default: final bank balance at terminal step only
                obs.reward = self._inner_env.final_score()
            else:
                obs.reward = 0.0
        else:
            obs.reward = 0.0

        return obs

    def reset(
        self,
        seed: int | None = None,
        episode_id: str | None = None,
        **kwargs: Any,
    ) -> CallToolObservation:
        effective_seed = seed if seed is not None else self._seed
        self._inner_env = VendingBench2Environment(
            config=self._config,
            seed=effective_seed,
            use_dense_rewards=self._use_dense_rewards,
        )
        self._prev_score = self._inner_env.final_score()
        snapshot = self._inner_env.snapshot()
        snapshot["reward"] = 0.0
        snapshot["done"] = False
        return CallToolObservation(
            tool_name="reset",
            result=snapshot,
            reward=0.0,
            done=False,
        )

    def _step_impl(
        self,
        action: Action,
        timeout_s: float | None = None,
        **kwargs: Any,
    ) -> Observation:
        raise NotImplementedError("All actions are routed through MCP tools.")

    @property
    def state(self) -> dict[str, Any]:
        if self._inner_env is None:
            return {}
        return self._inner_env.snapshot()
