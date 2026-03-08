"""Compatibility shims for optional third-party dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(slots=True)
class Route:
    method: str
    path: str
    endpoint: Callable[..., Any]


class FastAPI:
    """Small subset of FastAPI used for local smoke tests when FastAPI is absent."""

    def __init__(self, *, title: str) -> None:
        self.title = title
        self.routes: list[Route] = []

    def get(self, path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._register("GET", path)

    def post(self, path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._register("POST", path)

    def _register(
        self, method: str, path: str
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.routes.append(Route(method=method, path=path, endpoint=func))
            return func

        return decorator
