import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.file_tools.edit_file import (
    EditOperation,
    EditOptions,
    MatchResult,
    apply_edits,
    create_unified_diff,
    detect_indentation,
    edit_file,
    find_exact_match,
    find_fuzzy_match,
    get_line_indentation,
    is_markdown_bullets,
    normalize_line_endings,
    normalize_whitespace,
    preserve_indentation,
)


class TestEditFileUtils(unittest.TestCase):

    def test_normalize_line_endings(self):
        text = "line1\r\nline2\nline3\r\nline4"
        normalized = normalize_line_endings(text)
        self.assertEqual(normalized, "line1\nline2\nline3\nline4")
        self.assertNotIn("\r\n", normalized)

    def test_normalize_whitespace(self):
        text = "  line1   with    spaces\n\t\tline2\twith\ttabs  "
        normalized = normalize_whitespace(text)
        self.assertEqual(normalized, "line1 with spaces\nline2 with tabs")

    def test_detect_indentation_spaces(self):
        text = "def function():\n    line1\n    line2\n        nested"
        indent_str, indent_size = detect_indentation(text)
        self.assertEqual(indent_str, "    ")
        self.assertEqual(indent_size, 4)

    def test_detect_indentation_tabs(self):
        text = "def function():\n\tline1\n\tline2\n\t\tnested"
        indent_str, indent_size = detect_indentation(text)
        self.assertEqual(indent_str, "\t")
        self.assertEqual(indent_size, 1)

    def test_get_line_indentation(self):
        self.assertEqual(get_line_indentation("    indented line"), "    ")
        self.assertEqual(get_line_indentation("\t\tindented line"), "\t\t")
        self.assertEqual(get_line_indentation("no indentation"), "")

    def test_preserve_indentation(self):
        old_text = "    def function():\n        return True"
        new_text = "def new_function():\n    return False"
        preserved = preserve_indentation(old_text, new_text)
        self.assertEqual(preserved, "    def new_function():\n        return False")

    def test_find_exact_match(self):
        content = "line1\nline2\nline3\nline4"
        pattern = "line2\nline3"
        result = find_exact_match(content, pattern)
        self.assertTrue(result.matched)
        self.assertEqual(result.confidence, 1.0)
        self.assertEqual(result.line_index, 1)
        self.assertEqual(result.line_count, 2)

    def test_find_exact_match_not_found(self):
        content = "line1\nline2\nline3\nline4"
        pattern = "line5"
        result = find_exact_match(content, pattern)
        self.assertFalse(result.matched)
        self.assertEqual(result.confidence, 0.0)

    def test_find_fuzzy_match(self):
        content_lines = ["line1", "line2 with some extra text", "line3", "line4"]
        pattern_lines = ["line2", "line3"]
        result = find_fuzzy_match(content_lines, pattern_lines)
        self.assertTrue(result.matched)
        self.assertGreater(result.confidence, 0.8)
        self.assertEqual(result.line_index, 1)
        self.assertEqual(result.line_count, 2)

    def test_find_fuzzy_match_not_found(self):
        content_lines = ["line1", "line2", "line3", "line4"]
        pattern_lines = ["completely", "different"]
        result = find_fuzzy_match(content_lines, pattern_lines)
        self.assertFalse(result.matched)
        self.assertLess(result.confidence, 0.8)

    def test_create_unified_diff(self):
        original = "line1\nline2\nline3"
        modified = "line1\nmodified\nline3"
        diff = create_unified_diff(original, modified, "test.txt")
        self.assertIn("--- a/test.txt", diff)
        self.assertIn("+++ b/test.txt", diff)
        self.assertIn("-line2", diff)
        self.assertIn("+modified", diff)


