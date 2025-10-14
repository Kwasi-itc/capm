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

import os
import json
from typing import Any, Dict, List

import openai

from .base_tool import BaseTool, ToolError


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
    # Public metadata ----------------------------------------------------------------
    name = "specification_builder"
    description = (
        "Generate a thorough specification document through an internal draft/review "
        "loop between two LLM agents (drafter & reviewer)."
    )
    # JSON-schema for LLM-function calling or UI auto-generation
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "Short description of what the specification should cover.",
            },
            "spec_type": {
                "type": "string",
                "description": (
                    "Kind of document to generate. Allowed values: "
                    "Specification, TechnicalArchitecture, Technical, Product, API, "
                    "Architecture, Security, Data, UX, Testing, Deployment, Business, Research."
                ),
                "enum": [
                    "Specification",
                    "TechnicalArchitecture",
                    "Technical",
                    "Product",
                    "API",
                    "Architecture",
                    "Security",
                    "Data",
                    "UX",
                    "Testing",
                    "Deployment",
                    "Business",
                    "Research",
                ],
                "default": "Specification",
            },
            "iterations": {
                "type": "integer",
                "description": "Maximum draft/review cycles.",
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


    # Prompt templates for each spec_type
    SPEC_PROMPTS: Dict[str, Dict[str, str]] = {
    "Specification": {
        "drafter": (
            "You are a meticulous specification drafter.\n"
            "Write a comprehensive specification document for the topic below.\n\n"
            "Topic: {topic}\n\n"
            "The document must include: goals, non-goals, stakeholders, functional "
            "and non-functional requirements, acceptance criteria, glossary, "
            "open questions and an implementation plan. Provide clear markdown headings."
        ),
        "reviewer": (
            "You are an exacting reviewer.\n"
            "Evaluate the specification below. Respond with:\n"
            " • A bullet list of issues to improve, **or**\n"
            " • The single word 'APPROVED' if the spec is complete and flawless.\n\n"
            "Specification:\n\n{spec}"
        ),
    },
    "TechnicalArchitecture": {
        "drafter": (
            "You are a senior solutions architect.\n"
            "Create a detailed technical architecture document for the topic below.\n\n"
            "Topic: {topic}\n\n"
            "Include: context diagram, component list with responsibilities, "
            "sequence diagrams or interaction flows, data models, technology choices "
            "with rationale, scalability/security/reliability considerations, risks, "
            "and a migration or rollout plan. Use markdown with appropriate mermaid "
            "diagrams where helpful."
        ),
        "reviewer": (
            "You are a principal architect reviewing the architecture below.\n"
            "Respond with a concise bullet list of deficiencies **or** 'APPROVED' "
            "if the document is production-ready.\n\nArchitecture:\n\n{spec}"
        ),
    },
}

    # -------------------------- main entry point -------------------------- #

    def run(  # noqa: D401
        self,
        topic: str,
        spec_type: str = "Specification",
        iterations: int = 3,
        model: str | None = None,
        **kwargs,
    ) -> str:
        """
        Draft and iteratively refine a specification until the reviewer approves it.

        Returns
        -------
        str
            The final specification markdown (or JSON with note if unapproved).
        """
        model_name = model or "gpt-4o"
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ToolError("OPENAI_API_KEY environment variable not set")

        # Select prompts based on requested document type
        templates = SPEC_PROMPTS.get(spec_type, SPEC_PROMPTS["Specification"])
        drafter_prompt = templates["drafter"]
        reviewer_prompt = templates["reviewer"]

        def chat(messages: List[Dict[str, str]]) -> str:
            resp = openai.ChatCompletion.create(model=model_name, messages=messages)
            return resp.choices[0].message.content.strip()

        draft: str | None = None

        for _ in range(iterations):
            if draft is None:
                draft = chat(
                    [
                        {
                            "role": "system",
                            "content": drafter_prompt.format(spec_type=spec_type, topic=topic),
                        }
                    ]
                )
            else:
                review = chat(
                    [
                        {
                            "role": "system",
                            "content": reviewer_prompt.format(spec=draft),
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
                                "You are the original drafter. Improve the specification according "
                                "to the reviewer comments below:\n\n---\n{review}\n---\n\n"
                                "Current specification:\n{spec}"
                            ).format(review=review, spec=draft),
                        }
                    ]
                )

        # After max iterations, return latest draft plus note
        return json.dumps(
            {
                "specification": draft,
                "note": "Returned after reaching max iterations without explicit APPROVED.",
            },
            ensure_ascii=False,
        )
