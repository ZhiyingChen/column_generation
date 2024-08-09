import pandas as pd
from typing import Dict, Tuple, List, Union
from itertools import chain
import logging
from collections import defaultdict
from .input_data import InputData
from . import do
from .utils import timing
from .utils import header
from .utils import filename


class ResultStorage:
    def __init__(self, input_data: InputData):
        self.input_data = input_data
        self.solution_dict: Dict[str, do.Solution] = dict()
        self.supply_dict: Dict[Tuple[str, int, float], do.Supply] = dict()

    # region dump
    def dict_to_list(self, d: dict):
        result = sorted(list(chain.from_iterable([[k] * int(v) for k, v in d.items()])))
        while len(result) < self.input_data.max_cut + 1:
            result.append('')
        return result

    def dump(self):
        self.output_sol()
        self.output_supply()
        self.output_demand()
        self.output_fulfillment()
        self.output_kpi()

    def output_sol(self):
        osh = header.OutSolutionHeader
        mode_col = ['切割方案_第{}段'.format(i)
                    for i in range(1, self.input_data.max_cut + 2)]
        col = [
                  osh.date
              ] + mode_col + [osh.used_times, osh.original_size, osh.remain, osh.waste, osh.pattern_id]
        if not self.input_data.consider_waste:
            col.remove(osh.waste)
        if self.input_data.whether_process_remain:
            col.append(osh.added_cuts)
        record_lt = []

        for date, solutions in self.solution_dict.items():
            for pattern_id, pattern in solutions.pattern_used_dict.items():
                remain_qty = round(pattern.remain)
                remain = remain_qty
                waste = ''
                if self.input_data.consider_waste:
                    remain = remain_qty if remain_qty >= self.input_data.remain_low_limit else ''
                    waste = remain_qty if remain_qty < self.input_data.remain_low_limit else ''
                record = {
                    osh.date: date,
                    osh.used_times: round(pattern.used_times),
                    osh.original_size: self.input_data.original_size,
                    osh.remain: remain,
                    osh.waste: waste,
                    osh.pattern_id: pattern_id,
                    osh.added_cuts: ';'.join([str(cut) for cut in pattern.added_cuts])
                }
                mode_value_list = self.dict_to_list(pattern.mode)
                record.update(
                    dict(zip(mode_col, mode_value_list))
                )
                record_lt.append(record)
        sol_df = pd.DataFrame(record_lt, columns=col, dtype=object)
        sol_df.to_csv('{}{}'.format(self.input_data.output_folder, filename.OUT_SOLUTION_FILE), index=False)

    def output_supply(self):
        osh = header.OutSupplyHeader
        col = [
            osh.date,
            osh.pattern_id,
            osh.size,
            osh.supply_amount,
            osh.unfulfilled_amount
        ]
        record_lt = []
        for (date, pattern, size), supply in self.supply_dict.items():
            record = {
                osh.date: date,
                osh.pattern_id: pattern,
                osh.size: size,
                osh.supply_amount: round(supply.supply_amount),
                osh.unfulfilled_amount: round(supply.amount)
            }
            record_lt.append(record)
        supply_df = pd.DataFrame(record_lt, columns=col, dtype=object)
        supply_df.to_csv('{}{}'.format(self.input_data.output_folder, filename.OUT_SUPPLY_FILE), index=False)

    def output_demand(self):
        odh = header.OutDemandHeader
        col = [
            odh.date,
            odh.size,
            odh.demand_amount,
            odh.unfulfilled_amount
        ]
        record_lt = []
        for date, demand_dict in self.input_data.demand_dict.items():
            for size, demand in demand_dict.items():
                record = {
                    odh.date: date,
                    odh.size: size,
                    odh.demand_amount: demand.original_amount,
                    odh.unfulfilled_amount: round(demand.amount)
                }
                record_lt.append(record)

        demand_df = pd.DataFrame(record_lt, columns=col, dtype=object)
        demand_df.to_csv('{}{}'.format(self.input_data.output_folder, filename.OUT_DEMAND_FILE), index=False)

    def output_fulfillment(self):
        ofh = header.OutFulfillmentHeader
        col = [
            ofh.size,
            ofh.supply_date,
            ofh.pattern_id,
            ofh.demand_date,
            ofh.supply_amount
        ]
        record_lt = []
        for demand_date, dmd_dict in self.input_data.demand_dict.items():
            for size, dmd in dmd_dict.items():
                for (supply_date, pattern_id), qty in dmd.supply_amount_dict.items():
                    record = {
                        ofh.size: size,
                        ofh.supply_date: supply_date,
                        ofh.pattern_id: pattern_id,
                        ofh.demand_date: demand_date,
                        ofh.supply_amount: round(qty)
                    }
                    record_lt.append(record)
        fulfillment_df = pd.DataFrame(record_lt, columns=col, dtype=object)
        fulfillment_df.to_csv('{}{}'.format(self.input_data.output_folder, filename.OUT_FULFILLMENT_FILE), index=False)

    def output_kpi(self):
        okh = header.OutKpiHeader
        col = [
            okh.date,
            okh.original_used_times,
            okh.pattern_num,
            okh.running_time
        ]

        record_lt = []
        for date, solution in self.solution_dict.items():
            record = {
                okh.date: date,
                okh.original_used_times: round(solution.used_original_roll_num),
                okh.pattern_num: len(solution.pattern_used_dict),
                okh.running_time: round(solution.running_time, 2)
            }
            record_lt.append(record)
        kpi_df = pd.DataFrame(record_lt, columns=col, dtype=object)
        kpi_df.to_csv('{}{}'.format(self.input_data.output_folder, filename.OUT_KPI_FILE), index=False)

    # endregion

    # region fulfillment
    def generate_supply_by_date(self, date: str):
        solution = self.solution_dict[date]
        supply_dict = dict()
        for pattern_id, pattern in solution.pattern_used_dict.items():
            for size, qty in pattern.mode.items():
                if qty < 1e-2:
                    continue
                supply = do.Supply(
                    date=date,
                    pattern_id=pattern_id,
                    size=size,
                    supply_amount=qty * pattern.used_times
                )
                supply_dict[(date, pattern_id, size)] = supply
        self.supply_dict.update(supply_dict)

    @timing.record_time_decorator(task_name="生成供应关系时长")
    def generate_fulfillment_relationship_by_date(self, date: str):
        """
        满足当前日期的需求
        :param date: 当前日期
        :return:
        """
        self.generate_supply_by_date(date=date)
        supply_queue_by_size, demand_queue_by_size = self.generate_supply_and_demand_queue_by_size()

        for size, demand_queue in demand_queue_by_size.items():
            supply_queue = supply_queue_by_size.get(size, [])
            if len(supply_queue) == 0:
                continue
            for (demand_date, _) in demand_queue:
                if (not self.input_data.whether_process_remain) and demand_date != date:
                    continue
                demand = self.input_data.demand_dict[demand_date][size]
                while demand.amount > 1e-4:
                    if len(supply_queue) == 0:
                        break
                    (supply_date, pattern_id, _) = supply_queue[0]
                    if pd.to_datetime(supply_date) > pd.to_datetime(demand_date):
                        break
                    supply = self.supply_dict[(supply_date, pattern_id, size)]

                    fill_amount = min(demand.amount, supply.amount)

                    supply.demand_amount_dict[demand_date] = supply.demand_amount_dict.get(demand_date, 0) + fill_amount
                    demand.supply_amount_dict[(supply_date, pattern_id)] = demand.supply_amount_dict.get(
                        (supply_date, pattern_id), 0) + fill_amount

                    if supply.amount < 1e-2:
                        supply_queue.pop(0)

                if demand_date == date and demand.amount > 1e-4:
                    logging.error("Demand of size: {} on date {} is not satisfied in time: {}".format(
                        size, date, demand.amount
                    ))

    def generate_supply_and_demand_queue_by_size(
            self
    ) -> Tuple[
        Dict[float, List[do.Supply]]
        , Dict[float, List[do.Demand]]
    ]:
        """
        提前遍历好每个幅宽的 供应和需求， 按日期排序
        :return: {幅宽：供应列表}， {幅宽：需求列表}
        """
        supply_queue_by_size = defaultdict(list)
        demand_queue_by_size = defaultdict(list)

        for (supply_date, pattern_id, size), supply in self.supply_dict.items():
            if supply.amount < 1e-2:
                continue
            supply_queue_by_size[size].append((supply_date, pattern_id, size))

        supply_queue_by_size = {
            size: sorted(supply_queue, key=lambda x: pd.to_datetime(x[0]))
            for size, supply_queue in supply_queue_by_size.items()
        }

        for date, dmd_dict in self.input_data.demand_dict.items():
            for size, demand in dmd_dict.items():
                if demand.amount < 1e-2:
                    continue
                demand_queue_by_size[size].append((date, size))
        demand_queue_by_size = {
            size: sorted(demand_queue, key=lambda x: pd.to_datetime(x[0]))
            for size, demand_queue in demand_queue_by_size.items()
        }
        return supply_queue_by_size, demand_queue_by_size
    # endregion

    # region post_process
    def generate_size_demand_dict(
            self
            , date: str
    ) -> Dict[float, do.Size]:
        """
        提前生成字典，记录每个幅宽剩余的需求，按需求量进行排序
        :param date: 日期
        :return: 输入日期的每个幅宽对应的剩余需求
        """
        size_dict = dict()
        for demand_date, demand_dict in self.input_data.demand_dict.items():
            if demand_date <= date:
                continue

            for size, demand in demand_dict.items():
                if size not in size_dict:
                    size_do = do.Size(
                        size=size
                    )
                else:
                    size_do = size_dict[size]
                size_do.demand_dict[demand_date] = demand
                size_dict.update({size: size_do})
        size_dict = dict(sorted(size_dict.items(), key=lambda x: x[1].demand_amount, reverse=True))
        return size_dict

    @timing.record_time_decorator(task_name="后处理时长")
    def post_process(self, date: str):
        self.post_process_remain(date=date)
        self.sort_by_min_knife_change(date=date)

    @timing.record_time_decorator(task_name="后处理remain时长")
    def post_process_remain(self, date: str):
        """
        对当前日期的结果进行后处理，如果pattern有剩余，则从需求中取选择最高销量的
        :param date: 当前日期
        :return:
        """
        size_dict = self.generate_size_demand_dict(date)
        solution = self.solution_dict[date]
        for pattern_id in solution.pattern_used_dict:
            pattern = solution.pattern_used_dict[pattern_id]
            current_cut = sum(v for k, v in pattern.mode.items())
            # 如果该pattern还有remain，则从销量由大到小的size去fill
            for size in size_dict:
                size_do = size_dict[size]
                total_demand_amount = size_do.demand_amount
                while size <= pattern.remain and total_demand_amount >= 1:
                    if current_cut > 4 or (current_cut == 4 and size != pattern.remain):
                        break
                    # 继续从remain中cut出size大小的纸卷，提供 used_times 个
                    pattern_provide_amount = pattern.used_times

                    # update supply
                    if (date, pattern_id, size) not in self.supply_dict:
                        supply = do.Supply(
                            date=date,
                            pattern_id=pattern_id,
                            size=size,
                            supply_amount=pattern_provide_amount
                        )
                    else:
                        supply = self.supply_dict[(date, pattern_id, size)]
                        supply.supply_amount += pattern_provide_amount

                    # update size_do and demand
                    for demand_date in size_do.demand_dict:
                        if pattern_provide_amount == 0:
                            break
                        demand = size_do.demand_dict[demand_date]
                        if demand.amount < 1e-4:
                            continue
                        fill_amount = min(demand.amount, pattern_provide_amount)
                        pattern_provide_amount -= fill_amount

                        logging.info("Provide size: {} on demand date: {} with amount: {} on date {} in advance".format(
                            size, demand_date, fill_amount, date
                        ))
                        # update demand
                        demand.supply_amount_dict[(date, pattern_id)] = demand.supply_amount_dict.get(
                            (date, pattern_id), 0) + fill_amount
                        # update supply
                        supply.demand_amount_dict[demand_date] = supply.demand_amount_dict.get(demand_date,
                                                                                               0) + fill_amount
                    # update supply dict
                    self.supply_dict.update({(date, pattern_id, size): supply})
                    # update pattern and pattern.remain will update syn-chronically
                    pattern.mode[size] = pattern.mode.get(size, 0) + 1
                    pattern.added_cuts.append(size)
                    logging.info("Add one cut in pattern: {} with size {} on date {}".format(
                        pattern_id, size, date))
                    current_cut = sum(v for k, v in pattern.mode.items())
                    total_demand_amount = size_do.demand_amount

    @timing.record_time_decorator(task_name="最小化换刀时长")
    def sort_by_min_knife_change(self, date: str):
        solution = self.solution_dict[date]
        min_change, corresponding_path = solution.get_min_knife_change()
        solution.resort_pattern(update_key=corresponding_path)
        solution.knife_change_times = min_change

    # endregion

