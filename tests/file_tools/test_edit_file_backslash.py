import tempfile
import unittest
from pathlib import Path

from mcp_workspace.file_tools.edit_file import edit_file


class TestEditFileBackslashHint(unittest.TestCase):
    def test_single_backslash_old_text_gives_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "windows_path.json"
            # File on disk stores double backslashes (raw JSON-encoded Windows path)
            test_file.write_text(
                '{"path": "C:\\\\Users\\\\test\\\\file.json"}', encoding="utf-8"
            )

            # LLM constructs old_text with single backslashes (decoded understanding)
            result = edit_file(
                str(test_file),
                [
                    {
                        "old_text": '{"path": "C:\\Users\\test\\file.json"}',
                        "new_text": '{"path": "C:\\Users\\test\\file_NEW.json"}',
                    }
                ],
            )

            self.assertFalse(result["success"])
            self.assertEqual(result["match_results"][0]["match_type"], "failed")
            self.assertIn(
                "Hint: file may store backslashes as `\\\\` (double backslashes)",
                result["match_results"][0]["details"],
            )
            self.assertEqual(
                result["message"], "Failed to find exact match for 1 edit(s)"
            )
            self.assertEqual(
                result["error"], "Failed to find exact match for 1 edit(s)"
            )
