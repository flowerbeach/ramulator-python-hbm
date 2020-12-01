from typing import List
from configs import strings
from offchip.dram_spec.spec_base import BaseSpec


class DRAM(object):
    def __init__(self, spec: BaseSpec, level, level_idx, id_):
        self.id_ = id_
        self.spec = spec
        self.level = level
        self.level_idx = level_idx
        
        self.size = -1
        self.parent = None  # type: DRAM
        self.children = []  # type: List[DRAM]
        
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
        self._row_state = {}
        
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
        
        if child_level == strings.str_level_row:
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
    
    def decode(self):
        pass
    
    def check(self):
        pass
    
    def check_row_hit(self):
        pass
    
    def check_row_open(self):
        pass
    
    def get_next(self):
        pass
    
    def update(self):
        pass
    
    def update_serving_requests(self):
        pass
    
    def finish(self):
        pass
    
    def get_state(self):
        return self._state
