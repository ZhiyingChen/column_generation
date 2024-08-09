from typing import Dict


class Supply:
    def __init__(self, date: str, pattern_id: int, size: float, supply_amount: float):
        self.date = date
        self.pattern_id = pattern_id
        self.size = size
        self.supply_amount = supply_amount
        self.demand_amount_dict: Dict[str, float] = dict()

    def __repr__(self):
        return 'Supply(date={}, pattern_id={}, size={}, supply_amount={}, left_amount={})'.format(
            self.date, self.pattern_id, self.size, self.supply_amount, self.amount)

    @property
    def amount(self):
        return self.supply_amount - sum(self.demand_amount_dict.values())
