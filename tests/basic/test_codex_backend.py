import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

from aider.codex_backend import _quote_for_shell, run_codex_backend


class TestCodexBackend(TestCase):
    def make_args(self, **overrides):
        values = dict(
            codex_command="codex",
            codex_model=None,
            codex_skip_login=False,
            message=None,
            message_file=None,
            encoding="utf-8",
        )
        values.update(overrides)
        return type("Args", (), values)()

    @patch("aider.codex_backend.shutil.which", return_value=None)
    def test_missing_codex_cli(self, _):
        io = MagicMock()
        status = run_codex_backend(self.make_args(), io)

        self.assertEqual(status, 1)
        io.tool_error.assert_called_once()
        io.tool_output.assert_called()

    @patch("aider.codex_backend.subprocess.call")
    @patch("aider.codex_backend.shutil.which", return_value="C:/bin/codex.cmd")
    @patch("aider.codex_backend.sys.platform", "linux")
    def test_runs_login_then_codex(self, _, mock_call):
        mock_call.side_effect = [0, 0]
        io = MagicMock()

        status = run_codex_backend(
            self.make_args(codex_model="gpt-5.1-codex", message="fix the tests"),
            io,
            cwd="repo",
        )

        self.assertEqual(status, 0)
        self.assertEqual(mock_call.call_args_list[0].args[0], ["C:/bin/codex.cmd", "login"])
        self.assertEqual(
            mock_call.call_args_list[1].args[0],
            ["C:/bin/codex.cmd", "-m", "gpt-5.1-codex", "fix the tests"],
        )

    @patch("aider.codex_backend.subprocess.call", return_value=0)
    @patch("aider.codex_backend.shutil.which", return_value="codex")
    @patch("aider.codex_backend.sys.platform", "linux")
    def test_skip_login(self, _, mock_call):
        io = MagicMock()

        status = run_codex_backend(self.make_args(codex_skip_login=True), io)

        self.assertEqual(status, 0)
        mock_call.assert_called_once_with(["codex"], cwd=None)

    @patch("aider.codex_backend.subprocess.call", return_value=0)
    @patch("aider.codex_backend.shutil.which", return_value="codex")
    @patch("aider.codex_backend.sys.platform", "linux")
    def test_message_file(self, _, mock_call):
        io = MagicMock()
        with tempfile.TemporaryDirectory() as tempdir:
            message_file = Path(tempdir) / "message.txt"
            message_file.write_text("from file", encoding="utf-8")

            status = run_codex_backend(
                self.make_args(codex_skip_login=True, message_file=str(message_file)), io
            )

        self.assertEqual(status, 0)
        mock_call.assert_called_once_with(["codex", "from file"], cwd=None)

    @patch("aider.codex_backend.subprocess.call", return_value=0)
    @patch("aider.codex_backend.shutil.which", return_value="C:/Users/Me/AppData/Roaming/npm/codex")
    @patch("aider.codex_backend.sys.platform", "win32")
    def test_windows_uses_shell(self, _, mock_call):
        io = MagicMock()

        status = run_codex_backend(self.make_args(codex_skip_login=True, message="hello there"), io)

        self.assertEqual(status, 0)
        mock_call.assert_called_once_with(
            _quote_for_shell(["C:/Users/Me/AppData/Roaming/npm/codex", "hello there"]),
            cwd=None,
            shell=True,
        )

    @patch("aider.codex_backend.subprocess.call", side_effect=OSError("[WinError 193] bad app"))
    @patch("aider.codex_backend.shutil.which", return_value="codex")
    def test_launch_oserror_is_reported(self, _, _mock_call):
        io = MagicMock()

        status = run_codex_backend(self.make_args(codex_skip_login=True), io)

        self.assertEqual(status, 1)
        io.tool_error.assert_called_once()
