"""
SpecificationTool
-----------------
Interactive dual-agent tool for drafting and iteratively refining a
comprehensive specification document.

Usage
~~~~~
`aider.tools.SpecificationTool` is auto-discovered via `discover_tools()`
because it subclasses `BaseTool` and sets a non-empty ``name`` attribute.

The tool runs a simple ReAct-style loop:

1. **DraftAgent** writes an initial specification.
2. **ReviewAgent** critiques it and either marks it APPROVED or returns
   revision instructions.
3. Loop continues (max 3 iterations) until APPROVED.

The final, approved specification is returned from ``run()``.
"""

from __future__ import annotations

from typing import List, Dict

from .base_tool import BaseTool


DRAFT_PROMPT = """You are DraftAgent, a senior engineer.
Draft a complete, clear and thorough technical specification
addressing the user's request below.

The document MUST be:
* Well-structured with sections, headings and sub-headings.
* Written in the third person, concise but exhaustive.
* Include goals, non-goals, stakeholders, open questions,
  acceptance criteria and implementation plan.

Respond ONLY with the specification Markdown — no prose outside it.
"""

REVIEW_PROMPT = """You are ReviewAgent, a critical technical reviewer.
Evaluate the **SPECIFICATION** below.

If it is fully comprehensive, well-structured and ready for implementation,
respond exactly with:

APPROVED

Otherwise respond with a numbered list of concise change requests needed
to achieve approval. Do NOT rewrite the full spec yourself.
"""


class SpecificationTool(BaseTool):
    """
    Generate a comprehensive specification through a self-critique loop.
    """

    # Tool metadata understood by the surrounding framework
    name = "specification"
    description = "Iteratively draft and review a technical specification document."
    inputs = ["prompt"]  # single free-form user prompt
    outputs = ["specification"]  # final approved specification text

    MAX_ITERATIONS = 3

    # --------------------------------------------------------------------- #
    # Public entry-point expected by BaseTool
    # --------------------------------------------------------------------- #
    def run(self, prompt: str, llm, io=None, **kwargs) -> Dict[str, str]:
        """
        Parameters
        ----------
        prompt:
            The user's high-level request or requirements.
        llm:
            An object exposing ``chat(messages: List[dict]) -> dict``
            compatible with `openai.ChatCompletion` format.
        io:
            Optional InputOutput for logging / streaming (if available).

        Returns
        -------
        dict
            { "specification": "<markdown document>" }
        """
        spec = None
        review_feedback = ""
        messages: List[Dict[str, str]]

        # ----------------------------------------------------------------- #
        # ReAct loop
        # ----------------------------------------------------------------- #
        for iteration in range(1, self.MAX_ITERATIONS + 1):
            # 1. DraftAgent creates / revises spec
            messages = [
                {"role": "system", "content": DRAFT_PROMPT},
                {"role": "user", "content": prompt},
            ]
            if spec:
                # Provide reviewer feedback as context for next draft
                messages.append(
                    {
                        "role": "assistant",
                        "content": spec,
                    }
                )
                messages.append(
                    {
                        "role": "user",
                        "content": review_feedback,
                    }
                )

            draft_resp = llm.chat(messages)
            spec = draft_resp["content"] if isinstance(draft_resp, dict) else draft_resp

            if io:
                io.tool_output(f"[DraftAgent #{iteration}] produced spec ({len(spec)} chars)")

            # 2. ReviewAgent evaluates
            review_messages = [
                {"role": "system", "content": REVIEW_PROMPT},
                {
                    "role": "user",
                    "content": f"Here is the SPECIFICATION:\n\n{spec}",
                },
            ]
            review_resp = llm.chat(review_messages)
            review_feedback = (
                review_resp["content"] if isinstance(review_resp, dict) else review_resp
            )

            if io:
                io.tool_output(f"[ReviewAgent #{iteration}] feedback:\n{review_feedback}")

            # 3. Check for approval
            if review_feedback.strip().upper().startswith("APPROVED"):
                if io:
                    io.tool_output(f"[SpecificationTool] Approved after {iteration} iteration(s).")
                return {"specification": spec}

        # Fallback – return latest draft even if unapproved
        if io:
            io.tool_warning("[SpecificationTool] Max iterations reached without approval.")

        return {"specification": spec or ""}
