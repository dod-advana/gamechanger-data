"""
Alex Martelli's Borg non-pattern - not a singleton

See: http://www.aleax.it/5ep.html

"""


class Borg:
    _shared_state = dict()

    def __init__(self):
        self.__dict__ = self._shared_state

    def __hash__(self):
        return 1

    def __eq__(self, other):
        try:
            return self.__dict__ is other.__dict__
        except Exception:
            return 0
