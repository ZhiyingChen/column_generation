import pyomo.environ as pe
from typing import Dict
import pandas as pd
import logging
from .. import do
from .master_problem import MasterProblem


class OriginalProblem(MasterProblem):

    def __init__(
            self
            , demand_dict: Dict[float, do.Demand]
            , pattern_dict: Dict[str, do.Pattern]
            , min_pattern_used_num: int = 0
    ):
        super(OriginalProblem, self).__init__(
            demand_dict=demand_dict
            , pattern_dict=pattern_dict
        )

        # create model
        self.model = pe.ConcreteModel('Original')
        self.min_pattern_used_num = min_pattern_used_num

    def build_model(self):
        super(OriginalProblem, self).build_model()

    def create_sets(self):
        super(OriginalProblem, self).create_sets()

    def create_vars(self):
        self.model.x = pe.Var(self.model.set_j, name='x', within=pe.NonNegativeIntegers)
        # logging.info('x created')

    def create_whether_pattern_used_var(self):
        self.model.whether_pattern_used_var = pe.Var(self.model.set_j, within=pe.Binary)

    def create_ctrs(self):

        # demand satisfying constraints
        def demand_satisfaction(model, i):
            return sum(self.pattern_dict[j].mode.get(i, 0) * self.model.x[j]
                       for j in self.model.set_j) >= self.demand_dict[i].amount

        self.model.demand_satisfaction = pe.Constraint(self.model.set_i, rule=demand_satisfaction)
        # logging.info('constraints demand_satisfaction created: {}'.format(len(self.model.demand_satisfaction)))

    def create_constraints(self):
        super().create_constraints()
        self.create_min_pattern_used_num_constr()

    def create_min_pattern_used_num_constr(self):
        if self.min_pattern_used_num is None or self.min_pattern_used_num <= 1:
            logging.info("No min pattern used num limit.")
            return
        self.create_whether_pattern_used_var()

        def whether_pattern_used_rule(model, j):
            return model.x[j] <= 10*len(self.demand_dict) * model.whether_pattern_used_var[j]

        self.model.whether_pattern_used_constr = pe.Constraint(self.model.set_j, rule=whether_pattern_used_rule)
        logging.info("created whether_pattern_used_constr: {}".format(len(self.model.whether_pattern_used_constr)))

        def min_pattern_used_num_rule(model, j):
            return model.x[j] >= self.min_pattern_used_num * model.whether_pattern_used_var[j]

        self.model.min_pattern_used_constr = pe.Constraint(self.model.set_j, rule=min_pattern_used_num_rule)
        logging.info("created min_pattern_used_constr: {}".format(len(self.model.min_pattern_used_constr)))

    def create_obj(self):
        super().create_obj()

    def solve_model(self):
        self.opt.solve(self.model, tee=True, options={'mipgap': 0.001, 'tmlim': 30})
        obj = pe.value(self.model.obj)
        x_dict = {j: pe.value(self.model.x[j]) for j in self.model.set_j}

        cut_used = []
        for pattern_id, times in x_dict.items():
            if times < 1e-4:
                continue
            sol = [self.pattern_dict[pattern_id].mode.get(size, 0) for size in self.demand_dict]
            cut_used.append([sol, times])
        return obj, cut_used
