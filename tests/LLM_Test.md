## Test instructions for the LLM to verify the functionality

I want you to test the different mcp tools.

- Can you please get a list of all files. How many files do you see? (If it is more than 150, I think there is an issue.)
- Can you please check if any of these files should be ignored according to gitignore?
- Please create / save a file
- Read the file and check whether the content is the same
- Append content to the file
- Read the file again and verify the combined content
- Check with list files whether it shows up there
- Delete the file
- List all files and check whether it disappeared

Please let me know whether you find any issues.

## Edit File Functionality Test Plan

Each test below is self-contained and should be run independently. All commands shown are meant to be executed using the MCP tools interface.

### Test 1: Basic Text Replacement
**Goal**: Verify basic text replacement functionality

**Step 1**: Create a test file
```
save_file(
    file_path="test_basic.txt", 
    content="Hello world\nThis is a test file\nEnd of file"
)
```

**Step 2**: Verify file was created
```
read_file(file_path="test_basic.txt")
```

**Step 3**: Perform a basic text replacement
```
edit_file(
    path="test_basic.txt",
    edits=[{"oldText": "Hello world", "newText": "Greetings earth"}]
)
```

**Step 4**: Verify changes were applied correctly
```
read_file(file_path="test_basic.txt")
# Expected: "Greetings earth" should appear in the file
```

**Step 5**: Clean up after test
```
delete_this_file(file_path="test_basic.txt")
```

### Test 2: Multiple Simultaneous Edits
**Goal**: Verify ability to make multiple edits in a single operation

**Step 1**: Create a test file with multiple distinct sections
```
save_file(
    file_path="test_multiple.txt",
    content="First section\nSecond section\nThird section\nFourth section"
)
```

**Step 2**: Verify file was created
```
read_file(file_path="test_multiple.txt")
```

**Step 3**: Perform multiple edits simultaneously
```
edit_file(
    path="test_multiple.txt",
    edits=[
        {"oldText": "First section", "newText": "Section one"},
        {"oldText": "Third section", "newText": "Section three"}
    ]
)
```

**Step 4**: Verify all changes were applied correctly
```
read_file(file_path="test_multiple.txt")
# Expected: Both "Section one" and "Section three" should appear in the file
```

**Step 5**: Clean up after test
```
delete_this_file(file_path="test_multiple.txt")
```

### Test 3: Whitespace and Indentation Preservation
**Goal**: Verify that code indentation and formatting is preserved

**Step 1**: Create a test file with structured Python code
```
save_file(
    file_path="test_indentation.py",
    content="""def example():
    # This is a comment
    x = 5
    if x > 3:
        print("Greater than 3")
    return x
"""
)
```

**Step 2**: Verify file was created with proper formatting
```
read_file(file_path="test_indentation.py")
```

**Step 3**: Edit the file while preserving indentation
```
edit_file(
    path="test_indentation.py",
    edits=[
        {"oldText": "# This is a comment", "newText": "# This function returns a value"},
        {"oldText": "Greater than 3", "newText": "Value exceeds threshold"}
    ]
)
```

**Step 4**: Verify changes were applied with indentation preserved
```
read_file(file_path="test_indentation.py")
# Expected: Changes made with proper indentation intact
```

**Step 5**: Clean up after test
```
delete_this_file(file_path="test_indentation.py")
```

### Test 4: Partial/Fuzzy Matching
**Goal**: Test the fuzzy matching capabilities

**Step 1**: Create a test file
```
save_file(
    file_path="test_fuzzy.txt",
    content="The quick brown fox jumps over the lazy dog"
)
```

**Step 2**: Verify file was created
```
read_file(file_path="test_fuzzy.txt")
```

**Step 3**: Use edit_file with fuzzy matching enabled
```
edit_file(
    path="test_fuzzy.txt",
    edits=[{"oldText": "quick brown", "newText": "clever orange"}],
    options={"partialMatch": True}
)
```

**Step 4**: Verify changes with fuzzy matching
```
read_file(file_path="test_fuzzy.txt")
# Expected: "The clever orange fox" in the content
```

**Step 5**: Clean up after test
```
delete_this_file(file_path="test_fuzzy.txt")
```

### Test 5: Dry Run Mode
**Goal**: Verify preview functionality without applying changes

**Step 1**: Create a test file
```
save_file(
    file_path="test_dryrun.txt",
    content="This is line one\nThis is line two\nThis is line three"
)
```

**Step 2**: Verify file was created
```
read_file(file_path="test_dryrun.txt")
```

