from typing import List
from configs import strings
from offchip.memory_data_structure import Request
from offchip.dram_spec import BaseSpec
from enum import Enum, unique


class Scheduler(object):
    from offchip.memory_controller import Controller
    from offchip.dram_spec import BaseSpec as t_spec
    
    @unique
    class Type(Enum):
        FCFS = 0
        FRFCFS = 1
        FRFCFS_CAP = 2
        FRFCFS_PriorHit = 3
    
    def __init__(self, controller):
        self.ctrl = controller  # type: Scheduler.Controller
        # Change the following line to change scheduling policy
        self.type = Scheduler.Type.FRFCFS_CAP  # type: Scheduler.Type
        # Change the following line to change cap
        self.cap = 16
        
        self._compare = [self._compare_FCFS,
                         self._compare_FRFCFS,
                         self._compare_FRFCFS_CAP,
                         self._compare_FRFCFS_PriorHit
                         ]  # type: List[Scheduler._compare_FCFS]
    
    def get_head(self, queue_req: List[Request]):
        
        # If queue is empty, return end of queue
        if len(queue_req) == 0:
            return None
        
        # Else return based on the policy
        head = queue_req[0]
        for i in range(1, len(queue_req)):
            head = self._compare[self.type.value](head, queue_req[i])
        
        if self.type != self.Type.FRFCFS_PriorHit:
            return head
        elif self.ctrl.is_ready_req(head) and self.ctrl.is_row_hit_req(head):
            return head
        
        hit_reqs = []
        for req in queue_req:
            if self.ctrl.is_row_hit_req(req):
                begin = 0
                end = begin + self.ctrl.channel.spec.scope[self.t_spec.cmd.pre.value] + 1
                hit_reqs.append([begin, end])
        
        # if we can't find proper request, we need to return q.end(),
        # so that no command will be scheduled
        head = None
        for req in queue_req:
            violate_hit = False
            if self.ctrl.is_row_hit_req(req) is False and self.ctrl.is_row_open_req(req):
                begin = 0
                end = begin + self.ctrl.channel.spec.scope[self.t_spec.cmd.pre.value] + 1
                for hit_req_rowgroup in hit_reqs:
                    if hit_req_rowgroup == [begin, end]:
                        violate_hit = True
                        break
            if violate_hit is True:
                continue
            
            # If it comes here, that means it won't violate any hit request
            if head is None:
                head = req
            else:
                head = self._compare[Scheduler.Type.FRFCFS](head, req)
        return head
    
    def _compare_FCFS(self, req1, req2):
        head = None
        return head
    
    def _compare_FRFCFS(self, req1, req2):
        head = None
        return head
    
    def _compare_FRFCFS_CAP(self, req1, req2):
        head = None
        return head
    
    def _compare_FRFCFS_PriorHit(self, req1, req2):
        head = None
        return head
