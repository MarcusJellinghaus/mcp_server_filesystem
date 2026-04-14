# Python Guidelines

- **f-strings are preferred.**
- **Use type hint syntax appropriate for the project's minimum supported Python version.**
- **Avoid conditional imports.** If a dependency is missing, stop and escalate to the user rather than working around it.
- **Tests for optional resources should skip, not fake.** When a test depends on something that may not be available (an optional SDK, a database, an API, a CLI tool), use `pytest.importorskip` or `pytest.mark.skipif` to skip transparently. Don't mock the resource just to make the test run everywhere — skipping is honest and avoids false confidence.
