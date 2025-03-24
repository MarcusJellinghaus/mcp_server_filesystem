import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.file_tools.edit_file import (
    EditOperation,
    MatchResult,
    apply_edits,
    create_unified_diff,
    edit_file,
    preserve_indentation,
)


class TestEditFileUtils(unittest.TestCase):
    def test_preserve_indentation(self):
        old_text = "    def function():\n        return True"
        new_text = "def new_function():\n    return False"
        preserved = preserve_indentation(old_text, new_text)
        self.assertEqual(preserved, "    def new_function():\n        return False")

    def test_preserve_indentation_empty_lines(self):
        # Test with empty lines to ensure they're preserved correctly
        old_text = "    def function():\n\n        return True"
        new_text = "def new_function():\n\n    return False"
        preserved = preserve_indentation(old_text, new_text)
        self.assertEqual(preserved, "    def new_function():\n\n        return False")

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
        modified, results, changes_made = apply_edits(content, edits)
        self.assertEqual(modified, "def new_function():\n    return True")
        self.assertEqual(results[0]["match_type"], "exact")

    def test_apply_edits_multiple(self):
        content = (
            "def function_one():\n    return 1\n\ndef function_two():\n    return 2"
        )
        edits = [
            EditOperation(old_text="function_one", new_text="function_1"),
            EditOperation(old_text="function_two", new_text="function_2"),
        ]
        modified, results, changes_made = apply_edits(content, edits)
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
        modified, results, changes_made = apply_edits(content, edits)
        self.assertEqual(modified, "    if new_condition:\n        return False")

    def test_apply_edits_no_match(self):
        content = "def function():\n    return True"
        edits = [EditOperation(old_text="nonexistent", new_text="replacement")]
        modified, results, changes_made = apply_edits(content, edits)
        # Check that the match was marked as failed
        self.assertEqual(results[0]["match_type"], "failed")


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

        # Use options parameter with snake_case
        options = {"preserve_indentation": True, "normalize_whitespace": False}
        result = edit_file(str(self.test_file), edits, options=options)

        self.assertTrue(result["success"])
        self.assertIn("diff", result)

        # Check the file was modified
        with open(self.test_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertEqual(content, "def modified_function():\n    return 'test'\n")

    def test_edit_file_not_found(self):
        edits = [{"old_text": "test_function", "new_text": "modified_function"}]

        with self.assertRaises(FileNotFoundError):
            edit_file("nonexistent_file.txt", edits)

    def test_edit_file_failed_match(self):
        edits = [{"old_text": "nonexistent_function", "new_text": "modified_function"}]

        result = edit_file(str(self.test_file), edits)

        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("match_results", result)


class TestEditFileOptimization(unittest.TestCase):
    """Tests for the optimization in edit_file that checks if edits are already applied."""

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

    def test_edit_already_applied(self):
        # First apply an edit
        edits = [{"old_text": "test_function", "new_text": "modified_function"}]
        result1 = edit_file(str(self.test_file), edits)
        self.assertTrue(result1["success"])
        self.assertNotEqual(result1["diff"], "")

        # Try to apply the same edit again
        result2 = edit_file(str(self.test_file), edits)
        self.assertTrue(result2["success"])
        self.assertEqual(result2["diff"], "")
        self.assertEqual(
            result2["message"], "No changes needed - content already in desired state"
        )


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

    def test_edit_large_block(self):
        """Test editing a large block of code."""
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

        # Check that the file was modified
        with open(self.test_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify the edit was applied
        self.assertIn("filtered_data = self.filter_data()", content)
        self.assertIn('"filtered": len(filtered_data),', content)

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

    def test_indentation_changes(self):
        """Test editing code with extreme indentation discrepancies."""
        # Create a Python file with extreme indentation
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(
                'def main():\n    input_file, output_dir, verbose = parse_arguments()\n\n    if verbose:\n        print(f"Verbose mode enabled")\n\n    if processor.load_data():\n        if processor.save_results(results):\n            if verbose and results[\'total_lines\'] > 0:\n                                                                            print(f"Summary:")\n                                                                            print(f"  - Found {len(results[\'word_counts\'])} unique words")\n'
            )

        # Edit the indentation issues
        edits = [
            {
                "old_text": "            if verbose and results['total_lines'] > 0:\n                                                                            print(f\"Summary:\")\n                                                                            print(f\"  - Found {len(results['word_counts'])} unique words\")",
                "new_text": "            if verbose and results['total_lines'] > 0:\n                print(f\"Summary:\")\n                print(f\"  - Found {len(results['word_counts'])} unique words\")",
            }
        ]

        result = edit_file(str(self.test_file), edits)
        self.assertTrue(result["success"])

        with open(self.test_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify the edit fixed the indentation
        self.assertIn("            if verbose and results['total_lines'] > 0:", content)
        self.assertIn('                print(f"Summary:")', content)

    def test_nested_code_blocks_with_empty_diff(self):
        """Test the issue where edit_file reports success but returns empty diffs."""
        # Create a Python file with nested structures
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(
                "def process_data(data):\n    results = []\n    if data.valid:\n        for item in data.items:\n            if item.enabled:\n                # Process the item\n                value = transform(item)\n                results.append(value)\n    return results\n"
            )

        # Try to change a nested block
        edits = [
            {
                "old_text": "            if item.enabled:\n                # Process the item\n                value = transform(item)\n                results.append(value)",
                "new_text": "            if item.enabled and not item.processed:\n                # Process only unprocessed items\n                value = transform(item)\n                item.processed = True\n                results.append(value)",
            }
        ]

        # First run will succeed and make the changes
        result1 = edit_file(str(self.test_file), edits)
        self.assertTrue(result1["success"])
        self.assertNotEqual(
            result1["diff"], "", "First edit should produce a non-empty diff"
        )

        # Get the content after first edit
        with open(self.test_file, "r", encoding="utf-8") as f:
            first_edit_content = f.read()

        # Make the exact same edit again - should be a no-op
        result2 = edit_file(str(self.test_file), edits)

        # The issue: The second edit reports success but shows an empty diff and makes no changes
        # because the content already contains the edit. However, the API doesn't clearly indicate
        # that no changes were needed.
        self.assertTrue(result2["success"])

        # The diff should be empty since no changes were made
        self.assertEqual(
            result2["diff"], "", "Second identical edit should produce an empty diff"
        )

        # Content should be unchanged
        with open(self.test_file, "r", encoding="utf-8") as f:
            second_edit_content = f.read()

        self.assertEqual(
            first_edit_content,
            second_edit_content,
            "Content should be unchanged after second identical edit",
        )

        # Verify success even though no changes were made
        self.assertTrue(
            result2["success"],
            "Edit operations with no changes needed should still report success",
        )

    def test_first_occurrence_replacement(self):
        """Test that only the first occurrence of a pattern is replaced."""
        # Create a file with repeating identical patterns
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(
                'def process(data):\n    print("Processing data...")\n    return data\n\ndef analyze(data):\n    print("Processing data...")\n    return data * 2\n'
            )

        # Try to edit a pattern that appears multiple times
        edits = [
            {
                "old_text": '    print("Processing data...")',
                "new_text": '    print("Data processing started...")',
            }
        ]

        # The edit should only replace the first occurrence
        result = edit_file(str(self.test_file), edits)
        self.assertTrue(result["success"])

        # Verify only the first occurrence was changed
        with open(self.test_file, "r", encoding="utf-8") as f:
            content = f.read()

        # The first occurrence should be changed
        self.assertIn('    print("Data processing started...")', content)

        # Count occurrences of each pattern
        original_pattern_count = content.count('    print("Processing data...")')
        new_pattern_count = content.count('    print("Data processing started...")')

        # There should be exactly one occurrence of each pattern
        self.assertEqual(
            original_pattern_count,
            1,
            "One occurrence of the original pattern should remain",
        )
        self.assertEqual(
            new_pattern_count,
            1,
            "Only one occurrence should be replaced with the new pattern",
        )

    def test_markdown_bullet_point_indentation(self):
        """Test proper handling of markdown bullet point indentation."""
        # Step 1: Create a markdown file with nested bullet points
        markdown_file = self.project_dir / "test_markdown.md"
        with open(markdown_file, "w", encoding="utf-8") as f:
            f.write(
                "# Documentation\n\n## Features\n\n- Top level feature\n- Available options:\n- option1: description\n- option2: description\n- Another top level feature"
            )

        # Step 2: Verify file was created
        with open(markdown_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("# Documentation", content)
        self.assertIn("- Available options:", content)

        # Step 3: Correct bullet point indentation
        edits = [
            {
                "old_text": "- Available options:\n- option1: description\n- option2: description",
                "new_text": "- Available options:\n  - option1: description\n  - option2: description",
            }
        ]
        result = edit_file(str(markdown_file), edits)
        self.assertTrue(result["success"])

        # Step 4: Verify file was modified
        with open(markdown_file, "r", encoding="utf-8") as f:
            updated_content = f.read()
        # Using a more lenient check due to possible indentation differences
        self.assertIn("- Available options:", updated_content)
        self.assertIn("option1: description", updated_content)
        self.assertIn("option2: description", updated_content)

        # Count occurrences to ensure proper nesting
        non_indented_count = updated_content.count("\n- option")
        indented_count = updated_content.count("\n  - option")
        self.assertEqual(
            non_indented_count,
            0,
            "There should be no non-indented option bullet points",
        )
        self.assertEqual(
            indented_count,
            2,
            "There should be exactly two properly indented option bullet points",
        )

        # Step 5: Clean up after test
        os.remove(markdown_file)
        self.assertFalse(os.path.exists(markdown_file))
