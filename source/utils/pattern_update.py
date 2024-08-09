from .timing import record_time_decorator
from .. import do
from typing import Dict, List


@record_time_decorator(task_name="update pattern时长")
def pattern_update(pattern_dict: Dict[int, do.Pattern],
                   size_list: List[float],
                   new_column: List[int], original_size:float):
    new_pattern_mode = dict(zip(size_list, new_column))
    pattern_id = len(pattern_dict)
    new_pattern = do.Pattern(
        pattern_id=pattern_id,
        original_size=original_size,
        mode=new_pattern_mode
    )
    pattern_dict.update({pattern_id: new_pattern})


