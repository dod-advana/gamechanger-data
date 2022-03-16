import sys

def announce(text: str):
    print("#### PIPELINE INFO #### " + text, file=sys.stderr)