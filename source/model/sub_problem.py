import pyomo.environ as pe
from typing import Dict
from .. import do


class SubProblem:

    def __init__(
            self
            , input_data
            , duals
            , demand_dict
    ):
        self.consider_waste = input_data.consider_waste
        self.waste_up_limit = input_data.waste_up_limit
        self.waste_low_limit = input_data.waste_low_limit
        self.remain_low_limit = input_data.remain_low_limit
        self.max_cut = input_data.max_cut
        # extract data
        self.size_array = [d for d in demand_dict]

        # create model
        self.model = pe.ConcreteModel('Sub')
        self.opt = pe.SolverFactory("glpk")
        # self.opt.options['OutputFlag'] = 1

        # create parameters
        self.model.phi_i = duals
        self.model.L = input_data.original_size
        self.model.s_i = [d for d in demand_dict]

    def build_model(self):
        self.create_sets()
        self.create_vars()
        self.create_ctrs()
        self.create_obj()

    def create_sets(self):
        self.model.set_i = [i for i in range(len(self.size_array))]
        # logging.info('set_i created with I = {}'.format(len(self.size_array)))

    def create_vars(self):
        self.model.y_i = pe.Var(self.model.set_i, name='y_i', within=pe.NonNegativeIntegers)
        self.model.c_y = pe.Var(name='c_y', within=pe.Reals)
        # logging.info('y_i, c_y created')
        self.model.r_c = pe.Var(name='r_c', within=pe.Reals)
        # var: if remain
        self.model.z = pe.Var(name='z', within=pe.Binary)
        self.model.whether_remain = pe.Var(within=pe.Binary)

    def create_ctrs(self):
        # original roll length constraint
        waste_low_limit = self.waste_low_limit if self.consider_waste else 0

        # wasted length if apply y
        self.model.wasted_length = pe.Constraint(
            expr=self.model.L - sum(self.model.s_i[i] * self.model.y_i[i] for i in self.model.set_i) == self.model.c_y)

        self.model.length_limit = pe.Constraint(
            expr=self.model.c_y >= waste_low_limit
        )
        self.model.if_remain = pe.Constraint(expr=self.model.c_y <= self.model.L * self.model.z)

        # cutting time limit new
        self.model.cutting_time_1 = pe.Constraint(
            expr=sum(self.model.y_i[i] for i in self.model.set_i) <= self.max_cut * self.model.z + (
                    self.max_cut + 1) * (1 - self.model.z))
        self.model.cutting_time_2 = pe.Constraint(
            expr=sum(self.model.y_i[i] for i in self.model.set_i) <= (self.max_cut + 1) * (
                    1 - self.model.z) + self.max_cut * self.model.z)
        self.model.cutting_time_3 = pe.Constraint(
            expr=sum(self.model.y_i[i] for i in self.model.set_i) >= (self.max_cut + 1) * (
                    1 - self.model.z))

        self.model.reduced_cost = pe.Constraint(
            expr=sum(self.model.phi_i[i] * self.model.y_i[i] for i in self.model.set_i) == self.model.r_c)

        if not self.consider_waste:
            return

        self.model.treat_wasted_length_as_remain = pe.Constraint(
            expr=(self.model.c_y >= self.remain_low_limit * self.model.whether_remain +
                  (
                          (1 - self.model.whether_remain) * waste_low_limit
                  )
                  )
        )

        self.model.treat_wasted_length_as_waste = pe.Constraint(
            expr=(self.model.c_y <= self.waste_up_limit * (
                    1 - self.model.whether_remain) + self.model.L * self.model.whether_remain)
        )

    def create_obj(self):
        # maximize reduced cost
        self.model.obj = pe.Objective(expr=self.model.r_c, sense=pe.maximize)

    def solve_model(self):
        self.opt.solve(self.model)
        obj = pe.value(self.model.obj)
        remain = pe.value(self.model.c_y)
        column = [pe.value(self.model.y_i[i]) for i in self.model.set_i]
        return obj, column, remain

    def solution_dict(self):
        sol_dict = {}
        for k, v in self.model.component_map(ctype=pe.Var).items():
            sol_dict[v.getname()] = {kk: vv() for kk, vv in v.items()}
        return sol_dict
