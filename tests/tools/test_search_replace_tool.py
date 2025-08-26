import pytest

from aider.tools.search_replace_tool import SearchReplaceTool, ToolError


def test_search_replace_success():
    """
    The `SearchReplaceTool` should successfully replace an exact match
    of `search_text` inside `original_text`.
    """
    tool = SearchReplaceTool()
    original_text = "Hello World\n"
    search_text = "World"
    replace_text = "Universe"

    result = tool.run(search_text, replace_text, original_text)

    assert result == "Hello Universe\n"


def test_search_replace_failure():
    """
    Attempting to replace text that does not exist in `original_text`
    should raise a `ToolError`.
    """
    tool = SearchReplaceTool()
    original_text = "Hello World\n"
    search_text = "Mars"
    replace_text = "Venus"

    with pytest.raises(ToolError):
        tool.run(search_text, replace_text, original_text)
