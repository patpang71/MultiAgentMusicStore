import re


def normalize_phone(phone: str | None) -> str | None:
    """Strip all non-digit characters from a phone number.

    A leading '+' is preserved for international numbers; all other
    non-digit characters (spaces, dashes, dots, parentheses, etc.) are removed.

    Args:
        phone: Raw phone string, e.g. "+1 (800) 555-0199" or "800.555.0199".

    Returns:
        Normalised string such as "+18005550199" or "8005550199",
        or None if the input is None or contains no digits at all.
    """
    if phone is None:
        return None

    stripped = phone.strip()
    international = stripped.startswith("+")
    digits = re.sub(r"\D", "", stripped)

    if not digits:
        return None

    return ("+" if international else "") + digits
