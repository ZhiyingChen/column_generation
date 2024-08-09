from typing import Dict
from .. import do


def init_pattern(demand_dict: Dict[float, do.Demand], og_size: float):
    pattern_dict = {}
    pattern_id = 0
    for size, demand in demand_dict.items():
        pattern = do.Pattern(
            pattern_id=pattern_id,
            original_size=og_size,
            mode={size: 1}
        )

        pattern_dict.update({pattern_id: pattern})
        pattern_id += 1
    return pattern_dict
