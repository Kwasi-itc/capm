"""Base definitions for Aider tools (function-calling / plug-in helpers)."""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Dict

import os
import jsonschema
import logging
from aider.waiting import WaitingSpinner

logger = logging.getLogger(__name__)


def print_proposed_edits(tool_call_data: dict) -> None:
    """
    Neatly prints proposed edits, with background colors in a seamless, solid block.
    """
    try:
        terminal_width = os.get_terminal_size().columns
    except OSError:
        terminal_width = 80

    DELETION_STYLE = "\033[47;31m"
    ADDITION_STYLE = "\033[47;32m"
    BLUE = "\033[94m"
    ENDC = "\033[0m"

    file_path = tool_call_data.get("file_path")
    edits = tool_call_data.get("edits", [])

    if not file_path or not edits:
        print("Invalid tool call data provided.")
        return

    print(f"{BLUE}Proposed changes for: {file_path}{ENDC}")
    print("=" * 50)

    for i, edit in enumerate(edits, 1):
        print(f"\n--- Edit {i} of {len(edits)} ---")

        old_string = edit.get("old_string", "")
        new_string = edit.get("new_string", "")

        if old_string:
            processed_lines = []
            for line in old_string.splitlines():
                output_line = f"- {line}"
                padded_line = output_line.ljust(terminal_width)
                processed_lines.append(padded_line)
            full_block = "\n".join(processed_lines)
            print(f"{DELETION_STYLE}{full_block}{ENDC}")

        if new_string:
            processed_lines = []
            for line in new_string.splitlines():
                output_line = f"+ {line}"
                padded_line = output_line.ljust(terminal_width)
                processed_lines.append(padded_line)
            full_block = "\n".join(processed_lines)
            print(f"{ADDITION_STYLE}{full_block}{ENDC}")


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
    # Default JSON-schema – subclasses should override or extend this.
    # By explicitly setting ``additionalProperties`` to True we allow tools
    # to accept *any* extra keyword arguments unless they opt-in to stricter
    # validation.  Concrete tools can still set it to False if they want a
    # closed schema.
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": True,
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

    # -------- runtime behaviour tweaks (sub-classes may override) ----------
    def wants_spinner(self) -> bool:
        """
        Return True if a waiting spinner should be displayed while the tool
        executes.  Individual tools can override this to suppress the spinner
        when they need full, unbuffered control of stdin/stdout (eg. BashTool
        which may prompt the user for input).
        """
        return True

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
            if self.wants_spinner():
                with WaitingSpinner(f"Running {self.name}"):
                    result = self.run(**args)
            else:
                result = self.run(**args)
            logger.debug("Tool %s completed successfully", self.name)
            return result
        except ToolError as exc:
            # Surface *expected* tool failures (eg validation issues) as a
            # normal textual result so the conversation can continue instead
            # of aborting the execution loop.
            logger.debug("Tool %s reported ToolError: %s", self.name, exc)
            return f"Tool error: {exc}"
        except Exception as exc:  # noqa: BLE001
            # Log only a concise debug line so the end-user doesn't see a traceback.
            logger.debug("Error while running %s: %s", self.name, exc)
            raise ToolError(f"Error while running {self.name}: {exc}") from exc

    # -------- concrete tool must implement -----------------------
    @abstractmethod
    def run(self, **kwargs) -> str:  # noqa: D401
        """Execute the tool and return its output as a string."""
        ...
