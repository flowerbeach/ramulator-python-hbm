from typing import List
from configs import strings
from offchip.memory_data_structure import Request
from offchip.memory_module import DRAM


class Scheduler(object):
    def __init__(self, controller):
        pass


class RowPolicy(object):
    def __init__(self, controller):
        pass


class RowTable(object):
    def __init__(self, controller):
        pass


class Refresh(object):
    def __init__(self, controller):
        pass


class Controller(object):
    class Queue(object):
        def __init__(self, max=32):
            self.queue_requests = []  # type: List[Request]
            self.max = max
        
        def size(self):
            return len(self.queue_requests)
    
    def __init__(self, args_, channel: DRAM):
        self.num_cycles = 0
        self.channel = channel
        self.scheduler = Scheduler(self)
        self.row_policy = RowPolicy(self)
        self.row_table = RowTable(self)
        self.refresh = Refresh(self)
        self.spec = channel.spec
        
        self.queue_read = Controller.Queue()
        self.queue_write = Controller.Queue()
        self.queue_activate = Controller.Queue()
        # read and write requests for which activate was issued are moved to
        # actq, which has higher priority than readq and writeq.
        # This is an optimization for avoiding useless activations (i.e., PRECHARGE
        # after ACTIVATE w/o READ of WRITE command)
        self.queue_other = Controller.Queue()  # queue for all "other" requests (e.g., refresh)
        
        self.pending_reads = Controller.Queue()  # read requests that are about to receive data from DRAM
        self.write_mode = False
        
        self.wr_high_watermark = 0.8
        self.wr_low_watermark = 0.2
        
        # statistics
        self._bytes_read = 0
        self._bytes_write = 0
        
        self._hits_row = 0
        self._hits_row_read = 0
        self._hits_row_write = 0
        self._misses_row = 0
        self._misses_row_read = 0
        self._misses_row_write = 0
        self._conflicts_row = 0
        self._conflicts_row_read = 0
        self._conflicts_row_write = 0
        self.useless_activates = 0
        
        self._latency_read_sum = 0
        self._latency_read_avg = 0
        
        self._req_queue_length_avg = 0
        self._req_queue_length_sum = 0
        self._req_queue_length_read_avg = 0
        self._req_queue_length_read_sum = 0
        self._req_queue_length_write_avg = 0
        self._req_queue_length_write_sum = 0
        
        self._record_hits_read = 0
        self._record_misses_read = 0
        self._record_conflicts_read = 0
        self._record_hits_write = 0
        self._record_misses_write = 0
        self._record_conflicts_write = 0
    
    def finish(self, read_req):
        self._latency_read_avg = self._latency_read_sum / read_req
        self._req_queue_length_avg = self._req_queue_length_sum / self.num_cycles
        self._req_queue_length_read_avg = self._req_queue_length_read_sum / self.num_cycles
        self._req_queue_length_write_avg = self._req_queue_length_write_sum / self.num_cycles
        self.channel.finish(self.num_cycles)
    
    def _get_queue(self, type_):
        if type_ == strings.req_type_read:
            return self.queue_read
        elif type_ == strings.req_type_write:
            return self.queue_write
        elif type_ in strings.list_req_type_all:
            return self.queue_other
        else:
            raise Exception(type_)
    
    def enqueue(self, req: Request):
        queue = self._get_queue(req.type)
        if queue.size() == queue.max:
            return False
        elif queue.size() > queue.max:
            raise Exception(queue.size())
        
        req.arrive = self.num_cycles
        queue.queue_requests.append(req)
        
        if req.type == strings.req_type_read:
            for wreq in self.queue_write.queue_requests:
                if wreq.addr_int == req.addr_int:
                    req.depart = self.num_cycles + 1
                    self.pending_reads.queue_requests.append(req)
                    self.queue_read.queue_requests.pop()
                    break
        return True
    
    def cycle(self):
        pass
    
    def is_ready(self, command, addr_vec):
        pass
    
    def is_row_hit(self):
        pass
    
    def is_row_open(self):
        pass
    
    def is_active(self):
        pass
    
    def is_refresh(self):
        pass
    
    def set_high_writeq_watermark(self, mark):
        pass
    
    def set_low_writeq_watermark(self, mark):
        pass
    
    #
    def _get_first_cmd(self):
        pass
    
    def _cmd_issue_autoprecharge(self):
        pass
    
    def _issue_cmd(self):
        pass
    
    def _get_addr_vec(self):
        pass
    
    def print_state(self):
        print('   queue_read: {}'.format(self.queue_read.size()))
        print('   queue_write: {}'.format(self.queue_write.size()))
        print('   queue_other: {}'.format(self.queue_other.size()))
