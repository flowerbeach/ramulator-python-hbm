from typing import Dict, List
from offchip.standard.spec_data_structure import TimingEntry, SpeedEntry, OrgEntry
from configs import strings
from enum import Enum, unique


@unique
class Command(Enum):
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
    MAX = 13


@unique
class Level(Enum):
    channel = 0
    rank = 1
    bankgroup = 2
    bank = 3
    row = 4
    column = 5


class BaseSpec(object):
    from main import Argument
    cmd = Command
    level = Level
    
    name_spec = strings.standard.hbm
    
    # ._num_ranks = args.num_ranks
    # ._num_channels = args.num_channels
    
    start = {Level.channel: None,
             Level.rank: strings.state_powerup,
             Level.bankgroup: None,
             Level.bank: strings.state_closed,
             Level.row: strings.state_closed,
             Level.column: None}
    
    prereq = {l: {c: None for c in Command} for l in Level}
    rowhit = {l: {c: None for c in Command} for l in Level}
    rowopen = {l: {c: None for c in Command} for l in Level}
    lambda_ = {l: {c: None for c in Command} for l in Level}
    timing = {l: {c: [] for c in Command} for l in Level
              }  # type: Dict[str,Dict[str,List[TimingEntry]]]
    
    org_table = {
        strings.org_1Gb: OrgEntry(1 << 10, 128, [0, 0, 4, 2, 1 << 13, 1 << (6 + 1)]),
        strings.org_2Gb: OrgEntry(2 << 10, 128, [0, 0, 4, 2, 1 << 14, 1 << (6 + 1)]),
        strings.org_4Gb: OrgEntry(4 << 10, 128, [0, 0, 4, 4, 1 << 14, 1 << (6 + 1)])}
    org_entry = org_table[Argument.args.org]
    org_entry.count[Level.rank.value] = Argument.args.num_ranks
    org_entry.count[Level.channel.value] = Argument.args.num_channels
    
    speed_table = {
        strings.speed_1Gbps: SpeedEntry(1000, 500, 2.0, 2, 2, 3, 7, 7, 6, 7, 4, 17, 24, 7, 2, 4, 8, 4, 5, 20, 0, 1950, 0, 5, 5, 5, 0)}
    speed_entry = speed_table[Argument.args.speed]
    read_latency = speed_entry.nCL + speed_entry.nBL
    
    prefetch_size = 4  # burst length could be 2 and 4 (choose 4 here), 2n prefetch
    channel_width = 128
    
    scope = [
        Level.row, Level.bank, Level.rank,
        Level.column, Level.column, Level.column, Level.column,
        Level.rank, Level.bank, Level.rank, Level.rank, Level.rank, Level.rank
    ]
    
    from offchip.data_structure import Request
    translate = {Request.Type.read: Command.rd,
                 Request.Type.write: Command.wr,
                 Request.Type.refresh: Command.ref,
                 Request.Type.powerdown: Command.pde,
                 Request.Type.selfrefresh: Command.sre}
    
    @staticmethod
    def initialize():
        assert BaseSpec.Argument.args.name_spec == BaseSpec.name_spec
        
        BaseSpec._init_speed()
        BaseSpec._init_prereq()
        BaseSpec._init_rowhit()
        BaseSpec._init_rowopen()
        BaseSpec._init_lambda()
        BaseSpec._init_timing()
    
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
    
    @staticmethod
    def _init_speed():
        RFC_TABLE = [55, 80, 130]
        REFI1B_TABLE = [64, 128, 256]
        XS_TABLE = [60, 85, 135]
        
        if BaseSpec.speed_entry.rate == 1000:
            speed = 0
        else:
            raise Exception(BaseSpec.speed_entry.rate)
        if BaseSpec.org_entry.size >> 10 == 1:
            density = 0
        elif BaseSpec.org_entry.size >> 10 == 2:
            density = 1
        elif BaseSpec.org_entry.size >> 10 == 4:
            density = 2
        else:
            raise Exception(BaseSpec.org_entry.size)
        len_speed = len(BaseSpec.speed_table)
        BaseSpec.speed_entry.nRFC = RFC_TABLE[speed * len_speed + density]
        BaseSpec.speed_entry.nREFI1B = REFI1B_TABLE[speed * len_speed + density]
        BaseSpec.speed_entry.nXS = XS_TABLE[speed * len_speed + density]
    
    @staticmethod
    def _init_prereq():
        from offchip.dram_module import DRAM
        
        def prereq_rank_rd(node: DRAM, cmd, id_):
            node_state = node.get_state()
            if node_state == strings.state_powerup:
                return None
            elif node_state == strings.state_actpowerdown:
                return BaseSpec.cmd.pdx
            elif node_state == strings.state_prepowerdown:
                return BaseSpec.cmd.pdx
            elif node_state == strings.state_selfrefresh:
                return BaseSpec.cmd.srx
            else:
                raise Exception(node_state)
        
        def prereq_bank_rd(node: DRAM, cmd, id_):
            node_state = node.get_state()
            if node_state == strings.state_closed:
                return BaseSpec.cmd.act
            elif node_state == strings.state_opened:
                if id_ in node.row_state:
                    return cmd
                return BaseSpec.cmd.pre
            else:
                raise Exception(node_state)
        
        def prereq_rank_ref(node: DRAM, cmd, id_):
            for bg in node.children:
                for bank in bg.children:
                    if bank.get_state() == strings.state_closed:
                        continue
                    return BaseSpec.cmd.prea
            return BaseSpec.cmd.ref
        
        def prereq_bank_refsb(node: DRAM, cmd, id_):
            if node.get_state() == strings.state_closed:
                return BaseSpec.cmd.refsb
            return BaseSpec.cmd.pre
        
        def prereq_rank_pde(node: DRAM, cmd, id_):
            node_state = node.get_state()
            if node_state == strings.state_powerup:
                return BaseSpec.cmd.pde
            elif node_state == strings.state_actpowerdown:
                return BaseSpec.cmd.pde
            elif node_state == strings.state_prepowerdown:
                return BaseSpec.cmd.pde
            elif node_state == strings.state_selfrefresh:
                return BaseSpec.cmd.srx
            else:
                raise Exception(node_state)
        
        def prereq_rank_sre(node: DRAM, cmd, id_):
            node_state = node.get_state()
            if node_state == strings.state_powerup:
                return BaseSpec.cmd.sre
            elif node_state == strings.state_actpowerdown:
                return BaseSpec.cmd.pdx
            elif node_state == strings.state_prepowerdown:
                return BaseSpec.cmd.pde
            elif node_state == strings.state_selfrefresh:
                return BaseSpec.cmd.sre
            else:
                raise Exception(node_state)
        
        BaseSpec.prereq[BaseSpec.level.bank][BaseSpec.cmd.rd] = prereq_bank_rd
        BaseSpec.prereq[BaseSpec.level.rank][BaseSpec.cmd.rd] = prereq_rank_rd
        BaseSpec.prereq[BaseSpec.level.bank][BaseSpec.cmd.wr] = prereq_bank_rd
        BaseSpec.prereq[BaseSpec.level.rank][BaseSpec.cmd.wr] = prereq_rank_rd
        
        BaseSpec.prereq[BaseSpec.level.rank][BaseSpec.cmd.ref] = prereq_rank_ref
        BaseSpec.prereq[BaseSpec.level.bank][BaseSpec.cmd.refsb] = prereq_bank_refsb
        BaseSpec.prereq[BaseSpec.level.rank][BaseSpec.cmd.pde] = prereq_rank_pde
        BaseSpec.prereq[BaseSpec.level.rank][BaseSpec.cmd.sre] = prereq_rank_sre
    
    @staticmethod
    def _init_rowhit():
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
        
        BaseSpec.rowhit[BaseSpec.level.bank][BaseSpec.cmd.rd] = rowhit
        BaseSpec.rowhit[BaseSpec.level.bank][BaseSpec.cmd.wr] = rowhit
    
    @staticmethod
    def _init_rowopen():
        from offchip.dram_module import DRAM
        
        def rowopen(node: DRAM, cmd, id_):
            node_state = node.get_state()
            if node_state == strings.state_closed:
                return False
            elif node_state == strings.state_opened:
                return True
            else:
                raise Exception(node_state)
        
        BaseSpec.rowopen[BaseSpec.level.bank][BaseSpec.cmd.rd] = rowopen
        BaseSpec.rowopen[BaseSpec.level.bank][BaseSpec.cmd.wr] = rowopen
    
    @staticmethod
    def _init_lambda():
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
        
        BaseSpec.lambda_[BaseSpec.level.bank][BaseSpec.cmd.act] = lambda_bank_act
        BaseSpec.lambda_[BaseSpec.level.bank][BaseSpec.cmd.pre] = lambda_bank_pre
        BaseSpec.lambda_[BaseSpec.level.rank][BaseSpec.cmd.prea] = lambda_rank_prea
        BaseSpec.lambda_[BaseSpec.level.rank][BaseSpec.cmd.ref] = lambda_rank_ref
        BaseSpec.lambda_[BaseSpec.level.bank][BaseSpec.cmd.rd] = lambda_bank_rd
        BaseSpec.lambda_[BaseSpec.level.bank][BaseSpec.cmd.wr] = lambda_bank_wr
        BaseSpec.lambda_[BaseSpec.level.bank][BaseSpec.cmd.rda] = lambda_bank_pre
        BaseSpec.lambda_[BaseSpec.level.bank][BaseSpec.cmd.wra] = lambda_bank_pre
        BaseSpec.lambda_[BaseSpec.level.rank][BaseSpec.cmd.pde] = lambda_rank_pde
        BaseSpec.lambda_[BaseSpec.level.rank][BaseSpec.cmd.pdx] = lambda_rank_pdx
        BaseSpec.lambda_[BaseSpec.level.rank][BaseSpec.cmd.sre] = lambda_rank_sre
        BaseSpec.lambda_[BaseSpec.level.rank][BaseSpec.cmd.srx] = lambda_rank_pdx
    
    @staticmethod
    def _init_timing():
        s = BaseSpec.speed_entry
        # Channel
        t = BaseSpec.timing[BaseSpec.level.channel]
        
        # CAS <-> CAS
        t[BaseSpec.cmd.rd].append(TimingEntry(BaseSpec.cmd.rd, 1, s.nBL))
        t[BaseSpec.cmd.rd].append(TimingEntry(BaseSpec.cmd.rda, 1, s.nBL))
        t[BaseSpec.cmd.rda].append(TimingEntry(BaseSpec.cmd.rd, 1, s.nBL))
        t[BaseSpec.cmd.rda].append(TimingEntry(BaseSpec.cmd.rda, 1, s.nBL))
        t[BaseSpec.cmd.wr].append(TimingEntry(BaseSpec.cmd.wr, 1, s.nBL))
        t[BaseSpec.cmd.wr].append(TimingEntry(BaseSpec.cmd.wra, 1, s.nBL))
        t[BaseSpec.cmd.wra].append(TimingEntry(BaseSpec.cmd.wr, 1, s.nBL))
        t[BaseSpec.cmd.wra].append(TimingEntry(BaseSpec.cmd.wra, 1, s.nBL))
        
        # Rank
        t = BaseSpec.timing[BaseSpec.level.rank]
        
        # CAS <-> CAS
        t[BaseSpec.cmd.rd].append(TimingEntry(BaseSpec.cmd.rd, 1, s.nCCDS))
        t[BaseSpec.cmd.rd].append(TimingEntry(BaseSpec.cmd.rda, 1, s.nCCDS))
        t[BaseSpec.cmd.rda].append(TimingEntry(BaseSpec.cmd.rd, 1, s.nCCDS))
        t[BaseSpec.cmd.rda].append(TimingEntry(BaseSpec.cmd.rda, 1, s.nCCDS))
        t[BaseSpec.cmd.wr].append(TimingEntry(BaseSpec.cmd.wr, 1, s.nCCDS))
        t[BaseSpec.cmd.wr].append(TimingEntry(BaseSpec.cmd.wra, 1, s.nCCDS))
        t[BaseSpec.cmd.wra].append(TimingEntry(BaseSpec.cmd.wr, 1, s.nCCDS))
        t[BaseSpec.cmd.wra].append(TimingEntry(BaseSpec.cmd.wra, 1, s.nCCDS))
        t[BaseSpec.cmd.rd].append(TimingEntry(BaseSpec.cmd.wr, 1, s.nCL + s.nCCDS + 2 - s.nCWL))
        t[BaseSpec.cmd.rd].append(TimingEntry(BaseSpec.cmd.wra, 1, s.nCL + s.nCCDS + 2 - s.nCWL))
        t[BaseSpec.cmd.rda].append(TimingEntry(BaseSpec.cmd.wr, 1, s.nCL + s.nCCDS + 2 - s.nCWL))
        t[BaseSpec.cmd.rda].append(TimingEntry(BaseSpec.cmd.wra, 1, s.nCL + s.nCCDS + 2 - s.nCWL))
        t[BaseSpec.cmd.wr].append(TimingEntry(BaseSpec.cmd.rd, 1, s.nCWL + s.nBL + s.nWTRS))
        t[BaseSpec.cmd.wr].append(TimingEntry(BaseSpec.cmd.rda, 1, s.nCWL + s.nBL + s.nWTRS))
        t[BaseSpec.cmd.wra].append(TimingEntry(BaseSpec.cmd.rd, 1, s.nCWL + s.nBL + s.nWTRS))
        t[BaseSpec.cmd.wra].append(TimingEntry(BaseSpec.cmd.rda, 1, s.nCWL + s.nBL + s.nWTRS))
        
        t[BaseSpec.cmd.rd].append(TimingEntry(BaseSpec.cmd.prea, 1, s.nRTP))
        t[BaseSpec.cmd.wr].append(TimingEntry(BaseSpec.cmd.prea, 1, s.nCWL + s.nBL + s.nWR))
        
        # CAS <-> PD
        t[BaseSpec.cmd.rd].append(TimingEntry(BaseSpec.cmd.pde, 1, s.nCL + s.nBL + 1))
        t[BaseSpec.cmd.rda].append(TimingEntry(BaseSpec.cmd.pde, 1, s.nCL + s.nBL + 1))
        t[BaseSpec.cmd.wr].append(TimingEntry(BaseSpec.cmd.pde, 1, s.nCWL + s.nBL + s.nWR))
        t[BaseSpec.cmd.wra].append(TimingEntry(BaseSpec.cmd.pde, 1, s.nCWL + s.nBL + s.nWR + 1))  # +1 for pre
        t[BaseSpec.cmd.pdx].append(TimingEntry(BaseSpec.cmd.rd, 1, s.nXP))
        t[BaseSpec.cmd.pdx].append(TimingEntry(BaseSpec.cmd.rda, 1, s.nXP))
        t[BaseSpec.cmd.pdx].append(TimingEntry(BaseSpec.cmd.wr, 1, s.nXP))
        t[BaseSpec.cmd.pdx].append(TimingEntry(BaseSpec.cmd.wra, 1, s.nXP))
        
        # CAS <-> SR: none(all banks have to be pre-charged)
        
        # RAS <-> RAS
        t[BaseSpec.cmd.act].append(TimingEntry(BaseSpec.cmd.act, 1, s.nRRDS))
        t[BaseSpec.cmd.act].append(TimingEntry(BaseSpec.cmd.act, 4, s.nFAW))
        t[BaseSpec.cmd.act].append(TimingEntry(BaseSpec.cmd.prea, 1, s.nRAS))
        t[BaseSpec.cmd.prea].append(TimingEntry(BaseSpec.cmd.act, 1, s.nRP))
        
        # RAS <-> REF
        t[BaseSpec.cmd.pre].append(TimingEntry(BaseSpec.cmd.ref, 1, s.nRP))
        t[BaseSpec.cmd.prea].append(TimingEntry(BaseSpec.cmd.ref, 1, s.nRP))
        t[BaseSpec.cmd.ref].append(TimingEntry(BaseSpec.cmd.act, 1, s.nRFC))
        
        # RAS <-> PD
        t[BaseSpec.cmd.act].append(TimingEntry(BaseSpec.cmd.pde, 1, 1))
        t[BaseSpec.cmd.pdx].append(TimingEntry(BaseSpec.cmd.act, 1, s.nXP))
        t[BaseSpec.cmd.pdx].append(TimingEntry(BaseSpec.cmd.pre, 1, s.nXP))
        t[BaseSpec.cmd.pdx].append(TimingEntry(BaseSpec.cmd.prea, 1, s.nXP))
        
        # RAS <-> SR
        t[BaseSpec.cmd.pre].append(TimingEntry(BaseSpec.cmd.sre, 1, s.nRP))
        t[BaseSpec.cmd.prea].append(TimingEntry(BaseSpec.cmd.sre, 1, s.nRP))
        t[BaseSpec.cmd.srx].append(TimingEntry(BaseSpec.cmd.act, 1, s.nXS))
        
        # REF <-> REF
        t[BaseSpec.cmd.ref].append(TimingEntry(BaseSpec.cmd.ref, 1, s.nRFC))
        
        # REF <-> PD
        t[BaseSpec.cmd.ref].append(TimingEntry(BaseSpec.cmd.pde, 1, 1))
        t[BaseSpec.cmd.pdx].append(TimingEntry(BaseSpec.cmd.ref, 1, s.nXP))
        
        # REF <-> SR
        t[BaseSpec.cmd.srx].append(TimingEntry(BaseSpec.cmd.ref, 1, s.nXS))
        
        # PD <-> PD
        t[BaseSpec.cmd.pde].append(TimingEntry(BaseSpec.cmd.pdx, 1, s.nPD))
        t[BaseSpec.cmd.pdx].append(TimingEntry(BaseSpec.cmd.pde, 1, s.nXP))
        
        # PD <-> SR
        t[BaseSpec.cmd.pdx].append(TimingEntry(BaseSpec.cmd.sre, 1, s.nXP))
        t[BaseSpec.cmd.srx].append(TimingEntry(BaseSpec.cmd.pde, 1, s.nXS))
        
        # SR <-> SR
        t[BaseSpec.cmd.sre].append(TimingEntry(BaseSpec.cmd.srx, 1, s.nCKESR))
        t[BaseSpec.cmd.srx].append(TimingEntry(BaseSpec.cmd.sre, 1, s.nXS))
        
        # Bank Group
        t = BaseSpec.timing[BaseSpec.level.bankgroup]
        # CAS <-> CAS
        t[BaseSpec.cmd.rd].append(TimingEntry(BaseSpec.cmd.rd, 1, s.nCCDL))
        t[BaseSpec.cmd.rd].append(TimingEntry(BaseSpec.cmd.rda, 1, s.nCCDL))
        t[BaseSpec.cmd.rda].append(TimingEntry(BaseSpec.cmd.rd, 1, s.nCCDL))
        t[BaseSpec.cmd.rda].append(TimingEntry(BaseSpec.cmd.rda, 1, s.nCCDL))
        t[BaseSpec.cmd.wr].append(TimingEntry(BaseSpec.cmd.wr, 1, s.nCCDL))
        t[BaseSpec.cmd.wr].append(TimingEntry(BaseSpec.cmd.wra, 1, s.nCCDL))
        t[BaseSpec.cmd.wra].append(TimingEntry(BaseSpec.cmd.wr, 1, s.nCCDL))
        t[BaseSpec.cmd.wra].append(TimingEntry(BaseSpec.cmd.wra, 1, s.nCCDL))
        t[BaseSpec.cmd.wr].append(TimingEntry(BaseSpec.cmd.wr, 1, s.nCCDL))
        t[BaseSpec.cmd.wr].append(TimingEntry(BaseSpec.cmd.wra, 1, s.nCCDL))
        t[BaseSpec.cmd.wra].append(TimingEntry(BaseSpec.cmd.wr, 1, s.nCCDL))
        t[BaseSpec.cmd.wra].append(TimingEntry(BaseSpec.cmd.wra, 1, s.nCCDL))
        t[BaseSpec.cmd.wr].append(TimingEntry(BaseSpec.cmd.rd, 1, s.nCWL + s.nBL + s.nWTRL))
        t[BaseSpec.cmd.wr].append(TimingEntry(BaseSpec.cmd.rda, 1, s.nCWL + s.nBL + s.nWTRL))
        t[BaseSpec.cmd.wra].append(TimingEntry(BaseSpec.cmd.rd, 1, s.nCWL + s.nBL + s.nWTRL))
        t[BaseSpec.cmd.wra].append(TimingEntry(BaseSpec.cmd.rda, 1, s.nCWL + s.nBL + s.nWTRL))
        
        # RAS <-> RAS
        t[BaseSpec.cmd.act].append(TimingEntry(BaseSpec.cmd.act, 1, s.nRRDL))
        
        # Bank
        t = BaseSpec.timing[BaseSpec.level.bank]
        
        # CAS <-> RAS
        t[BaseSpec.cmd.act].append(TimingEntry(BaseSpec.cmd.rd, 1, s.nRCDR))
        t[BaseSpec.cmd.act].append(TimingEntry(BaseSpec.cmd.rda, 1, s.nRCDR))
        t[BaseSpec.cmd.act].append(TimingEntry(BaseSpec.cmd.wr, 1, s.nRCDW))
        t[BaseSpec.cmd.act].append(TimingEntry(BaseSpec.cmd.wra, 1, s.nRCDW))
        
        t[BaseSpec.cmd.rd].append(TimingEntry(BaseSpec.cmd.pre, 1, s.nRTP))
        t[BaseSpec.cmd.wr].append(TimingEntry(BaseSpec.cmd.pre, 1, s.nCWL + s.nBL + s.nWR))
        
        t[BaseSpec.cmd.rda].append(TimingEntry(BaseSpec.cmd.act, 1, s.nRTP + s.nRP))
        t[BaseSpec.cmd.wra].append(TimingEntry(BaseSpec.cmd.act, 1, s.nCWL + s.nBL + s.nWR + s.nRP))
        
        # RAS <-> RAS
        t[BaseSpec.cmd.act].append(TimingEntry(BaseSpec.cmd.act, 1, s.nRC))
        t[BaseSpec.cmd.act].append(TimingEntry(BaseSpec.cmd.pre, 1, s.nRAS))
        t[BaseSpec.cmd.pre].append(TimingEntry(BaseSpec.cmd.act, 1, s.nRP))
        
        # REFSB
        t[BaseSpec.cmd.pre].append(TimingEntry(BaseSpec.cmd.refsb, 1, s.nRP))
        t[BaseSpec.cmd.refsb].append(TimingEntry(BaseSpec.cmd.refsb, 1, s.nRFC))
        t[BaseSpec.cmd.refsb].append(TimingEntry(BaseSpec.cmd.act, 1, s.nRFC))
