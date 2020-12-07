from typing import List
from configs import strings
from offchip.standard.spec_base import BaseSpec
from configs.stat_data_structure import ScalarStatistic


class DRAM(object):
    def __init__(self, spec: BaseSpec, level: str, level_idx: int, id_: int):
        self.id_ = id_
        self.spec = spec  # type: BaseSpec
        self.level = level
        self.level_idx = level_idx
        
        self.size = -1
        self.parent = None  # type: DRAM
        self.children = []  # type: List[DRAM]
        self.row_state = {}
        
        self.cur_serving_requests = 0
        self.begin_of_serving = -1
        self.end_of_serving = -1
        self.begin_of_cur_reqcnt = -1
        self.begin_of_refreshing = -1
        self.end_of_refreshing = -1
        self.refresh_intervals = []  # type: List[List]
        
        self._prereq = []
        self._rowhit = []
        self._rowopen = []
        self._lambda = []
        self._timing = []
        self._next = []
        self._prev = {}
        self._state = None
        
        self._num_cycles_busy = ScalarStatistic(0)
        self._num_cycles_active = ScalarStatistic(0)
        self._num_cycles_refresh = ScalarStatistic(0)
        self._num_cycles_overlap = ScalarStatistic(0)
        self._num_reqs_served = ScalarStatistic(0)
        self._avg_reqs_served = ScalarStatistic(0)
        
        self.initialize()
    
    def initialize(self):
        self._state = self.spec.start[self.level]
        self._prereq = self.spec.prereq[self.level]
        self._rowhit = self.spec.rowhit[self.level]
        self._rowopen = self.spec.rowopen[self.level]
        self._lambda = self.spec.lambda_[self.level]
        self._timing = self.spec.timing[self.level]
        
        self._next = [-1 for _ in strings.dict_list_cmd_spec[self.spec.name_spec]]
        for cmd in strings.dict_list_cmd_spec[self.spec.name_spec]:
            dist = 0
            for t in self._timing[cmd]:
                dist = max(dist, t.dist)
            if dist > 0:
                self._prev[cmd] = [-1 for _ in range(dist)]
        child_level_idx = strings.dict_list_level_spec[self.spec.name_spec].index(self.level) + 1
        child_level = strings.dict_list_level_spec[self.spec.name_spec][child_level_idx]
        
        if child_level == strings.level_row:
            return
        child_max = self.spec.org_entry.count[child_level_idx]
        if child_max == 0:
            return
        
        for i in range(child_max):
            child = DRAM(self.spec, child_level, child_level_idx, id_=i)
            child.parent = self
            self.children.append(child)
    
    def insert(self, child):
        child: DRAM
        child.parent = self
        child.id_ = len(self.children)
        self.children.append(child)
    
    def decode(self, cmd_idx, addr: list):
        child_id = addr[self.level_idx + 1]
        if self._prereq[cmd_idx] is not None:
            prereq_cmd = self._prereq[cmd_idx](self, cmd_idx, child_id)
            if prereq_cmd is not None:
                # stop recursion: there is a prerequisite at this level
                return prereq_cmd
        
        if child_id < 0 or len(self.children) == 0:
            # stop recursion: there were no prequisites at any level
            return cmd_idx
        
        # recursively decode at my child
        return self.children[child_id].decode(cmd_idx, addr)
    
    def check(self):
        raise Exception('todo')
    
    def check_row_hit(self):
        raise Exception('todo')
    
    def check_row_open(self):
        raise Exception('todo')
    
    def get_next(self):
        raise Exception('todo')
    
    def update(self):
        raise Exception('todo')
    
    def update_serving_requests(self):
        raise Exception('todo')
    
    def finish(self, num_cycles):
        self._num_cycles_busy.scalar = self._num_cycles_active.scalar + \
                                       self._num_cycles_refresh.scalar + \
                                       self._num_cycles_overlap.scalar
        self._avg_reqs_served.scalar = self._num_reqs_served.scalar / num_cycles
        if len(self.children) == 0:
            return
        for child in self.children:
            child.finish(num_cycles)
    
    def get_state(self):
        return self._state
    
    # def set_state(self, state):
    #     self._state = state
