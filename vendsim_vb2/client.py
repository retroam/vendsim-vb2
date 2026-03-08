"""VB2 environment client for agents and training scripts."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from openenv.core.env_server.mcp_types import (
    CallToolAction,
    CallToolObservation,
    ListToolsAction,
    ListToolsObservation,
    Observation,
    Tool,
    ToolError,
)
from openenv.core.env_client import EnvClient, StepResult
from openenv.core.mcp_client import State


class VB2Client(EnvClient[Any, Observation, State]):
    """
    Client for the Vending-Bench 2 MCP environment.

    Provides typed convenience methods for every VB2 tool, plus the full
    ``step()`` / ``reset()`` API inherited from :class:`EnvClient`.

    Example::

        with VB2Client(base_url="http://localhost:8000") as env:
            env.reset()
            balance = env.check_balance()
            env.set_price("soda", 1.75)
            quote = env.request_supplier_quote("chips", 20)
            sales = env.wait_for_next_day()
    """

    def __init__(
        self,
        base_url: str,
        connect_timeout_s: float = 10.0,
        message_timeout_s: float = 60.0,
        provider: Optional[Any] = None,
    ) -> None:
        super().__init__(
            base_url=base_url,
            connect_timeout_s=connect_timeout_s,
            message_timeout_s=message_timeout_s,
            provider=provider,
        )
        self._tools_cache: Optional[List[Tool]] = None

    # ------------------------------------------------------------------
    # Abstract method implementations
    # ------------------------------------------------------------------

    def _step_payload(self, action: Any) -> Dict[str, Any]:
        if isinstance(action, ListToolsAction):
            return {"type": "list_tools"}
        if isinstance(action, CallToolAction):
            return {
                "type": "call_tool",
                "tool_name": action.tool_name,
                "arguments": action.arguments,
            }
        if hasattr(action, "model_dump"):
            return action.model_dump()
        return {"action": str(action)}

    def _parse_result(self, payload: Dict[str, Any]) -> StepResult[Observation]:
        obs_data = payload.get("observation", {})

        if "tools" in obs_data:
            tools = [
                Tool(
                    name=t.get("name", ""),
                    description=t.get("description", ""),
                    input_schema=t.get("input_schema", t.get("inputSchema", {})),
                )
                for t in obs_data.get("tools", [])
            ]
            observation: Observation = ListToolsObservation(
                tools=tools,
                done=payload.get("done", False),
                reward=payload.get("reward"),
                metadata=obs_data.get("metadata", {}),
            )
        elif "tool_name" in obs_data:
            error = None
            if obs_data.get("error"):
                error = ToolError(**obs_data["error"])
            observation = CallToolObservation(
                tool_name=obs_data.get("tool_name", ""),
                result=obs_data.get("result"),
                error=error,
                done=payload.get("done", False),
                reward=payload.get("reward"),
                metadata=obs_data.get("metadata", {}),
            )
        else:
            observation = Observation(
                done=payload.get("done", False),
                reward=payload.get("reward"),
                metadata=obs_data.get("metadata", {}),
            )

        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict[str, Any]) -> State:
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )

    # ------------------------------------------------------------------
    # Helper: call a tool and return its result
    # ------------------------------------------------------------------

    def _call_tool(self, tool_name: str, **kwargs: Any) -> Any:
        """Call a tool by name and return its result (or raise on error)."""
        result = self.call_tool_step(tool_name, **kwargs)
        obs = result.observation

        if isinstance(obs, CallToolObservation) and obs.error is not None:
            raise RuntimeError(
                f"Tool '{tool_name}' failed: {obs.error.message} "
                f"(type: {obs.error.error_type.value})"
            )

        if isinstance(obs, CallToolObservation):
            res = obs.result
            if hasattr(res, "data"):
                return res.data
            if isinstance(res, dict) and "data" in res:
                return res["data"]
            return res

        return obs

    def call_tool_step(self, tool_name: str, **kwargs: Any) -> StepResult[Observation]:
        """Call a tool and return the full StepResult with reward/done metadata."""
        action = CallToolAction(tool_name=tool_name, arguments=kwargs)
        return self.step(action)

    # ------------------------------------------------------------------
    # Convenience methods
    # ------------------------------------------------------------------

    def list_tools(self, use_cache: bool = True) -> List[Tool]:
        """Discover available tools from the environment."""
        if use_cache and self._tools_cache is not None:
            return self._tools_cache
        result = self.step(ListToolsAction())
        if isinstance(result.observation, ListToolsObservation):
            self._tools_cache = result.observation.tools
            return self._tools_cache
        return []

    def set_price(self, product: str, price: float) -> Any:
        """Update the price of a product in the vending machine."""
        return self._call_tool("set_price", product=product, price=price)

    def check_balance(self) -> Any:
        """Review current bank balance."""
        return self._call_tool("check_balance")

    def check_storage_inventory(self) -> Any:
        """Inspect the storage inventory."""
        return self._call_tool("check_storage_inventory")

    def wait_for_next_day(self, output_tokens: int = 0) -> Any:
        """Advance simulation to the next business day."""
        return self._call_tool("wait_for_next_day", output_tokens=output_tokens)

    def send_email(self, recipient: str, subject: str, body: str) -> Any:
        """Send an email to a supplier or service provider."""
        return self._call_tool(
            "send_email", recipient=recipient, subject=subject, body=body
        )

    def restock_machine(self, product: str, qty: int) -> Any:
        """Delegate to sub-agent: restock the vending machine from storage."""
        return self._call_tool(
            "run_sub_agent",
            tool_name="restock_machine",
            arguments={"product": product, "qty": qty},
        )

    def collect_cash(self) -> Any:
        """Delegate to sub-agent: collect cash from the vending machine."""
        return self._call_tool("run_sub_agent", tool_name="collect_cash", arguments={})

    def get_machine_inventory(self) -> Any:
        """Delegate to sub-agent: get current machine inventory."""
        return self._call_tool(
            "run_sub_agent",
            tool_name="get_machine_inventory",
            arguments={},
        )

    def chat_with_sub_agent(self, message: str) -> Any:
        """Message the sub-agent without taking action."""
        return self._call_tool("chat_with_sub_agent", message=message)

    def write_scratchpad(self, note: str) -> Any:
        """Append a note to working memory."""
        return self._call_tool("write_scratchpad", note=note)

    def read_scratchpad(self) -> Any:
        """Read the working-memory scratchpad."""
        return self._call_tool("read_scratchpad")

    def search_notes(self, query: str) -> Any:
        """Search saved notes for a keyword."""
        return self._call_tool("search_notes", query=query)

    def set_reminder(self, day: int, message: str) -> Any:
        """Schedule a future reminder."""
        return self._call_tool("set_reminder", day=day, message=message)

    def request_supplier_quote(self, product: str, qty: int) -> Any:
        """Request a price quote from a supplier for a product."""
        return self._call_tool("request_supplier_quote", product=product, qty=qty)

    def negotiate_supplier(self, quote_id: str, proposed_unit_price: float) -> Any:
        """Negotiate a supplier quote with a proposed unit price."""
        return self._call_tool("negotiate_supplier", quote_id=quote_id, proposed_unit_price=proposed_unit_price)

    def place_supplier_order(self, product: str, qty: int) -> Any:
        """Place a confirmed order with a supplier."""
        return self._call_tool("place_supplier_order", product=product, qty=qty)

    def check_delivery(self, order_id: str) -> Any:
        """Check the delivery status of a supplier order."""
        return self._call_tool("check_delivery", order_id=order_id)
