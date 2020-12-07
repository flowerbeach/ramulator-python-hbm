from typing import List, Dict
from configs import strings
from offchip.data_structure import Request
from offchip.standard import BaseSpec


class RowPolicy(object):
    from offchip.controller import Controller
    from offchip.standard import BaseSpec as t_spec

    class Entry:
        row = -1
        hits = -1
        timestamp = -1
    
    def __init__(self, controller):
        self.ctrl = controller  # type: RowPolicy.Controller
        self.table = {}  # type: Dict[int:RowPolicy.Entry]
    
    def update(self, cmd, addr_list, cycle_current):
        pass
    
    def get_hits(self, addr_list, to_opened_row=False):
        pass
