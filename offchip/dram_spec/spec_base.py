from offchip.dram_spec.spec_data_structure import TimingEntry, SpeedEntry, OrgEntry
from offchip.memory_module import DRAM
from configs import strings


class BaseSpec(object):
    def __init__(self, args):
        self.name_spec = args.name_spec
        assert self.name_spec in strings.list_str_spec
        
        self._org = args.org
        self._speed = args.speed
        self._num_ranks = args.num_ranks
        self._num_channels = args.num_channels
        
        self.start = {
            level: None for level in strings.dict_list_level_spec[self.name_spec]}
        
        self.prereq = {level: {cmd: [TimingEntry()] for cmd in strings.dict_list_cmd_spec[self.name_spec]}
                       for level in strings.dict_list_level_spec[self.name_spec]}
        self.rowhit = {level: {cmd: [TimingEntry()] for cmd in strings.dict_list_cmd_spec[self.name_spec]}
                       for level in strings.dict_list_level_spec[self.name_spec]}
        self.rowopen ={level: {cmd: [TimingEntry()] for cmd in strings.dict_list_cmd_spec[self.name_spec]}
                       for level in strings.dict_list_level_spec[self.name_spec]}
        self.lambda_ = {level: {cmd: [TimingEntry()] for cmd in strings.dict_list_cmd_spec[self.name_spec]}
                        for level in strings.dict_list_level_spec[self.name_spec]}
        self.timing = {level: {cmd: [TimingEntry()] for cmd in strings.dict_list_cmd_spec[self.name_spec]}
                       for level in strings.dict_list_level_spec[self.name_spec]}
        
        self.org_table = {
            strings.str_org_1Gb: OrgEntry(1 << 10, 128, [0, 0, 4, 2, 1 << 13, 1 << (6 + 1)]),
            strings.str_org_2Gb: OrgEntry(2 << 10, 128, [0, 0, 4, 2, 1 << 14, 1 << (6 + 1)]),
            strings.str_org_4Gb: OrgEntry(4 << 10, 128, [0, 0, 4, 4, 1 << 14, 1 << (6 + 1)])}
        self.org_entry = self.org_table[self._org]
        
        self.speed_table = {
            strings.str_speed_1Gbps: SpeedEntry(1000, 500, 2.0, 2, 2, 3, 7, 7, 6, 7, 4, 17, 24, 7, 2, 4, 8, 4, 5, 20, 0, 1950, 0, 5, 5, 5, 0)}
        self.speed_entry = self.speed_table[self._speed]
        self.read_latency = self.speed_entry.nCL + self.speed_entry.nBL
        
        self._init_speed()
        self._init_prereq()
        self._init_rowhit()
        self._init_rowopen()
        self._init_lambda()
        self._init_timing()
    
    def _init_speed(self):
        RFC_TABLE = [55, 80, 130]
        REFI1B_TABLE = [64, 128, 256]
        XS_TABLE = [60, 85, 135]
        
        if self.speed_entry.rate == 1000:
            speed = 0
        else:
            raise Exception(self.speed_entry.rate)
        if self.org_entry.size >> 10 == 1:
            density = 0
        elif self.org_entry.size >> 10 == 2:
            density = 1
        elif self.org_entry.size >> 10 == 4:
            density = 2
        else:
            raise Exception(self.org_entry.size)
        len_speed = len(self.speed_table)
        self.speed_entry.nRFC = RFC_TABLE[speed * len_speed + density]
        self.speed_entry.nREFI1B = REFI1B_TABLE[speed * len_speed + density]
        self.speed_entry.nXS = XS_TABLE[speed * len_speed + density]
    
    def _init_lambda(self):
        pass
    
    def _init_prereq(self):
        pass
    
    def _init_rowhit(self):
        
        def rowhit(node: DRAM):
            node_state = node.get_state()
            if node_state == strings.str_state_closed:
                return False
            elif node_state == strings.str_state_opened:
                return True
            else:
                raise Exception(node_state)
        
        self.rowhit[strings.str_level_bank] = rowhit
    
    def _init_rowopen(self):
        def rowopen(node: DRAM):
            node_state = node.get_state()
            if node_state == strings.str_state_closed:
                return False
            elif node_state == strings.str_state_opened:
                return True
            else:
                raise Exception(node_state)
        
        self.rowopen[strings.str_level_bank] = rowopen
    
    def _init_timing(self):
        pass
