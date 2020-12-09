import os
from typing import List
from enum import Enum, unique


class Trace(object):
    def __init__(self, trace_filename):
        self.ptr_line_next = 0
        self.list_trace = []
        if not os.path.exists(trace_filename):
            raise Exception('File {} does not exist.'.format(trace_filename))
        with open(trace_filename, 'r') as f:
            self.list_trace = f.readlines()
        self.dict_RW2string = {'R': Request.Type.read,
                               'W': Request.Type.write}
    
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
    @unique
    class Type(Enum):
        read = 'read'
        write = 'write'
        refresh = 'refresh'
        powerdown = 'powerdown'
        selfrefresh = 'selfrefresh'
        extension = 'extension'
    
    def __init__(self, addr, type_, device='', callback=None):
        self.device = device  # type: str
        self.type = type_  # type: str
        self.addr_int = -1  # type: int
        self.addr_list = []  # type: List[int]
        self.is_first_command = True
        
        if callback is None:
            
            def cb(req):
                return req
            
            self.callback = cb
        else:
            self.callback = callback
        
        if type(addr) == int:
            self.addr_int = addr
        elif type(addr) == list:
            self.addr_list = addr
        else:
            raise Exception(addr)
        
        self.cycle_arrive = None  # type: int
        self.cycle_depart = None  # type: int
        
        if type_ not in self.Type:
            raise Exception(type_)
    
    def print(self):
        print('{} {}:'.format(self.device, self.type), self.addr_list)
        print('arrive: {}, depart: {}'.format(self.cycle_arrive, self.cycle_depart))
