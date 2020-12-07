from typing import List, Dict
from configs import strings
from offchip.memory_data_structure import Request
from offchip.dram_spec import BaseSpec


class RowPolicy(object):
    from offchip.memory_controller import Controller
    from offchip.dram_spec import BaseSpec as t_spec

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
