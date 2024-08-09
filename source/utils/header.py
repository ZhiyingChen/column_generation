class ParamHeader:
    parameter_name = '参数名'
    parameter_value = '参数值'


class DemandHeader:
    size = '幅宽'
    date = '移库日期'
    amount = '订单件数'


class OutSolutionHeader:
    date = '日期'
    used_times = '套数'
    original_size = '原始幅宽'
    remain = '余量'
    waste = '边损'
    pattern_id = '切割方案编码'
    added_cuts = '补库'


class OutDemandHeader:
    size = '幅宽'
    date = '日期'
    demand_amount = '需求数量'
    unfulfilled_amount = '未满足数量'


class OutSupplyHeader:
    date = '日期'
    pattern_id = '切割方案编码'
    size = '幅宽'
    supply_amount = '供给数量'
    unfulfilled_amount = '剩余数量'


class OutFulfillmentHeader:
    supply_date = '供给日期'
    demand_date = '需求日期'
    pattern_id = '切割方案编码'
    size = '幅宽'
    supply_amount = '供给数量'


class OutKpiHeader:
    date = '日期'
    original_used_times = '原始纸卷使用个数'
    pattern_num = '切割方案数量'
    running_time = '运行时间（秒）'

