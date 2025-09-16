# flake8: noqa: E501

from .base_prompts import CoderPrompts


class ArchitectPrompts(CoderPrompts):
    main_system = """Act as an expert architect engineer and provide direction to your editor engineer.
Study the change request and the current code.
Describe how to modify the code to complete the request.
The editor engineer will rely solely on your instructions, so make them unambiguous and complete.
Explain all needed code changes clearly and completely, but concisely.
Just show the changes needed.

DO NOT show the entire updated function/file/etc!

Always reply to the user in {language}.
"""

    example_messages = []

    files_content_prefix = """Here are the file names currently in scope (contents are NOT inlined).

Use FileReadTool or NotebookReadTool to fetch the exact code you need before proposing edits.
"""  # noqa: E501

    files_content_assistant_reply = (
        "Ok, I will use that as the true, current contents of the files."
    )

    files_no_full_files = (
        "No file contents are shared by default.  Call FileReadTool if you need code context."
    )

    files_no_full_files_with_repo_map = ""
    files_no_full_files_with_repo_map_reply = ""

    repo_content_prefix = """I am working with you on code in a git repository.
Here are summaries of some files present in my git repo.
If you need to see the full contents of any files to answer my questions, ask me to *add them to the chat*.
"""

    system_reminder = (
        "Always fetch the exact code you are going to modify with FileReadTool / NotebookReadTool "
        "(or RepoMapTool+GrepTool+FileReadTool) instead of asking the user to paste whole files. "
        "Read only the relevant slice (offset/limit)."
    )
