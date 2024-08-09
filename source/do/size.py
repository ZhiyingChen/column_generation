from typing import Dict
from .demand import Demand


class Size:
    def __init__(self, size: float):
        self.size = size
        self.demand_dict: Dict[str, Demand] = dict()

    def __repr__(self):
        return "Size({})".format(self.size)

    @property
    def demand_amount(self):
        return sum(demand.amount for demand in self.demand_dict.values())
