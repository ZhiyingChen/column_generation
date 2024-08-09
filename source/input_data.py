import pandas as pd
import logging
from typing import Dict
from . import do
from .utils import filename
from .utils import header
from .utils import field


class InputData:
    def __init__(
            self
            , input_folder: str = "./"
            , output_folder: str = "output/"
    ):
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.original_size = None
        self.max_cut = None
        self.min_pattern_used_num = None
        self.consider_waste = False
        self.remain_low_limit = None
        self.waste_up_limit = None
        self.waste_low_limit = 0.0
        self.whether_process_remain = None
        self.demand_dict: Dict[str: do.Demand] = dict()

    # region read data
    def read_data(self):
        self.load_global_parameter()
        self.load_demand_dict()
        logging.info("loaded data")

    def load_global_parameter(self):
        ph = header.ParamHeader
        pn = field.ParamName

        df_global_param = pd.read_csv('{}{}'.format(self.input_folder, filename.PARAMETER_FILE))
        global_param_dict = dict(zip(df_global_param[ph.parameter_name], df_global_param[ph.parameter_value]))
        self.original_size = float(global_param_dict[pn.original_size])
        self.max_cut = int(global_param_dict[pn.max_cut])
        self.min_pattern_used_num = global_param_dict.get(pn.min_pattern_used_num, None)
        if self.min_pattern_used_num is not None:
            self.min_pattern_used_num = int(self.min_pattern_used_num)
        self.whether_process_remain = field.BoolCN.true in global_param_dict.get(pn.whether_process_remain,
                                                                                 field.BoolCN.false)
        self.consider_waste = field.BoolCN.true in global_param_dict.get(pn.consider_waste, field.BoolCN.false)
        if self.consider_waste:
            self.remain_low_limit = float(global_param_dict[pn.remain_low_limit])
            self.waste_up_limit = float(global_param_dict[pn.waste_up_limit])
            self.waste_low_limit = min(0.0,
                                       float(
                                           global_param_dict.get(pn.waste_low_limit, 0.0)
                                       )
                                       )
        logging.info("loaded global parameter")

    def load_demand_dict(self):
        dh = header.DemandHeader
        
        demand_df = pd.read_csv('demand.csv')
        demand_df = demand_df[(demand_df[dh.size] > 0) & (demand_df[dh.amount] > 0)]
        # rename columns
        demand_df.rename(columns={dh.size: dh.size, dh.amount: dh.amount, dh.date: dh.date}, inplace=True)

        demand_dict = dict()
        for date, df_by_date in demand_df.groupby(dh.date):
            demand_dict_by_date = {}
            for index, row in df_by_date.iterrows():
                demand_dict_by_date[row[dh.size]] = demand_dict_by_date.get(row[dh.size], 0) + row[dh.amount]

            update_demand_dict = {
                size: do.Demand(
                    date=date,
                    size=size,
                    amount=amount
                )
                for size, amount in demand_dict_by_date.items()
            }
            demand_dict[date] = update_demand_dict
        self.demand_dict = demand_dict
        logging.info("loaded demand dict: {}".format(len(self.demand_dict)))

    # endregion

    # region utils

    # endregion
