"""Base definitions for Aider tools (function-calling / plug-in helpers)."""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Dict

import jsonschema
import logging

logger = logging.getLogger(__name__)


class ToolError(Exception):
    """Raised when argument validation or execution fails."""


class BaseTool(ABC):
    """
    Derive concrete tools from this class.

    Required class attributes to override:
        name:         Unique identifier (str). Must match the value the LLM returns.
        description:  Short human-oriented description (str).
        parameters:   JSON-schema (dict) accepted by the tool.

    Required instance method to override:
        run(**kwargs) -> str
    """

    # -------- core attributes (override in subclass) -------------
    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    # -------- helper to expose schema to the LLM -----------------
    @classmethod
    def json_schema(cls) -> Dict[str, Any]:
        """Return OpenAI-compatible tool description dict."""
        return {
            "name": cls.name,
            "description": cls.description,
            "parameters": cls.parameters,
        }

    # -------- interface used after model returns tool call -------
    def handle_call(self, args_json: str | None) -> str:
        """
        Validate JSON arguments coming from the LLM and execute `run`.
        Returns the textual result that will be sent back into the chat.
        """
        # Parse the JSON arguments (the model may return `null` or an empty string)
        args = json.loads(args_json or "{}")
        logger.debug("Tool %s invoked with args=%s", self.name, args)

        try:
            jsonschema.validate(args, self.parameters)
        except jsonschema.ValidationError as exc:
            raise ToolError(f"Invalid arguments for {self.name}: {exc.message}") from exc

        try:
            result = self.run(**args)
            logger.debug("Tool %s completed successfully", self.name)
            return result
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error while running %s", self.name)
            raise ToolError(f"Error while running {self.name}: {exc}") from exc

    # -------- concrete tool must implement -----------------------
    @abstractmethod
    def run(self, **kwargs) -> str:  # noqa: D401
        """Execute the tool and return its output as a string."""
        ...
