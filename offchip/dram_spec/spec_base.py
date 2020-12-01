from typing import Dict, List
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
        self.rowopen = {level: {cmd: [TimingEntry()] for cmd in strings.dict_list_cmd_spec[self.name_spec]}
                        for level in strings.dict_list_level_spec[self.name_spec]}
        self.lambda_ = {level: {cmd: [TimingEntry()] for cmd in strings.dict_list_cmd_spec[self.name_spec]}
                        for level in strings.dict_list_level_spec[self.name_spec]}
        self.timing = {level: {cmd: [] for cmd in strings.dict_list_cmd_spec[self.name_spec]}
                       for level in strings.dict_list_level_spec[self.name_spec]}  # type: Dict[str:Dict[str:List[TimingEntry]]]
        
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
    
    def _init_prereq(self):
        def prereq_rank_rd(node: DRAM, cmd, id_):
            node_state = node.get_state()
            if node_state == strings.str_state_powerup:
                return '-1'
            elif node_state == strings.str_state_actpowerdown:
                return strings.str_cmd_pdx
            elif node_state == strings.str_state_prepowerdown:
                return strings.str_cmd_pdx
            elif node_state == strings.str_state_selfrefresh:
                return strings.str_cmd_srx
            else:
                raise Exception(node_state)
        
        def prereq_bank_rd(node: DRAM, cmd, id_):
            node_state = node.get_state()
            if node_state == strings.str_state_closed:
                return strings.str_cmd_act
            elif node_state == strings.str_state_opened:
                if id_ in node.row_state:
                    return cmd
                return strings.str_cmd_pre
            else:
                raise Exception(node_state)
        
        def prereq_rank_ref(node: DRAM, cmd, id_):
            for bg in node.children:
                for bank in bg.children:
                    if bank.get_state() == strings.str_state_closed:
                        continue
                    return strings.str_cmd_prea
            return strings.str_cmd_ref
        
        def prereq_bank_refsb(node: DRAM, cmd, id_):
            if node.get_state() == strings.str_state_closed:
                return strings.str_cmd_refsb
            return strings.str_cmd_pre
        
        def prereq_rank_pde(node: DRAM, cmd, id_):
            node_state = node.get_state()
            if node_state == strings.str_state_powerup:
                return strings.str_cmd_pde
            elif node_state == strings.str_state_actpowerdown:
                return strings.str_cmd_pde
            elif node_state == strings.str_state_prepowerdown:
                return strings.str_cmd_pde
            elif node_state == strings.str_state_selfrefresh:
                return strings.str_cmd_srx
            else:
                raise Exception(node_state)
        
        def prereq_rank_sre(node: DRAM, cmd, id_):
            node_state = node.get_state()
            if node_state == strings.str_state_powerup:
                return strings.str_cmd_sre
            elif node_state == strings.str_state_actpowerdown:
                return strings.str_cmd_pdx
            elif node_state == strings.str_state_prepowerdown:
                return strings.str_cmd_pde
            elif node_state == strings.str_state_selfrefresh:
                return strings.str_cmd_sre
            else:
                raise Exception(node_state)
        
        self.prereq[strings.str_level_bank][strings.str_cmd_rd] = prereq_bank_rd
        self.prereq[strings.str_level_rank][strings.str_cmd_rd] = prereq_rank_rd
        self.prereq[strings.str_level_bank][strings.str_cmd_wr] = prereq_bank_rd
        self.prereq[strings.str_level_rank][strings.str_cmd_wr] = prereq_rank_rd
        
        self.prereq[strings.str_level_rank][strings.str_cmd_ref] = prereq_rank_ref
        self.prereq[strings.str_level_bank][strings.str_cmd_refsb] = prereq_bank_refsb
        self.prereq[strings.str_level_rank][strings.str_cmd_pde] = prereq_rank_pde
        self.prereq[strings.str_level_rank][strings.str_cmd_sre] = prereq_rank_sre
    
    def _init_rowhit(self):
        def rowhit(node: DRAM, cmd, id_):
            node_state = node.get_state()
            if node_state == strings.str_state_closed:
                return False
            elif node_state == strings.str_state_opened:
                if id_ in node.row_state.keys():
                    return True
                return False
            else:
                raise Exception(node_state)
        
        self.rowhit[strings.str_level_bank][strings.str_cmd_rd] = rowhit
        self.rowhit[strings.str_level_bank][strings.str_cmd_wr] = rowhit
    
    def _init_rowopen(self):
        def rowopen(node: DRAM, cmd, id_):
            node_state = node.get_state()
            if node_state == strings.str_state_closed:
                return False
            elif node_state == strings.str_state_opened:
                return True
            else:
                raise Exception(node_state)
        
        self.rowopen[strings.str_level_bank][strings.str_cmd_rd] = rowopen
        self.rowopen[strings.str_level_bank][strings.str_cmd_wr] = rowopen
    
    def _init_lambda(self):
        
        def lambda_bank_act(node: DRAM, cmd, id_):
            node.set_state(strings.str_state_opened)
            node.row_state[id_] = strings.str_state_opened
        
        def lambda_bank_pre(node: DRAM, cmd, id_):
            node.set_state(strings.str_state_closed)
            node.row_state = {}
        
        def lambda_rank_prea(node: DRAM, cmd, id_):
            for bg in node.children:
                for bank in bg.children:
                    bank.set_state(strings.str_state_closed)
                    bank.row_state = {}
        
        def lambda_rank_ref(node: DRAM, cmd, id_):
            return
        
        def lambda_bank_rd(node: DRAM, cmd, id_):
            return
        
        def lambda_bank_wr(node: DRAM, cmd, id_):
            return
        
        def lambda_rank_pde(node: DRAM, cmd, id_):
            for bg in node.children:
                for bank in bg.children:
                    if bank.get_state() == strings.str_state_closed:
                        continue
                    node.set_state(strings.str_state_actpowerdown)
                    return
            node.set_state(strings.str_state_prepowerdown)
        
        def lambda_rank_pdx(node: DRAM, cmd, id_):
            node.set_state(strings.str_state_powerup)
        
        def lambda_rank_sre(node: DRAM, cmd, id_):
            node.set_state(strings.str_state_selfrefresh)
        
        self.lambda_[strings.str_level_bank][strings.str_cmd_act] = lambda_bank_act
        self.lambda_[strings.str_level_bank][strings.str_cmd_pre] = lambda_bank_pre
        self.lambda_[strings.str_level_rank][strings.str_cmd_prea] = lambda_rank_prea
        self.lambda_[strings.str_level_rank][strings.str_cmd_ref] = lambda_rank_ref
        self.lambda_[strings.str_level_bank][strings.str_cmd_rd] = lambda_bank_rd
        self.lambda_[strings.str_level_bank][strings.str_cmd_wr] = lambda_bank_wr
        self.lambda_[strings.str_level_bank][strings.str_cmd_rda] = lambda_bank_pre
        self.lambda_[strings.str_level_bank][strings.str_cmd_wra] = lambda_bank_pre
        self.lambda_[strings.str_level_rank][strings.str_cmd_pde] = lambda_rank_pde
        self.lambda_[strings.str_level_rank][strings.str_cmd_pdx] = lambda_rank_pdx
        self.lambda_[strings.str_level_rank][strings.str_cmd_sre] = lambda_rank_sre
        self.lambda_[strings.str_level_rank][strings.str_cmd_srx] = lambda_rank_pdx
    
    def _init_timing(self):
        pass  # todo
