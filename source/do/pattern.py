from typing import Dict, List


class Pattern:
    def __init__(self, pattern_id: int, original_size: float, mode=None):
        if mode is None:
            mode = dict()
        self.original_size = original_size
        self.pattern_id = pattern_id
        self.mode: Dict[float, int] = mode
        self.used_times = None
        self.added_cuts: List[float] = list()

    def __repr__(self):
        return 'Pattern(id={})'.format(self.pattern_id)

    @property
    def useful_size(self):
        return sum(k * v for k, v in self.mode.items())

    @property
    def remain(self):
        return self.original_size - self.useful_size
