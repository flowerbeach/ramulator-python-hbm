from typing import Dict, List
from offchip.dram_spec.spec_data_structure import TimingEntry, SpeedEntry, OrgEntry
from configs import strings


class BaseSpec(object):
    def __init__(self, args):
        self.name_spec = args.name_spec
        assert self.name_spec in strings.list_spec
        
        self._org = args.org
        self._speed = args.speed
        self._num_ranks = args.num_ranks
        self._num_channels = args.num_channels
        
        self.start = {
            level: None for level in strings.dict_list_level_spec[self.name_spec]}
        
        self.prereq = {level: {cmd: None for cmd in strings.dict_list_cmd_spec[self.name_spec]}
                       for level in strings.dict_list_level_spec[self.name_spec]}
        self.rowhit = {level: {cmd: None for cmd in strings.dict_list_cmd_spec[self.name_spec]}
                       for level in strings.dict_list_level_spec[self.name_spec]}
        self.rowopen = {level: {cmd: None for cmd in strings.dict_list_cmd_spec[self.name_spec]}
                        for level in strings.dict_list_level_spec[self.name_spec]}
        self.lambda_ = {level: {cmd: None for cmd in strings.dict_list_cmd_spec[self.name_spec]}
                        for level in strings.dict_list_level_spec[self.name_spec]}
        self.timing = {level: {cmd: [] for cmd in strings.dict_list_cmd_spec[self.name_spec]}
                       for level in strings.dict_list_level_spec[self.name_spec]}  # type: Dict[str:Dict[str:List[TimingEntry]]]
        
        self.org_table = {
            strings.org_1Gb: OrgEntry(1 << 10, 128, [0, 0, 4, 2, 1 << 13, 1 << (6 + 1)]),
            strings.org_2Gb: OrgEntry(2 << 10, 128, [0, 0, 4, 2, 1 << 14, 1 << (6 + 1)]),
            strings.org_4Gb: OrgEntry(4 << 10, 128, [0, 0, 4, 4, 1 << 14, 1 << (6 + 1)])}
        self.org_entry = self.org_table[self._org]
        
        self.speed_table = {
            strings.speed_1Gbps: SpeedEntry(1000, 500, 2.0, 2, 2, 3, 7, 7, 6, 7, 4, 17, 24, 7, 2, 4, 8, 4, 5, 20, 0, 1950, 0, 5, 5, 5, 0)}
        self.speed_entry = self.speed_table[self._speed]
        self.read_latency = self.speed_entry.nCL + self.speed_entry.nBL
        
        self.prefetch_size = 4  # burst length could be 2 and 4 (choose 4 here), 2n prefetch
        self.channel_width = 128
        
        self._init_speed()
        self._init_prereq()
        self._init_rowhit()
        self._init_rowopen()
        self._init_lambda()
        self._init_timing()
    
    @staticmethod
    def is_opening(self, cmd):
        if cmd in [strings.cmd_act]:
            return True
        return False
    
    @staticmethod
    def is_accessing(self, cmd):
        if cmd in [strings.cmd_rd,
                   strings.cmd_wr,
                   strings.cmd_rda,
                   strings.cmd_wra]:
            return True
        return False
    
    @staticmethod
    def is_closing(cmd):
        if cmd in [strings.cmd_pre,
                   strings.cmd_prea,
                   strings.cmd_rda,
                   strings.cmd_wra]:
            return True
        return False
    
    @staticmethod
    def is_refreshing(self, cmd):
        if cmd in [strings.cmd_ref,
                   strings.cmd_refsb]:
            return True
        return False
    
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
        from offchip.memory_module import DRAM
        
        def prereq_rank_rd(node: DRAM, cmd, id_):
            node_state = node.get_state()
            if node_state == strings.state_powerup:
                return '-1'
            elif node_state == strings.state_actpowerdown:
                return strings.cmd_pdx
            elif node_state == strings.state_prepowerdown:
                return strings.cmd_pdx
            elif node_state == strings.state_selfrefresh:
                return strings.cmd_srx
            else:
                raise Exception(node_state)
        
        def prereq_bank_rd(node: DRAM, cmd, id_):
            node_state = node.get_state()
            if node_state == strings.state_closed:
                return strings.cmd_act
            elif node_state == strings.state_opened:
                if id_ in node.row_state:
                    return cmd
                return strings.cmd_pre
            else:
                raise Exception(node_state)
        
        def prereq_rank_ref(node: DRAM, cmd, id_):
            for bg in node.children:
                for bank in bg.children:
                    if bank.get_state() == strings.state_closed:
                        continue
                    return strings.cmd_prea
            return strings.cmd_ref
        
        def prereq_bank_refsb(node: DRAM, cmd, id_):
            if node.get_state() == strings.state_closed:
                return strings.cmd_refsb
            return strings.cmd_pre
        
        def prereq_rank_pde(node: DRAM, cmd, id_):
            node_state = node.get_state()
            if node_state == strings.state_powerup:
                return strings.cmd_pde
            elif node_state == strings.state_actpowerdown:
                return strings.cmd_pde
            elif node_state == strings.state_prepowerdown:
                return strings.cmd_pde
            elif node_state == strings.state_selfrefresh:
                return strings.cmd_srx
            else:
                raise Exception(node_state)
        
        def prereq_rank_sre(node: DRAM, cmd, id_):
            node_state = node.get_state()
            if node_state == strings.state_powerup:
                return strings.cmd_sre
            elif node_state == strings.state_actpowerdown:
                return strings.cmd_pdx
            elif node_state == strings.state_prepowerdown:
                return strings.cmd_pde
            elif node_state == strings.state_selfrefresh:
                return strings.cmd_sre
            else:
                raise Exception(node_state)
        
        self.prereq[strings.level_bank][strings.cmd_rd] = prereq_bank_rd
        self.prereq[strings.level_rank][strings.cmd_rd] = prereq_rank_rd
        self.prereq[strings.level_bank][strings.cmd_wr] = prereq_bank_rd
        self.prereq[strings.level_rank][strings.cmd_wr] = prereq_rank_rd
        
        self.prereq[strings.level_rank][strings.cmd_ref] = prereq_rank_ref
        self.prereq[strings.level_bank][strings.cmd_refsb] = prereq_bank_refsb
        self.prereq[strings.level_rank][strings.cmd_pde] = prereq_rank_pde
        self.prereq[strings.level_rank][strings.cmd_sre] = prereq_rank_sre
    
    def _init_rowhit(self):
        from offchip.memory_module import DRAM
        
        def rowhit(node: DRAM, cmd, id_):
            node_state = node.get_state()
            if node_state == strings.state_closed:
                return False
            elif node_state == strings.state_opened:
                if id_ in node.row_state.keys():
                    return True
                return False
            else:
                raise Exception(node_state)
        
        self.rowhit[strings.level_bank][strings.cmd_rd] = rowhit
        self.rowhit[strings.level_bank][strings.cmd_wr] = rowhit
    
    def _init_rowopen(self):
        from offchip.memory_module import DRAM
        
        def rowopen(node: DRAM, cmd, id_):
            node_state = node.get_state()
            if node_state == strings.state_closed:
                return False
            elif node_state == strings.state_opened:
                return True
            else:
                raise Exception(node_state)
        
        self.rowopen[strings.level_bank][strings.cmd_rd] = rowopen
        self.rowopen[strings.level_bank][strings.cmd_wr] = rowopen
    
    def _init_lambda(self):
        from offchip.memory_module import DRAM
        
        def lambda_bank_act(node: DRAM, id_):
            node.set_state(strings.state_opened)
            node.row_state[id_] = strings.state_opened
        
        def lambda_bank_pre(node: DRAM, id_):
            node.set_state(strings.state_closed)
            node.row_state = {}
        
        def lambda_rank_prea(node: DRAM, id_):
            for bg in node.children:
                for bank in bg.children:
                    bank.set_state(strings.state_closed)
                    bank.row_state = {}
        
        def lambda_rank_ref(node: DRAM, id_):
            return
        
        def lambda_bank_rd(node: DRAM, id_):
            return
        
        def lambda_bank_wr(node: DRAM, id_):
            return
        
        def lambda_rank_pde(node: DRAM, id_):
            for bg in node.children:
                for bank in bg.children:
                    if bank.get_state() == strings.state_closed:
                        continue
                    node.set_state(strings.state_actpowerdown)
                    return
            node.set_state(strings.state_prepowerdown)
        
        def lambda_rank_pdx(node: DRAM, id_):
            node.set_state(strings.state_powerup)
        
        def lambda_rank_sre(node: DRAM, id_):
            node.set_state(strings.state_selfrefresh)
        
        self.lambda_[strings.level_bank][strings.cmd_act] = lambda_bank_act
        self.lambda_[strings.level_bank][strings.cmd_pre] = lambda_bank_pre
        self.lambda_[strings.level_rank][strings.cmd_prea] = lambda_rank_prea
        self.lambda_[strings.level_rank][strings.cmd_ref] = lambda_rank_ref
        self.lambda_[strings.level_bank][strings.cmd_rd] = lambda_bank_rd
        self.lambda_[strings.level_bank][strings.cmd_wr] = lambda_bank_wr
        self.lambda_[strings.level_bank][strings.cmd_rda] = lambda_bank_pre
        self.lambda_[strings.level_bank][strings.cmd_wra] = lambda_bank_pre
        self.lambda_[strings.level_rank][strings.cmd_pde] = lambda_rank_pde
        self.lambda_[strings.level_rank][strings.cmd_pdx] = lambda_rank_pdx
        self.lambda_[strings.level_rank][strings.cmd_sre] = lambda_rank_sre
        self.lambda_[strings.level_rank][strings.cmd_srx] = lambda_rank_pdx
    
    def _init_timing(self):
        s = self.speed_entry
        # Channel
        t = self.timing[strings.level_channel]
        
        # CAS <-> CAS
        t[strings.cmd_rd].append(TimingEntry(strings.cmd_rd, 1, s.nBL))
        t[strings.cmd_rd].append(TimingEntry(strings.cmd_rda, 1, s.nBL))
        t[strings.cmd_rda].append(TimingEntry(strings.cmd_rd, 1, s.nBL))
        t[strings.cmd_rda].append(TimingEntry(strings.cmd_rda, 1, s.nBL))
        t[strings.cmd_wr].append(TimingEntry(strings.cmd_wr, 1, s.nBL))
        t[strings.cmd_wr].append(TimingEntry(strings.cmd_wra, 1, s.nBL))
        t[strings.cmd_wra].append(TimingEntry(strings.cmd_wr, 1, s.nBL))
        t[strings.cmd_wra].append(TimingEntry(strings.cmd_wra, 1, s.nBL))
        
        # Rank
        t = self.timing[strings.level_rank]
        
        # CAS <-> CAS
        t[strings.cmd_rd].append(TimingEntry(strings.cmd_rd, 1, s.nCCDS))
        t[strings.cmd_rd].append(TimingEntry(strings.cmd_rda, 1, s.nCCDS))
        t[strings.cmd_rda].append(TimingEntry(strings.cmd_rd, 1, s.nCCDS))
        t[strings.cmd_rda].append(TimingEntry(strings.cmd_rda, 1, s.nCCDS))
        t[strings.cmd_wr].append(TimingEntry(strings.cmd_wr, 1, s.nCCDS))
        t[strings.cmd_wr].append(TimingEntry(strings.cmd_wra, 1, s.nCCDS))
        t[strings.cmd_wra].append(TimingEntry(strings.cmd_wr, 1, s.nCCDS))
        t[strings.cmd_wra].append(TimingEntry(strings.cmd_wra, 1, s.nCCDS))
        t[strings.cmd_rd].append(TimingEntry(strings.cmd_wr, 1, s.nCL + s.nCCDS + 2 - s.nCWL))
        t[strings.cmd_rd].append(TimingEntry(strings.cmd_wra, 1, s.nCL + s.nCCDS + 2 - s.nCWL))
        t[strings.cmd_rda].append(TimingEntry(strings.cmd_wr, 1, s.nCL + s.nCCDS + 2 - s.nCWL))
        t[strings.cmd_rda].append(TimingEntry(strings.cmd_wra, 1, s.nCL + s.nCCDS + 2 - s.nCWL))
        t[strings.cmd_wr].append(TimingEntry(strings.cmd_rd, 1, s.nCWL + s.nBL + s.nWTRS))
        t[strings.cmd_wr].append(TimingEntry(strings.cmd_rda, 1, s.nCWL + s.nBL + s.nWTRS))
        t[strings.cmd_wra].append(TimingEntry(strings.cmd_rd, 1, s.nCWL + s.nBL + s.nWTRS))
        t[strings.cmd_wra].append(TimingEntry(strings.cmd_rda, 1, s.nCWL + s.nBL + s.nWTRS))
        
        t[strings.cmd_rd].append(TimingEntry(strings.cmd_prea, 1, s.nRTP))
        t[strings.cmd_wr].append(TimingEntry(strings.cmd_prea, 1, s.nCWL + s.nBL + s.nWR))
        
        # CAS <-> PD
        t[strings.cmd_rd].append(TimingEntry(strings.cmd_pde, 1, s.nCL + s.nBL + 1))
        t[strings.cmd_rda].append(TimingEntry(strings.cmd_pde, 1, s.nCL + s.nBL + 1))
        t[strings.cmd_wr].append(TimingEntry(strings.cmd_pde, 1, s.nCWL + s.nBL + s.nWR))
        t[strings.cmd_wra].append(TimingEntry(strings.cmd_pde, 1, s.nCWL + s.nBL + s.nWR + 1))  # +1 for pre
        t[strings.cmd_pdx].append(TimingEntry(strings.cmd_rd, 1, s.nXP))
        t[strings.cmd_pdx].append(TimingEntry(strings.cmd_rda, 1, s.nXP))
        t[strings.cmd_pdx].append(TimingEntry(strings.cmd_wr, 1, s.nXP))
        t[strings.cmd_pdx].append(TimingEntry(strings.cmd_wra, 1, s.nXP))
        
        # CAS <-> SR: none(all banks have to be pre-charged)
        
        # RAS <-> RAS
        t[strings.cmd_act].append(TimingEntry(strings.cmd_act, 1, s.nRRDS))
        t[strings.cmd_act].append(TimingEntry(strings.cmd_act, 4, s.nFAW))
        t[strings.cmd_act].append(TimingEntry(strings.cmd_prea, 1, s.nRAS))
        t[strings.cmd_prea].append(TimingEntry(strings.cmd_act, 1, s.nRP))
        
        # RAS <-> REF
        t[strings.cmd_pre].append(TimingEntry(strings.cmd_ref, 1, s.nRP))
        t[strings.cmd_prea].append(TimingEntry(strings.cmd_ref, 1, s.nRP))
        t[strings.cmd_ref].append(TimingEntry(strings.cmd_act, 1, s.nRFC))
        
        # RAS <-> PD
        t[strings.cmd_act].append(TimingEntry(strings.cmd_pde, 1, 1))
        t[strings.cmd_pdx].append(TimingEntry(strings.cmd_act, 1, s.nXP))
        t[strings.cmd_pdx].append(TimingEntry(strings.cmd_pre, 1, s.nXP))
        t[strings.cmd_pdx].append(TimingEntry(strings.cmd_prea, 1, s.nXP))
        
        # RAS <-> SR
        t[strings.cmd_pre].append(TimingEntry(strings.cmd_sre, 1, s.nRP))
        t[strings.cmd_prea].append(TimingEntry(strings.cmd_sre, 1, s.nRP))
        t[strings.cmd_srx].append(TimingEntry(strings.cmd_act, 1, s.nXS))
        
        # REF <-> REF
        t[strings.cmd_ref].append(TimingEntry(strings.cmd_ref, 1, s.nRFC))
        
        # REF <-> PD
        t[strings.cmd_ref].append(TimingEntry(strings.cmd_pde, 1, 1))
        t[strings.cmd_pdx].append(TimingEntry(strings.cmd_ref, 1, s.nXP))
        
        # REF <-> SR
        t[strings.cmd_srx].append(TimingEntry(strings.cmd_ref, 1, s.nXS))
        
        # PD <-> PD
        t[strings.cmd_pde].append(TimingEntry(strings.cmd_pdx, 1, s.nPD))
        t[strings.cmd_pdx].append(TimingEntry(strings.cmd_pde, 1, s.nXP))
        
        # PD <-> SR
        t[strings.cmd_pdx].append(TimingEntry(strings.cmd_sre, 1, s.nXP))
        t[strings.cmd_srx].append(TimingEntry(strings.cmd_pde, 1, s.nXS))
        
        # SR <-> SR
        t[strings.cmd_sre].append(TimingEntry(strings.cmd_srx, 1, s.nCKESR))
        t[strings.cmd_srx].append(TimingEntry(strings.cmd_sre, 1, s.nXS))
        
        # Bank Group
        t = self.timing[strings.level_bankgroup]
        # CAS <-> CAS
        t[strings.cmd_rd].append(TimingEntry(strings.cmd_rd, 1, s.nCCDL))
        t[strings.cmd_rd].append(TimingEntry(strings.cmd_rda, 1, s.nCCDL))
        t[strings.cmd_rda].append(TimingEntry(strings.cmd_rd, 1, s.nCCDL))
        t[strings.cmd_rda].append(TimingEntry(strings.cmd_rda, 1, s.nCCDL))
        t[strings.cmd_wr].append(TimingEntry(strings.cmd_wr, 1, s.nCCDL))
        t[strings.cmd_wr].append(TimingEntry(strings.cmd_wra, 1, s.nCCDL))
        t[strings.cmd_wra].append(TimingEntry(strings.cmd_wr, 1, s.nCCDL))
        t[strings.cmd_wra].append(TimingEntry(strings.cmd_wra, 1, s.nCCDL))
        t[strings.cmd_wr].append(TimingEntry(strings.cmd_wr, 1, s.nCCDL))
        t[strings.cmd_wr].append(TimingEntry(strings.cmd_wra, 1, s.nCCDL))
        t[strings.cmd_wra].append(TimingEntry(strings.cmd_wr, 1, s.nCCDL))
        t[strings.cmd_wra].append(TimingEntry(strings.cmd_wra, 1, s.nCCDL))
        t[strings.cmd_wr].append(TimingEntry(strings.cmd_rd, 1, s.nCWL + s.nBL + s.nWTRL))
        t[strings.cmd_wr].append(TimingEntry(strings.cmd_rda, 1, s.nCWL + s.nBL + s.nWTRL))
        t[strings.cmd_wra].append(TimingEntry(strings.cmd_rd, 1, s.nCWL + s.nBL + s.nWTRL))
        t[strings.cmd_wra].append(TimingEntry(strings.cmd_rda, 1, s.nCWL + s.nBL + s.nWTRL))
        
        # RAS <-> RAS
        t[strings.cmd_act].append(TimingEntry(strings.cmd_act, 1, s.nRRDL))
        
        # Bank
        t = self.timing[strings.level_bank]
        
        # CAS <-> RAS
        t[strings.cmd_act].append(TimingEntry(strings.cmd_rd, 1, s.nRCDR))
        t[strings.cmd_act].append(TimingEntry(strings.cmd_rda, 1, s.nRCDR))
        t[strings.cmd_act].append(TimingEntry(strings.cmd_wr, 1, s.nRCDW))
        t[strings.cmd_act].append(TimingEntry(strings.cmd_wra, 1, s.nRCDW))
        
        t[strings.cmd_rd].append(TimingEntry(strings.cmd_pre, 1, s.nRTP))
        t[strings.cmd_wr].append(TimingEntry(strings.cmd_pre, 1, s.nCWL + s.nBL + s.nWR))
        
        t[strings.cmd_rda].append(TimingEntry(strings.cmd_act, 1, s.nRTP + s.nRP))
        t[strings.cmd_wra].append(TimingEntry(strings.cmd_act, 1, s.nCWL + s.nBL + s.nWR + s.nRP))
        
        # RAS <-> RAS
        t[strings.cmd_act].append(TimingEntry(strings.cmd_act, 1, s.nRC))
        t[strings.cmd_act].append(TimingEntry(strings.cmd_pre, 1, s.nRAS))
        t[strings.cmd_pre].append(TimingEntry(strings.cmd_act, 1, s.nRP))
        
        # REFSB
        t[strings.cmd_pre].append(TimingEntry(strings.cmd_refsb, 1, s.nRP))
        t[strings.cmd_refsb].append(TimingEntry(strings.cmd_refsb, 1, s.nRFC))
        t[strings.cmd_refsb].append(TimingEntry(strings.cmd_act, 1, s.nRFC))
