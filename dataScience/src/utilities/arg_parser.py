import argparse
import sys


class LocalParser(argparse.ArgumentParser):
    """
    https://stackoverflow.com/questions/4042452
    """

    def error(self, message):
        sys.stderr.write("error: %s\n" % message)
        self.print_help()
        sys.exit(2)
