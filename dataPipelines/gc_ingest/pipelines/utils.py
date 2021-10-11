import sys


def announce(text: str, *rest):
    print(f"#### PIPELINE INFO #### {text}" + " ".join(rest), file=sys.stderr)
