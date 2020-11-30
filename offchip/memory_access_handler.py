from configs import strings
from typing import List
from offchip.memory_controller import Controller


class MemoryAccessHandler(object):
    options = {}
    flag_stall = False
    flag_end = False
    
    _num_reads = 0
    _num_writes = 0
    _num_cycles = 0
    
    __latency = {}
    __ctrls = []  # type: List[Controller]
    
    @staticmethod
    def initialize(args_, ctrls):
        MemoryAccessHandler.__ctrls = ctrls
    
    @staticmethod
    def get_num_pending_requests():
        num_reqs = 0
        for ctrl in MemoryAccessHandler.__ctrls:
            num_reqs += (
                    len(ctrl.queue_read) +
                    len(ctrl.queue_write) +
                    len(ctrl.queue_other) +
                    len(ctrl.queue_activate) +
                    len(ctrl.pending_reads)
            )
        return num_reqs
    
    @staticmethod
    def send(request):
        MemoryAccessHandler.flag_stall = True
        if request.type == strings.str_req_type_read:
            MemoryAccessHandler._num_reads += 1
        elif request.type == strings.str_req_type_write:
            MemoryAccessHandler._num_writes += 1
        else:
            raise Exception(request.type)
        pass  # todo
    
    @staticmethod
    def cycle():
        MemoryAccessHandler._num_cycles += 1

    @staticmethod
    def finish():
        pass
    
    @staticmethod
    def set_high_writeq_watermark(mark):
        pass
