import os
from configs import strings


class Trace(object):
    def __init__(self, trace_filename):
        if not os.path.exists(trace_filename):
            raise Exception('File {} does not exist.'.format(trace_filename))
        
        self.ptr_line_next = 0
        self.list_trace = []
        with open(trace_filename, 'r') as f:
            self.list_trace = f.readlines()
    
    def get_trace_request(self):
        end, req_addr, req_type = True, None, None
        if self.ptr_line_next >= len(self.list_trace):
            return end, req_addr, req_type
        
        line = self.list_trace[self.ptr_line_next].strip()
        items = line.split(' ')
        req_addr = items[0]  # todo from 16 to 10
        if items[1] == 'R':
            req_type = strings.str_req_type_read
        elif items[1] == 'W':
            req_type = strings.str_req_type_write
        else:
            raise Exception('"{}"'.format(items[1]))
        return end, req_addr, req_type


class Request(object):
    def __init__(self, addr, type_, device):
        self.is_first_command = True  # todo why?
        self.device = device
        self.type = type_
        self.addr = addr
        # self.addr_list = []  # todo for what?
        
        if type_ not in strings.list_str_type_all:
            raise Exception(type_)
        
        self.arrive = -1
        self.depart = -1