class TestApplyEdits(unittest.TestCase):

    def test_apply_edits_exact_match(self):
        content = "def old_function():\n    return True"
        edits = [EditOperation(old_text="old_function", new_text="new_function")]
        modified, results = apply_edits(content, edits)
        self.assertEqual(modified, "def new_function():\n    return True")
        self.assertEqual(results[0]["match_type"], "exact")

    def test_apply_edits_fuzzy_match(self):
        content = "def old_function():\n    return True"
        edits = [
            EditOperation(
                old_text="def old_function():", new_text="def new_function():"
            )
        ]
        options = EditOptions(partial_match=True)
        modified, results = apply_edits(content, edits, options)
        self.assertEqual(modified, "def new_function():\n    return True")

    def test_apply_edits_multiple(self):
        content = (
            "def function_one():\n    return 1\n\ndef function_two():\n    return 2"
        )
        edits = [
            EditOperation(old_text="function_one", new_text="function_1"),
            EditOperation(old_text="function_two", new_text="function_2"),
        ]
        modified, results = apply_edits(content, edits)
        self.assertEqual(
            modified,
            "def function_1():\n    return 1\n\ndef function_2():\n    return 2",
        )
        self.assertEqual(len(results), 2)

    def test_apply_edits_preserve_indentation(self):
        content = "    if condition:\n        return True"
        edits = [
            EditOperation(
                old_text="if condition:\n        return True",
                new_text="if new_condition:\n    return False",
            )
        ]
        options = EditOptions(preserve_indentation=True)
        modified, results = apply_edits(content, edits, options)
        self.assertEqual(modified, "    if new_condition:\n        return False")

    def test_is_markdown_bullets(self):
        # Test detection of markdown bullet lists
        old_text = "- First bullet\n- Second bullet\n- Third bullet"
        new_text = "- First bullet\n  - Nested bullet 1\n  - Nested bullet 2"
        self.assertTrue(is_markdown_bullets(old_text, new_text))

        # Should return false for non-bullet content
        old_text = "Regular text\nNo bullets here\nJust plain text"
        new_text = "Modified text\nStill no bullets\nUpdated content"
        self.assertFalse(is_markdown_bullets(old_text, new_text))

    def test_markdown_bullet_indentation(self):
        # Test specific issue with markdown bullet point indentation in documentation
        content = "- Top level item\n- Parameters:\n- param1: value1\n- param2: value2"
        edits = [
            EditOperation(
                old_text="- Parameters:\n- param1: value1\n- param2: value2",
                new_text="- Parameters:\n  - param1: value1\n  - param2: value2",
            )
        ]
        options = EditOptions(preserve_indentation=True)
        modified, results = apply_edits(content, edits, options)
        self.assertEqual(
            modified,
            "- Top level item\n- Parameters:\n  - param1: value1\n  - param2: value2",
        )
        self.assertEqual(results[0]["match_type"], "exact")

    def test_apply_edits_no_match(self):
        content = "def function():\n    return True"
        edits = [EditOperation(old_text="nonexistent", new_text="replacement")]
        options = EditOptions(partial_match=False)
        with self.assertRaises(ValueError):
            apply_edits(content, edits, options)


