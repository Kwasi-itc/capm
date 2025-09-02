"AgenticCoder – a GenericCoder subclass that uses AgenticPrompts and provides\n"
"hooks for future autonomous planning features."
from __future__ import annotations

from .generic_coder import GenericCoder  # Provided by the existing code-base
from .agentic_prompts import AgenticPrompts


class AgenticCoder(GenericCoder):  # type: ignore[misc]
    """
    A coder that applies an agentic, plan-then-execute workflow.

    The current implementation is intentionally lightweight; it simply swaps in the
    AgenticPrompts.  Additional agentic utilities (planning, tool selection, etc.)
    can be added incrementally without touching other coder classes.
    """

    default_prompts_cls = AgenticPrompts

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
        # TODO: implement real planning (possibly via an LLM call)
        return [goal]

    def execute_plan(self, tasks: list[str]) -> None:
        """
        Execute each task in sequence.  Hook point for tool integration.

        Right now this is a no-op placeholder.  Future versions might loop over the
        tasks, call internal methods, external tools, or spawn sub-coders.
        """
        for task in tasks:
            # Placeholder – replace with real execution logic
            self.io.tool_output(f"[Agentic] Executing task: {task}", log_only=False)
