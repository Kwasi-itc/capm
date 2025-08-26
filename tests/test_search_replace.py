import pytest

from aider.tools.search_replace_tool import SearchReplaceTool


@pytest.fixture(scope="module")
def tool():
    """Provide a single SearchReplaceTool instance for all tests."""
    return SearchReplaceTool()


def test_simple_replace(tool):
    original_text = "hello world"
    search_text = "world"
    replace_text = "universe"

    result = tool.run(
        search_text=search_text,
        replace_text=replace_text,
        original_text=original_text,
    )

    assert result == "hello universe"


def test_multiline_replace(tool):
    original_text = (
        "def greet(name):\n"
        "    print(f'Hello, {name}!')\n"
        "\n"
        "def farewell(name):\n"
        "    print(f'Goodbye, {name}!')\n"
    )
    search_text = (
        "def farewell(name):\n"
        "    print(f'Goodbye, {name}!')\n"
    )
    replace_text = (
        "def farewell(name):\n"
        "    print(f'See you soon, {name}!')\n"
    )

    result = tool.run(
        search_text=search_text,
        replace_text=replace_text,
        original_text=original_text,
    )

    assert "See you soon" in result
    assert "Goodbye" not in result
