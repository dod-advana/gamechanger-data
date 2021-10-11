import sys


def announce(text: str, *rest):
    print(f"#### PIPELINE INFO #### {text}" +
          " ".join([str(i) for i in rest]), file=sys.stderr)
