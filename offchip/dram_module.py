from typing import List, Dict
from configs import strings
from offchip.standard.spec_base import BaseSpec
from configs.stat_data_structure import ScalarStatistic


class DRAM(object):
    from offchip.standard import BaseSpec as t_spec
    
    def __init__(self, spec: BaseSpec, level: t_spec.level, id_: int):
        from offchip.controller import Controller
        
        self.id_ = id_
        self.spec = spec  # type: BaseSpec
        self.level = level
        
        self.size = -1
        self.parent = None  # type: DRAM
        self.children = []  # type: List[DRAM]
        self.row_state = {}
        self.cycle_curr = 0
        
        self.serving_requests = 0
        self.cur_serving_requests = 0
        self.begin_of_serving = -1
        self.end_of_serving = -1
        self.begin_of_cur_reqcnt = -1
        self.begin_of_refreshing = -1
        self.end_of_refreshing = -1
        self.refresh_intervals = []  # type: List[List]
        
        self._prereq = {}
        self._rowhit = {}
        self._rowopen = {}
        self._lambda = {}
        self._timing = {}
        self._next = []
        self._prev = {cmd: Controller.Queue() for cmd in self.t_spec.cmd}
        self._state = None
        
        self._num_cycles_busy = ScalarStatistic(0)
        self._num_cycles_active = ScalarStatistic(0)
        self._num_cycles_refresh = ScalarStatistic(0)
        self._num_cycles_overlap = ScalarStatistic(0)
        self._num_reqs_served = ScalarStatistic(0)
        self._avg_reqs_served = ScalarStatistic(0)
        
        self.initialize()
    
    def initialize(self):
        from offchip.controller import Controller
        self._prev: Dict[DRAM.t_spec.cmd, Controller.Queue]
        
        self._state = self.spec.start[self.level]
        self._prereq = self.spec.prereq[self.level]
        self._rowhit = self.spec.rowhit[self.level]
        self._rowopen = self.spec.rowopen[self.level]
        self._lambda = self.spec.lambda_[self.level]
        self._timing = self.spec.timing[self.level]
        
        self._next = [-1 for _ in DRAM.t_spec.cmd]
        for cmd in DRAM.t_spec.cmd:
            dist = 0
            for t in self._timing[cmd]:
                dist = max(dist, t.dist)
            if dist > 0:
                self._prev[cmd].resize(dist, -1)
        child_level = DRAM.t_spec.level(self.level.value + 1)  # type: DRAM.t_spec.level
        
        if child_level == DRAM.t_spec.level.row:
            return
        child_max = self.spec.org_entry.count[child_level.value]
        if child_max == 0:
            return
        
        for i in range(child_max):
            child = DRAM(self.spec, child_level, id_=i)
            child.parent = self
            self.children.append(child)
    
    def insert(self, child):
        child: DRAM
        child.parent = self
        child.id_ = len(self.children)
        self.children.append(child)
    
    def decode(self, cmd, addr_list: list):
        child_id = addr_list[self.level.value + 1]
        if self._prereq[cmd]:
            prereq_cmd = self._prereq[cmd.value](self, cmd, child_id)
            if prereq_cmd is not None:
                # stop recursion: there is a prerequisite at this level
                return prereq_cmd
        
        if child_id < 0 or len(self.children) == 0:
            # stop recursion: there were no prequisites at any level
            return cmd
        
        # recursively decode at my child
        return self.children[child_id].decode(cmd, addr_list)
    
    def check(self, cmd, addr_list, cycle_current):
        if self._next[cmd.value] != -1 and cycle_current < self._next[cmd.value]:
            # stop recursion: the check failed at this level
            return False
        
        child_id = addr_list[self.level.value + 1]
        if child_id < 0 or self.level == self.spec.scope[cmd.value] or \
                len(self.children) == 0:
            # stop recursion: the check passed at all levels
            return True
        
        # recursively check my child
        return self.children[child_id].check(cmd, addr_list, cycle_current)
    
    def check_row_hit(self, cmd, addr_list):
        child_id = addr_list[self.level.value + 1]
        if self._rowhit[cmd.value]:
            # stop recursion: there is a row hit at this level
            return self._rowhit[cmd.value](self, cmd, child_id)
        
        if child_id < 0 or len(self.children) == 0:
            # stop recursion: there were no row hits at any level
            return False
        
        # recursively check for row hits at my child
        return self.children[child_id].check_row_hit(cmd, addr_list)
    
    def check_row_open(self, cmd, addr_list):
        child_id = addr_list[self.level.value + 1]
        if self._rowopen[cmd.value]:
            # stop recursion: there is a row open at this level
            return self._rowopen[cmd.value](self, cmd, child_id)
        
        if child_id < 0 or len(self.children) == 0:
            # stop recursion: there were no row hits at any level
            return False
        
        # recursively check for row hits at my child
        return self.children[child_id].check_row_open(cmd, addr_list)
    
    def update(self, cmd, addr_list, cycle_curr):
        self.cycle_curr = cycle_curr
        self._update_state(cmd, addr_list)
        self._update_timing(cmd, addr_list, cycle_curr)
    
    def _update_state(self, cmd, addr_list):
        child_id = addr_list[self.level.value + 1]
        if self._lambda[cmd] is not None:
            # update this level
            self._lambda[cmd](self, child_id)
        
        if self.level == self.spec.scope[cmd.value] or len(self.children) == 0:
            # stop recursion: updated all levels
            return
        
        # recursively update the child
        self.children[child_id]._update_state(cmd, addr_list)
    
    def _update_timing(self, cmd, addr_list, cycle_curr):
        from offchip.standard.spec_data_structure import TimingEntry
        self._timing: Dict[DRAM.t_spec.cmd, List[TimingEntry]]
        
        if self.id_ != addr_list[self.level.value]:
            for t in self._timing[cmd]:
                if not t.sibling:
                    # not an applicable timing parameter
                    continue
                
                # update future
                assert t.dist == 1
                future = cycle_curr + t.val
                self._next[t.cmd.value] = max(future, self._next[t.cmd.value])
            
            # stop recursion: only target nodes should be recursed
            return
        
        from offchip.controller import Controller
        self._prev: Dict[DRAM.t_spec.cmd, Controller.Queue]
        if self._prev[cmd].size() > 0:
            self._prev[cmd].pop_i()
            self._prev[cmd].push(cycle_curr)
        
        for t in self._timing[cmd]:
            pass
        
        # Some commands have timings that are higher that their scope levels, thus
        # we do not stop at the cmd's scope level
        if len(self.children) == 0:
            # stop recursion: updated all levels
            return
        
        # recursively update *all* of the children
        for child in self.children:
            child._update_timing(cmd, addr_list, cycle_curr)
    
    def update_serving_requests(self, addr_list, delta, cycle_curr):
        assert self.id_ == addr_list[self.level.value]
        assert delta in [1, -1]
        
        # update total serving requests
        if self.begin_of_cur_reqcnt != -1 and self.cur_serving_requests > 0:
            self.serving_requests += (cycle_curr - self.begin_of_cur_reqcnt) * self.cur_serving_requests
            self._num_cycles_active += cycle_curr - self.begin_of_cur_reqcnt
        
        # update begin of current request number
        self.begin_of_cur_reqcnt = cycle_curr
        self.cur_serving_requests += delta
        assert self.cur_serving_requests >= 0
        
        if delta == 1 and self.cur_serving_requests == 1:
            # transform from inactive to active
            self.begin_of_serving = cycle_curr
            if self.end_of_refreshing > self.begin_of_serving:
                self._num_cycles_overlap += self.end_of_refreshing - self.begin_of_serving
        elif self.cur_serving_requests == 0:
            # transform from active to inactive
            assert self.begin_of_serving != -1
            assert delta == -1
            self._num_cycles_active += cycle_curr - self.begin_of_cur_reqcnt
            self.end_of_serving = cycle_curr
            
            for ref in self.refresh_intervals:
                self._num_cycles_overlap += min(self.end_of_serving, ref[1]) - ref[0]
            self.refresh_intervals = []
        
        child_id = addr_list[self.level.value + 1]
        # We only count the level bank or the level higher than bank
        if child_id < 0 or len(self.children) == 0 or self.level.value > DRAM.t_spec.level.bank.value:
            return
        self.children[child_id].update_serving_requests(addr_list, delta, cycle_curr)
    
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
    
    def set_state(self, state):
        self._state = state
