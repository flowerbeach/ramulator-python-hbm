from typing import List
from enum import Enum, unique


class RowPolicy(object):
    from offchip.controller import Controller
    # from offchip.standard import BaseSpec as t_spec
    
    @unique
    class Type(Enum):
        closed = 0
        closedAP = 1
        opened = 2
        timeout = 3
    
    def __init__(self, ctrl):
        self.ctrl = ctrl  # type: RowPolicy.Controller
        self.type = self.Type.opened
        self.timeout = 50
        
        self._policy = {
            self.Type.closed: self._policy_closed,
            self.Type.closedAP: self._policy_closedAP,
            self.Type.opened: self._policy_opened,
            self.Type.timeout: self._policy_timeout,
        }  # type: List[RowPolicy._policy_closed]
    
    def get_victim(self, cmd):
        return self._policy[self.type.value](cmd)
    
    def _policy_closed(self, cmd):
        for k in self.ctrl.row_table.table.keys():
            if not self.ctrl.is_ready_cmd(cmd, k):
                continue
            return k
        return list()
    
    def _policy_closedAP(self, cmd):
        for k in self.ctrl.row_table.table.keys():
            if not self.ctrl.is_ready_cmd(cmd, k):
                continue
            return k
        return list()
    
    def _policy_opened(self, cmd):
        return list()
    
    def _policy_timeout(self, cmd):
        for k, v in self.ctrl.row_table.table.items():
            if self.ctrl.cycle_curr - v.timestamp < self.timeout:
                continue
            if not self.ctrl.is_ready_cmd(cmd, k):
                continue
            return k
        return list()
