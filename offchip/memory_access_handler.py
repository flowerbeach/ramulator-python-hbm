# from configs import strings

class MemoryAccessHandler(object):
    options = {}
    flag_stall = False
    flag_end = False
    
    num_reads = 0
    num_writes = 0
    num_cycles = 0
    
    latency = {}
    read_complele = []  # todo for what ?
    
    @staticmethod
    def initialize(args_, ctrls):
        pass
    
    @staticmethod
    def have_pending_requests():
        pass
    
    @staticmethod
    def send(request):
        pass
    
    @staticmethod
    def cycle():
        pass
    
    @staticmethod
    def finish():
        pass
    
    @staticmethod
    def set_high_writeq_watermark(mark):
        pass
