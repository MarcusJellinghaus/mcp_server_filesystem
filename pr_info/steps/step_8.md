# Step 8: Update Documentation

## Objective
Update README.md and other documentation to explain reference project functionality.

## WHERE
- **File**: `README.md` - main documentation
- **Sections**: Features, Installation, Running the Server, Available Tools, CLI arguments
- **Examples**: Usage examples and configuration samples

## WHAT
```markdown
# Add to Features section
- `get_reference_projects`: Discover available reference projects
- `list_reference_directory`: List files in reference projects  
- `read_reference_file`: Read files from reference projects

# Add to CLI arguments section
- `--reference-project`: Add reference project in format name=/path/to/dir (repeatable)

# Add new section: Reference Projects
Detailed explanation of reference project functionality, use cases, and examples
```

## HOW
- Add reference project tools to the existing "Available Tools" table
- Update CLI arguments section with new `--reference-project` option
- Create new "Reference Projects" section with overview and examples
- Update feature list in overview section
- Add configuration examples for different use cases

## ALGORITHM
```
1. Update Features section: add 3 new tools
2. Update CLI arguments: add --reference-project description
3. Add Reference Projects section:
   - Overview and use cases
   - Configuration examples
   - Security notes (read-only)
4. Update Available Tools table with new tools
5. Add examples to Running the Server section
```

## DATA
**Sections Updated**: Features, CLI Args, Available Tools, new Reference Projects section  
**Examples**: CLI usage with reference projects, practical use cases  
**Format**: Maintain existing README.md style and structure  
**Completeness**: Cover all new functionality with clear explanations

## LLM Prompt
```
Based on the summary in pr_info/steps/summary.md and completing Steps 1-7, implement Step 8: Update documentation for reference projects.

Update README.md to document the new reference project functionality. Add the new tools to the Available Tools table, document the --reference-project CLI argument, and create a new "Reference Projects" section explaining the feature.

Follow the existing documentation style and include practical examples. Explain the read-only nature and use cases for reference projects.
```
