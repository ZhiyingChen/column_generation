from typing import List, Dict
import logging
from itertools import chain
from .. import do


class Solution:
    def __init__(self, date: str):
        self.date = date
        self.pattern_used_dict = dict()
        self.running_time: float = 0
        self.knife_change_times: float = 0

    @property
    def used_original_roll_num(self):
        return sum(
            pattern.used_times for pattern_id, pattern in self.pattern_used_dict.items())

    def generate_pattern_used_dict(self, demand_dict: Dict[float, do.Demand],
                                   original_size: float,
                                   solution: list):
        pattern_used_dict = dict()
        idx = 0
        for (pattern, used_num) in solution:
            mode = dict(zip(demand_dict.keys(), pattern))
            new_pattern = do.Pattern(
                pattern_id=idx,
                original_size=original_size,
                mode=mode,
            )
            new_pattern.used_times = used_num
            pattern_used_dict.update({idx: new_pattern})
            idx += 1
        self.pattern_used_dict = pattern_used_dict
        logging.info("generated solution for date: {}".format(self.date))

    @staticmethod
    def get_cut_point(original: list, counts: list):
        repeated = [[num] * int(count) for num, count in zip(original, counts)]
        result = list(chain(*repeated))
        return result

    def get_pattern_change_matrix(self):
        cut_point = [
            self.get_cut_point(original=pattern.mode.keys(), counts=pattern.mode.values())
            for pattern_id, pattern in self.pattern_used_dict.items()
        ]
        # initial knife change from None pattern
        exchange_sets = []
        knife_change_times = []
        for i in range(len(cut_point)):
            for j in range(i + 1, len(cut_point)):
                uni_cuts = set(cut_point[i]) & set(cut_point[j])
                number_change = len(cut_point[i]) + len(cut_point[j]) - 2 * len(uni_cuts)
                exchange_sets.append({i, j})
                knife_change_times.append(number_change)
        return exchange_sets, knife_change_times

    def get_min_knife_change(self):
        exchange_sets, knife_change_times = self.get_pattern_change_matrix()

        min_change_by_pattern_id = dict()
        pattern_change_path_by_pattern_id = dict()
        for i in self.pattern_used_dict:
            # i 表示从 当前第 i 个pattern作为init pattern
            remain_patterns = [k for k in self.pattern_used_dict if k != i]
            current_pattern = i
            pattern_change_path = [i]
            current_knife_change = 0
            while remain_patterns:
                available_change = [{current_pattern, pattern} for pattern in remain_patterns]
                exchange_dict = {
                    tuple(pattern_set): times
                    for pattern_set, times in zip(exchange_sets, knife_change_times)
                    if pattern_set in available_change
                }
                min_value = min(exchange_dict.values())
                current_knife_change += min_value
                min_exchange_list = [key for key, value in exchange_dict.items() if value == min_value]
                next_current_pattern_list = [value for pair in min_exchange_list for value in pair if
                                             value != current_pattern]
                current_pattern = next_current_pattern_list[0]
                pattern_change_path.append(current_pattern)
                remain_patterns.remove(current_pattern)
            min_change_by_pattern_id[i] = current_knife_change
            pattern_change_path_by_pattern_id[i] = pattern_change_path

        min_key = min(min_change_by_pattern_id, key=min_change_by_pattern_id.get)
        min_change = min_change_by_pattern_id[min_key]
        corresponding_path = pattern_change_path_by_pattern_id[min_key]
        logging.info("min change is {}".format(min_change))
        return min_change, corresponding_path

    def resort_pattern(self, update_key: List[int]):
        update_pattern_used_dict = {k: self.pattern_used_dict[k] for k in update_key}
        update_pattern_used_dict = dict(
            zip(
                range(len(update_pattern_used_dict)),
                update_pattern_used_dict.values()
            )
        )
        self.pattern_used_dict = update_pattern_used_dict
        logging.info("resorted pattern with corresponding_path.")
