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

The agents may call other ``aider.tools`` such as **WebSearch** or **WebFetch**
to gather information whenever helpful during drafting or review.
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
        "loop between two LLM agents (drafter & reviewer). "
        "Agents may transparently invoke research tools like WebSearch or WebFetch "
        "to collect information before writing or revising the document."
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
                    "TechnicalArchitecture, Technical, Product, API, "
                    "Security, Data, UX, Testing, Deployment, Business, Research."
                ),
                "enum": [
                    "TechnicalArchitecture",
                    "Technical",
                    "Product",
                    "API",
                    "Security",
                    "Data",
                    "UX",
                    "Testing",
                    "Deployment",
                    "Business",
                    "Research",
                ],
                "default": "Technical",
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
    "TechnicalArchitecture": {
        "drafter": (
            "You are a senior solutions architect.\n"
            "Create a detailed technical architecture document for the topic below.\n\n"
            "Topic: {topic}\n\n"
            "Include: context diagram, component list with responsibilities, "
            "sequence diagrams or interaction flows, data models, technology choices "
            "with rationale, scalability/security/reliability considerations, risks, "
            "and a migration or rollout plan. Use markdown with appropriate mermaid "
            "diagrams where helpful.\n\n"
            "You may call the WebSearch tool to research best practices or reference "
            "architectures. Cite sources when relevant."
        ),
        "reviewer": (
            "You are a principal architect reviewing the architecture below.\n"
            "Respond with a concise bullet list of deficiencies **or** 'APPROVED' "
            "if the document is production-ready.\n\nArchitecture:\n\n{spec}"
        ),
    },
    "Technical": {
        "drafter": (
            "You are a senior engineer tasked with producing a technical specification.\n"
            "Draft a complete document for the topic below.\n\n"
            "Topic: {topic}\n\n"
            "Include: overview, context, detailed requirements, system design, "
            "data models, algorithms, constraints, acceptance criteria and glossary.\n"
            "Use WebSearch when external standards or libraries need to be referenced."
        ),
        "reviewer": (
            "Critically review the technical specification below and reply with either "
            "'APPROVED' or a bullet list of improvements.\n\nSpecification:\n\n{spec}"
        ),
    },
    "Product": {
        "drafter": (
            "You are a product manager creating a **Project Requirements Document (PRD)**.\n"
            "Write the PRD for the topic below.\n\n"
            "Topic: {topic}\n\n"
            "The document MUST contain the following sections **in order**:\n"
            "1. Acronyms & Conventions table\n"
            "2. Problem Statement\n"
            "3. Proposed Solution and Use-Case Scenario(s)\n"
            "4. Stakeholders & Personas (include role and relevance)\n"
            "5. In-Scope Items\n"
            "6. Out-of-Scope Items\n"
            "7. Functional Requirements – present **each** requirement as a *Use Case* with:\n"
            "   • Use Case ID\n   • Summary\n   • Basic Flow\n   • Alternate Flow\n"
            "   • Preconditions\n   • Post-conditions\n   • Acceptance Criteria\n"
            "8. Non-functional Requirements\n"
            "9. Success Criteria explained and how they will be achieved\n"
            "10. Assumptions\n\n"
            "Use clear markdown headings and tables where helpful. You may invoke the "
            "WebSearch tool to gather competitive or market data."
        ),
        "reviewer": (
            "Review the PRD below and verify that every required section is present and complete. "
            "If the document is fully satisfactory respond with 'APPROVED'; otherwise provide a "
            "bullet list of deficiencies.\n\nPRD:\n\n{spec}"
        ),
    },
    "API": {
        "drafter": (
            "You are an API designer.\n"
            "Produce a REST/GraphQL API specification for the topic below.\n\n"
            "Topic: {topic}\n\n"
            "Include: high-level overview, authentication, versioning, all endpoints "
            "with methods, parameters, request/response JSON schemas, error codes, "
            "rate limits and examples. Use markdown tables where helpful.\n"
            "Use WebSearch to reference RFCs or industry guidelines."
        ),
        "reviewer": (
            "Review the API specification below and respond with 'APPROVED' or issues.\n\nAPI Spec:\n\n{spec}"
        ),
    },
    "Security": {
        "drafter": (
            "Create a security specification for the topic below.\n\n"
            "Topic: {topic}\n\n"
            "Include threat model, attack surfaces, security controls, encryption, "
            "access management, compliance requirements, monitoring and incident response.\n"
            "You may WebSearch relevant standards (eg NIST, OWASP) and cite them."
        ),
        "reviewer": (
            "Review the security spec and reply 'APPROVED' or list gaps.\n\nSpec:\n\n{spec}"
        ),
    },
    "Data": {
        "drafter": (
            "Write a data specification / data model document for the topic below.\n\n"
            "Topic: {topic}\n\n"
            "Include entity-relationship diagrams, schemas, data ownership, retention, "
            "quality requirements, privacy considerations and migration strategy.\n"
            "Use WebSearch for best-practice references."
        ),
        "reviewer": (
            "Evaluate the data specification below. Reply 'APPROVED' or improvement list.\n\nSpec:\n\n{spec}"
        ),
    },
    "UX": {
        "drafter": (
            "Create a UX design specification for the topic below.\n\n"
            "Topic: {topic}\n\n"
            "Include personas, user journeys, information architecture, interaction flows, "
            "wireframe descriptions and accessibility requirements.\n"
            "Leverage WebSearch to reference design guidelines."
        ),
        "reviewer": (
            "Review the UX spec and return 'APPROVED' or issues.\n\nSpec:\n\n{spec}"
        ),
    },
    "Testing": {
        "drafter": (
            "Produce a comprehensive test plan for the topic below.\n\n"
            "Topic: {topic}\n\n"
            "Cover test objectives, scope, types of testing, environments, data, "
            "automation strategy, entry/exit criteria and schedule.\n"
            "WebSearch may be used to gather framework best practices."
        ),
        "reviewer": (
            "Assess the test plan. Respond 'APPROVED' or list deficiencies.\n\nPlan:\n\n{spec}"
        ),
    },
    "Deployment": {
        "drafter": (
            "Draft a deployment specification for the topic below.\n\n"
            "Topic: {topic}\n\n"
            "Describe environments, CI/CD pipeline, infrastructure as code, "
            "rollback strategy, monitoring, scaling and operational runbooks.\n"
            "Use WebSearch to reference tooling or cloud patterns."
        ),
        "reviewer": (
            "Review the deployment spec and reply 'APPROVED' or improvement bullets.\n\nSpec:\n\n{spec}"
        ),
    },
    "Business": {
        "drafter": (
            "Create a business requirements document for the topic below.\n\n"
            "Topic: {topic}\n\n"
            "Include problem statement, objectives, KPIs, stakeholders, financial "
            "analysis, risks, assumptions and timeline.\n"
            "WebSearch may be invoked for market data."
        ),
        "reviewer": (
            "Review the business requirements below and respond 'APPROVED' or issues.\n\nBRD:\n\n{spec}"
        ),
    },
    "Research": {
        "drafter": (
            "Write a research proposal for the topic below.\n\n"
            "Topic: {topic}\n\n"
            "Include background, literature review (use WebSearch to cite sources), "
            "research questions, methodology, expected outcomes, timeline and ethics.\n"
        ),
        "reviewer": (
            "Evaluate the research proposal. Reply with 'APPROVED' or required changes.\n\nProposal:\n\n{spec}"
        ),
    },
}

    # -------------------------- main entry point -------------------------- #

    def run(  # noqa: D401
        self,
        topic: str,
        spec_type: str = "Technical",
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
        templates = self.SPEC_PROMPTS.get(spec_type, self.SPEC_PROMPTS["Technical"])
        drafter_prompt = templates["drafter"]
        reviewer_prompt = templates["reviewer"]

        def chat(messages: List[Dict[str, str]]) -> str:
            """
            Call the OpenAI chat completion API in a way that works for both the
            pre-1.0 and 1.x versions of the ``openai`` python package.

            The older (<1.0) package exposes ``openai.ChatCompletion.create`` while
            the 1.x package moved the entry-point to
            ``openai.OpenAI().chat.completions.create``.
            """
            # Newer `openai>=1.0`
            if hasattr(openai, "OpenAI"):
                client = openai.OpenAI()
                resp = client.chat.completions.create(model=model_name, messages=messages)
                return resp.choices[0].message.content.strip()

            # Fallback for legacy `openai<1.0`
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
