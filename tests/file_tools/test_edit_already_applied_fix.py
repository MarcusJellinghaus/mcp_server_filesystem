import tempfile
import unittest
from pathlib import Path

from src.file_tools.edit_file import _is_edit_already_applied, edit_file


class TestEditAlreadyAppliedFix(unittest.TestCase):
    """Tests for the fix to already-applied detection false positives."""

    def setUp(self) -> None:
        # Create a temporary directory and file for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)
        self.test_file = self.project_dir / "test_file.py"

    def tearDown(self) -> None:
        # Clean up after tests
        self.temp_dir.cleanup()

    def test_is_edit_already_applied_helper_function(self) -> None:
        """Test the _is_edit_already_applied helper function directly."""
        # Test case 1: Edit not applied yet (old text exists, new text doesn't)
        content = "function_name = 'original'"
        old_text = "function_name"
        new_text = "new_function_name"
        self.assertFalse(_is_edit_already_applied(content, old_text, new_text))

        # Test case 2: Edit already applied (old text gone, new text present)
        content = "modified_function = 'original'"
        old_text = "function_name"
        new_text = "modified_function"
        self.assertTrue(_is_edit_already_applied(content, old_text, new_text))

        # Test case 3: False positive scenario (new text appears elsewhere)
        content = 'function_name = "test"\nprint("test")'
        old_text = "function_name"
        new_text = "test"
        # Should return False because old_text still exists, even though new_text appears in file
        self.assertFalse(_is_edit_already_applied(content, old_text, new_text))

        # Test case 4: Both old and new text exist (partial edit state)
        content = "function_name = 'test'\nmodified_function = 'other'"
        old_text = "function_name"
        new_text = "modified_function"
        self.assertFalse(_is_edit_already_applied(content, old_text, new_text))

    def test_false_positive_prevention_single_line(self) -> None:
        """Test that the fix prevents false positives with single-line edits."""
        # Create a file where new_text appears elsewhere but edit is not applied
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write('function_name = "test"\nprint("test")\n')

        # This edit should be applied, not skipped
        edits = [{"old_text": "function_name", "new_text": "test"}]

        result = edit_file(str(self.test_file), edits)

        # Should succeed and make changes (not skip due to false positive)
        self.assertTrue(result["success"])
        self.assertNotEqual(result["diff"], "")

        # Verify the edit was actually applied
        with open(self.test_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn('test = "test"', content)
        self.assertNotIn('function_name = "test"', content)

    def test_false_positive_prevention_multiline(self) -> None:
        """Test that the fix prevents false positives with multi-line edits."""
        # Create a file where part of new_text appears elsewhere
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(
                "def old_function():\n"
                '    return "result"\n'
                "\n"
                '# Comment mentions: return "result"\n'
                'print("Debug info")\n'
            )

        # This multi-line edit should be applied, not skipped
        edits = [
            {
                "old_text": 'def old_function():\n    return "result"',
                "new_text": 'def new_function():\n    return "result"',
            }
        ]

        result = edit_file(str(self.test_file), edits)

        # Should succeed and make changes
        self.assertTrue(result["success"])
        self.assertNotEqual(result["diff"], "")

        # Verify the edit was applied
        with open(self.test_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("def new_function():", content)
        self.assertNotIn("def old_function():", content)
        # The comment should still be there (unchanged)
        self.assertIn('# Comment mentions: return "result"', content)

    def test_legitimate_already_applied_detection(self) -> None:
        """Test that legitimate already-applied cases are still detected correctly."""
        # Create a file and apply an edit
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write("def test_function():\n    return 'test'\n")

        edits = [{"old_text": "test_function", "new_text": "modified_function"}]

        # First application should succeed
        result1 = edit_file(str(self.test_file), edits)
        self.assertTrue(result1["success"])
        self.assertNotEqual(result1["diff"], "")

        # Second application should be skipped (already applied)
        result2 = edit_file(str(self.test_file), edits)
        self.assertTrue(result2["success"])
        self.assertEqual(result2["diff"], "")
        self.assertEqual(
            result2["message"], "No changes needed - content already in desired state"
        )

    def test_false_positive_with_preserve_indentation(self) -> None:
        """Test false positive prevention when preserve_indentation is enabled."""
        # Create a file where new_text appears with different indentation
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(
                '    old_variable = "value"\n'
                'new_variable = "other"\n'  # new_text appears but not indented
            )

        edits = [{"old_text": "    old_variable", "new_text": "new_variable"}]
        options = {"preserve_indentation": True}

        result = edit_file(str(self.test_file), edits, options=options)

        # Should succeed and make changes (not skip due to false positive)
        self.assertTrue(result["success"])
        self.assertNotEqual(result["diff"], "")

        # Verify the edit was applied with proper indentation
        with open(self.test_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn('    new_variable = "value"', content)
        self.assertNotIn('    old_variable = "value"', content)

    def test_complex_false_positive_scenario(self) -> None:
        """Test a complex scenario that could trigger false positives."""
        # Create a file with function names that could conflict
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(
                "def process_data():\n"
                "    return process(data)\n"
                "\n"
                "def handle_process():\n"
                '    print("Handling process")\n'
                "\n"
                "# TODO: Update process_data function\n"
            )

        # Edit that renames a function
        edits = [{"old_text": "process_data", "new_text": "process"}]

        result = edit_file(str(self.test_file), edits)

        # Should succeed and make changes (only first occurrence)
        self.assertTrue(result["success"])
        self.assertNotEqual(result["diff"], "")

        # Verify only the first occurrence was changed
        with open(self.test_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Function definition should be changed
        self.assertIn("def process():", content)
        self.assertNotIn("def process_data():", content)

        # But other occurrences should remain (since we only replace first occurrence)
        self.assertIn("return process(data)", content)
        self.assertIn("handle_process", content)
        self.assertIn("# TODO: Update process_data function", content)


if __name__ == "__main__":
    unittest.main()
