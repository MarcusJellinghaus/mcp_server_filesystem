"""Redacted token fingerprint formatter for safe logging."""


def format_token_fingerprint(token: str | None) -> str:
    """Return ``'<first4>...<last4>'`` for tokens longer than 8 characters.

    For short tokens (1..=8 characters) returns ``'****'`` so no characters of
    the secret leak. For empty or ``None`` input returns ``''`` (the consumer
    omits the field when empty).
    """
    if not token:
        return ""
    if len(token) > 8:
        return f"{token[:4]}...{token[-4:]}"
    return "****"
