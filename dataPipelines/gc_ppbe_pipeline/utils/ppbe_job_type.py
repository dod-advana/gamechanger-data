from enum import Enum


class PPBEJobType(Enum):
    PROCUREMENT = 'procurement'
    RDTE = 'rdte'

    def __str__(self):
        return str(self.value)
