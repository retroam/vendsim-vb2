from __future__ import annotations

from fastapi import FastAPI
from openenv.core.env_server.http_server import HTTPEnvServer
from openenv.core.env_server.mcp_types import CallToolAction, CallToolObservation

from vendsim_vb2.mcp_env import VB2MCPEnvironment


def create_app() -> FastAPI:
    app = FastAPI(title="Vending-Bench 2 Environment")
    server = HTTPEnvServer(
        env=VB2MCPEnvironment,
        action_cls=CallToolAction,
        observation_cls=CallToolObservation,
    )
    server.register_routes(app)
    return app


app = create_app()
