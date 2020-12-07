import os
from configs import strings
from typing import List


class Trace(object):
    def __init__(self, trace_filename):
        self.ptr_line_next = 0
        self.list_trace = []
        if not os.path.exists(trace_filename):
            raise Exception('File {} does not exist.'.format(trace_filename))
        with open(trace_filename, 'r') as f:
            self.list_trace = f.readlines()
        self.dict_RW2string = {'R': strings.req_type_read,
                               'W': strings.req_type_write}
    
    def get_trace_request(self):
        end, request = True, None
        if self.ptr_line_next >= len(self.list_trace):
            return end, request
        
        end = False
        line = self.list_trace[self.ptr_line_next].strip()
        items = line.split(' ')
        req_addr = int(items[0][2:], 16)
        req_type = self.dict_RW2string[items[1]]
        request = Request(req_addr, req_type)
        
        self.ptr_line_next += 1
        return end, request


class Request(object):
    def __init__(self, addr_int, type_, device='None'):
        self.type = type_  # type: str
        self.device = device  # type: str
        self.addr_int = addr_int  # type: int
        
        self.is_first_command = True  # todo why?
        self.addr_list = []  # type: List[int]
        
        self.arrive = None  # type: int
        self.depart = None  # type: int
        
        if type_ not in strings.list_req_type_all:
            raise Exception(type_)
    
    def print(self):
        print('{} {}:'.format(self.device, self.type), self.addr_list)
        print('arrive: {}, depart: {}'.format(self.arrive, self.depart))
