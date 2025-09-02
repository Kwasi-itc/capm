"""
AgenticCoder – a GenericCoder subclass that uses AgenticPrompts and provides
hooks for future autonomous planning features.
"""
from __future__ import annotations

from .generic_coder import GenericCoder  # Use full-featured Coder as the parent
from .agentic_prompts import AgenticPrompts

import json
import re


class AgenticCoder(GenericCoder):  # type: ignore[misc]
    """
    A coder that applies an agentic, plan-then-execute workflow.

    The current implementation is intentionally lightweight; it simply swaps in the
    AgenticPrompts.  Additional agentic utilities (planning, tool selection, etc.)
    can be added incrementally without touching other coder classes.
    """

    default_prompts_cls = AgenticPrompts

    # ------------------------------------------------------------------ #
    # Factory – mirror the Coder.create() helper so main() can instantiate
    # ------------------------------------------------------------------ #
    @classmethod
    def create(cls, **kwargs) -> "AgenticCoder":  # noqa: D401
        """
        Lightweight factory used by main().

        This mirrors aider.coders.base_coder.Coder.create() so that the
        --agentic flag can drop-in replace the regular Coder without
        changing the call-site.  All positional/keyword arguments are
        forwarded directly to ``__init__``.
        """
        return cls(**kwargs)

    # --------------------------------------------------------------------- #
    # Agentic extensions – stubs for future functionality
    # --------------------------------------------------------------------- #
    def plan_tasks(self, goal: str) -> list[str]:
        """
        Break a high-level goal into actionable steps.

        Parameters
        ----------
        goal : str
            The high-level objective provided by the user.

        Returns
        -------
        list[str]
            A list of task descriptions to execute in order.
        """
        # Ask the underlying LLM to break the goal into a short, JSON-encoded list
        # of tasks.  We request a *pure* JSON array so we can parse it reliably.
        planning_prompt = (
            "You are planning the following software-development goal:\n"
            f"{goal}\n\n"
            "Respond ONLY with a JSON array (no surrounding text) containing the "
            "ordered list of concise task strings required to achieve the goal."
        )

        # Use the built-in streaming call; we only need the final response text.
        llm_response = self.run_stream(planning_prompt)

        tasks = self._extract_tasks_from_response(llm_response, goal)
        return tasks

    # --------------------------------------------------------------------- #
    # Helpers
    # --------------------------------------------------------------------- #
    @staticmethod
    def _extract_tasks_from_response(response: str, fallback_goal: str) -> list[str]:
        """
        Parse the JSON task list returned by the planning prompt.  On failure, fall
        back to a single-step plan containing the original goal.
        """
        # Try to locate a JSON array in the response
        match = re.search(r"\[[\s\S]*\]", response)
        if not match:
            return [fallback_goal]

        try:
            tasks = json.loads(match.group(0))
            if isinstance(tasks, list) and all(isinstance(t, str) for t in tasks):
                return tasks
        except json.JSONDecodeError:
            pass

        return [fallback_goal]

    def execute_plan(self, tasks: list[str]) -> None:
        """
        Execute each task in sequence.  Hook point for tool integration.

        Right now this is a no-op placeholder.  Future versions might loop over the
        tasks, call internal methods, external tools, or spawn sub-coders.
        """
        self.io.tool_output("[Agentic] Beginning plan execution…")
        for task in tasks:
            self.io.tool_output(f"[Agentic] ➜ {task}")
            # Delegate each sub-task to the LLM in the current chat context.
            # The result is streamed back to the user through GenericCoder.
            self.run_stream(task)
