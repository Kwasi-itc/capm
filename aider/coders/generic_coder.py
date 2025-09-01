"""
GenericCoder: A minimal, repo-agnostic coder core.

This class runs an agentic chat loop with optional tool
invocations returned by the LLM.  It purposefully excludes
repo-map logic, file-editing formats and other specialised
behaviour so that subclasses can layer their own features
on top (eg. code-editing, document Q&A, etc.).
"""
from __future__ import annotations

import json
from typing import Any, Dict, List

from aider.llm import litellm
from aider.tools import discover_tools
from aider.tools.base_tool import BaseTool, ToolError


class GenericCoder:
    """
    Lightweight chat/agent loop with pluggable tools.

    Subclasses should:
    • provide prompt-formatting logic
    • call run()/run_stream() to engage the model
    • optionally override _send/_handle_* for custom handling
    """

    def __init__(
        self,
        main_model,
        io,
        functions: List[Dict[str, Any]] | None = None,
        **kwargs,
    ):
        self.main_model = main_model
        self.io = io

        # ---------- tool discovery / registration -------------------------
        if functions is None:
            tool_classes = discover_tools()
            self._tools: dict[str, BaseTool] = {cls.name: cls() for cls in tool_classes}
            for _tool in self._tools.values():
                setattr(_tool, "coder", self)
            self.functions = [tool.json_schema() for tool in self._tools.values()]
        else:
            # External list supplied (eg. tests)
            self._tools = {f["name"]: None for f in functions}
            self.functions = functions

        # rolling dialogue
        self.cur_messages: List[Dict[str, Any]] = []
        self.partial_response_content: str = ""
        self.partial_response_function_call: Dict[str, str] = {}

    # ------------------------------------------------------------------ #
    # Public helpers                                                     #
    # ------------------------------------------------------------------ #
    def run_stream(self, user_message: str):
        "Yield assistant output chunks while streaming."
        self.cur_messages.append({"role": "user", "content": user_message})
        yield from self._send(self.cur_messages)

    def run(self, user_message: str) -> str:
        "Blocking wrapper that returns the full assistant reply."
        for _ in self.run_stream(user_message):
            pass
        return self.partial_response_content

    # ------------------------------------------------------------------ #
    # Core send logic                                                    #
    # ------------------------------------------------------------------ #
    def _send(self, messages):
        # Reset state
        self.partial_response_content = ""
        self.partial_response_function_call = {}

        completion = litellm.completion(
            model=self.main_model.name,
            messages=messages,
            stream=bool(self.main_model.streaming),
            functions=self.functions if self.functions else None,
            **self.main_model.extra_params,
        )

        if self.main_model.streaming:
            yield from self._handle_stream(completion)
        else:
            self._handle_single(completion)
            yield self.partial_response_content

        # If assistant requested a tool, execute it and recurse
        if self.partial_response_function_call:
            self._handle_tool(self.partial_response_function_call)
            yield from self._send(self.cur_messages)

    # ------------------------------------------------------------------ #
    # Response handling                                                  #
    # ------------------------------------------------------------------ #
    def _handle_single(self, completion):
        msg = completion.choices[0].message
        self.partial_response_content = msg.content or ""
        if msg.tool_calls:
            self.partial_response_function_call = msg.tool_calls[0].function
        self.cur_messages.append({"role": "assistant", "content": self.partial_response_content})

    def _handle_stream(self, completion):
        for chunk in completion:
            if not chunk.choices or not chunk.choices[0].delta:
                continue
            delta = chunk.choices[0].delta
            if delta.content:
                self.partial_response_content += delta.content
                yield delta.content
            if delta.function_call:
                for k, v in delta.function_call.items():
                    self.partial_response_function_call[k] = (
                        self.partial_response_function_call.get(k, "") + v
                    )
        self.cur_messages.append(
            {"role": "assistant", "content": self.partial_response_content}
        )

    # ------------------------------------------------------------------ #
    # Tool execution                                                     #
    # ------------------------------------------------------------------ #
    def _handle_tool(self, func_call: Dict[str, str]):
        fn_name = func_call.get("name")
        raw_args = func_call.get("arguments", "{}")
        tool = self._tools.get(fn_name)
        if not tool:
            self.io.tool_error(f"Unknown tool requested: {fn_name}")
            return

        try:
            args = json.loads(raw_args or "{}")
        except json.JSONDecodeError:
            self.io.tool_error(f"Malformed tool arguments JSON: {raw_args}")
            return

        try:
            result = tool.run(**args)
        except ToolError as e:
            result = f"Tool error: {e}"

        # Echo call & result to user
        self.io.assistant_output(self.io.format_tool_call(fn_name, raw_args))
        self.io.assistant_output(self.io.format_tool_result(fn_name, result))

        # Feed back into chat
        self.cur_messages.append({"role": "tool", "name": fn_name, "content": str(result)})
