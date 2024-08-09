import logging
import time
from .input_data import InputData
from .result_storage import ResultStorage
from .utils.init_pattern import init_pattern
from .model.original_problem import OriginalProblem
from .model.master_problem import MasterProblem
from .model.sub_problem import SubProblem
from .utils.pattern_update import pattern_update
from . import do


class Context:
    def __init__(
            self
    ):

        self.results = None
        self.input_data: InputData = InputData()
        self.result_storage: ResultStorage = ResultStorage(
            input_data=InputData()
        )
        self.master_problem: MasterProblem = MasterProblem(
            demand_dict={},
            pattern_dict={},
        )
        self.sub_problem: SubProblem = SubProblem(
            input_data=InputData(),
            duals=[],
            demand_dict={},
        )
        self.original_problem: OriginalProblem = OriginalProblem(
            demand_dict={},
            pattern_dict={},
            min_pattern_used_num=0
        )

    def execute4specific_date(self, date: str):
        input_data = self.input_data
        result_storage = self.result_storage

        demand_dict = input_data.demand_dict[date]
        logging.info("start solving for date: {}".format(date))
        start = time.time()
        pattern_dict = init_pattern(demand_dict=demand_dict, og_size=input_data.original_size)

        improvable = True
        iteration = 0
        while improvable:
            self.master_problem = MasterProblem(demand_dict=demand_dict, pattern_dict=pattern_dict)
            self.master_problem.build_model()
            master_obj, duals = self.master_problem.solve_model()

            self.sub_problem = SubProblem(
                input_data=input_data,
                duals=duals,
                demand_dict=demand_dict
            )
            self.sub_problem.build_model()
            sub_obj, new_column, remain = self.sub_problem.solve_model()
            logging.info("sub_obj: {}".format(sub_obj))

            improvable = sub_obj > 1 + 1e-8

            pattern_update(pattern_dict=pattern_dict, size_list=[d for d in demand_dict],
                           new_column=new_column, original_size=input_data.original_size)
            iteration += 1

        self.original_problem = OriginalProblem(
            demand_dict=demand_dict
            , pattern_dict=pattern_dict
            , min_pattern_used_num=input_data.min_pattern_used_num
        )
        self.original_problem.build_model()
        og_obj, solution = self.original_problem.solve_model()

        logging.info("Iterations: {}".format(iteration))

        solution_do = do.Solution(date=date)
        solution_do.generate_pattern_used_dict(
            demand_dict=demand_dict,
            original_size=input_data.original_size,
            solution=solution
        )

        result_storage.solution_dict.update({date: solution_do})
        result_storage.generate_fulfillment_relationship_by_date(date=date)

        if input_data.whether_process_remain:
            result_storage.post_process_remain(date=date)

        stamp4 = time.time()
        total_run_time = stamp4 - start
        result_storage.solution_dict[date].running_time = total_run_time
        logging.info("Running time for date {}: {}".format(date, total_run_time))
        return date, result_storage

    def run(self):

        self.input_data.read_data()

        self.result_storage = ResultStorage(input_data=self.input_data)
        if self.input_data.whether_process_remain:
            self.execute_sequentially()
        else:
            self.execute_in_parallel()

        self.result_storage.dump()

    def execute_in_parallel(self):
        from joblib import Parallel, delayed
        dates = [date for date in self.input_data.demand_dict]

        self.results = Parallel(n_jobs=4)(delayed(self.execute4specific_date)(date) for date in dates)

        for (date, result_storage) in self.results:
            self.result_storage.input_data.demand_dict[date].update(result_storage.input_data.demand_dict[date])
            self.result_storage.supply_dict.update(result_storage.supply_dict)
            self.result_storage.solution_dict.update(result_storage.solution_dict)

    def execute_sequentially(self):
        for date in self.input_data.demand_dict:
            self.execute4specific_date(date=date)

