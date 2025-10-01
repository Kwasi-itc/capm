# flake8: noqa: E501

from .editblock_prompts import EditBlockPrompts


class EditorEditBlockPrompts(EditBlockPrompts):
    main_system = """Act as an expert software developer who edits source code.
{final_reminders}
Use the dedicated editing tools (`multi_edit`, `file_edit`, `file_write`) to apply all code
changes. Call those tools directly instead of emitting raw *SEARCH/REPLACE* blocks or unified
diffs. When no changes are required, reply with a short explanatory message – do NOT output code
blocks.
"""

    shell_cmd_prompt = ""
    no_shell_cmd_prompt = ""
    shell_cmd_reminder = ""
    go_ahead_tip = ""
    rename_with_shell = ""
