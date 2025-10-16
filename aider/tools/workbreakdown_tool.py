"""
WorkBreakdownTool
-----------------
Generate a hierarchical **Work-Breakdown Structure (WBS)** or task list for a
software project.

The tool behaves similarly to *SpecificationTool*: it runs an internal loop
between a **DraftAgent** (creates the initial WBS) and a **ReviewAgent**
(critiques & requests changes) until the structure is approved or the maximum
number of iterations is reached.

Typical usage
~~~~~~~~~~~~~
```python
tool = WorkBreakdownTool()
wbs_md = tool.run(
    topic="E-commerce Platform Revamp",
    context="PRD and Technical Architecture already approved. 6-month delivery.",
    iterations=3,
)
```

The returned string is Markdown – normally a tree or table showing phases,
epics, stories / tasks, with IDs, owners, estimates, dependencies, and
acceptance criteria ready for import into a project-management system.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List

import openai

from .base_tool import BaseTool, ToolError

# --------------------------------------------------------------------------- #
# Prompt templates
# --------------------------------------------------------------------------- #

DRAFT_PROMPT = """You are DraftAgent, a senior project manager.

Create a detailed **Work-Breakdown Structure (WBS)** for the project below.

Project topic:
{topic}

Additional context (constraints, requirements, architecture, etc.):
{context}

Guidelines
~~~~~~~~~~
* Break work down into at most 4 hierarchical levels (Phase ▸ Epic ▸ Story ▸ Task).
* Use a Markdown ordered list or table with columns:
  ID • Level • Name • Description • Owner (role) • Est. Effort (person-days) • Dependencies
* Ensure IDs are unique and reflect hierarchy (eg `1`, `1.2`, `1.2.3` …).
* Include **acceptance criteria** for leaf-level tasks.
* Do **NOT** allocate real people – use generic roles (Backend Dev, QA, PM).
* Keep total effort realistic given the context.
Respond ONLY with the Markdown WBS.
"""

REVIEW_PROMPT = """You are ReviewAgent, a programme director.

Evaluate the **WBS** below for completeness, logical breakdown, reasonable
estimates and dependency correctness.

If the WBS is fully acceptable, respond exactly with:

APPROVED

Otherwise respond with a concise numbered list of change requests.
Do NOT rewrite the WBS yourself.
"""

# --------------------------------------------------------------------------- #
# Tool class
# --------------------------------------------------------------------------- #


class WorkBreakdownTool(BaseTool):
    """
    Generate a hierarchical Work-Breakdown Structure through a draft/review loop.
    """

    name = "workbreakdown_builder"
    description = (
        "Generate a Work-Breakdown Structure (hierarchical task list) for a project "
        "using an internal draft/review loop between two LLM agents."
    )

    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "Short description or title of the project.",
            },
            "context": {
                "type": "string",
                "description": (
                    "Relevant background such as PRD, technical architecture, constraints, "
                    "team size, timeline, etc.  Passed to the LLM to refine the WBS."
                ),
            },
            "iterations": {
                "type": "integer",
                "description": "Maximum draft/review cycles (default 3).",
                "minimum": 1,
                "default": 3,
            },
            "model": {
                "type": "string",
                "description": "Override the LLM model name (defaults to gpt-4o).",
            },
        },
        "required": ["topic"],
        "additionalProperties": False,
    }

    # ------------------------------------------------------------------ #
    # main entry point
    # ------------------------------------------------------------------ #
    def run(  # noqa: D401
        self,
        topic: str,
        context: str | None = None,
        iterations: int = 3,
        model: str | None = None,
        **kwargs,
    ) -> str:
        """
        Return an approved WBS markdown string (or JSON with note if unapproved).
        """
        model_name = model or "gpt-4o"
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ToolError("OPENAI_API_KEY environment variable not set")

        def chat(messages: List[Dict[str, str]]) -> str:
            """Wrapper for OpenAI chat completion supporting v1.x & <1.0 packages."""
            if hasattr(openai, "OpenAI"):  # newer SDK
                client = openai.OpenAI()
                resp = client.chat.completions.create(model=model_name, messages=messages)
                return resp.choices[0].message.content.strip()
            resp = openai.ChatCompletion.create(model=model_name, messages=messages)
            return resp.choices[0].message.content.strip()

        draft: str | None = None

        for _ in range(iterations):
            if draft is None:
                draft = chat(
                    [
                        {
                            "role": "system",
                            "content": DRAFT_PROMPT.format(
                                topic=topic, context=context or "N/A"
                            ),
                        }
                    ]
                )
            else:
                review = chat(
                    [
                        {
                            "role": "system",
                            "content": REVIEW_PROMPT + "\n\nWBS:\n\n" + draft,
                        }
                    ]
                )
                if review.upper().startswith("APPROVED"):
                    return draft
                draft = chat(
                    [
                        {
                            "role": "system",
                            "content": (
                                "You are the original DraftAgent. Improve the WBS according to "
                                "the reviewer comments below:\n\n---\n{review}\n---\n\n"
                                "Current WBS:\n{wbs}"
                            ).format(review=review, wbs=draft),
                        }
                    ]
                )

        # fallback after max iterations
        return json.dumps(
            {
                "wbs": draft,
                "note": "Returned after reaching max iterations without explicit APPROVED.",
            },
            ensure_ascii=False,
        )
