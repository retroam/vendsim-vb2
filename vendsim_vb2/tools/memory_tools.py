from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MemoryToolSpec:
    name: str
    description: str


MEMORY_TOOL_SPECS: tuple[MemoryToolSpec, ...] = (
    MemoryToolSpec("write_scratchpad", "Append a note to working memory."),
    MemoryToolSpec("read_scratchpad", "Read the working-memory scratchpad."),
    MemoryToolSpec("search_notes", "Search saved notes for a keyword."),
    MemoryToolSpec("set_reminder", "Schedule a future reminder."),
)


def list_memory_tools() -> list[str]:
    return [spec.name for spec in MEMORY_TOOL_SPECS]


def get_memory_tool_specs() -> tuple[MemoryToolSpec, ...]:
    return MEMORY_TOOL_SPECS
