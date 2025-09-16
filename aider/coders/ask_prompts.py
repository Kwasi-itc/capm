# flake8: noqa: E501

from .base_prompts import CoderPrompts


class AskPrompts(CoderPrompts):
    main_system = """Act as an expert code analyst.
Answer questions about the supplied code.
Always reply to the user in {language}.

If you need to describe code changes, do so *briefly*.
"""

    example_messages = []

    files_content_prefix = """Here are the file names currently in scope (contents are NOT inlined).

Use FileReadTool or NotebookReadTool to fetch only the specific code you need before answering.
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
        "{final_reminders}\n\n"
        "Always fetch the exact code you need with FileReadTool / NotebookReadTool (use RepoMapTool first to map relevant files, then GrepTool "
        "to locate it when helpful).  Read only the necessary slice via offset/limit, never "
        "ask the user to paste whole files."
    )
