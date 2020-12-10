from offchip.data_structure import Request


class Controller(object):
    from offchip.dram_module import DRAM
    from offchip.data_structure import Queue
    
    def __init__(self, t_spec, channel: DRAM):
        from offchip.schedule import Scheduler, RowTable, RowPolicy
        from offchip.refresh import Refresh
        from offchip.standard.spec_base import BaseSpec
        self.t_spec = t_spec  # type:BaseSpec
        self.cycle_curr = 0
        self.channel = channel
        self.spec = channel.t_spec
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
        self._latency_read_avg = 0 if read_req == 0 else self._latency_read_sum / read_req
        self._req_queue_length_avg = self._req_queue_length_sum / self.cycle_curr
        self._req_queue_length_read_avg = self._req_queue_length_read_sum / self.cycle_curr
        self._req_queue_length_write_avg = self._req_queue_length_write_sum / self.cycle_curr
        self.channel.finish(self.cycle_curr)
    
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
        
        req.cycle_arrive = self.cycle_curr
        queue.push_i(req)
        
        if req.type == Request.Type.read:
            for wreq in self.queue_write.queue_req:
                if wreq.addr_int == req.addr_int:
                    req.cycle_depart = self.cycle_curr + 1
                    self.pending_reads.queue_req.append(req)
                    self.queue_read.queue_req.pop(-1)
                    break
        return True
    
    def cycle(self):
        self.cycle_curr += 1
        
        # 1. Serve completed reads
        if self.pending_reads.size() > 0:
            req = self.pending_reads.get_i(0)
            if req.cycle_depart <= self.cycle_curr:
                if req.cycle_depart - req.cycle_arrive > 1:  # this request really accessed a row
                    self._latency_read_sum += req.cycle_depart - req.cycle_arrive
                    self.channel.update_serving_requests(req.addr_list, -1, self.cycle_curr)
                req.callback(req)
                self.pending_reads.pop_i(0)
        
        # 2. Refresh scheduler
        self.refresh.cycle()
        
        # 3. Should we schedule writes?
        if self.write_mode is False:
            # write queue is almost full or read queue is empty
            if self.queue_write.size() > int(self.wr_high_watermark * self.queue_write.max) or self.queue_read.size() == 0:
                self.write_mode = True
        else:
            # write queue is almost empty and read queue is not empty
            if self.queue_write.size() < int(self.wr_low_watermark * self.queue_write.max) and self.queue_read.size() != 0:
                self.write_mode = False
        
        # 4. Find the best command to schedule, if any
        
        # First check the actq (which has higher priority) to see if there
        # are requests available to service in this cycle
        cmd = None
        queue = self.queue_activate
        req = self.scheduler.get_head(queue.queue_req)
        is_valid_req = (req is not None)
        if is_valid_req is True:
            cmd = self._get_first_cmd(req)
            is_valid_req = self.is_ready_cmd(cmd, req.addr_list)
        
        if is_valid_req is False:
            # "other" requests are rare, so we give them precedence over reads/writes
            if self.queue_other.size() > 0:
                queue = self.queue_other
            elif self.write_mode is True:
                queue = self.queue_write
            else:
                queue = self.queue_read
            
            req = self.scheduler.get_head(queue.queue_req)
            is_valid_req = (req is not None)
            if is_valid_req is True:
                cmd = self._get_first_cmd(req)
                is_valid_req = self.is_ready_cmd(cmd, req.addr_list)
        
        if is_valid_req is False:
            # we couldn't find a command to schedule -- let's try to be speculative
            from offchip.standard.spec_base import BaseSpec as t_spec
            cmd = t_spec.cmd.pre
            victim = self.row_policy.get_victim(cmd)
            if len(victim) > 0:
                self._issue_cmd(cmd, victim)
            return
        
        if req.is_first_command is True:
            req.is_first_command = False
            device = req.device
            if req.type in [Request.Type.read, Request.Type.write]:
                self.channel.update_serving_requests(req.addr_list, 1, self.cycle_curr)
            
            tx = (self.channel.t_spec.prefetch_size * self.channel.t_spec.channel_width / 8)
            if req.type == Request.Type.read:
                if self.is_row_hit_req(req):
                    self._hits_row_read += 1
                    self._hits_row += 1
                elif self.is_row_open_req(req):
                    self._conflicts_row_read += 1
                    self._conflicts_row += 1
                else:
                    self._misses_row_read += 1
                    self._misses_row += 1
                self._bytes_read += tx
            
            elif req.type == Request.Type.write:
                if self.is_row_hit_req(req):
                    self._hits_row_write += 1
                    self._hits_row += 1
                elif self.is_row_open_req(req):
                    self._conflicts_row_write += 1
                    self._conflicts_row += 1
                else:
                    self._misses_row_write += 1
                    self._misses_row += 1
                self._bytes_write += tx
        
        # issue command on behalf of request
        self._issue_cmd(cmd, self._get_addr_list(cmd, req))
        
        if cmd != self.channel.t_spec.translate[req.type]:
            if self.channel.t_spec.is_opening(cmd):
                # promote the request that caused issuing activation to actq
                self.queue_activate.push_i(req)
                queue.queue_req.remove(req)
            return
        
        # set a future completion time for read requests
        if req.type == Request.Type.read:
            req.cycle_depart = self.cycle_curr + self.channel.t_spec.read_latency
            self.pending_reads.push_i(req)
        
        if req.type == Request.Type.write:
            self.channel.update_serving_requests(req.addr_list, -1, self.cycle_curr)
            req.callback(req)
        
        queue.queue_req.remove(req)
    
    def is_ready_req(self, request: Request):
        cmd = self._get_first_cmd(request)
        return self.channel.check(cmd, request.addr_list, self.cycle_curr)
    
    def is_ready_cmd(self, cmd, addr_list):
        return self.channel.check(cmd, addr_list, self.cycle_curr)
    
    def is_row_hit_req(self, request: Request):
        cmd = self.channel.t_spec.translate[request.type]
        return self.channel.check_row_hit(cmd, request.addr_list)
    
    def is_row_hit_cmd(self, cmd, addr_list):
        return self.channel.check_row_hit(cmd, addr_list)
    
    def is_row_open_req(self, request: Request):
        cmd = self.channel.t_spec.translate[request.type]
        return self.channel.check_row_open(cmd, request.addr_list)
    
    def is_row_open_cmd(self, cmd, addr_list):
        return self.channel.check_row_open(cmd, addr_list)
    
    def is_active(self):
        return self.channel.cur_serving_requests > 0
    
    def is_refresh(self):
        return self.cycle_curr <= self.channel.end_of_refreshing
    
    def set_high_writeq_watermark(self, mark):
        self.wr_high_watermark = mark
    
    def set_low_writeq_watermark(self, mark):
        self.wr_low_watermark = mark
    
    def set_temperature(self, current_temperature):
        return
    
    ###
    
    def _get_first_cmd(self, request: Request):
        cmd = self.channel.t_spec.translate[request.type]
        return self.channel.decode(cmd, request.addr_list)
    
    def _cmd_issue_autoprecharge(self, cmd, addr_list):
        from offchip.schedule import RowPolicy
        if self.channel.t_spec.is_accessing(cmd) and \
                self.row_policy.type == RowPolicy.Type.closedAP:
            # check if it is the last request to the opened row
            queue = self.queue_write if self.write_mode else self.queue_read
            row_group = addr_list[:self.t_spec.level.row.value + 1]
            
            num_row_hits = 0
            
            for req in queue.queue_req:
                if self.is_row_hit_req(req):
                    row_group_2 = req.addr_list[:self.t_spec.level.row.value + 1]
                    if row_group == row_group_2:
                        num_row_hits += 1
            
            if num_row_hits == 0:
                queue = self.queue_activate
                for req in queue.queue_req:
                    if self.is_row_hit_req(req):
                        row_group_2 = req.addr_list[:self.t_spec.level.row.value + 1]
                        raise Exception(row_group, row_group_2)
                        if row_group == row_group_2:
                            num_row_hits += 1
            
            assert num_row_hits > 0  # The current request should be a hit,
            # so there should be at least one request that hits in the current open row
            
            if num_row_hits == 1:
                if cmd == self.t_spec.cmd.rd:
                    cmd = self.t_spec.cmd.rda
                elif cmd == self.t_spec.cmd.wr:
                    cmd = self.t_spec.cmd.wra
                else:
                    raise Exception(cmd)
        return cmd
    
    def _issue_cmd(self, cmd, addr_list):
        # print(cmd, end='')
        cmd = self._cmd_issue_autoprecharge(cmd, addr_list)
        assert self.is_ready_cmd(cmd, addr_list)
        self.channel.update(cmd, addr_list, self.cycle_curr)
        
        if cmd == self.t_spec.cmd.pre:
            if self.row_table.get_hits(addr_list, True) == 0:
                self.useless_activates += 1
        
        self.row_table.update(cmd, addr_list, self.cycle_curr)
    
    @staticmethod
    def _get_addr_list(cmd, req: Request):
        return req.addr_list
    
    def print_state(self):
        print('   queue_read: {}'.format(self.queue_read.size()))
        print('   queue_write: {}'.format(self.queue_write.size()))
        print('   queue_other: {}'.format(self.queue_other.size()))
