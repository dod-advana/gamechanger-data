from re import VERBOSE, compile, sub


# Ex: "Do D"
DOD_PATTERN = compile(
    rf"""
        \b      # Word boundary
        Do      # "Do"
        \s      # Whitespace
        D       # "D"
        \b      # Word boundary
    """,
    flags=VERBOSE,
)

# Ex: "DoD D"
DODD_PATTERN = compile(
    rf"""
        \b      # Word boundary
        DoD     # "DoD"
        \s      # Whitespace
        D       # "D"
        \b      # Word boundary
    """,
    flags=VERBOSE,
)

# Ex: "DoD I"
DODI_PATTERN = compile(
    rf"""
        \b      # Word boundary
        DoD     # "DoD"
        \s      # Whitespace
        I       # "I"
        \b      # Word boundary
    """,
    flags=VERBOSE,
)

# Ex: "DoD M"
DODM_PATTERN = compile(
    rf"""
        \b      # Word boundary
        DoD     # "DoD"
        \s      # Whitespace
        M       # "M"
        \b      # Word boundary
    """,
    flags=VERBOSE,
)


def normalize_dod(text):
    """Normalize references to DoD organizations.

    Example: "DoD M" -> "DoDM"

    Args:
        text (str)

    Returns:
        str
    """
    text = sub(DOD_PATTERN, "DoD", text)
    text = sub(DODD_PATTERN, "DoDD", text)
    text = sub(DODI_PATTERN, "DoDI", text)
    text = sub(DODM_PATTERN, "DoDM", text)

    return text

