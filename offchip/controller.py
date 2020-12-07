from typing import List
from configs import strings
from offchip.data_structure import Request
from offchip.dram_module import DRAM


class Controller(object):
    class Queue(object):
        def __init__(self, max=32):
            self.queue_requests = []  # type: List[Request]
            self.max = max
        
        def size(self):
            return len(self.queue_requests)
    
    def __init__(self, args_, channel: DRAM):
        from offchip.schedule import Scheduler, RowTable, RowPolicy
        from offchip.refresh import Refresh
        
        self.cycle_current = 0
        self.channel = channel
        self.spec = channel.spec
        self.scheduler = Scheduler(self)
        self.row_policy = RowPolicy(self)
        self.row_table = RowTable(self)
        self.refresh = Refresh(self)
        
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
        self._req_queue_length_avg = self._req_queue_length_sum / self.cycle_current
        self._req_queue_length_read_avg = self._req_queue_length_read_sum / self.cycle_current
        self._req_queue_length_write_avg = self._req_queue_length_write_sum / self.cycle_current
        self.channel.finish(self.cycle_current)
    
    def _get_queue(self, type_):
        if type_ == Request.Type.read:
            return self.queue_read
        elif type_ == Request.Type.write:
            return self.queue_write
        elif type_ in Request.Type:
            return self.queue_other
        else:
            raise Exception(type_)
    
    def enqueue(self, req: Request):
        queue = self._get_queue(req.type)
        if queue.size() == queue.max:
            return False
        elif queue.size() > queue.max:
            raise Exception(queue.size())
        
        req.cycle_arrive = self.cycle_current
        queue.queue_requests.append(req)
        
        if req.type == Request.Type.read:
            for wreq in self.queue_write.queue_requests:
                if wreq.addr_int == req.addr_int:
                    req.cycle_depart = self.cycle_current + 1
                    self.pending_reads.queue_requests.append(req)
                    self.queue_read.queue_requests.pop()
                    break
        return True
    
    def cycle(self):
        raise Exception('todo')
    
    def is_ready_req(self, request: Request):
        cmd = self._get_first_cmd(request)
        return self.channel.check(cmd, request.addr_list, self.cycle_current)
    
    def is_ready_cmd(self, cmd, addr_list):
        return self.channel.check(cmd, addr_list, self.cycle_current)
    
    def is_row_hit_req(self, request: Request):
        cmd = self.channel.spec.translate[request.type]
        return self.channel.check_row_hit(cmd, request.addr_list)
    
    def is_row_hit_cmd(self, cmd, addr_list):
        return self.channel.check_row_hit(cmd, addr_list)
    
    def is_row_open_req(self, request: Request):
        cmd = self.channel.spec.translate[request.type]
        return self.channel.check_row_open(cmd, request.addr_list)
    
    def is_row_open_cmd(self, cmd, addr_list):
        return self.channel.check_row_open(cmd, addr_list)
    
    def is_active(self):
        return self.channel.cur_serving_requests > 0
    
    def is_refresh(self):
        return self.cycle_current <= self.channel.end_of_refreshing
    
    def set_high_writeq_watermark(self, mark):
        self.wr_high_watermark = mark
    
    def set_low_writeq_watermark(self, mark):
        self.wr_low_watermark = mark
    
    def set_temperature(self, current_temperature):
        return
    
    ###
    
    def _get_first_cmd(self, request: Request):
        cmd = self.channel.spec.translate[request.type]
        return self.channel.decode(cmd, request.addr_list)
    
    def _cmd_issue_autoprecharge(self):
        raise Exception('todo')
    
    def _issue_cmd(self):
        raise Exception('todo')
    
    @staticmethod
    def _get_addr_vec(cmd, req: Request):
        return req.addr_list
    
    def print_state(self):
        print('   queue_read: {}'.format(self.queue_read.size()))
        print('   queue_write: {}'.format(self.queue_write.size()))
        print('   queue_other: {}'.format(self.queue_other.size()))