class TestEditFile(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory and file for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)
        self.test_file = self.project_dir / "test_file.py"
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write("def test_function():\n    return 'test'\n")

    def tearDown(self):
        # Clean up after tests
        self.temp_dir.cleanup()

    def test_edit_file_success(self):
        edits = [
            {"old_text": "test_function", "new_text": "modified_function"},
            {"old_text": "'test'", "new_text": "'modified'"},
        ]

        result = edit_file(str(self.test_file), edits)

        self.assertTrue(result["success"])
        self.assertIn("diff", result)
        self.assertEqual(len(result["match_results"]), 2)

        # Check the file was actually modified
        with open(self.test_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertEqual(content, "def modified_function():\n    return 'modified'\n")

    def test_edit_file_with_project_dir(self):
        edits = [{"old_text": "test_function", "new_text": "modified_function"}]

        # Use relative path with project_dir
        relative_path = "test_file.py"
        result = edit_file(relative_path, edits, project_dir=self.project_dir)

        self.assertTrue(result["success"])
        self.assertIn("diff", result)

        # Check the file was modified
        with open(self.test_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertEqual(content, "def modified_function():\n    return 'test'\n")

    def test_edit_file_with_project_dir_security(self):
        edits = [{"old_text": "test_function", "new_text": "modified_function"}]

        # Create a file outside the project directory
        outside_dir = tempfile.TemporaryDirectory()
        outside_file = Path(outside_dir.name) / "outside.py"
        with open(outside_file, "w", encoding="utf-8") as f:
            f.write("def outside_function():\n    return 'outside'\n")

        # Try to edit a file outside the project directory
        with self.assertRaises(ValueError):
            edit_file(str(outside_file), edits, project_dir=self.project_dir)

        outside_dir.cleanup()

    def test_edit_file_dry_run(self):
        edits = [{"old_text": "test_function", "new_text": "modified_function"}]

        result = edit_file(str(self.test_file), edits, dry_run=True)

        self.assertTrue(result["success"])
        self.assertIn("diff", result)
        self.assertEqual(len(result["match_results"]), 1)

        # Check the file was NOT modified (dry run)
        with open(self.test_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertEqual(content, "def test_function():\n    return 'test'\n")

    def test_edit_file_with_options(self):
        edits = [{"old_text": "test_function", "new_text": "modified_function"}]
        options = {
            "preserve_indentation": True,
            "normalize_whitespace": False,
            "partial_match": True,
            "match_threshold": 0.7,
        }

        result = edit_file(str(self.test_file), edits, options=options)

        self.assertTrue(result["success"])
        self.assertIn("diff", result)

        # Check the file was modified with the correct options
        with open(self.test_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertEqual(content, "def modified_function():\n    return 'test'\n")

    def test_edit_file_not_found(self):
        edits = [{"old_text": "test_function", "new_text": "modified_function"}]

        with self.assertRaises(FileNotFoundError):
            edit_file("nonexistent_file.txt", edits)

    def test_edit_file_failed_match(self):
        edits = [{"old_text": "nonexistent_function", "new_text": "modified_function"}]
        options = {"partial_match": False}

        result = edit_file(str(self.test_file), edits, options=options)

        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("match_results", result)


class TestEditFileChallenges(unittest.TestCase):
    """Tests that verify specific challenges with the edit_file function."""

    def setUp(self):
        # Create a temporary directory and file for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)
        self.test_file = self.project_dir / "test_file.py"

    def tearDown(self):
        # Clean up after tests
        self.temp_dir.cleanup()

    def test_large_block_replacement_indentation(self):
        """Test that large block replacements can result in indentation issues."""
        # Create a Python file with nested indentation
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(
                'class DataProcessor:\n    def __init__(self):\n        self.data = []\n    \n    def process_data(self):\n        if not self.data:\n            return {}\n        \n        result = {\n            "count": len(self.data),\n            "processed": True\n        }\n        \n        return result\n'
            )

        # Try to replace entire process_data method with new content
        edits = [
            {
                "old_text": '    def process_data(self):\n        if not self.data:\n            return {}\n        \n        result = {\n            "count": len(self.data),\n            "processed": True\n        }\n        \n        return result',
                "new_text": '    def process_data(self):\n        if not self.data:\n            return {}\n        \n        filtered_data = self.filter_data()\n        result = {\n            "count": len(self.data),\n            "filtered": len(filtered_data),\n            "processed": True\n        }\n        \n        return result',
            }
        ]

        result = edit_file(str(self.test_file), edits)
        self.assertTrue(result["success"])

        # Check for correct indentation in the modified file
        with open(self.test_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify that indentation is preserved in the result
        self.assertIn("    def process_data", content)
        self.assertIn("        if not self.data", content)

    def test_multiple_edits_to_same_region(self):
        """Test handling of multiple edits that target overlapping regions."""
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(
                "def calculate(x, y):\n    # Calculate the sum and product\n    sum_val = x + y\n    product = x * y\n    return sum_val, product\n"
            )

        # Make multiple edits to the same function
        edits = [
            {
                "old_text": "def calculate(x, y):",
                "new_text": "def calculate(x, y, z=0):",
            },
            {"old_text": "    sum_val = x + y", "new_text": "    sum_val = x + y + z"},
            {
                "old_text": "    product = x * y",
                "new_text": "    product = x * y * (1 if z == 0 else z)",
            },
        ]

        result = edit_file(str(self.test_file), edits)
        self.assertTrue(result["success"])

        # Check all edits were applied correctly
        with open(self.test_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("def calculate(x, y, z=0):", content)
        self.assertIn("    sum_val = x + y + z", content)
        self.assertIn("    product = x * y * (1 if z == 0 else z)", content)

    def test_fuzzy_matching_with_similar_patterns(self):
        """Test fuzzy matching when similar patterns exist."""
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(
                '# Configuration settings\nconfig = {\n    "timeout": 30,\n    "retries": 3\n}\n\n# Connection settings\nconnection = {\n    "timeout": 60,\n    "keep_alive": True\n}\n'
            )

        # Try to edit a pattern that appears similarly in multiple places
        edits = [{"old_text": '    "timeout": 30,', "new_text": '    "timeout": 45,'}]

        result = edit_file(str(self.test_file), edits)
        self.assertTrue(result["success"])

        # Verify the correct pattern was modified
        with open(self.test_file, "r", encoding="utf-8") as f:
            content = f.read()

        # First timeout should be changed, second should be unchanged
        self.assertIn('    "timeout": 45,', content)
        self.assertIn('    "timeout": 60,', content)

    def test_adding_new_method_vs_editing(self):
        """Test adding a new method to a class vs editing an existing one."""
        # Create a class with methods
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(
                "class DataProcessor:\n    def __init__(self):\n        self.data = []\n    \n    def process(self):\n        return len(self.data)\n"
            )

        # Add a completely new method
        edits = [
            {
                "old_text": "    def process(self):\n        return len(self.data)",
                "new_text": "    def process(self):\n        return len(self.data)\n    \n    def validate(self):\n        return len(self.data) > 0",
            }
        ]

        result = edit_file(str(self.test_file), edits)
        self.assertTrue(result["success"])

        # Verify new method was added with correct indentation
        with open(self.test_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("    def validate(self):", content)
        self.assertIn("        return len(self.data) > 0", content)

    def test_handling_mixed_indentation(self):
        """Test handling files with mixed indentation styles."""
        # Create a file with mixed tabs and spaces indentation
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(
                "def function_one():\n    return 1\n\ndef function_two():\n\treturn 2\n"
            )

        # Edit both functions
        edits = [
            {"old_text": "    return 1", "new_text": "    return 1 + 10"},
            {"old_text": "\treturn 2", "new_text": "\treturn 2 + 20"},
        ]

        result = edit_file(str(self.test_file), edits)
        self.assertTrue(result["success"])

        # Verify indentation style was preserved for each function
        with open(self.test_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("    return 1 + 10", content)  # spaces preserved
        self.assertIn("\treturn 2 + 20", content)  # tab preserved

    def test_indentation_regression_with_complex_blocks(self):
        """Test indentation regression with nested code blocks."""
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(
                'def process_data(data):\n    results = []\n    for item in data:\n        if item.valid:\n            processed = transform(item)\n            results.append(processed)\n        else:\n            logger.warning(f"Invalid item: {item}")\n    return results\n'
            )

        # Replace a nested block
        edits = [
            {
                "old_text": '        if item.valid:\n            processed = transform(item)\n            results.append(processed)\n        else:\n            logger.warning(f"Invalid item: {item}")',
                "new_text": '        try:\n            if item.valid:\n                processed = transform(item)\n                results.append(processed)\n            else:\n                logger.warning(f"Invalid item: {item}")\n        except Exception as e:\n            logger.error(f"Error processing item: {e}")',
            }
        ]

        result = edit_file(str(self.test_file), edits)
        self.assertTrue(result["success"])

        # Verify nested indentation is preserved
        with open(self.test_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("        try:", content)
        self.assertIn("            if item.valid:", content)
        self.assertIn("                processed = transform(item)", content)

    def test_error_handling_with_partial_match(self):
        """Test error handling when partial matching fails."""
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(
                "def function1():\n    return 1\n\ndef function2():\n    return 2\n"
            )

        # Try to match with very low confidence
        edits = [
            {
                "old_text": "def functions(): # completely different",
                "new_text": "def modified_function():",
            }
        ]

        # Should fail even with partial_match=True but low threshold
        options = {"partial_match": True, "match_threshold": 0.9}
        result = edit_file(str(self.test_file), edits, options=options)

        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("confidence too low", result["error"].lower())

    def test_complex_python_indentation_preservation(self):
        """Test indentation preservation in complex Python structures."""
        # Create a Python file with complex indentation patterns
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(
                "class TestClass:\n    def method1(self):\n        if condition1:\n            if condition2:\n                do_something()\n            else:\n                for item in items:\n                    process(item)\n        return result\n"
            )

        # Replace the nested structure
        edits = [
            {
                "old_text": "            if condition2:\n                do_something()\n            else:\n                for item in items:\n                    process(item)",
                "new_text": "            try:\n                if condition2:\n                    do_something()\n                else:\n                    for item in items:\n                        process(item)\n            except Exception:\n                handle_error()",
            }
        ]

        result = edit_file(str(self.test_file), edits)
        self.assertTrue(result["success"])

        # Verify indentation is properly preserved in complex nesting
        with open(self.test_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("            try:", content)
        self.assertIn("                if condition2:", content)
        self.assertIn("                    do_something()", content)
        self.assertIn("                        process(item)", content)
        self.assertIn("            except Exception:", content)
