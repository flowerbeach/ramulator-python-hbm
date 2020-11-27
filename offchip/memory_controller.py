class Controller(object):
    def __init__(self, args_, dram):
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
        
        # public
        self.num_cycles = 0
        self.channel = None
        self.scheduler = None
        self.rowpolicy = None
        self.rowtable = None
        self.refresh = None
        
        self.queue_read = []
        self.queue_write = []
        self.queue_activate = []
        # read and write requests for which activate was issued are moved to
        # actq, which has higher priority than readq and writeq.
        # This is an optimization for avoiding useless activations (i.e., PRECHARGE
        # after ACTIVATE w/o READ of WRITE command)
        self.queue_other = []  # queue for all "other" requests (e.g., refresh)
        
        self.pending_reads = []  # read requests that are about to receive data from DRAM
        self.write_mode = False
        
        self.wr_high_watermark = 0.8
        self.wr_low_watermark = 0.2
        
        self.initialize()
    
    def initialize(self):
        pass
    
    def finish(self):
        pass
    
    def get_queue(self):
        pass
    
    def enqueue(self):
        pass
    
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
    
    def set_high_writeq_watermark(self):
        pass
    
    def set_low_writeq_watermark(self):
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
