import logging
from pathlib import Path

from diff_match_patch import diff_match_patch

try:
    import git
except ImportError:
    git = None

# Assumes BaseTool and ToolError are imported from your existing module, like so:
# from .base import BaseTool, ToolError
#
# Also assumes the following utility is available:
# from aider.utils import GitTemporaryDirectory

logger = logging.getLogger(__name__)


# Helper Classes and Functions for Search/Replace Logic
class RelativeIndenter:
    """
    Rewrites text files to have relative indentation, making it easier
    to search and apply edits to code blocks with different indentation levels.
    """

    def __init__(self, texts):
        chars = set()
        for text in texts:
            chars.update(text)

        ARROW = "←"
        if ARROW not in chars:
            self.marker = ARROW
        else:
            self.marker = self.select_unique_marker(chars)

    def select_unique_marker(self, chars):
        for codepoint in range(0x10FFFF, 0x10000, -1):
            marker = chr(codepoint)
            if marker not in chars:
                return marker
        raise ValueError("Could not find a unique marker")

    def make_relative(self, text):
        if self.marker in text:
            raise ValueError(f"Text already contains the outdent marker: {self.marker}")

        lines = text.splitlines(keepends=True)
        output = []
        prev_indent = ""
        for line in lines:
            line_without_end = line.rstrip("\n\r")
            len_indent = len(line_without_end) - len(line_without_end.lstrip())
            indent = line[:len_indent]
            change = len_indent - len(prev_indent)
            if change > 0:
                cur_indent = indent[-change:]
            elif change < 0:
                cur_indent = self.marker * -change
            else:
                cur_indent = ""

            out_line = cur_indent + "\n" + line[len_indent:]
            output.append(out_line)
            prev_indent = indent
        return "".join(output)

    def make_absolute(self, text):
        lines = text.splitlines(keepends=True)
        output = []
        prev_indent = ""
        for i in range(0, len(lines), 2):
            dent = lines[i].rstrip("\r\n")
            non_indent = lines[i + 1]

            if dent.startswith(self.marker):
                len_outdent = len(dent)
                cur_indent = prev_indent[:-len_outdent]
            else:
                cur_indent = prev_indent + dent

            if not non_indent.rstrip("\r\n"):
                out_line = non_indent
            else:
                out_line = cur_indent + non_indent

            output.append(out_line)
            prev_indent = cur_indent
        res = "".join(output)
        if self.marker in res:
            raise ValueError("Error transforming text back to absolute indents")
        return res


def relative_indent(texts):
    ri = RelativeIndenter(texts)
    texts = list(map(ri.make_relative, texts))
    return ri, texts


def lines_to_chars(lines, mapping):
    new_text = []
    for char in lines:
        new_text.append(mapping[ord(char)])
    return "".join(new_text)


def dmp_lines_apply(texts):
    search_text, replace_text, original_text = texts
    dmp = diff_match_patch()
    dmp.Diff_Timeout = 5
    dmp.Match_Threshold = 0.1
    dmp.Match_Distance = 100_000
    dmp.Patch_Margin = 1

    all_text = search_text + replace_text + original_text
    all_lines, _, mapping = dmp.diff_linesToChars(all_text, "")
    
    search_num = len(search_text.splitlines())
    replace_num = len(replace_text.splitlines())
    
    search_lines = all_lines[:search_num]
    replace_lines = all_lines[search_num:search_num + replace_num]
    original_lines = all_lines[search_num + replace_num:]

    diff_lines = dmp.diff_main(search_lines, replace_lines, None)
    dmp.diff_cleanupSemantic(diff_lines)
    dmp.diff_cleanupEfficiency(diff_lines)

    patches = dmp.patch_make(search_lines, diff_lines)
    new_lines, success = dmp.patch_apply(patches, original_lines)

    if False in success:
        return None

    new_text = lines_to_chars(new_lines, mapping)
    return new_text


def search_and_replace(texts):
    search_text, replace_text, original_text = texts
    if original_text.count(search_text) == 0:
        return None
    return original_text.replace(search_text, replace_text)


def git_cherry_pick_osr_onto_o(texts):
    if not git:
        return None
        
    search_text, replace_text, original_text = texts
    try:
        with GitTemporaryDirectory() as dname:
            repo = git.Repo(dname)
            fname = Path(dname) / "file.txt"

            # O -> S -> R
            fname.write_text(original_text)
            repo.git.add(str(fname))
            repo.git.commit("-m", "original")
            original_hash = repo.head.commit.hexsha

            fname.write_text(search_text)
            repo.git.add(str(fname))
            repo.git.commit("-m", "search")

            fname.write_text(replace_text)
            repo.git.add(str(fname))
            repo.git.commit("-m", "replace")
            replace_hash = repo.head.commit.hexsha

            repo.git.checkout(original_hash)

            # cherry pick R onto O
            repo.git.cherry_pick(replace_hash, "--minimal")
            return fname.read_text()
    except (git.exc.ODBError, git.exc.GitError):
        return None


def reverse_lines(text):
    lines = text.splitlines(keepends=True)
    lines.reverse()
    return "".join(lines)


def strip_blank_lines(texts):
    return [text.strip("\n") + "\n" for text in texts]


def try_strategy(texts, strategy, preproc):
    preproc_strip_blank_lines, preproc_relative_indent, preproc_reverse = preproc
    ri = None

    try:
        if preproc_strip_blank_lines:
            texts = strip_blank_lines(texts)
        if preproc_relative_indent:
            ri, texts = relative_indent(texts)
        if preproc_reverse:
            texts = list(map(reverse_lines, texts))

        res = strategy(texts)

        if res and preproc_reverse:
            res = reverse_lines(res)
        if res and ri:
            res = ri.make_absolute(res)

        return res
    except Exception:
        return None


all_preprocs = [
    (False, False, False),
    (True, False, False),
    (False, True, False),
    (True, True, False),
]

editblock_strategies = [
    (search_and_replace, all_preprocs),
    (git_cherry_pick_osr_onto_o, all_preprocs),
    (dmp_lines_apply, all_preprocs),
]


def flexible_search_and_replace(texts, strategies):
    for strategy, preprocs in strategies:
        for preproc in preprocs:
            res = try_strategy(texts, strategy, preproc)
            if res is not None:
                return res


# SearchReplaceTool Definition
class SearchReplaceTool(BaseTool):
    """
    A tool to perform a flexible search and replace on the content of a file.
    """

    name = "search_replace"
    description = (
        "Apply a search and replace operation to a file's content. "
        "This tool is useful for refactoring, correcting, or modifying code blocks."
    )
    parameters = {
        "type": "object",
        "properties": {
            "search_text": {
                "type": "string",
                "description": "The exact block of text to search for in the original content.",
            },
            "replace_text": {
                "type": "string",
                "description": "The text that will replace the `search_text`.",
            },
            "original_text": {
                "type": "string",
                "description": "The full original content of the file to be modified.",
            },
        },
        "required": ["search_text", "replace_text", "original_text"],
    }

    def run(self, search_text: str, replace_text: str, original_text: str) -> str:
        """
        Executes a series of search and replace strategies to apply the
        requested change to the original text.
        """
        texts = (search_text, replace_text, original_text)
        
        result = flexible_search_and_replace(texts, editblock_strategies)

        if result is None:
            raise ToolError(
                "Failed to apply the search/replace operation. "
                "The `search_text` might not have been found, or the patch was not applicable."
            )
        
        return result