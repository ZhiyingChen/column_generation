from typing import Dict, Tuple


class Demand:
    def __init__(self, date: str, size: float, amount: int):
        self.date = date
        self.size = size
        self.original_amount = amount
        self.supply_amount_dict: Dict[Tuple[str, str], int] = dict()

    def __repr__(self):
        return 'Demand(size={}, amount={})'.format(self.size, self.amount)

    @property
    def amount(self):
        return self.original_amount - sum(self.supply_amount_dict.values())