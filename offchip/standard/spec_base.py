from typing import Dict, List
from offchip.standard.spec_data_structure import TimingEntry, SpeedEntry, OrgEntry
from configs import strings
from enum import Enum, unique


class BaseSpec(object):
    @unique
    class cmd(Enum):
        act = 0
        pre = 1
        prea = 2
        rd = 3
        rda = 4
        wr = 5
        wra = 6
        ref = 7
        refsb = 8
        pde = 9
        pdx = 10
        sre = 11
        srx = 12
    
    @unique
    class level(Enum):
        channel = 0
        rank = 1
        bankgroup = 2
        bank = 3
        row = 4
        column = 5
    
    def __init__(self, args):
        self.name_spec = args.name_spec
        assert self.name_spec in strings.standard
        
        self._org = args.org
        self._speed = args.speed
        self._num_ranks = args.num_ranks
        self._num_channels = args.num_channels
        
        self.start = {level: None for level in self.level}
        
        self.prereq = {level: {cmd: None for cmd in self.cmd} for level in self.level}
        self.rowhit = {level: {cmd: None for cmd in self.cmd} for level in self.level}
        self.rowopen = {level: {cmd: None for cmd in self.cmd} for level in self.level}
        self.lambda_ = {level: {cmd: None for cmd in self.cmd} for level in self.level}
        self.timing = {level: {cmd: [] for cmd in self.cmd} for level in self.level
                       }  # type: Dict[str,Dict[str,List[TimingEntry]]]
        
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
        
        self.scope = [
            self.level.row, self.level.bank, self.level.rank,
            self.level.column, self.level.column, self.level.column, self.level.column,
            self.level.rank, self.level.bank, self.level.rank, self.level.rank, self.level.rank, self.level.rank
        ]
        
        from offchip.data_structure import Request
        self.translate = {Request.Type.read: self.cmd.rd,
                          Request.Type.write: self.cmd.wr,
                          Request.Type.refresh: self.cmd.ref,
                          Request.Type.powerdown: self.cmd.pde,
                          Request.Type.selfrefresh: self.cmd.sre}
        
        self._init_speed()
        self._init_prereq()
        self._init_rowhit()
        self._init_rowopen()
        self._init_lambda()
        self._init_timing()
    
    @staticmethod
    def is_opening(cmd):
        if cmd in [BaseSpec.cmd.act]:
            return True
        return False
    
    @staticmethod
    def is_accessing(cmd):
        if cmd in [BaseSpec.cmd.rd,
                   BaseSpec.cmd.wr,
                   BaseSpec.cmd.rda,
                   BaseSpec.cmd.wra]:
            return True
        return False
    
    @staticmethod
    def is_closing(cmd):
        if cmd in [BaseSpec.cmd.pre,
                   BaseSpec.cmd.prea,
                   BaseSpec.cmd.rda,
                   BaseSpec.cmd.wra]:
            return True
        return False
    
    @staticmethod
    def is_refreshing(cmd):
        if cmd in [BaseSpec.cmd.ref,
                   BaseSpec.cmd.refsb]:
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
        from offchip.dram_module import DRAM
        
        def prereq_rank_rd(node: DRAM, cmd, id_):
            node_state = node.get_state()
            if node_state == strings.state_powerup:
                return '-1'
            elif node_state == strings.state_actpowerdown:
                return self.cmd.pdx
            elif node_state == strings.state_prepowerdown:
                return self.cmd.pdx
            elif node_state == strings.state_selfrefresh:
                return self.cmd.srx
            else:
                raise Exception(node_state)
        
        def prereq_bank_rd(node: DRAM, cmd, id_):
            node_state = node.get_state()
            if node_state == strings.state_closed:
                return self.cmd.act
            elif node_state == strings.state_opened:
                if id_ in node.row_state:
                    return cmd
                return self.cmd.pre
            else:
                raise Exception(node_state)
        
        def prereq_rank_ref(node: DRAM, cmd, id_):
            for bg in node.children:
                for bank in bg.children:
                    if bank.get_state() == strings.state_closed:
                        continue
                    return self.cmd.prea
            return self.cmd.ref
        
        def prereq_bank_refsb(node: DRAM, cmd, id_):
            if node.get_state() == strings.state_closed:
                return self.cmd.refsb
            return self.cmd.pre
        
        def prereq_rank_pde(node: DRAM, cmd, id_):
            node_state = node.get_state()
            if node_state == strings.state_powerup:
                return self.cmd.pde
            elif node_state == strings.state_actpowerdown:
                return self.cmd.pde
            elif node_state == strings.state_prepowerdown:
                return self.cmd.pde
            elif node_state == strings.state_selfrefresh:
                return self.cmd.srx
            else:
                raise Exception(node_state)
        
        def prereq_rank_sre(node: DRAM, cmd, id_):
            node_state = node.get_state()
            if node_state == strings.state_powerup:
                return self.cmd.sre
            elif node_state == strings.state_actpowerdown:
                return self.cmd.pdx
            elif node_state == strings.state_prepowerdown:
                return self.cmd.pde
            elif node_state == strings.state_selfrefresh:
                return self.cmd.sre
            else:
                raise Exception(node_state)
        
        self.prereq[self.level.bank][self.cmd.rd] = prereq_bank_rd
        self.prereq[self.level.rank][self.cmd.rd] = prereq_rank_rd
        self.prereq[self.level.bank][self.cmd.wr] = prereq_bank_rd
        self.prereq[self.level.rank][self.cmd.wr] = prereq_rank_rd
        
        self.prereq[self.level.rank][self.cmd.ref] = prereq_rank_ref
        self.prereq[self.level.bank][self.cmd.refsb] = prereq_bank_refsb
        self.prereq[self.level.rank][self.cmd.pde] = prereq_rank_pde
        self.prereq[self.level.rank][self.cmd.sre] = prereq_rank_sre
    
    def _init_rowhit(self):
        from offchip.dram_module import DRAM
        
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
        
        self.rowhit[self.level.bank][self.cmd.rd] = rowhit
        self.rowhit[self.level.bank][self.cmd.wr] = rowhit
    
    def _init_rowopen(self):
        from offchip.dram_module import DRAM
        
        def rowopen(node: DRAM, cmd, id_):
            node_state = node.get_state()
            if node_state == strings.state_closed:
                return False
            elif node_state == strings.state_opened:
                return True
            else:
                raise Exception(node_state)
        
        self.rowopen[self.level.bank][self.cmd.rd] = rowopen
        self.rowopen[self.level.bank][self.cmd.wr] = rowopen
    
    def _init_lambda(self):
        from offchip.dram_module import DRAM
        
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
        
        self.lambda_[self.level.bank][self.cmd.act] = lambda_bank_act
        self.lambda_[self.level.bank][self.cmd.pre] = lambda_bank_pre
        self.lambda_[self.level.rank][self.cmd.prea] = lambda_rank_prea
        self.lambda_[self.level.rank][self.cmd.ref] = lambda_rank_ref
        self.lambda_[self.level.bank][self.cmd.rd] = lambda_bank_rd
        self.lambda_[self.level.bank][self.cmd.wr] = lambda_bank_wr
        self.lambda_[self.level.bank][self.cmd.rda] = lambda_bank_pre
        self.lambda_[self.level.bank][self.cmd.wra] = lambda_bank_pre
        self.lambda_[self.level.rank][self.cmd.pde] = lambda_rank_pde
        self.lambda_[self.level.rank][self.cmd.pdx] = lambda_rank_pdx
        self.lambda_[self.level.rank][self.cmd.sre] = lambda_rank_sre
        self.lambda_[self.level.rank][self.cmd.srx] = lambda_rank_pdx
    
    def _init_timing(self):
        s = self.speed_entry
        # Channel
        t = self.timing[self.level.channel]
        
        # CAS <-> CAS
        t[self.cmd.rd].append(TimingEntry(self.cmd.rd, 1, s.nBL))
        t[self.cmd.rd].append(TimingEntry(self.cmd.rda, 1, s.nBL))
        t[self.cmd.rda].append(TimingEntry(self.cmd.rd, 1, s.nBL))
        t[self.cmd.rda].append(TimingEntry(self.cmd.rda, 1, s.nBL))
        t[self.cmd.wr].append(TimingEntry(self.cmd.wr, 1, s.nBL))
        t[self.cmd.wr].append(TimingEntry(self.cmd.wra, 1, s.nBL))
        t[self.cmd.wra].append(TimingEntry(self.cmd.wr, 1, s.nBL))
        t[self.cmd.wra].append(TimingEntry(self.cmd.wra, 1, s.nBL))
        
        # Rank
        t = self.timing[self.level.rank]
        
        # CAS <-> CAS
        t[self.cmd.rd].append(TimingEntry(self.cmd.rd, 1, s.nCCDS))
        t[self.cmd.rd].append(TimingEntry(self.cmd.rda, 1, s.nCCDS))
        t[self.cmd.rda].append(TimingEntry(self.cmd.rd, 1, s.nCCDS))
        t[self.cmd.rda].append(TimingEntry(self.cmd.rda, 1, s.nCCDS))
        t[self.cmd.wr].append(TimingEntry(self.cmd.wr, 1, s.nCCDS))
        t[self.cmd.wr].append(TimingEntry(self.cmd.wra, 1, s.nCCDS))
        t[self.cmd.wra].append(TimingEntry(self.cmd.wr, 1, s.nCCDS))
        t[self.cmd.wra].append(TimingEntry(self.cmd.wra, 1, s.nCCDS))
        t[self.cmd.rd].append(TimingEntry(self.cmd.wr, 1, s.nCL + s.nCCDS + 2 - s.nCWL))
        t[self.cmd.rd].append(TimingEntry(self.cmd.wra, 1, s.nCL + s.nCCDS + 2 - s.nCWL))
        t[self.cmd.rda].append(TimingEntry(self.cmd.wr, 1, s.nCL + s.nCCDS + 2 - s.nCWL))
        t[self.cmd.rda].append(TimingEntry(self.cmd.wra, 1, s.nCL + s.nCCDS + 2 - s.nCWL))
        t[self.cmd.wr].append(TimingEntry(self.cmd.rd, 1, s.nCWL + s.nBL + s.nWTRS))
        t[self.cmd.wr].append(TimingEntry(self.cmd.rda, 1, s.nCWL + s.nBL + s.nWTRS))
        t[self.cmd.wra].append(TimingEntry(self.cmd.rd, 1, s.nCWL + s.nBL + s.nWTRS))
        t[self.cmd.wra].append(TimingEntry(self.cmd.rda, 1, s.nCWL + s.nBL + s.nWTRS))
        
        t[self.cmd.rd].append(TimingEntry(self.cmd.prea, 1, s.nRTP))
        t[self.cmd.wr].append(TimingEntry(self.cmd.prea, 1, s.nCWL + s.nBL + s.nWR))
        
        # CAS <-> PD
        t[self.cmd.rd].append(TimingEntry(self.cmd.pde, 1, s.nCL + s.nBL + 1))
        t[self.cmd.rda].append(TimingEntry(self.cmd.pde, 1, s.nCL + s.nBL + 1))
        t[self.cmd.wr].append(TimingEntry(self.cmd.pde, 1, s.nCWL + s.nBL + s.nWR))
        t[self.cmd.wra].append(TimingEntry(self.cmd.pde, 1, s.nCWL + s.nBL + s.nWR + 1))  # +1 for pre
        t[self.cmd.pdx].append(TimingEntry(self.cmd.rd, 1, s.nXP))
        t[self.cmd.pdx].append(TimingEntry(self.cmd.rda, 1, s.nXP))
        t[self.cmd.pdx].append(TimingEntry(self.cmd.wr, 1, s.nXP))
        t[self.cmd.pdx].append(TimingEntry(self.cmd.wra, 1, s.nXP))
        
        # CAS <-> SR: none(all banks have to be pre-charged)
        
        # RAS <-> RAS
        t[self.cmd.act].append(TimingEntry(self.cmd.act, 1, s.nRRDS))
        t[self.cmd.act].append(TimingEntry(self.cmd.act, 4, s.nFAW))
        t[self.cmd.act].append(TimingEntry(self.cmd.prea, 1, s.nRAS))
        t[self.cmd.prea].append(TimingEntry(self.cmd.act, 1, s.nRP))
        
        # RAS <-> REF
        t[self.cmd.pre].append(TimingEntry(self.cmd.ref, 1, s.nRP))
        t[self.cmd.prea].append(TimingEntry(self.cmd.ref, 1, s.nRP))
        t[self.cmd.ref].append(TimingEntry(self.cmd.act, 1, s.nRFC))
        
        # RAS <-> PD
        t[self.cmd.act].append(TimingEntry(self.cmd.pde, 1, 1))
        t[self.cmd.pdx].append(TimingEntry(self.cmd.act, 1, s.nXP))
        t[self.cmd.pdx].append(TimingEntry(self.cmd.pre, 1, s.nXP))
        t[self.cmd.pdx].append(TimingEntry(self.cmd.prea, 1, s.nXP))
        
        # RAS <-> SR
        t[self.cmd.pre].append(TimingEntry(self.cmd.sre, 1, s.nRP))
        t[self.cmd.prea].append(TimingEntry(self.cmd.sre, 1, s.nRP))
        t[self.cmd.srx].append(TimingEntry(self.cmd.act, 1, s.nXS))
        
        # REF <-> REF
        t[self.cmd.ref].append(TimingEntry(self.cmd.ref, 1, s.nRFC))
        
        # REF <-> PD
        t[self.cmd.ref].append(TimingEntry(self.cmd.pde, 1, 1))
        t[self.cmd.pdx].append(TimingEntry(self.cmd.ref, 1, s.nXP))
        
        # REF <-> SR
        t[self.cmd.srx].append(TimingEntry(self.cmd.ref, 1, s.nXS))
        
        # PD <-> PD
        t[self.cmd.pde].append(TimingEntry(self.cmd.pdx, 1, s.nPD))
        t[self.cmd.pdx].append(TimingEntry(self.cmd.pde, 1, s.nXP))
        
        # PD <-> SR
        t[self.cmd.pdx].append(TimingEntry(self.cmd.sre, 1, s.nXP))
        t[self.cmd.srx].append(TimingEntry(self.cmd.pde, 1, s.nXS))
        
        # SR <-> SR
        t[self.cmd.sre].append(TimingEntry(self.cmd.srx, 1, s.nCKESR))
        t[self.cmd.srx].append(TimingEntry(self.cmd.sre, 1, s.nXS))
        
        # Bank Group
        t = self.timing[self.level.bankgroup]
        # CAS <-> CAS
        t[self.cmd.rd].append(TimingEntry(self.cmd.rd, 1, s.nCCDL))
        t[self.cmd.rd].append(TimingEntry(self.cmd.rda, 1, s.nCCDL))
        t[self.cmd.rda].append(TimingEntry(self.cmd.rd, 1, s.nCCDL))
        t[self.cmd.rda].append(TimingEntry(self.cmd.rda, 1, s.nCCDL))
        t[self.cmd.wr].append(TimingEntry(self.cmd.wr, 1, s.nCCDL))
        t[self.cmd.wr].append(TimingEntry(self.cmd.wra, 1, s.nCCDL))
        t[self.cmd.wra].append(TimingEntry(self.cmd.wr, 1, s.nCCDL))
        t[self.cmd.wra].append(TimingEntry(self.cmd.wra, 1, s.nCCDL))
        t[self.cmd.wr].append(TimingEntry(self.cmd.wr, 1, s.nCCDL))
        t[self.cmd.wr].append(TimingEntry(self.cmd.wra, 1, s.nCCDL))
        t[self.cmd.wra].append(TimingEntry(self.cmd.wr, 1, s.nCCDL))
        t[self.cmd.wra].append(TimingEntry(self.cmd.wra, 1, s.nCCDL))
        t[self.cmd.wr].append(TimingEntry(self.cmd.rd, 1, s.nCWL + s.nBL + s.nWTRL))
        t[self.cmd.wr].append(TimingEntry(self.cmd.rda, 1, s.nCWL + s.nBL + s.nWTRL))
        t[self.cmd.wra].append(TimingEntry(self.cmd.rd, 1, s.nCWL + s.nBL + s.nWTRL))
        t[self.cmd.wra].append(TimingEntry(self.cmd.rda, 1, s.nCWL + s.nBL + s.nWTRL))
        
        # RAS <-> RAS
        t[self.cmd.act].append(TimingEntry(self.cmd.act, 1, s.nRRDL))
        
        # Bank
        t = self.timing[self.level.bank]
        
        # CAS <-> RAS
        t[self.cmd.act].append(TimingEntry(self.cmd.rd, 1, s.nRCDR))
        t[self.cmd.act].append(TimingEntry(self.cmd.rda, 1, s.nRCDR))
        t[self.cmd.act].append(TimingEntry(self.cmd.wr, 1, s.nRCDW))
        t[self.cmd.act].append(TimingEntry(self.cmd.wra, 1, s.nRCDW))
        
        t[self.cmd.rd].append(TimingEntry(self.cmd.pre, 1, s.nRTP))
        t[self.cmd.wr].append(TimingEntry(self.cmd.pre, 1, s.nCWL + s.nBL + s.nWR))
        
        t[self.cmd.rda].append(TimingEntry(self.cmd.act, 1, s.nRTP + s.nRP))
        t[self.cmd.wra].append(TimingEntry(self.cmd.act, 1, s.nCWL + s.nBL + s.nWR + s.nRP))
        
        # RAS <-> RAS
        t[self.cmd.act].append(TimingEntry(self.cmd.act, 1, s.nRC))
        t[self.cmd.act].append(TimingEntry(self.cmd.pre, 1, s.nRAS))
        t[self.cmd.pre].append(TimingEntry(self.cmd.act, 1, s.nRP))
        
        # REFSB
        t[self.cmd.pre].append(TimingEntry(self.cmd.refsb, 1, s.nRP))
        t[self.cmd.refsb].append(TimingEntry(self.cmd.refsb, 1, s.nRFC))
        t[self.cmd.refsb].append(TimingEntry(self.cmd.act, 1, s.nRFC))
