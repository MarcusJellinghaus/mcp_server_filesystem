import tempfile
import unittest
from pathlib import Path

import pytest

from mcp_workspace.file_tools.edit_file import edit_file


class TestEditFileBackslashHint(unittest.TestCase):
    def test_single_backslash_old_string_gives_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "windows_path.json"
            # File on disk stores double backslashes (raw JSON-encoded Windows path)
            test_file.write_text(
                '{"path": "C:\\\\Users\\\\test\\\\file.json"}', encoding="utf-8"
            )

            # LLM constructs old_string with single backslashes (decoded understanding)
            with pytest.raises(ValueError, match="double backslashes"):
                edit_file(
                    str(test_file),
                    old_string='{"path": "C:\\Users\\test\\file.json"}',
                    new_string='{"path": "C:\\Users\\test\\file_NEW.json"}',
                )