**Step 3**: Run edit in dry run mode
```
edit_file(
    path="test_dryrun.txt",
    edits=[{"oldText": "line two", "newText": "second line"}],
    dry_run=True
)
# Expected: Result should show diff but not apply changes
```

**Step 4**: Verify original file wasn't changed
```
read_file(file_path="test_dryrun.txt")
# Expected: "This is line two" should still be in the file
```

**Step 5**: Run the same edit without dry_run
```
edit_file(
    path="test_dryrun.txt",
    edits=[{"oldText": "line two", "newText": "second line"}]
)
```

**Step 6**: Verify changes were applied this time
```
read_file(file_path="test_dryrun.txt")
# Expected: "This is second line" should be in the file
```

**Step 7**: Clean up after test
```
delete_this_file(file_path="test_dryrun.txt")
```

### Test 6: Failed Match Handling
**Goal**: Verify behavior when requested text is not found

**Step 1**: Create a test file
```
save_file(
    file_path="test_failed_match.txt",
    content="This is some sample content"
)
```

**Step 2**: Verify file was created
```
read_file(file_path="test_failed_match.txt")
```

**Step 3**: Attempt to edit with non-existent text
```
edit_file(
    path="test_failed_match.txt",
    edits=[{"oldText": "text that doesn't exist", "newText": "replacement text"}]
)
# Expected: Should return information about failed match
```

**Step 4**: Verify file content was not changed
```
read_file(file_path="test_failed_match.txt")
# Expected: Original content should be unchanged
```

**Step 5**: Clean up after test
```
delete_this_file(file_path="test_failed_match.txt")
```

### Test 7: Edge Cases
**Goal**: Test behavior with complex patterns

**Step 1**: Create file with special regex characters
```
save_file(
    file_path="test_special_chars.txt",
    content="This has (parentheses) and [brackets] and {braces} and other *special* ^characters$ like + and ."
)
```

**Step 2**: Verify file was created
```
read_file(file_path="test_special_chars.txt")
```

**Step 3**: Edit content with regex special characters
```
edit_file(
    path="test_special_chars.txt",
    edits=[{"oldText": "(parentheses) and [brackets]", "newText": "<angle brackets> and |pipes|"}]
)
```

**Step 4**: Verify changes were applied correctly
```
read_file(file_path="test_special_chars.txt")
# Expected: "This has <angle brackets> and |pipes| and {braces}"
```

**Step 5**: Clean up after test
```
delete_this_file(file_path="test_special_chars.txt")
```

### Test 8: Multi-line Content Editing
**Goal**: Verify editing across multiple lines

**Step 1**: Create a file with multi-line structures
```
save_file(
    file_path="test_multiline.txt",
    content="""This is the first line.
This is the second line.
This is the third line.
This is the fourth line.
This is the fifth line."""
)
```

**Step 2**: Verify file was created
```
read_file(file_path="test_multiline.txt")
```

**Step 3**: Edit content spanning multiple lines
```
edit_file(
    path="test_multiline.txt",
    edits=[{
        "oldText": "This is the second line.\nThis is the third line.\nThis is the fourth line.",
        "newText": "These are\nthe middle\nlines of the text."
    }]
)
```

**Step 4**: Verify multi-line edit was applied correctly
```
read_file(file_path="test_multiline.txt")
# Expected: Multi-line replacement should be visible
```

**Step 5**: Clean up after test
```
delete_this_file(file_path="test_multiline.txt")
```

### Test 9: Markdown Bullet Point Indentation
**Goal**: Verify proper handling of markdown bullet point indentation

**Step 1**: Create a markdown file with nested bullet points
```
save_file(
file_path="test_markdown.md",
content="# Documentation

## Features

- Top level feature
- Available options:
- option1: description
- option2: description
- Another top level feature"
)
```

**Step 2**: Verify file was created
```
read_file(file_path="test_markdown.md")
```

**Step 3**: Correct bullet point indentation
```
edit_file(
path="test_markdown.md",
edits=[{
"oldText": "- Available options:\n- option1: description\n- option2: description",
"newText": "- Available options:\n  - option1: description\n  - option2: description"
}],
options={
"preserveIndentation": true
}
)
```

**Step 4**: Verify indentation was applied correctly
```
read_file(file_path="test_markdown.md")
# Expected: Nested bullet points should be properly indented with 2 spaces
```

**Step 5**: Clean up after test
```
delete_this_file(file_path="test_markdown.md")
```
