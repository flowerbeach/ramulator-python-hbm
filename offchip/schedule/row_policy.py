from typing import List, Dict
from configs import strings
from offchip.data_structure import Request
from offchip.standard import BaseSpec
from enum import Enum, unique


class RowPolicy(object):
    from offchip.controller import Controller
    from offchip.standard import BaseSpec as t_spec
    
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
        raise Exception('todo')
    
    def _policy_closedAP(self, cmd):
        raise Exception('todo')
    
    def _policy_opened(self, cmd):
        raise Exception('todo')
    
    def _policy_timeout(self, cmd):
        raise Exception('todo')
