import pyomo.environ as pe
import logging
from typing import Dict
from .. import do


class MasterProblem:

    def __init__(self, demand_dict: Dict[float, do.Demand],
                 pattern_dict: Dict[str, do.Pattern]):
        self.demand_dict = demand_dict
        self.pattern_dict = pattern_dict
        # create model
        self.model = pe.ConcreteModel('Master')
        self.model.dual = pe.Suffix(direction=pe.Suffix.IMPORT)
        self.opt = pe.SolverFactory("gurobi", solver_io="python")
        # self.opt.options['OutputFlag'] = 1

    def build_model(self):
        self.create_sets()
        self.create_vars()
        self.create_constraints()
        self.create_obj()

    def create_sets(self):
        self.model.set_i = [size for size in self.demand_dict]
        # logging.info('set_i created with I = {}'.format(len(self.demand_list)))
        self.model.set_j = [p for p in self.pattern_dict]
        # logging.info('set_j created with J = {}'.format(len(self.pattern_mode)))

    def create_vars(self):
        self.model.x = pe.Var(self.model.set_j, name='x', within=pe.NonNegativeReals)
        # logging.info('x created')

    def create_constraints(self):
        self.create_ctrs()

    def create_ctrs(self):

        # demand satisfying constraints
        def demand_satisfaction(model, i):
            return sum(self.pattern_dict[j].mode.get(i, 0) * self.model.x[j]
                       for j in self.model.set_j) == self.demand_dict[i].amount

        self.model.demand_satisfaction = pe.Constraint(self.model.set_i, rule=demand_satisfaction)
        # logging.info('constraints demand_satisfaction created: {}'.format(len(self.model.demand_satisfaction)))

    def create_obj(self):
        self.model.obj = pe.Objective(expr=sum(self.model.x[j] for j in self.model.set_j), sense=pe.minimize)
        # logging.info('objective created')

    def solve_model(self):
        self.opt.solve(self.model)
        duals = self.get_duals()
        obj = pe.value(self.model.obj)
        return obj, duals

    def get_duals(self):
        duals = []
        # get duals for all constraints (demands)
        for k in self.model.demand_satisfaction.keys():
            duals.append(self.model.dual[self.model.demand_satisfaction[k]])
        return duals

    def solution_dict(self):
        sol_dict = {}
        for k, v in self.model.component_map(ctype=pe.Var).items():
            sol_dict[v.getname()] = {kk: vv() for kk, vv in v.items()}
        return sol_dict
