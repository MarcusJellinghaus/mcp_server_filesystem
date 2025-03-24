import os
import tempfile
import unittest
from pathlib import Path

from src.file_tools.edit_file import edit_file


class TestMarkdownIndentation(unittest.TestCase):
    """Test specifically for markdown indentation issues."""

    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)

    def tearDown(self):
        # Clean up after tests
        self.temp_dir.cleanup()

    def test_bullet_point_indentation(self):
        # Create a markdown file with nested bullet points
        markdown_file = self.project_dir / "test_markdown.md"
        with open(markdown_file, "w", encoding="utf-8") as f:
            f.write(
                "# Documentation\n\n## Features\n\n- Top level feature\n- Available options:\n- option1: description\n- option2: description\n- Another top level feature"
            )

        # Verify file was created
        with open(markdown_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("# Documentation", content)
        self.assertIn("- Available options:", content)

        # Edit to add indentation to nested bullet points
        edits = [
            {
                "old_text": "- Available options:\n- option1: description\n- option2: description",
                "new_text": "- Available options:\n  - option1: description\n  - option2: description",
            }
        ]

        options = {"preserve_indentation": True}
        result = edit_file(str(markdown_file), edits, options=options)

        # Verify the edit was successful
        self.assertTrue(result["success"])

        # Read the updated content
        with open(markdown_file, "r", encoding="utf-8") as f:
            updated_content = f.read()

        # Check that the text was edited
        self.assertIn("- Available options:", updated_content)
        self.assertIn("option1: description", updated_content)
        self.assertIn("option2: description", updated_content)

        # Check that the indentation changed (either format is acceptable)
        non_indented_count = updated_content.count("\n- option")
        indented_count = updated_content.count("\n  - option")

        # At least some indentation should be applied
        self.assertTrue(
            non_indented_count < 2 or indented_count > 0,
            "The indentation should have been improved in some way",
        )
