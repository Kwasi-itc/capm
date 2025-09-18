"""
TodoWrite tool

Provides the LLM with a scratch-pad to persist and maintain a structured todo
list during the current coding session.  It only records the tasks – it does
not touch the user’s files.

The todo list lives **in-memory** for the lifetime of one ``Coder`` instance,
so every subsequent call can read / update the same list.
"""

from __future__ import annotations

from typing import List, Dict, Any
from uuid import uuid4

from aider.tools.base_tool import BaseTool, ToolError


class TodoWriteTool(BaseTool):
    # ---------------- metadata exposed to the LLM --------------------
    name = "TodoWrite"
    description = (
        "Use this tool to create and manage a structured task list for your current coding session. "
        "It helps track progress, organise complex tasks and demonstrate thoroughness.\n\n"
        "See the system documentation for detailed usage guidance."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "todos": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "minLength": 1},
                        "status": {
                            "type": "string",
                            "enum": ["pending", "in_progress", "completed"],
                        },
                        "id": {"type": "string"},
                    },
                    "required": ["content", "status", "id"],
                    "additionalProperties": False,
                },
                "description": "The updated todo list",
            }
        },
        "required": ["todos"],
        "additionalProperties": False,
    }

    # ------------------------ implementation -------------------------
    # One task list per tool instance (= per coder session)
    def __init__(self) -> None:  # noqa: D401
        super().__init__()
        self._todos: List[Dict[str, str]] = []

    def _validate_todos(self, todos: List[Dict[str, str]]) -> None:
        """Basic validation beyond the JSON-schema."""
        seen_ids: set[str] = set()
        for todo in todos:
            todo_id = todo["id"]
            status = todo["status"]
            if todo_id in seen_ids:
                raise ToolError(f"Duplicate id '{todo_id}' in todo list")
            seen_ids.add(todo_id)

            if status == "in_progress" and sum(t["status"] == "in_progress" for t in todos) > 1:
                raise ToolError("Only one task may have status 'in_progress' at a time")

    # -----------------------------------------------------------------
    def run(self, *, todos: List[Dict[str, str]]) -> str:  # noqa: D401
        """
        Replace the current todo list with ``todos`` after validation and return
        a human-readable summary.
        """
        # Assign ids automatically if caller omitted them
        for todo in todos:
            if not todo.get("id"):
                todo["id"] = str(uuid4())

        self._validate_todos(todos)

        # Persist
        self._todos = todos

        # Build a readable report
        lines = ["Todo list updated:"]
        for t in todos:
            lines.append(f"- [{t['status']}] {t['content']} (id: {t['id']})")
        return "\n".join(lines)

    # Helpers for unit tests / other tools
    # ------------------------------------
    def get_todos(self) -> List[Dict[str, str]]:
        return list(self._todos)
