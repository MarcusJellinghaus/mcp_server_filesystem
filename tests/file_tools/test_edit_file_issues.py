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


class TestEditFileIndentationIssues(unittest.TestCase):
    """Tests specifically designed to highlight indentation handling challenges."""

    def test_indentation_approach(self):
        """Test the indentation handling approach."""
        # Create a simple test case
        old = "    def test():\n        if True:\n            return 1\n        else:\n            return 0"
        new = "def improved_test():\n    if condition:\n        return 2\n    else:\n        return -1"

        # Apply our indentation preservation
        result = preserve_indentation(old, new)

        # The result should preserve the original indentation pattern
        expected = "    def improved_test():\n        if condition:\n            return 2\n        else:\n            return -1"

        self.assertEqual(result, expected)

    def setUp(self):
        # Create a temporary directory and file for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)
        self.test_file = self.project_dir / "test_file.py"

    def tearDown(self):
        # Clean up after tests
        self.temp_dir.cleanup()

    def test_extreme_indentation_handling(self):
        """Test handling code with extreme indentation discrepancies."""
        # Create a Python file with complex and inconsistent indentation
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(
                'def main():\n    input_file, output_dir, verbose = parse_arguments()\n\n    if verbose:\n        print(f"Verbose mode enabled")\n        print(f"Input file: {input_file}")\n\n    processor = DataProcessor(input_file, output_dir)\n\n    if processor.load_data():\n        print(f"Successfully loaded {len(processor.data)} lines")\n\n        results = processor.process_data()\n\n        if processor.save_results(results):\n            print(f"Results saved to {output_dir}")\n\n            if verbose and results[\'total_lines\'] > 0:\n                                                                            print(f"Summary:")\n                                                                            print(f"  - Processed {results[\'total_lines\']} lines")\n                                                                            print(f"  - Found {len(results[\'word_counts\'])} unique words")\n        else:\n            print("Failed to save results")\n    else:\n        print("Failed to load data")\n'
            )

        # Attempt to fix the indentation issue
        edits = [
            {
                "old_text": "            if verbose and results['total_lines'] > 0:\n                                                                            print(f\"Summary:\")\n                                                                            print(f\"  - Processed {results['total_lines']} lines\")\n                                                                            print(f\"  - Found {len(results['word_counts'])} unique words\")",
                "new_text": "            if verbose and results['total_lines'] > 0:\n                print(f\"Summary:\")\n                print(f\"  - Processed {results['total_lines']} lines\")\n                print(f\"  - Found {len(results['word_counts'])} unique words\")",
            }
        ]

        result = edit_file(str(self.test_file), edits)
        self.assertTrue(result["success"])

        with open(self.test_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify the edit fixed the indentation
        self.assertIn("            if verbose and results['total_lines'] > 0:", content)
        self.assertIn('                print(f"Summary:")', content)

    def test_optimization_edit_already_applied(self):
        """Test the optimization in edit_file that checks if edits are already applied."""
        # Create a file
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write("def test_function():\n    return 'test'\n")

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

    def test_mixed_tab_space_indentation(self):
        """Test handling of mixed tab and space indentation."""
        # Create test with tabs and spaces
        old = "def outer():\n\tdef inner():\n\t    # Mixed tabs and spaces\n\t    return True"
        new = "def modified():\n    def inner_func():\n        # All spaces now\n        return False"

        # Apply our indentation preservation
        result = preserve_indentation(old, new)

        # Should maintain the original indentation style
        expected = "def modified():\n\tdef inner_func():\n\t    # All spaces now\n\t    return False"

        self.assertEqual(result, expected)

    def test_snake_case_options(self):
        """Test that only snake_case options are supported."""
        # Create a test file
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write("def test_function():\n    return 'test'\n")

        # Define edit with snake_case options
        edits = [{"old_text": "test_function", "new_text": "modified_function"}]
        options = {"preserve_indentation": True, "normalize_whitespace": False}

        # Apply the edit with options
        result = edit_file(str(self.test_file), edits, options=options)

        # Verify success
        self.assertTrue(result["success"])

        # Check the file was modified as expected
        with open(self.test_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertEqual(content, "def modified_function():\n    return 'test'\n")
